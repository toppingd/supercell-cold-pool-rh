import argparse
# import os
import numpy as np
import csv
import xarray as xr
from pathlib import Path

import warnings
warnings.simplefilter(action='ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='zarr')


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


def buoyancy_mean(ds):
    cp = ds['cp_clean'].isel(time=0, zh=0)
    # cp_neg = cp.where(cp <= -0.01)
    threshold = -0.01563
    return np.nanmean(cp.where(cp < threshold))


def active_area(ds):
    cp = ds['cp_clean'].isel(time=0, zh=0).values
    hspace = round(ds.xh.values[1] - ds.xh.values[0], 2)
    gp_area = hspace** 2
    neg_count = np.count_nonzero(cp[~np.isnan(cp)])
    return neg_count * gp_area


def depth_mean(ds):
    depth = ds['cp_depth'].isel(time=0)*1000
    threshold = 75.0
    return np.nanmean(depth.where(depth > threshold))


def prate_mean(ds):
    sfc_prate = ds['prate'].isel(time=0)
    # nonzero_rain = sfc_prate.where(np.round(sfc_prate, 3) > 0)
    threshold = 0.00069
    return np.nanmean(sfc_prate.where(sfc_prate > threshold))


def lh_norm_mean(ds):
    zmax = 0.5

    lh = ds['ptb_mp'].isel(time=0).sel(zh=slice(0, zmax)).values
    lh_small = -1.35e-05
    lh_mask = lh < lh_small

    hydro_mass = ds['total_hydro_mass'].isel(time=0).sel(zh=slice(0, zmax)).values
    hydro_small = 3.26 # kg
    hydro_mask = hydro_mass > hydro_small

    combined_mask = lh_mask & hydro_mask

    lh_norm = ds['lh_norm2'].isel(time=0).sel(zh=slice(0, zmax)).values
    lh_norm_valid = np.where(combined_mask, lh_norm, np.nan)

    return np.nanmean(lh_norm_valid)


def calc_q10s(ds):
    cp = ds['cp_clean'].isel(time=0, zh=0)
    cp_neg = cp.where(cp <= -0.01)
    b_q10 = np.nanquantile(cp_neg, q=0.9) # use < since values are negative

    depth = ds['cp_depth'].isel(time=0)*1000
    depth_q10 = np.nanquantile(depth, q=0.1)

    sfc_prate = ds['prate'].isel(time=0)
    nonzero_rain = sfc_prate.where(np.round(sfc_prate, 3) > 0)
    prate_q10 = np.nanquantile(nonzero_rain, 0.1)

    return b_q10, depth_q10, prate_q10


def calc_hydro_q10s(ds):
    zmax = 10.5

    lh = ds['ptb_mp'].isel(time=0).sel(zh=slice(0, zmax)).values
    lh_neg_mask = lh < 0
    lh_q10 = np.nanquantile(lh[lh_neg_mask], 0.9)

    hydro_mass = ds['total_hydro_mass'].isel(time=0).sel(zh=slice(0, zmax)).values
    hydro_mass_q10 = np.nanquantile(hydro_mass[lh_neg_mask], 0.1)

    return hydro_mass_q10, lh_q10


# def write_run_to_csv(outpath, exp_name, sim_name, b, area, depth, prate, lh_norm):
def write_run_to_csv(outpath, exp_name, sim_name, b, depth, prate):
# def write_run_to_csv(outpath, exp_name, sim_name, qb, qdepth, qprate):
# def write_run_to_csv(outpath, exp_name, sim_name, lh_norm):
# def write_run_to_csv(outpath, exp_name, sim_name, qhydro, qlh_norm):
    csv_data = [sim_name] + b
    csv_path = f'{outpath}/{exp_name}_buoyancy_means_const_thresh.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(csv_data)

    # csv_data = [sim_name] + area
    # csv_path = f'{outpath}/{exp_name}_area_means.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(csv_data)

    csv_data = [sim_name] + depth
    csv_path = f'{outpath}/{exp_name}_depth_means_const_thresh.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(csv_data)

    csv_data = [sim_name] + prate
    csv_path = f'{outpath}/{exp_name}_prate_means_const_thresh.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(csv_data)

    # csv_data = [sim_name] + lh_norm
    # csv_path = f'{outpath}/{exp_name}_lh_norm_means_500m.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(csv_data)

    ######################################################

    # csv_data = qb
    # csv_path = f'{outpath}/{exp_name}_b_q10.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(csv_data)
    #
    # csv_data = qdepth
    # csv_path = f'{outpath}/{exp_name}_depth_q10.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(csv_data)
    #
    # csv_data = qprate
    # csv_path = f'{outpath}/{exp_name}_prate_q10.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(csv_data)

    # csv_data = qhydro
    # csv_path = f'{outpath}/{exp_name}_hydro_q10.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(csv_data)
    #
    # csv_data = qlh_norm
    # csv_path = f'{outpath}/{exp_name}_lh_norm_q10.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(csv_data)


def main(exp_dir):
# def main():

    # exp_dir = '/storm/topping/cold_pools/runs/2500_core'
    # exp_dir = '/storm/topping/cold_pools/runs/1500_core'
    # exp_dir = '/storm/topping/cold_pools/runs/3500_core'
    #
    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set1'
    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set2'
    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set3'
    # exp_dir = '/storm/topping/cold_pools/runs/moderateCAPE/set4'
    #
    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set1'
    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set2'
    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set3'
    # exp_dir = '/storm/topping/cold_pools/runs/highCAPE/set4'
    #
    # exp_dir = '/storm/topping/cold_pools/runs/lowCAPE/set1'
    # exp_dir = '/storm/topping/cold_pools/runs/lowCAPE/set2'
    #
    # exp_dir = '/storm/topping/cold_pools/runs/nssl3'
    # exp_dir = '/storm/topping/cold_pools/runs/morrison'
    #
    # exp_dir = '/storm/topping/cold_pools/runs/sigtor'
    #
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
        sim_name = str(exp_dir / regime).replace('/storm/topping/cold_pools/runs/', '').replace('/', '-')
        print(f'\n{sim_name}:')
        exp_name = sim_name[:-3]

        analysis_dir = exp_dir / regime / 'derived_vars'

        file_list = create_file_list(analysis_dir, sf, ef)

        regime_b = []
        # regime_area = []
        regime_depth = []
        regime_prate = []
        # regime_lh = []
        # b_q10s = []
        # depth_q10s = []
        # prate_q10s = []
        # hydro_q10s = []
        # lh_q10s = []

        for i, f in enumerate(file_list):
            print(f'\t- Processing {f}...')

            with xr.open_zarr(
                f,
                zarr_format=3,
                consolidated=False,
                decode_timedelta=False
            ) as ds:

                b_mean = buoyancy_mean(ds)
                # print(f'\t\t> b_mean: {b_mean} m2 s-2')
                # cp_area = active_area(ds)
                # print(f'\t\t> cp_area: {cp_area} km2')
                cp_depth_mean = depth_mean(ds)
                # print(f'\t\t> cp_depth_mean: {cp_depth_mean} m')
                sfc_prate_mean = prate_mean(ds)
                # print(f'\t\t> sfc_prate_mean: {sfc_prate_mean} kg m-2 s-1')
                # lh_mean = lh_norm_mean(ds)
                # print(f'\t\t> lh_norm_mean: {lh_mean} K s-1 kg-1')
                # b_q10, depth_q10, prate_q10 = calc_q10s(ds)
                # hydro_q10, lh_q10 = calc_hydro_q10s(ds)

                regime_b.append(b_mean)
                # regime_area.append(cp_area)
                regime_depth.append(cp_depth_mean)
                regime_prate.append(sfc_prate_mean)
                # regime_lh.append(lh_mean)
                # b_q10s.append(b_q10)
                # depth_q10s.append(depth_q10)
                # prate_q10s.append(prate_q10)
                # hydro_q10s.append(hydro_q10)
                # lh_q10s.append(lh_q10)

        outpath = '/storm/topping/cold_pools/sim_means'
        # write_run_to_csv(outpath, exp_name, sim_name, regime_b, regime_area, regime_depth, regime_prate, regime_lh)
        write_run_to_csv(outpath, exp_name, sim_name, regime_b, regime_depth, regime_prate)
        # write_run_to_csv(outpath, exp_name, sim_name, b_q10s, depth_q10s, prate_q10s)
        # write_run_to_csv(outpath, exp_name, sim_name, regime_lh)
        # write_run_to_csv(outpath, exp_name, sim_name, hydro_q10s, lh_q10s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--exp_dir',
        type=str,
        required=True,
        help='Path to the experiment directory'
    )
    args = parser.parse_args()
    main(args.exp_dir)
    # main()