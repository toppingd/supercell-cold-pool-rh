#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 14:02:49 2024

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
# from metpy.plots import ctables
import matplotlib.colors as colors
import cmweather as cmw
import numpy as np
import os


###############################################################################
###############################################################################

# Core set of simulations
indir = '/t1/topping/runs/2500/'

# CAPE sensitivity
# indir = '/t1/topping/runs/1500/'
# indir = '/t1/topping/runs/3500/'

# Microphysics sensitivity
# indir = '/t1/topping/runs/morrison/'
# indir = '/strm4/topping/runs/nssl_3moment/'

# Surface drag sensitivity
# indir = '/t1/topping/runs/freeslip/'

# Shear sensitivity
# indir = '/t1/topping/runs/sigtor/'
# indir = '/t1/topping/runs/sigtor2/'

# Random temperature perturbations
# indir = '/strm4/topping/runs/ensemble/'
# indir = '/t1/topping/runs/ensemble/'

###############################################################################

runs = ['mm','md','dm','dd']
member = '0'

HODO = 'QT'
CAPE = '2500'
MP = 'NSSL'


fig,axs = plt.subplots(2,2,figsize=(16,11.5))#, sharex=True, sharey=True)
axs = axs.flatten()

plot=False

# fig,axs = plt.subplots(1,1,figsize=(10,7.2))


for folder in os.listdir(indir):

    cp_tseries = []
    dbz_tseries = []
    uh_tseries = []
    times = []

    if os.path.isdir(os.path.join(indir,folder)) and folder[:2] in runs:
       
        print(folder[:2]+' -----')
        
        if int(member) != 0:
            run = indir+folder+'/'+folder[:2]+member+'/run/'
            outpath = indir+'figures/member'+member+'/'
        else:
            run = indir+folder+'/run/'
            outpath = indir+'figures/'
        
        comp_ds = xr.open_dataset(run+'basic_comps.nc', decode_times=True)

        
        cp_comp = comp_ds.b_comp
        
        ref_comp = comp_ds.ref_comp
        
        uh_comp = comp_ds.uh_comp
        
        
        comp_ds.close()
        
        
        if 'mm' in folder:
            i=0
            title='  (a)  Moist PBL / Moist FT'#-' + HODO + '-' + CAPE
        elif 'md' in folder:
            i=1
            title='  (b)  Moist PBL / Dry FT'#-' + HODO + '-' + CAPE
        elif 'dm' in folder:
            i=2
            title='  (c)  Dry PBL / Moist FT'#-' + HODO + '-' + CAPE
        elif 'dd' in folder:
            i=3
            title='  (d)  Dry PBL / Dry FT'#-' + HODO + '-' + CAPE

        
        axs[i].set_title(title,fontsize=20,loc='left')

        ref_mask = np.ma.masked_array(ref_comp,ref_comp<=10)
        # norm,cmap = ctables.registry.get_with_range('NWSReflectivity',0,75)
        cmap = 'HomeyerRainbow'
        norm = colors.Normalize(0,75)
        ref_plot = axs[i].pcolormesh(ref_mask, 
                                     shading='gouraud',cmap=cmap,norm=norm,
                                     zorder=0)
        
        axs[i].contour(cp_comp,[-0.01],
                       colors='purple',linestyles='dashed',linewidths=2, 
                       zorder=1)
        
        
        axs[i].contour(uh_comp,[500],
                       colors='k',
                       linewidths=2,zorder=2)          

    

axs[2].set_xlabel('x-distance (km)', fontsize=18)
axs[3].set_xlabel('x-distance (km)', fontsize=18)
axs[3].tick_params(axis='x', which='major', labelsize=14)

axs[0].set_ylabel('y-distance (km)', fontsize=18)
axs[0].tick_params(axis='y', which='major', labelsize=14)
axs[2].set_ylabel('y-distance (km)', fontsize=18)
axs[2].tick_params(axis='both', which='major', labelsize=14)

axs[0].tick_params(axis='x', which='major', labelcolor='white')
axs[1].tick_params(axis='both', which='major', labelcolor='white')
axs[3].tick_params(axis='y', which='major', labelcolor='white')

axs[0].tick_params(axis='both', which='major', length=8, width=2)
axs[1].tick_params(axis='both', which='major', length=8, width=2)
axs[2].tick_params(axis='both', which='major', length=8, width=2)
axs[3].tick_params(axis='both', which='major', length=8, width=2)


fig.subplots_adjust(right=0.8, hspace=0.26, wspace=0.25)
cbar_ax = fig.add_axes([0.82, 0.15, 0.01, 0.7])
cb = plt.colorbar(ref_plot,cax=cbar_ax, extend='max')
cb.set_label(label='Mean Reflectivity (dBZ)',fontsize=18)
cb.ax.tick_params(labelsize=14) 

plt.subplots_adjust(wspace=0.08, hspace=0.2)

# if int(member) != 0:
#     plt.savefig(outpath+'pdf/'+'member'+member+ '_90min_ref_comp'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/'+'member'+member+ '_90min_ref_comp'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + MP + '_90min_ref_comp'+'.pdf')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + MP + '_90min_ref_comp'+'.png',dpi=300)

outpath = '/strm4/topping/revised_figs/ref_comp_2500.pdf'
plt.savefig(outpath, bbox_inches='tight')


