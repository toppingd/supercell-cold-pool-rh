#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 13:23:33 2024

@author: dtopping
"""

import sharppy.plot.skew as skew
from sharppy.sharptab import winds, utils, params, thermo, interp, profile

import matplotlib.pyplot as plt
# import matplotlib.projections as proj
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from matplotlib.collections import LineCollection
import matplotlib.transforms as transforms

from metpy.units import units
import numpy as np


def plot_skewt_logp(file):
    fig, ax = plt.subplots(1,1, figsize=(8, 8), subplot_kw={'projection': 'skewx'})

    with open(file, 'r') as f:
        data = f.readlines()[6:-1]
        for i in range(len(data)):
            data[i] = data[i].split(',')
            for j in range(len(data[i])):
                data[i][j] = float(data[i][j].strip())

        # Extract the necessary columns and convert to appropriate units
        prs = np.array([data[h][0] for h in range(len(data))]) * units('hPa')
        heights = np.array([data[h][1] for h in range(len(data))]) * units.meter
        temperature = np.array([data[h][2] for h in range(len(data))]) * units('degC')
        dewpoint = np.array([data[h][3] for h in range(len(data))]) * units('degC')
        wdir = np.array([data[h][4] for h in range(len(data))]) * units('degrees')
        wspd = np.array([data[h][5] for h in range(len(data))]) * units('knots')

        # Create a profile object for SHARPpy
        prof = profile.create_profile(pres=prs.magnitude,
                                      hght=heights.magnitude,
                                      tmpc=temperature.magnitude,
                                      dwpc=dewpoint.magnitude,
                                      wdir=wdir.magnitude,
                                      wspd=wspd.magnitude)

        mlparcel = params.parcelx(prof, flag=4)

        ax.semilogy(prof.tmpc[~prof.tmpc.mask], prof.pres[~prof.tmpc.mask], 'r', lw=3)
        ax.semilogy(prof.dwpc[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'g', lw=3)
        ax.semilogy(prof.vtmp[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'r--', lw=2)
        ax.semilogy(mlparcel.ttrace, mlparcel.ptrace, 'k', lw=2)

        #######################

        # Highlight the 0 C and -20 C isotherms.
        ax.axvline(0, color='steelblue', ls='--', lw=1.5)
        ax.axvline(-20, color='steelblue', ls='--', lw=1.5)

        # Disables the log-formatting that comes with semilogy
        ax.yaxis.set_major_formatter(ScalarFormatter())
        ax.set_yticks(np.linspace(100, 1000, 10))
        ax.set_xticks(np.linspace(-100, 50, 16))
        ax.set_ylim(1050, 100)
        ax.set_xlim(-45, 45)
        ax.set_xticks(np.arange(-40, 50, 10))

        ax.tick_params(axis='both', which='major', labelsize=18, length=8, width=2)
        ax.tick_params(axis='x', which='major', rotation=-30)

        # Add gridlines
        ax.grid(True)

    ax.set_ylabel('Pressure (hPa)', fontsize=20)
    ax.set_xlabel('Temperature (°C)', fontsize=20)

    plt.grid(True)

    plt.subplots_adjust(wspace=0.08, hspace=0.15)
    # plt.tight_layout()


###############################################################################

sounding_file = 'D:/cold_pool_mwr/soundings/final/sharppy/sigtor_203050504_mkl_moistPBL_moistFT_moderateCAPE_qt_sharppy'

plot_skewt_logp(sounding_file)

###############################################################################

plt.show()

