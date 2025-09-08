#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 14:27:39 2024

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import metpy.calc
from metpy.units import units
import os


# indir = '/t1/topping/runs/1500/'
indir = '/t1/topping/runs/2500/'
# indir = '/t1/topping/runs/3500/'

runs = ['mm','md','dm','dd']

CAPE = '2500'


for folder in os.listdir(indir):
    
    if os.path.isdir(os.path.join(indir,folder)) and folder in runs:
        
        print(folder[:2]+' -----')
        plot = True
        run = indir+folder+'/run/'

        ds0 = xr.open_dataset(indir+folder+'/run/cm1out_000001.nc', 
                              decode_times=True).squeeze(('one','time'))
        
        heights = ds0.zh
        
        theta = ds0.th0.mean(dim=['xh','yh'])
        prs = ds0.prs.mean(dim=['xh','yh'])
        qv = ds0.qv0.mean(dim=['xh','yh'])
        
        temp = metpy.calc.temperature_from_potential_temperature(prs*units.Pa,
                                                                 theta*units.kelvin)
        
        rh = metpy.calc.relative_humidity_from_mixing_ratio(prs*units.hPa,temp,qv)
        
        if 'mm' in folder:
            mm_rh = rh
            # mm_prs = prs/100
        elif 'md' in folder:
            md_rh = rh
            # md_prs = prs/100
        elif 'dm' in folder:
            dm_rh = rh
            # dm_prs = prs/100
        elif 'dd' in folder:
            dd_rh = rh
            # dd_prs = prs/100
        else:
            pass
        
        
fig,ax = plt.subplots(figsize=(10,10))
                      
ax.set_ylabel('Height (km)', fontsize=16)
ax.set_xlabel('Relative Humidity (%)', fontsize=16)
       
ax.plot(mm_rh,heights, label='Moist PBL / Moist FT',
        c='#005AB5', linestyle='solid', linewidth=2.5)
ax.plot(md_rh,heights, label='Moist PBL / Dry FT',
        c='#005AB5', linestyle='dashed', linewidth=2.5)
ax.plot(dm_rh,heights, label='Dry PBL / Moist FT',
        c='#DC3220', linestyle='solid', linewidth=2.5)
ax.plot(dd_rh,heights, label='Dry PBL / Dry FT',
        c='#DC3220', linestyle='dashed', linewidth=2.5)

ax.xaxis.set_major_locator(MultipleLocator(10))
ax.xaxis.set_minor_locator(MultipleLocator(5))
ax.yaxis.set_major_locator(MultipleLocator(1))
ax.yaxis.set_minor_locator(MultipleLocator(0.5))

ax.set_xlim(xmin=0,xmax=100)
ax.set_ylim(ymin=0,ymax=12)

ax.tick_params(axis='both', which='major', labelsize=12, length=8, width=2)

ax.grid(which='both',axis='both', c='dimgray', alpha=0.5, ls='--')
ax.legend(loc='lower left',fontsize=16)


outpath = indir + 'figures/'
plt.savefig(outpath+'pdf/'+CAPE+'_base_state_RH'+'.pdf',bbox_inches='tight')
plt.savefig(outpath+'png/'+CAPE+'_base_state_RH''.png',dpi=300,bbox_inches='tight')

