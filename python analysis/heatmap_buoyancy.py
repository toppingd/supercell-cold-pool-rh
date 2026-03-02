#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 14:01:12 2024

@author: dtopping
"""


import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patheffects as path_effects
import cmasher as cmr
import numpy as np

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

        time = ds.time.values[0]/60

        print(f'\t\t--> {str(time)}')

        cp = ds['cp_clean'].isel(time=0, zh=0)
        cp_hist = np.histogram(cp, 50, range=(-0.25, -0.0))
        # cp_hist = np.histogram(cp_isolated,80,range=(-0.4,-0.0))
        bins = cp_hist[1][:-1]

        cp_median = np.nanmean(cp.where(cp < np.nanquantile(cp, q=0.9))) # use < since values are negative

    return cp_hist[0],bins, cp_median, time


def make_plot(axs,times,hist_ts,bins,cp_ts,regime):

    if regime == 'mm':
        label='Moist PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=0
    elif regime == 'md':
        label='Moist PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=1
    elif regime == 'dm':
        label='Dry PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=2
    elif regime == 'dd':
        label='Dry PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=3
    else:
        pass
    
    axs[i].set_title(label,fontsize=22,loc='left')
    
    cp_grid = np.asarray(hist_ts).transpose()
    
    norm = colors.Normalize(vmin=0,vmax=1800)
    # cmap = cmr.fall_r
    cmap = cmr.gothic_r
    cp_plot = axs[i].pcolormesh(times,bins,cp_grid, 
                                shading='gouraud',cmap=cmap,norm=norm,
                                zorder=0)
    
    axs[i].plot(times, cp_ts,
                color='w', linestyle='solid', linewidth=5)
    
    axs[i].plot(times, cp_ts,
                color='k', linestyle='dashed', linewidth=3)
    
    # shadow_effect = path_effects.withStroke(linestyle='solid', linewidth=8, foreground='white')
    # line.set_path_effects([shadow_effect])
    
    axs[i].set_xlim(min(times),max(times))
    axs[i].set_ylim(np.min(bins),-0.01)    
    
    return cp_plot  
    

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

fig,axs = plt.subplots(4,1,figsize=(15,20))
axs = axs.flatten()

plot_lines = []
orders = []

for regime in regimes:

    sim_name = str(exp_dir / regime).replace('/storm/topping/cold_pools/runs/', '').replace('/', '-')
    print(f'\n{sim_name}:')

    analysis_dir = exp_dir / regime / 'derived_vars'

    file_list = create_file_list(analysis_dir, sf, ef)

    hist_ts = []
    cp_ts = []
    times = []

    for i, f in enumerate(file_list):

        cp_hist, bins, cp_mean, timestep = cp_data(f)
                    
        hist_ts.append(cp_hist)
        cp_ts.append(cp_mean)
        times.append(timestep)

    cp_plot = make_plot(axs,times,hist_ts,bins,cp_ts, regime)


axs[3].set_xlabel('Time (min)', fontsize=20)
axs[3].tick_params(axis='x', which='major', labelsize=16)

axs[0].set_ylabel('Buoyancy (m $s^{-2}$)', fontsize=20)
axs[0].tick_params(axis='y', which='major', labelsize=16)
axs[1].set_ylabel('Buoyancy (m $s^{-2}$)', fontsize=20)
axs[1].tick_params(axis='y', which='major', labelsize=16)
axs[2].set_ylabel('Buoyancy (m $s^{-2}$)', fontsize=20)
axs[2].tick_params(axis='both', which='major', labelsize=16)
axs[3].set_ylabel('Buoyancy (m $s^{-2}$)', fontsize=20)
axs[3].tick_params(axis='both', which='major', labelsize=16)

axs[0].tick_params(axis='x', which='major', labelcolor='white')
axs[1].tick_params(axis='x', which='major', labelcolor='white')
axs[2].tick_params(axis='x', which='major', labelcolor='white')

axs[0].tick_params(axis='both', which='major', length=8, width=2)
axs[1].tick_params(axis='both', which='major', length=8, width=2)
axs[2].tick_params(axis='both', which='major', length=8, width=2)
axs[3].tick_params(axis='both', which='major', length=8, width=2)


fig.subplots_adjust(right=0.8, hspace=0.26, wspace=0.25)
cbar_ax = fig.add_axes([0.82, 0.15, 0.01, 0.7])
cb = plt.colorbar(cp_plot,cax=cbar_ax, extend='max')
cb.set_label(label='Number of Gridpoints',fontsize=20)
cb.ax.tick_params(labelsize=16) 

plt.subplots_adjust(wspace=0.08, hspace=0.25)


outdir = exp_dir
plt.savefig(outdir / 'b_heatmap_NEW.pdf', bbox_inches='tight')
plt.savefig(outdir / 'b_heatmap_NEW.png', dpi=300, bbox_inches='tight')
