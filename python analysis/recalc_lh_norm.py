
import os
import numpy as np
import xarray as xr
import dask
from pathlib import Path
import argparse

from zarr.codecs.numcodecs import Blosc
from dask.diagnostics import ProgressBar

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='zarr')

# Dask config
dask.config.set({'array.chunk-size': '128MiB'})
os.environ.setdefault('DASK_TEMPORARY_DIRECTORY', '/storm/topping/tmp/dask-tmp')


def create_file_list(analysis_dir, sf, ef):

    analysis_dir = Path(analysis_dir)
    all_files = sorted(analysis_dir.glob('derived_vars_000*.zarr'))

    if not all_files:
        raise RuntimeError(f'No zarr files in {analysis_dir}')

    selected_files = []
    for f in all_files:
        try:
            num = int(f.stem.split('_')[-1])
        except ValueError:
            continue
        if sf <= num <= ef:
            selected_files.append(f)

    if not selected_files:
        raise RuntimeError(f'No files found in range {sf}–{ef}')

    return selected_files


def calc_latent_cooling(
        ds,
        *,
        w_thresh=1.0,
        density_var='rho',
        q_names=('qc', 'qr', 'qi', 'qs', 'qg', 'qhl')
):

    sub = ds

    w = sub['winterp'].values
    total_mass = sub['total_hydro_mass'].values
    lh = sub['ptb_mp'].values

    safe = (total_mass > 0 + 1e-6) & (w < w_thresh)  # only want values outside the updraft

    lh_norm = np.full_like(lh, np.nan, dtype=np.float32)
    np.divide(lh, total_mass, out=lh_norm, where=safe)

    ds_out = xr.Dataset(
        {
            'lh_norm2': xr.DataArray(
                lh_norm,
                dims=sub['ptb_mp'].dims,
                coords=sub['ptb_mp'].coords,
            ),
        }
    )

    ds_out['lh_norm2'].attrs.update({
        'long_name': 'latent heating normalized by hydrometeor mass',
        'units': 'K s-1 kg-1'
    })

    return ds_out


def update_zarr(ds_out, outdir, outfile):

    outdir.mkdir(parents=True, exist_ok=True)
    outpath = f'{outdir}/{outfile}.zarr'

    ds_cp = ds_out[['lh_norm2']]

    delayed = ds_cp.to_zarr(
        outpath,
        mode='a',
        compute=False,
        zarr_version=3,
        consolidated=False,
    )

    with ProgressBar():
        dask.compute(delayed)

    return


def main(exp_dir):
# def main():

    # exp_dir = '/storm/topping/cold_pools/runs/2500_core'
    # exp_dir = '/storm/topping/cold_pools/runs/1500_core'
    # exp_dir = '/storm/topping/cold_pools/runs/3500_core'

    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set1'
    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set2'
    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set3'
    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set4'

    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set1'
    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set2'
    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set3'
    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set4'

    # exp_dir = '/storm/topping/cold_pools/runs/lowCAPE/set1'
    # exp_dir = '/storm/topping/cold_pools/runs/lowCAPE/set2'

    # exp_dir = '/storm/topping/cold_pools/runs/nssl3'
    # exp_dir = '/storm/topping/cold_pools/runs/morrison'

    # exp_dir = '/storm/topping/cold_pools/runs/sigtor'

    # exp_dir = '/storm/topping/cold_pools/runs/freeslip'

    # exp_dir = '/storm/topping/cold_pools/runs/random_pert/set1'
    # exp_dir = '/storm/topping/cold_pools/runs/random_pert/set2'
    # exp_dir = '/storm/topping/cold_pools/runs/random_pert/set3'
    # exp_dir = '/storm/topping/cold_pools/runs/random_pert/set4'
    # exp_dir = '/storm/topping/cold_pools/runs/random_pert/set5'

    exp_dir = Path(exp_dir)
    print(f'Experiment directory: {exp_dir}')

    st = 90  # start time
    et = 180  # end time

    ft = 45  # first time after initialization
    ff = 2  # number of first file after initialization
    dt = 1  # large timestep (minutes)
    i1 = int((st - ft) / dt)
    i2 = int((et - ft) / dt)
    sf = i1 + ff
    ef = i2 + ff

    regimes = ['mm', 'md', 'dm', 'dd']

    for regime in regimes:

        print(f'\t{regime}:')

        sim_dir = exp_dir / regime
        analysis_dir = sim_dir / 'derived_vars'
        outdir = analysis_dir

        file_list = create_file_list(analysis_dir, sf, ef)

        for i, f in enumerate(file_list):
            print(f'\t\t- Processing {f}...')

            outfile = f.stem

            with xr.open_zarr(
                    f,
                    zarr_format=3,
                    consolidated=False,
                    decode_timedelta=False
            ) as ds:

                ds_lh = calc_latent_cooling(ds)

            print(f'\t\t- Writing to {outfile}')

            update_zarr(ds_lh, outdir, outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process CM1 outputs and write derived variables.'
    )
    parser.add_argument(
        '--sim_dir',
        type=str,
        required=True,
        help='Path to the simulation directory containing "run"'
    )

    args = parser.parse_args()
    main(args.sim_dir)
    # main()



