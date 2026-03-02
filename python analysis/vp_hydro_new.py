#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 12:53:11 2024

@author: dtopping
"""

import xarray as xr
import matplotlib.pyplot as plt
from IPython.core.pylabtools import figsize
from matplotlib.ticker import ScalarFormatter
import numpy as np
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


def hydro_vps(ds):
    zmax = 10.5

    z = ds['zh'].sel(zh=slice(0, zmax)).values

    # lh = ds['ptb_mp'].isel(time=0).sel(zh=slice(0, zmax)).values
    # lh_small = -1.35e-05
    # lh_mask = lh < 0 # lh_small

    hydro_mass = ds['total_hydro_mass'].isel(time=0).sel(zh=slice(0, zmax)).values
    hydro_small = 3.26  # kg
    hydro_mask = hydro_mass > hydro_small
    hydro_valid = np.where(hydro_mask, hydro_mass, np.nan)

    lh_norm = ds['lh_norm2'].isel(time=0).sel(zh=slice(0, zmax)).values
    lh_norm_valid = np.where(hydro_mask, lh_norm, np.nan)

    return np.nanmean(hydro_valid, axis=(1,2)), np.nanmean(lh_norm_valid, axis=(1,2)), z


def make_plot(axs, heights, hydro_prof, lh_prof, regime):
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


    hydro_plot = axs[0].plot(hydro_prof, heights, color=color,
                             linewidth=2.5, linestyle=style, label=label)

    axs[1].plot(lh_prof, heights, color=color,
                linewidth=2.5,linestyle=style, label=label)

    return hydro_plot, order


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

fig, axs = plt.subplots(1,2, figsize=(12, 7))
axs = axs.flatten()

plot_lines = []
orders = []
for regime in regimes:
    sim_name = str(exp_dir / regime).replace('/storm/topping/cold_pools/runs/', '').replace('/', '-')
    print(f'\n{sim_name}:')
    exp_name = sim_name[:-3]

    analysis_dir = exp_dir / regime / 'derived_vars'

    file_list = create_file_list(analysis_dir, sf, ef)

    regime_hydro = []
    regime_lh = []

    for i, f in enumerate(file_list):
        print(f'\t- Processing {f}...')

        with xr.open_zarr(
                f,
                zarr_format=3,
                consolidated=False,
                decode_timedelta=False
        ) as ds:

            hydro_prof, lh_prof, heights = hydro_vps(ds)
            regime_hydro.append(hydro_prof)
            regime_lh.append(lh_prof)

            mean_hydro_prof = np.nanmean(regime_hydro, axis=0)
            mean_lh_prof = np.nanmean(regime_lh, axis=0)

    plot_line = make_plot(axs, heights, mean_hydro_prof, mean_lh_prof, regime)
    plot_lines.append(plot_line[0][0])
    orders.append(plot_line[1])


plot_lines_ordered = list(np.full_like(plot_lines, None))
for i in range(len(orders)):
    plot_lines_ordered[orders[i]] = plot_lines[i]


formatter = ScalarFormatter(useOffset=True)
formatter.set_scientific(True)
formatter.set_powerlimits((0, 0))

axs[0].text(x=0.06, y=0.94, s='a)',
        horizontalalignment='left',
        verticalalignment='top',
        transform=axs[0].transAxes,
        fontsize=18)
axs[0].set_ylabel('Height (km)', fontsize=18, labelpad=10)
axs[0].set_xlabel('Total hydrometeor mass ($kg$)', fontsize=18, labelpad=20)
axs[0].set_ylim(0, 10.5)
axs[0].set_xlim(xmin=0)

axs[0].set_yticks(np.arange(0, 11, 1))
labels = [str(label) for label in np.arange(0, 11, 1)]
axs[0].set_yticklabels(labels)
axs[0].tick_params(axis='both', which='major', labelsize=14)
axs[0].xaxis.set_major_formatter(formatter)
axs[0].xaxis.get_offset_text().set_fontsize(10)


axs[1].text(x=0.06, y=0.94, s='b)',
        horizontalalignment='left',
        verticalalignment='top',
        transform=axs[1].transAxes,
        fontsize=18)
axs[1].axvline(x=0, color='k', linestyle='dashed')
axs[1].set_xlabel('Normalized latent heating rate ($K$ s$^{-1}$ kg$^{-1}$)', fontsize=18, labelpad=20)
axs[1].set_ylim(0, 10.5)

axs[1].set_ylabel('')
axs[1].set_yticks(np.arange(0, 11, 1))
axs[1].tick_params(axis='y', labelleft=False)
axs[1].tick_params(axis='both', which='major', labelsize=14)
axs[1].xaxis.set_major_formatter(formatter)
axs[1].xaxis.get_offset_text().set_fontsize(10)


axs[1].legend(handles=plot_lines_ordered, ncols=2, fontsize=18,
              bbox_to_anchor=(0.55, 1.25))

plt.tight_layout()
plt.subplots_adjust(wspace=0.1, hspace=0.6)

outdir = exp_dir
plt.savefig(outdir / 'vps_hydro_NEW.pdf', bbox_inches='tight')
plt.savefig(outdir / 'vps_hydro_NEW.png', dpi=300, bbox_inches='tight')
plt.show()


