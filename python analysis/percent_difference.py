#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 16:46:41 2025

@author: dtopping
"""


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import textwrap
from pathlib import Path


def diff_plot(df_diff):

    df_plot = (
        df_diff.groupby(['variable', 'regime'])
        .agg(
            pct_diff_mean=('pct_diff', 'mean'),
            pct_diff_sd=('pct_diff', 'std')
        )
        .reset_index()
    )

    variable_order = [
        'Cold Pool Intensity',
        'Cold Pool Area',
        'Cold Pool Depth',
        'Surface Precipitaion Rate',
        'Normalized Latent Cooling Rate'
    ]
    regime_order = ['mm', 'md', 'dm', 'dd']

    # Colors & hatches
    group_to_color = {'mm': 'cornflowerblue', 'md': 'cornflowerblue', 'dm': 'orange', 'dd': 'orange'}
    group_to_hatch = {'mm': '', 'md': '///', 'dm': '', 'dd': '///'}
    group_long_names = {
        'mm': 'MOIST PBL / MOIST FT',
        'md': 'MOIST PBL / DRY FT',
        'dm': 'DRY PBL / MOIST FT',
        'dd': 'DRY PBL / DRY FT'
    }

    # Get positions for grouped bars
    n_variables = len(variable_order)
    n_regimes = len(regime_order)
    bar_width = 0.18
    x = np.arange(n_variables)

    fig, ax = plt.subplots(figsize=(12, 3.5))
    # Get means and stds for each variable/regime
    # If df_plot is tidy: one row per variable/regime
    for j, regime in enumerate(regime_order):
        regime_mask = df_plot['regime'] == regime
        yvals = []
        yerrs = []
        for v in variable_order:
            idx = regime_mask & (df_plot['variable'] == v)
            row = df_plot[idx]
            # assert len(row) == 1, "Your df_plot is not unique per variable/regime"
            yvals.append(float(row['pct_diff_mean'].values[0]))
            yerrs.append(row['pct_diff_sd'].iloc[0])
        # Bar positions
        bar_pos = x + bar_width * (j - n_regimes / 2 + 0.5)
        barlist = ax.bar(
            bar_pos,
            yvals,
            width=bar_width,
            color=group_to_color[regime],
            edgecolor='black',
            linewidth=1.5,
            label=group_long_names[regime],
            hatch=group_to_hatch[regime],
            alpha=1,
            zorder=3,
            yerr=yerrs,
            capsize=5,
            error_kw=dict(ecolor='gray', lw=1.2, capthick=1.1)
        )

    # X-axis labels, wrap if needed
    labels = [textwrap.fill(label, 22) for label in variable_order]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=14, rotation=0)

    # Styling - grid, despine, axis, etc.
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', linewidth=0.7, color='lightgrey', zorder=0)
    ax.set_xlabel('')
    ax.set_ylabel('Mean percent difference (%)', fontsize=14)
    ax.tick_params(axis='y', labelsize=14)
    ax.set_ylim(-100,130)

    plt.rcParams['hatch.linewidth'] = 2

    # Build custom legend
    legend_handles = [
        mpatches.Rectangle(
            (0, 0), 1, 1,
            facecolor=group_to_color[g],
            edgecolor='k',
            hatch=group_to_hatch[g],
            linewidth=1.2,
            label=group_long_names[g]
        ) for g in regime_order
    ]
    fig.legend(
        handles=legend_handles,
        loc='upper center',
        ncol=4,
        fontsize=14,
        frameon=True,
        borderaxespad=0.5,
    )

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)  # room for legend


    outpath = Path('/storm/topping/cold_pools')
    fig.savefig(outpath / 'pct_diff.pdf', bbox_inches='tight')
    fig.savefig(outpath / 'pct_diff.png', dpi=300, bbox_inches='tight')
    plt.show()


infile = '/storm/topping/cold_pools/sim_means/single_value_metrics_FINAL.csv'
df = pd.read_csv(infile)
df.replace(0, np.nan, inplace=True)

cols = ['simulation',
        'regime',
        'b',
        'area',
        'depth',
        'prate',
        'lh_norm']

new_names = {'b':'Cold Pool Intensity',
            'area':'Cold Pool Area',
            'depth':'Cold Pool Depth',
            'prate':'Surface Precipitaion Rate',
            'lh_norm':'Normalized Latent Cooling Rate'}

data = df[cols]

sims = ['2500_core',
        '1500_core',
        '3500_core',
        'moderateCAPE-set1',
        'moderateCAPE-set2',
        'moderateCAPE-set3',
        'moderateCAPE-set4',
        'highCAPE-set1',
        'highCAPE-set2',
        'highCAPE-set3',
        'highCAPE-set4',
        'lowCAPE-set1',
        'lowCAPE-set2',
        'morrison',
        'nssl3',
        'freeslip',
        'sigtor',
        'random_pert-set1',
        'random_pert-set2',
        'random_pert-set3',
        'random_pert-set4',
        'random_pert-set5']


regimes = ['mm','md','dm','dd']

diff_data = []
for sim in sims:

    for regime in regimes:

        for col in data.columns[2:]:
            
            sim_median = df[(df['simulation'] == sim) & \
                         (df['regime'] == 'overall')][col].values[0]
                
            regime_val = df[(df['simulation'] == sim) & \
                         (df['regime'] == regime)][col].values[0]
            
            pct_diff = ((regime_val - sim_median) / abs(sim_median)) * 100
            
            diff_data.append({'simulation':sim,
                             'regime':regime,
                             'variable': new_names[col],
                             'pct_diff':pct_diff})


df_diff = pd.DataFrame(diff_data)

    
diff_plot(df_diff)




