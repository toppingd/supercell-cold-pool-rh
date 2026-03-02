# -*- coding: utf-8 -*-

"""
Classify SHARPpy-style sounding text files by relative humidity (RH) regimes in the
Planetary Boundary Layer (PBL) and Free Troposphere (FT).

- Uses the Mixed-Layer LFC (MLLFC) height as a proxy for PBL depth when SHARPpy is available.
- Bounds the FT layer between MLLFC and the Mixed-Layer Equilibrium Level (MLEL).
- Computes the mean RH in the PBL (<= MLLFC height) and in the FT (MLLFC < z <= MLEL) for each file.
- Across the collection, determines tertile thresholds (67th percentile) separately for PBL and FT
  mean RH distributions.
- Sorts files into folders: `moistPBL_moistFT`, `moistPBL_dryFT`, `dryPBL_moistFT`, `dryPBL_dryFT`.
- Writes a summary CSV with per-file metrics and the thresholds used.
"""


import os
import csv
import math
import shutil
from typing import Dict, List, Optional, Tuple

import numpy as np
from metpy.calc import relative_humidity_from_dewpoint
from metpy.units import units
from sharppy.sharptab.profile import create_profile
from sharppy.sharptab import params


def parse_sharppy_text(file_path: str) -> Dict[str, np.ndarray]:
    pres = []
    hght = []
    tmpc = []
    dwpc = []
    wdir = []
    wspd = []

    in_raw = False
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not in_raw:
                if line.startswith('%RAW%'):
                    in_raw = True
                continue
            if line.startswith('%END%'):
                break
            if not line:
                continue
            parts = [p.strip() for p in line.split(',')]

            p = float(parts[0])
            z = float(parts[1])
            t = float(parts[2])
            td_str = parts[3]
            td = float(td_str) if td_str.lower() != 'nan' else math.nan
            wd = float(parts[4])
            ws = float(parts[5])

            pres.append(p)
            hght.append(z)
            tmpc.append(t)
            dwpc.append(td)
            wdir.append(wd)
            wspd.append(ws)

    if len(pres) == 0:
        raise ValueError(f"No %RAW% data found in '{file_path}'.")

    return {
        'pres': np.array(pres, dtype=float),
        'hght': np.array(hght, dtype=float),
        'tmpc': np.array(tmpc, dtype=float),
        'dwpc': np.array(dwpc, dtype=float),
        'wdir': np.array(wdir, dtype=float),
        'wspd': np.array(wspd, dtype=float),
    }


def compute_rh_fraction(tmpc: np.ndarray, dwpc: np.ndarray) -> np.ndarray:
    mask_valid = ~np.isnan(dwpc) & ~np.isnan(tmpc)
    rh = np.full_like(tmpc, np.nan, dtype=float)

    T = (tmpc[mask_valid] * units.degC).to('kelvin')
    Td = (dwpc[mask_valid] * units.degC).to('kelvin')
    rh_metpy = relative_humidity_from_dewpoint(T, Td)
    rh[mask_valid] = np.asarray(rh_metpy.m)
    return rh


def get_mlpbl_bounds(pres: np.ndarray, hght: np.ndarray, tmpc: np.ndarray, dwpc: np.ndarray,
                     wdir: np.ndarray, wspd: np.ndarray) -> Tuple[Optional[float], Optional[float]]:
    """Return Mixed-Layer LFC and EL heights (m) using SHARPpy if available; else (None, None)."""

    prof = create_profile(pres=pres, hght=hght, tmpc=tmpc, dwpc=dwpc,
                          wdir=wdir, wspd=wspd, strict=False)
    mlpcl = params.parcelx(prof,flag=4) # 100 mb Mean Layer Parcel
    mllfc_hgt = mlpcl.lfchght
    mlel_hgt = mlpcl.elhght

    if mllfc_hgt is None or (isinstance(mllfc_hgt, float) and np.isnan(mllfc_hgt)):
        mllfc_hgt = None
    if mlel_hgt is None or (isinstance(mlel_hgt, float) and np.isnan(mlel_hgt)):
        mlel_hgt = None
    return (None if mllfc_hgt is None else float(mllfc_hgt),
            None if mlel_hgt is None else float(mlel_hgt))


def layer_mean(values: np.ndarray, layer_mask: np.ndarray) -> float:
    if not np.any(layer_mask):
        return float('nan')
    return float(np.nanmedian(values[layer_mask]))


def process_file(file_path: str, default_pbl_height_m: float, default_el_height_m:float) -> Dict[str, float]:
    data = parse_sharppy_text(file_path)

    pres = data['pres']
    hght = data['hght']
    tmpc = data['tmpc']
    dwpc = data['dwpc']
    wdir = data['wdir']
    wspd = data['wspd']

    rh_frac = compute_rh_fraction(tmpc, dwpc)
    mllfc_hgt, mlel_hgt = get_mlpbl_bounds(pres, hght, tmpc, dwpc, wdir, wspd)

    if mllfc_hgt is None or np.isnan(mllfc_hgt):
        print('using default pbl height')
        mllfc_hgt = float(default_pbl_height_m)

    if mlel_hgt is None or np.isnan(mlel_hgt):
        print('using default el height')
        mlel_hgt = float(default_el_height_m)

    pbl_mask = (hght <= mllfc_hgt)
    ft_mask = (hght > mllfc_hgt) & (hght <= mlel_hgt)

    pbl_mean_rh = layer_mean(rh_frac, pbl_mask)
    ft_mean_rh = layer_mean(rh_frac, ft_mask)

    return {
        'file': os.path.basename(file_path),
        'mllfc_hgt_m': mllfc_hgt,
        'mlel_hgt_m': mlel_hgt,
        'pbl_mean_rh': pbl_mean_rh,
        'ft_mean_rh': ft_mean_rh,
    }


def classify_all(input_dir: str, output_dir: str, move_files: bool, default_pbl_height_m: float,
                 default_el_height_m: float) -> str:

    print(f'Computing sounding rh statistics for {input_dir}')
    os.makedirs(output_dir, exist_ok=True)

    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir)
             if os.path.isfile(os.path.join(input_dir, f))]
    if len(files) == 0:
        raise RuntimeError(f"No files found in '{input_dir}'.")

    results: List[Dict[str, float]] = []
    for fp in sorted(files):
        print(f'Processing {fp}')
        try:
            res = process_file(fp, default_pbl_height_m, default_el_height_m)
            results.append(res)
        except Exception as e:
            results.append({'file': os.path.basename(fp), 'mllfc_hgt_m': float('nan'),
                            'mlel_hgt_m': float('nan'),
                            'pbl_mean_rh': float('nan'), 'ft_mean_rh': float('nan'),
                            'error': str(e)})

    print(f'Sorting files')

    pbl_values = np.array([r['pbl_mean_rh'] for r in results], dtype=float)
    ft_values = np.array([r['ft_mean_rh'] for r in results], dtype=float)

    pbl_clean = pbl_values[~np.isnan(pbl_values)]
    ft_clean = ft_values[~np.isnan(ft_values)]

    if pbl_clean.size == 0 or ft_clean.size == 0:
        raise RuntimeError('Insufficient valid RH data to compute tertiles.')

    pbl_thresh = float(np.percentile(pbl_clean, 66.6667))
    ft_thresh = float(np.percentile(ft_clean, 66.6667))

    folder_map = {
        ('moist', 'moist'): 'moistPBL_moistFT',
        ('moist', 'dry'): 'moistPBL_dryFT',
        ('dry', 'moist'): 'dryPBL_moistFT',
        ('dry', 'dry'): 'dryPBL_dryFT',
    }
    for folder in set(folder_map.values()):
        os.makedirs(os.path.join(output_dir, folder), exist_ok=True)

    for r in results:
        pbl_state = 'moist' if (not np.isnan(r['pbl_mean_rh']) and r['pbl_mean_rh'] >= pbl_thresh) else 'dry'
        ft_state = 'moist' if (not np.isnan(r['ft_mean_rh']) and r['ft_mean_rh'] >= ft_thresh) else 'dry'
        final_folder = folder_map[(pbl_state, ft_state)]
        src = os.path.join(input_dir, r['file'])
        dst = os.path.join(output_dir, final_folder, r['file'])

        if move_files:
            shutil.move(src, dst)
        else:
            shutil.copy2(src, dst)

        r['pbl_class'] = pbl_state
        r['ft_class'] = ft_state
        r['final_folder'] = final_folder

    summary_csv = os.path.join(output_dir, 'rh_classification_summary.csv')
    with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'file', 'lfc_hgt_m', 'el_hgt_m', 'pbl_mean_rh', 'ft_mean_rh',
            'pbl_tertile_threshold', 'ft_tertile_threshold', 'pbl_class', 'ft_class', 'final_folder', 'error'
        ])
        for r in results:
            writer.writerow([
                r.get('file'),
                r.get('lfc_hgt_m'),
                r.get('lel_hgt_m'),
                r.get('pbl_mean_rh'),
                r.get('ft_mean_rh'),
                pbl_thresh,
                ft_thresh,
                r.get('pbl_class'),
                r.get('ft_class'),
                r.get('final_folder'),
                r.get('error', '')
            ])


def main():
    indir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/adjusted_soundings'
    outdir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/adjusted_soundings'
    default_pbl_height = 1500.0 # when MLLFC is unavailable
    default_el_height = 12000.0 # when MLEL is unavailable
    move_files = False

    classify_all(indir, outdir, move_files, default_pbl_height, default_el_height)


if __name__ == '__main__':
    main()
