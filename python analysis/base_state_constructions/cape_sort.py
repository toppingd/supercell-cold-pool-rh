# -*- coding: utf-8 -*-

import os
import csv
import math
import shutil
from typing import Dict, List, Optional, Tuple

import numpy as np
from sharppy.sharptab.profile import create_profile
from sharppy.sharptab import params


RH_FOLDERS = [
    'moistPBL_moistFT',
    'moistPBL_dryFT',
    'dryPBL_moistFT',
    'dryPBL_dryFT',
]

CAPE_TARGETS = {
    'lowCAPE': 1500.0,
    'moderateCAPE': 2500.0,
    'highCAPE': 3500.0,
}


def parse_sharppy_text(file_path: str) -> Dict[str, np.ndarray]:
    pres = []
    hght = []
    tmpc = []
    dwpc = []
    wdir = []
    wspd = []

    in_raw = False
    with open(file_path, 'r', encoding='utf-8') as f:
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


def compute_mlcape(pres: np.ndarray, hght: np.ndarray, tmpc: np.ndarray, dwpc: np.ndarray,
                   wdir: np.ndarray, wspd: np.ndarray) -> Optional[float]:

    prof = create_profile(pres=pres, hght=hght, tmpc=tmpc, dwpc=dwpc,
                          wdir=wdir, wspd=wspd, strict=False)
    mlpcl = params.parcelx(prof, flag=4)  # 100 mb Mean Layer Parcel
    mlcape = mlpcl.bplus
    mlcin = mlpcl.bminus

    if mlcape is None or (isinstance(mlcape, float) and np.isnan(mlcape)):
        return None
    return float(mlcape), float(mlcin)


def nearest_cape_category(mlcape: float) -> str:
    diffs = {cat: abs(mlcape - target) for cat, target in CAPE_TARGETS.items()}
    best = sorted(diffs.items(), key=lambda kv: (kv[1], -CAPE_TARGETS[kv[0]]))[0][0]
    return best


def process_folder(rh_dir: str, move_files: bool) -> str:
    for cat in CAPE_TARGETS.keys():
        os.makedirs(os.path.join(rh_dir, cat), exist_ok=True)

    files = [f for f in os.listdir(rh_dir) if os.path.isfile(os.path.join(rh_dir, f))]

    results: List[Dict[str, str]] = []
    for fname in sorted(files):
        src = os.path.join(rh_dir, fname)
        try:
            data = parse_sharppy_text(src)
            mlcape,mlcin = compute_mlcape(data['pres'], data['hght'], data['tmpc'], data['dwpc'], data['wdir'], data['wspd'])
            if mlcape is None:
                results.append({'file': fname, 'mlcape': '', 'mlcin':'',
                                'cape_category': '', 'action': 'skipped', 'error': 'MLCAPE unavailable'})
                continue
            cape_cat = nearest_cape_category(mlcape)
            dst = os.path.join(rh_dir, cape_cat, fname)
            if move_files:
                shutil.move(src, dst)
                action = 'moved'
            else:
                shutil.copy2(src, dst)
                action = 'copied'
            results.append({'file': fname, 'mlcape': f"{mlcape:.1f}", 'mlcin': f"{mlcin:.1f}",
                            'cape_category': cape_cat, 'action': action, 'error': ''})
        except Exception as e:
            results.append({'file': fname, 'mlcape': '', 'mlcin':'',
                            'cape_category': '', 'action': 'error', 'error': str(e)})

    summary_csv = os.path.join(rh_dir, 'mlcape_sort_summary.csv')
    with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['file', 'mlcape', 'mlcin', 'cape_category', 'action', 'error'])
        for r in results:
            w.writerow([r['file'], r['mlcape'], r['mlcin'], r['cape_category'], r['action'], r['error']])
    return summary_csv


def sort_within_rh_root(root_dir: str, move_files: bool) -> str:
    master_rows: List[List[str]] = []
    header = ['rh_folder', 'file', 'mlcape', 'mlcin', 'cape_category', 'action', 'error']

    for rh_folder in ['moistPBL_moistFT','moistPBL_dryFT','dryPBL_moistFT','dryPBL_dryFT']:
        full = os.path.join(root_dir, rh_folder)
        if not os.path.isdir(full):
            continue
        print(f'Processing {full}')
        folder_csv = process_folder(full, move_files)

        with open(folder_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                master_rows.append([rh_folder] + row)


    master_csv = os.path.join(root_dir, 'mlcape_sort_master_summary.csv')
    with open(master_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(master_rows)


def main():
    root_dir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/adjusted_soundings'
    move_files = True

    sort_within_rh_root(root_dir, move_files)


if __name__ == '__main__':
    main()
