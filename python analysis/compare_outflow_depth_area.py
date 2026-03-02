#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 17:23:50 2024

@author: dtopping
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import median_filter
import os
from pathlib import Path
import warnings

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


def cp_data(f):
    with xr.open_zarr(
            f,
            zarr_format=3,
            consolidated=False,
            decode_times=True,
            decode_timedelta=False
    ) as ds:
        time = ds.time.values[0] / 60

        print(f'\t\t--> {str(time)}')

        cpd = ds['cp_depth'].isel(time=0) * 1000
        avg_cpd = np.nanmean(cpd.where(cpd > np.nanquantile(cpd, q=0.1)))
        # avg_cpd = np.nanquantile(cpd.where(cpd > 176), 0.75)
        # avg_cpd = np.nanmean(cpd.where(cpd > 176))

        cp = ds['cp_clean'].isel(time=0, zh=0)
        hspace = round(ds.xh.values[1] - ds.xh.values[0], 2)
        neg_count = np.count_nonzero(~np.isnan(cp))
        neg_area = neg_count * hspace ** 2

    return neg_area, avg_cpd, time


def median_smooth(data, size=5):
    return median_filter(data, size=size)


def make_plot(axs, times, depth_ts, regime):
    if regime == 'mm':
        color = '#005AB5'
        style = 'solid'
        label = 'Moist PBL / Moist FT'  # '-' + CAPE + '-' + HODO + '-' + MP
        order = 0
    elif regime == 'md':
        color = '#005AB5'
        style = 'dashed'
        label = 'Moist PBL / Dry FT'  # '-' + CAPE + '-' + HODO + '-' + MP
        order = 1
    elif regime == 'dm':
        color = '#DC3220'
        style = 'solid'
        label = 'Dry PBL / Moist FT'  # '-' + CAPE + '-' + HODO + '-' + MP
        order = 2
    elif regime == 'dd':
        color = '#DC3220'
        style = 'dashed'
        label = 'Dry PBL / Dry FT'  # '-' + CAPE + '-' + HODO + '-' + MP
        order = 3
    else:
        pass

    axs[0].set_title('(a)    Active Cold Pool Area', fontsize=18, loc='left')
    axs[0].plot(times, area_ts,
                label=label, color=color, linestyle=style)

    axs[1].set_title('(b)    Mean Active Cold Pool Depth', fontsize=18, loc='left')
    depth_plot = axs[1].plot(times, depth_ts,
                             label=label, color=color, linestyle=style)

    return depth_plot, order


###############################################################################
###############################################################################

exp_dir = '/storm/topping/cold_pools/runs/2500_core'
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

fig, axs = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
axs = axs.flatten()

plot_lines = []
orders = []

for regime in regimes:

    sim_name = str(exp_dir / regime).replace('/storm/topping/cold_pools/runs/', '').replace('/', '-')
    print(f'\n{sim_name}:')

    analysis_dir = exp_dir / regime / 'derived_vars'

    file_list = create_file_list(analysis_dir, sf, ef)

    times = []
    area_ts = []
    depth_ts = []

    for i, f in enumerate(file_list):
        area, depth, time = cp_data(f)

        area_ts.append(area)
        depth_ts.append(depth.flatten())
        times.append(time)

    smooth_ts = median_smooth(depth_ts, size=1)
    depth_plot = make_plot(axs, times, smooth_ts, regime)
    plot_lines.append(depth_plot[0][0])
    orders.append(depth_plot[1])

plot_lines_ordered = list(np.full_like(plot_lines, None))
for i in range(len(orders)):
    plot_lines_ordered[orders[i]] = plot_lines[i]


axs[0].set_xlabel('')

axs[1].set_xlabel('Time (min)', fontsize=18)
axs[1].tick_params(axis='x', which='major', labelsize=14)

axs[0].set_ylabel('Area ($km^2$)', fontsize=18)
axs[0].tick_params(axis='both', which='major', labelsize=14)
axs[0].tick_params(axis='both', which='major', length=8, width=2)

axs[1].set_ylabel('Depth ($m$)', fontsize=18)
axs[1].tick_params(axis='both', which='major', labelsize=14)
axs[1].tick_params(axis='both', which='major', length=8, width=2)

axs[1].legend(handles=plot_lines_ordered, ncols=2, fontsize=18,
           bbox_to_anchor=(0.84, 1.55))

axs[0].set_ylim(0,2500)
axs[1].set_xlim(90, 180)
axs[1].set_ylim(0, 4000)

plt.tight_layout()
plt.subplots_adjust(wspace=0.08, hspace=0.6)

outdir = exp_dir
plt.savefig(outdir / 'ts_cp_area_depth.pdf', bbox_inches='tight')
plt.savefig(outdir / 'ts_cp_area_depth.png', dpi=300, bbox_inches='tight')
plt.show()
