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


def plot_skewt_logp(file_paths):
    fig = plt.figure(figsize=(15, 15))
    # global projs
    # projs = proj.get_projection_names()

    axs = [None, None, None, None]

    for a, (regime, files) in enumerate(file_paths.items()):
        print(a, regime, files)

        if 'mm' in regime:
            axs[0] = fig.add_subplot(221, projection='skewx')
            axs[0].set_title('a)  Moist PBL / Moist FT', loc='left', size=24)
        elif 'md' in regime:
            axs[1] = fig.add_subplot(222, projection='skewx')
            axs[1].set_title('b)  Moist PBL / Dry FT', loc='left', size=24)
        elif 'dm' in regime:
            axs[2] = fig.add_subplot(223, projection='skewx')
            axs[2].set_title('c)  Dry PBL / Moist FT', loc='left', size=24)
        elif 'dd' in regime:
            axs[3] = fig.add_subplot(224, projection='skewx')
            axs[3].set_title('d)  Dry PBL / Dry FT', loc='left', size=24)


        ####################
        # For final sounding
        with open(files[1], 'r') as f2:
            data2 = f2.readlines()[6:-1]
            for i in range(len(data2)):
                data2[i] = data2[i].split(',')
                for j in range(len(data2[i])):
                    data2[i][j] = float(data2[i][j].strip())

        # Extract the necessary columns and convert to appropriate units
        prs2 = np.array([data2[h][0] for h in range(len(data2))]) * units('hPa')
        heights2 = np.array([data2[h][1] for h in range(len(data2))]) * units.meter
        temperature2 = np.array([data2[h][2] for h in range(len(data2))]) * units('degC')
        dewpoint2 = np.array([data2[h][3] for h in range(len(data2))]) * units('degC')
        wdir2 = np.array([data2[h][4] for h in range(len(data2))]) * units('degrees')
        wspd2 = np.array([data2[h][5] for h in range(len(data2))]) * units('knots')

        # Create a profile object for SHARPpy
        prof2 = profile.create_profile(pres=prs2.magnitude,
                                      hght=heights2.magnitude,
                                      tmpc=temperature2.magnitude,
                                      dwpc=dewpoint2.magnitude,
                                      wdir=wdir2.magnitude,
                                      wspd=wspd2.magnitude)

        mlparcel2 = params.parcelx(prof2, flag=4)

        axs[a].semilogy(prof2.tmpc[~prof2.tmpc.mask], prof2.pres[~prof2.tmpc.mask], 'r', lw=3)
        axs[a].semilogy(prof2.dwpc[~prof2.dwpc.mask], prof2.pres[~prof2.dwpc.mask], 'g', lw=3)
        # axs[a].semilogy(prof2.vtmp[~prof2.dwpc.mask], prof2.pres[~prof2.dwpc.mask], 'r--', lw=2)
        # axs[a].semilogy(mlparcel2.ttrace, mlparcel2.ptrace, 'k', lw=2)


        #######################
        # For original sounding

        with open(files[0], 'r') as f1:
            data1 = f1.readlines()[6:-1]
            for i in range(len(data1)):
                data1[i] = data1[i].split(',')
                for j in range(len(data1[i])):
                    data1[i][j] = float(data1[i][j].strip())

        # Extract the necessary columns and convert to appropriate units
        prs1 = np.array([data1[h][0] for h in range(len(data1))]) * units('hPa')
        heights1 = np.array([data1[h][1] for h in range(len(data1))]) * units.meter
        temperature1 = np.array([data1[h][2] for h in range(len(data1))]) * units('degC')
        dewpoint1 = np.array([data1[h][3] for h in range(len(data1))]) * units('degC')
        wdir1 = np.array([data1[h][4] for h in range(len(data1))]) * units('degrees')
        wspd1 = np.array([data1[h][5] for h in range(len(data1))]) * units('knots')

        # Create a profile object for SHARPpy
        prof1 = profile.create_profile(pres=prs1.magnitude,
                                       hght=heights1.magnitude,
                                       tmpc=temperature1.magnitude,
                                       dwpc=dewpoint1.magnitude,
                                       wdir=wdir1.magnitude,
                                       wspd=wspd1.magnitude)

        mlparcel1 = params.parcelx(prof1, flag=4)

        axs[a].semilogy(prof1.tmpc[~prof1.tmpc.mask], prof1.pres[~prof1.tmpc.mask], 'r--', lw=3)
        axs[a].semilogy(prof1.dwpc[~prof1.dwpc.mask], prof1.pres[~prof1.dwpc.mask], 'g--', lw=3)
        # axs[a].semilogy(prof1.vtmp[~pro1f.dwpc.mask], prof1.pres[~prof1.dwpc.mask], 'r--', lw=2)
        # axs[a].semilogy(mlparcel1.ttrace, mlparcel1.ptrace, 'k--', lw=2)

        #######################

        # Highlight the 0 C and -20 C isotherms.
        axs[a].axvline(0, color='steelblue', ls='--', lw=1.5)
        axs[a].axvline(-20, color='steelblue', ls='--', lw=1.5)

        # Disables the log-formatting that comes with semilogy
        axs[a].yaxis.set_major_formatter(ScalarFormatter())
        axs[a].set_yticks(np.linspace(100, 1000, 10))
        axs[a].set_xticks(np.linspace(-100, 50, 16))
        axs[a].set_ylim(1050, 100)
        axs[a].set_xlim(-45, 45)
        axs[a].set_xticks(np.arange(-40, 50, 10))

        axs[a].tick_params(axis='both', which='major', labelsize=18,
                           length=8, width=2)
        axs[a].tick_params(axis='x', which='major', rotation=-30)

        # Add gridlines
        axs[a].grid(True)

    axs[0].set_ylabel('Pressure (hPa)', fontsize=20)
    axs[2].set_ylabel('Pressure (hPa)', fontsize=20)
    axs[2].set_xlabel('Temperature (°C)', fontsize=20)
    axs[3].set_xlabel('Temperature (°C)', fontsize=20)
    axs[0].tick_params(axis='x', which='major', labelcolor='white')
    axs[1].tick_params(axis='both', which='major', labelcolor='white')
    axs[3].tick_params(axis='y', which='major', labelcolor='white')

    plt.grid(True)

    plt.subplots_adjust(wspace=0.08, hspace=0.15)
    # plt.tight_layout()


###############################################################################

CAPE = '3500'

mm2 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_'+CAPE+'_extended_sharppy'
# mm1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_203050501_lzk_sigtor_sharppy' # 2500
# mm1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_204062402_osh_sigtor_sharppy' # 1500
mm1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/' + CAPE + '/mm_200051722_lxn_sigtor_sharppy'  # 3500

md2 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_'+CAPE+'_extended_sharppy'
# md1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_200022606_crs_nontor_sharppy' # 2500
# md1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_203111722_gls_wektor_sharppy' # 1500
md1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/' + CAPE + '/md_203050807_adm_sigtor_sharppy'  # 3500

dm2 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_'+CAPE+'_extended_sharppy'
# dm1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_200061122_mot_wektor_sharppy' # 2500
# dm1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_201050501_cot_nontor_sharppy' # 1500
dm1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/' + CAPE + '/dm_201051623_bie_nontor_sharppy'  # 3500

dd2 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_'+CAPE+'_extended_sharppy'
# dd1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_200070922_ggw_nontor_sharppy' # 2500
# dd1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_201050200_aum_sigtor_sharppy' # 1500
dd1 = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/' + CAPE + '/dd_204071823_gfk_sigtor_sharppy'  # 3500

plot_skewt_logp({'mm': (mm1,mm2), 'md': (md1,md2), 'dm': (dm1,dm2), 'dd': (dd1,dd2)})

###############################################################################

outpath = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/' + CAPE + '/'

plt.savefig(outpath + CAPE + '_thermo_profiles_change_compare' + '.pdf', bbox_inches='tight')

