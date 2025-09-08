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
    
    axs = [None,None,None,None]

    for a, (regime, file_path) in enumerate(file_paths.items()):
        print(a, regime, file_path)
        
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
            
            
        # Read in the data
        with open(file_path, 'r') as f:
            global data
            data = f.readlines()[6:-1]
            for i in range(len(data)):
                data[i] = data[i].split(',')
                for j in range(len(data[i])):
                    data[i][j] = float(data[i][j].strip())


        # Extract the necessary columns and convert to appropriate units
        global prs, heights, temperature, dewpoint, wdir, wspd
        prs = np.array([data[h][0] for h in range(len(data))]) * units('hPa')
        heights = np.array([data[h][1] for h in range(len(data))]) * units.meter
        temperature = np.array([data[h][2] for h in range(len(data))]) * units('degC')
        dewpoint = np.array([data[h][3] for h in range(len(data))]) * units('degC')
        wdir= np.array([data[h][4] for h in range(len(data))]) * units('degrees')
        wspd = np.array([data[h][5] for h in range(len(data))]) * units('knots')


        # Create a profile object for SHARPpy
        prof = profile.create_profile(pres=prs.magnitude,
                                      hght=heights.magnitude,
                                      tmpc=temperature.magnitude, 
                                      dwpc=dewpoint.magnitude,
                                      wdir=wdir.magnitude,
                                      wspd=wspd.magnitude)
        
        
        mlparcel = params.parcelx(prof, flag=4)  
        
        axs[a].semilogy(prof.tmpc[~prof.tmpc.mask], prof.pres[~prof.tmpc.mask], 'r', lw=3)
        axs[a].semilogy(prof.dwpc[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'g', lw=3)
        axs[a].semilogy(prof.vtmp[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'r--', lw=2)
        # axs[a].semilogy(prof.wetbulb[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'c-')
        
        global ttrace
        ttrace = mlparcel.ttrace

        axs[a].semilogy(mlparcel.ttrace, mlparcel.ptrace, 'k--', lw=2)
        
        # Highlight the 0 C and -20 C isotherms.
        axs[a].axvline(0, color='steelblue', ls='--', lw=1.5)
        axs[a].axvline(-20, color='steelblue', ls='--', lw=1.5)
        
        # Disables the log-formatting that comes with semilogy
        axs[a].yaxis.set_major_formatter(ScalarFormatter())
        axs[a].set_yticks(np.linspace(100,1000,10))
        axs[a].set_xticks(np.linspace(-100,50,16))
        axs[a].set_ylim(1050,100)
        axs[a].set_xlim(-45,45)
        axs[a].set_xticks(np.arange(-40, 50, 10))

        axs[a].tick_params(axis='both', which='major',labelsize=18,
                           length=8, width=2)
        axs[a].tick_params(axis='x', which='major',rotation=-30)
        
        
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

# CAPE = '3500'


# mm = '/t1/topping/soundings/2500CAPE/mm_extended_sharppy'
# mm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_'+CAPE+'_extended_sharppy'
# mm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_203050501_lzk_sigtor_sharppy' # 2500
# mm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_204062402_osh_sigtor_sharppy' # 1500
# mm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_200051722_lxn_sigtor_sharppy' # 3500
mm = 'C:/Users/dtopp/OneDrive/TAMU/Research/ms/soundings/rh_sort/moistPBL_moistFT/sharppy_soundings/sharppy_comp'

# md = '/t1/topping/soundings/2500CAPE/md_extended_sharppy'
# md = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_'+CAPE+'_extended_sharppy'
# md = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_200022606_crs_nontor_sharppy' # 2500
# md = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_203111722_gls_wektor_sharppy' # 1500
# md = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_203050807_adm_sigtor_sharppy' # 3500
md = 'C:/Users/dtopp/OneDrive/TAMU/Research/ms/soundings/rh_sort/moistPBL_dryFT/sharppy_soundings/sharppy_comp'

# dm = '/t1/topping/soundings/2500CAPE/dm_extended_sharppy'
# dm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_'+CAPE+'_extended_sharppy'
# dm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_200061122_mot_wektor_sharppy' # 2500
# dm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_201050501_cot_nontor_sharppy' # 1500
# dm = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_201051623_bie_nontor_sharppy' # 3500
dm = 'C:/Users/dtopp/OneDrive/TAMU/Research/ms/soundings/rh_sort/dryPBL_moistFT/sharppy_soundings/sharppy_comp'

# dd = '/t1/topping/soundings/2500CAPE/dd_extended_sharppy'
# dd = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_'+CAPE+'_extended_sharppy'
# dd = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_200070922_ggw_nontor_sharppy' # 2500
# dd = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_201050200_aum_sigtor_sharppy' # 1500
# dd = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_204071823_gfk_sigtor_sharppy' # 3500
dd = 'C:/Users/dtopp/OneDrive/TAMU/Research/ms/soundings/rh_sort/dryPBL_dryFT/sharppy_soundings/sharppy_comp'


plot_skewt_logp({'mm':mm,'md':md,'dm':dm,'dd':dd})

###############################################################################

# outpath = '/t1/topping/runs/2500/figures/'
# outpath = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/'

# plt.savefig(outpath+'pdf/'+CAPE+'_thermo_profiles'+'.pdf',bbox_inches='tight')
# plt.savefig(outpath+'png/'+CAPE+'_thermo_profiles'+'.png',dpi=300,bbox_inches='tight')

# plt.savefig(outpath+CAPE+'_thermo_profiles_original'+'.pdf',bbox_inches='tight')
# plt.savefig(outpath+CAPE+'_thermo_profiles_final'+'.pdf',bbox_inches='tight')

outpath = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'
plt.savefig(outpath+'composite_thermo_profiles'+'.pdf',bbox_inches='tight')
# plt.show()
