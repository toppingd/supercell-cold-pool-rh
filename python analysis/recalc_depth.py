

import os
import numpy as np
import xarray as xr
import dask
from pathlib import Path

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


def calc_cp_depth(ds):

    # cp = ds['cp_clean']
    #
    # cp_mask = cp <= -0.01
    #
    # valid = xr.where(cp_mask, np.isfinite(cp), False)
    # valid_np = valid.astype(np.int8).values  # shape: (T, Z, Y, X)
    #
    # # Cumulative product along Z turns True-run-from-bottom into 1s until first 0, then 0s
    # cum = np.cumprod(valid_np, axis=1, dtype=np.int16)  # (T, Z, Y, X)
    # runlen = np.sum(cum, axis=1)                       # (T, Y, X) = length of True run from surface
    #
    # # Map run length to height: depth=0 if runlen==0 else zh[runlen-1]
    # zh_vals = cp['zh'].values
    # T, Y, X = runlen.shape
    # depth = np.zeros((T, Y, X), dtype=zh_vals.dtype)
    #
    # mask_pos = runlen > 0
    # idx = np.maximum(runlen - 1, 0)  # safe index; only used where mask_pos is True
    #
    # # Vectorized lookup zh[idx] per (t,y,x)
    # flat_mask = mask_pos.ravel()
    # flat_idx  = idx.ravel()
    # depth_flat = depth.ravel()
    # depth_flat[flat_mask] = zh_vals[flat_idx[flat_mask]]
    # depth = depth_flat.reshape((T, Y, X))

    cp = ds['cp_clean']
    cp_mask = cp <= -0.01
    valid = xr.where(cp_mask, np.isfinite(cp), False)
    valid_np = valid.values.astype(bool)
    T, Z, Y, X = valid_np.shape

    bad = ~valid_np
    bad_int = bad.astype(np.int16)

    # Compute consecutive-bad run length by scanning upward.
    run_bad = np.zeros_like(bad_int, dtype=np.int16)
    run_bad[:, 0, :, :] = bad_int[:, 0, :, :]

    for k in range(1, Z):
        curr_bad = bad_int[:, k, :, :]  # 1 if bad, 0 if good
        prev_bad = bad_int[:, k - 1, :, :]  # 1 if previous level bad

        # extend where current bad and previous bad
        extend = (curr_bad == 1) & (prev_bad == 1)
        # new sequence where current bad and previous good
        newseq = (curr_bad == 1) & (prev_bad == 0)

        run_bad[:, k, :, :] = 0
        run_bad[:, k, :, :][extend] = run_bad[:, k - 1, :, :][extend] + 1
        run_bad[:, k, :, :][newseq] = 1

    breaker = run_bad > 2 # set int to desired gap depth

    any_break = np.any(breaker, axis=1)  # (T, Y, X)
    first_break_idx = np.argmax(breaker, axis=1)

    last_valid_index = np.where(
        any_break,
        first_break_idx - 1,  # just before first breaker
        Z - 1  # no breaker -> full column allowed
    )

    last_valid_index = np.where(last_valid_index < 0, -1, last_valid_index)

    runlen = np.where(last_valid_index >= 0, last_valid_index + 1, 0).astype(np.int32)  # (T, Y, X)

    zh_vals = cp['zh'].values
    depth = np.zeros((T, Y, X), dtype=zh_vals.dtype)

    mask_pos = runlen > 0
    idx = np.maximum(runlen - 1, 0)  # safe index

    flat_mask = mask_pos.ravel()
    flat_idx = idx.ravel()
    depth_flat = depth.ravel()
    depth_flat[flat_mask] = zh_vals[flat_idx[flat_mask]]
    depth = depth_flat.reshape((T, Y, X))


    da_depth = xr.DataArray(
        depth,
        dims=('time', 'yh', 'xh'),
        coords={'time': cp['time'], 'yh': cp['yh'], 'xh': cp['xh']},
        name='cp_depth2',
    )

    # Carry units from zh if present
    zh_units = cp['zh'].attrs.get('units', '')
    da_depth.attrs.update({
        'long_name': 'cold pool depth 2',
        'units': zh_units,
        'description': 'contiguous cold-pool depth from surface'
    })

    ds_cpd = xr.Dataset({'cp_depth2':da_depth})

    return ds_cpd


def update_zarr(ds_out, outdir, outfile):

    outdir.mkdir(parents=True, exist_ok=True)
    outpath = f'{outdir}/{outfile}.zarr'

    ds_cp = ds_out[['cp_depth2']]

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


def main():

    exp_dir = '/storm/topping/cold_pools/runs/2500_core'
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

    st = 45  # start time
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
    
                ds_cpd = calc_cp_depth(ds)
    
            print(f'\t\t- Writing to {outfile}')
    
            update_zarr(ds_cpd, outdir, outfile)


if __name__ == '__main__':
    main()
