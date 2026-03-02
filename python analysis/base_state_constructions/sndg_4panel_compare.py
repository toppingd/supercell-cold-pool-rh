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
    fig = plt.figure(figsize=(10, 10))
    # global projs
    # projs = proj.get_projection_names()

    axs = [None, None, None, None]

    for a, (regime, files) in enumerate(file_paths.items()):

        # if 'mm' in regime:
        #     axs[0] = fig.add_subplot(221, projection='skewx')
        #     axs[0].set_title('a)  Moist PBL / Moist FT', loc='left', size=24)
        # elif 'md' in regime:
        #     axs[1] = fig.add_subplot(222, projection='skewx')
        #     axs[1].set_title('b)  Moist PBL / Dry FT', loc='left', size=24)
        # elif 'dm' in regime:
        #     axs[2] = fig.add_subplot(223, projection='skewx')
        #     axs[2].set_title('c)  Dry PBL / Moist FT', loc='left', size=24)
        # elif 'dd' in regime:
        #     axs[3] = fig.add_subplot(224, projection='skewx')
        #     axs[3].set_title('d)  Dry PBL / Dry FT', loc='left', size=24)

        if 's1' in regime:
            axs[0] = fig.add_subplot(221, projection='skewx')
        elif 's2' in regime:
            axs[1] = fig.add_subplot(222, projection='skewx')
        elif 's3' in regime:
            axs[2] = fig.add_subplot(223, projection='skewx')
        elif 's4' in regime:
            axs[3] = fig.add_subplot(224, projection='skewx')

        if files[0] and files[1]:
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
            mllfc2 = mlparcel2.lfcpres
            axs[a].hlines(y=mllfc2, xmin=-100, xmax=100, color='k', lw=0.5, linestyle='-')

            axs[a].semilogy(prof2.tmpc[~prof2.tmpc.mask], prof2.pres[~prof2.tmpc.mask], 'r', lw=1.5)
            axs[a].semilogy(prof2.dwpc[~prof2.dwpc.mask], prof2.pres[~prof2.dwpc.mask], 'limegreen', lw=1.5)
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
            mllfc1 = mlparcel1.lfcpres
            axs[a].hlines(y=mllfc1, xmin=-100, xmax=100, color='k', lw=0.5, linestyle='--')

            axs[a].semilogy(prof1.tmpc[~prof1.tmpc.mask], prof1.pres[~prof1.tmpc.mask], color='darkred',linestyle='--',lw=1.5)
            axs[a].semilogy(prof1.dwpc[~prof1.dwpc.mask], prof1.pres[~prof1.dwpc.mask], color='darkgreen',linestyle='--',lw=1.5)
            # axs[a].semilogy(prof1.vtmp[~pro1f.dwpc.mask], prof1.pres[~prof1.dwpc.mask], 'r--', lw=2)
            # axs[a].semilogy(mlparcel1.ttrace, mlparcel1.ptrace, 'k--', lw=2)

            #######################

            # Highlight the 0 C and -20 C isotherms.
            axs[a].axvline(0, color='steelblue', ls='--', lw=1)
            axs[a].axvline(-20, color='steelblue', ls='--', lw=1)

            # Disables the log-formatting that comes with semilogy
            axs[a].yaxis.set_major_formatter(ScalarFormatter())
            axs[a].set_yticks(np.linspace(100, 1000, 10))
            axs[a].set_xticks(np.linspace(-100, 50, 16))
            axs[a].set_ylim(1050, 100)
            axs[a].set_xlim(-45, 45)
            axs[a].set_xticks(np.arange(-40, 50, 10))

            axs[a].tick_params(axis='both', which='major', labelsize=12,
                               length=6, width=1)
            axs[a].tick_params(axis='x', which='major', rotation=-30)

            # Add gridlines
            axs[a].grid(True)

    axs[0].set_ylabel('Pressure (hPa)', fontsize=14)
    axs[2].set_ylabel('Pressure (hPa)', fontsize=14)
    axs[2].set_xlabel('Temperature (°C)', fontsize=14)
    axs[3].set_xlabel('Temperature (°C)', fontsize=14)
    axs[0].tick_params(axis='x', which='major', labelcolor='white')
    axs[1].tick_params(axis='both', which='major', labelcolor='white')
    axs[3].tick_params(axis='y', which='major', labelcolor='white')

    plt.grid(True)

    plt.subplots_adjust(wspace=0.08, hspace=0.15)
    # plt.tight_layout()
    # plt.show()


###############################################################################

og_indir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/original_soundings/'
adjusted_indir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/adjusted_soundings/'

rh_options = ('moistPBL_moistFT', 'moistPBL_dryFT', 'dryPBL_moistFT', 'dryPBL_dryFT')
rh_choice = rh_options[3]

cape_options = ('lowCAPE', 'moderateCAPE', 'highCAPE')
cape_choice = cape_options[0]


# mm_choice = 'sigtor_204053020_sdf_sharppy'
# mm1 = f'{og_indir}/{mm_choice}'
# mm2 = f'{adjusted_indir}/moistPBL_moistFT/{cape_choice}/{mm_choice}_extended_adjusted'
# # mm2 = f'{adjusted_indir}/{mm_choice}_extended_adjusted'
#
# md_choice = 'sigtor_201052022_min_sharppy'
# md1 = f'{og_indir}/{md_choice}'
# md2 = f'{adjusted_indir}/moistPBL_dryFT/{cape_choice}/{md_choice}_extended_adjusted'
# # md2 = f'{adjusted_indir}/{md_choice}_extended_adjusted'
#
# dm_choice = 'sigtor_201053000_ama_sharppy'
# dm1 = f'{og_indir}/{dm_choice}'
# dm2 = f'{adjusted_indir}/dryPBL_moistFT/{cape_choice}/{dm_choice}_extended_adjusted'
# # dm2 = f'{adjusted_indir}/{dm_choice}_extended_adjusted'
#
# dd_choice = 'sigtor_204053002_okc_sharppy'
# dd1 = f'{og_indir}/{dd_choice}'
# dd2 = f'{adjusted_indir}/dryPBL_dryFT/{cape_choice}/{dd_choice}_extended_adjusted'
# # dd2 = f'{adjusted_indir}/{dd_choice}_extended_adjusted'

# plot_skewt_logp({'mm': (mm1,mm2), 'md': (md1,md2), 'dm': (dm1,dm2), 'dd': (dd1,dd2)})


###########################################################################################


# mm - low CAPE
# choice1 = 'wektor_204081420_hat_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'wektor_204051821_pia_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'


# md - low CAPE
# choice1 = 'sigtor_200010323_mei_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'nontor_203041922_p#0_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'


# dm - low CAPE
# choice1 = 'nontor_199091101_afw_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'wektor_200050802_rwf_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'


# dd - low CAPE
# choice1 = 'wektor_199090400_ako_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'nontor_199072922_fvx_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'


s3_og, s3_new, s4_og, s4_new = None, None, None, None

###########################################################################################


# mm - moderate CAPE
# choice1 = 'sigtor_203050504_mkl_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'sigtor_203050501_lzk_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'nontor_204050101_fwd_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'wektor_200071823_sus_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'


# md - moderate CAPE
# choice1 = 'wektor_204032723_c33_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'sigtor_199060200_tbn_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'wektor_204062202_ama_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'wektor_199060619_dvl_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'


# dm - moderate CAPE
# choice1 = 'nontor_203050221_hsv_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'nontor_203050100_brl_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'wektor_201050123_rpd_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'nontor_204082018_orh_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'

# dd - moderate CAPE
# choice1 = 'wektor_204071421_nhk_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'wektor_204062201_ama_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'wektor_199053122_lbl_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'wektor_200062923_gld_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'


###########################################################################################


# mm - high CAPE
# choice1 = 'wektor_204082401_foe_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'nontor_203050223_bmx_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'wektor_200061321_rdk_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'sigtor_200051722_lxn_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'


# md - high CAPE
# choice1 = 'sigtor_203050823_c34_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'sigtor_203062500_hon_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'sigtor_204082700_rdd_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'nontor_200081723_ind_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'


# dm - high CAPE
# choice1 = 'nontor_200061323_p28_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'nontor_200070922_mhe_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'nontor_199060200_ftw_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'nontor_204082522_fsm_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'

# dd - high CAPE
# choice1 = 'wektor_199062701_mck_sharppy'
# s1_og = f'{og_indir}/{choice1}'
# s1_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice1}_extended_adjusted'
#
# choice2 = 'wektor_200072500_anw_sharppy'
# s2_og = f'{og_indir}/{choice2}'
# s2_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice2}_extended_adjusted'
#
# choice3 = 'sigtor_204052300_p#8_sharppy'
# s3_og = f'{og_indir}/{choice3}'
# s3_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice3}_extended_adjusted'
#
# choice4 = 'nontor_203070720_dsm_sharppy'
# s4_og = f'{og_indir}/{choice4}'
# s4_new = f'{adjusted_indir}/{rh_choice}/{cape_choice}/{choice4}_extended_adjusted'


plot_skewt_logp({'s1': (s1_og,s1_new), 's2': (s2_og,s2_new), 's3': (s3_og,s3_new), 's4': (s4_og,s4_new)})

###############################################################################

outpath = 'D:/cold_pool_mwr/soundings'
plt.savefig(f'{outpath}/{rh_choice}_{cape_choice}.pdf', bbox_inches='tight')

