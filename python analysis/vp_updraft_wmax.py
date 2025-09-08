#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 11:04:49 2023

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import gc


def get_data(run,f,cx_in,cy_in):

    ds = xr.open_dataset(run+f, decode_times=True).squeeze(('one','time'))
    time = ds.time.dt.seconds/60
    
    print('\t\t--> '+f[-19:]+'\t'+str(time.values))

    x_center = ds.xh.sel(xh=cx_in, method='nearest')
    y_center = ds.yh.sel(yh=cy_in, method='nearest')
    
    heights = ds.zh.sel(zh=slice(0,9))
    
    
    bbox_storm = [-25.0,65.0,-15.0,57.0]
   
    global hspace
    hspace = round(ds.xh.values[1]-ds.xh.values[0],2)
    
    # make sure that all arrays will be same shape
    xshape = (bbox_storm[1]-bbox_storm[0])/hspace
    yshape = (bbox_storm[3]-bbox_storm[2])/hspace
    # print(xshape,yshape)
    xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox_storm[0],
                                        x_center+bbox_storm[1])))[0]
    ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox_storm[2],
                                        y_center+bbox_storm[3])))[0]
    if xtest != xshape:
        bbox_storm[1] += (xshape - xtest)*hspace
        xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox_storm[0],
                                            x_center+bbox_storm[1])))[0]
    if ytest != yshape:
        bbox_storm[3] += (yshape - ytest)*hspace
        ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox_storm[2],
                                            y_center+bbox_storm[3])))[0]

    
    w_storm = ds.winterp.sel(zh=heights,
                             xh=slice(x_center+bbox_storm[0],
                                      x_center+bbox_storm[1]),
                             yh=slice(y_center+bbox_storm[2],
                                      y_center+bbox_storm[3]))
    global downdraft
    downdraft = w_storm.where(w_storm<0, w_storm, np.nan)
    
    max_downdraft_prof = np.nanmin(downdraft, axis=(1,2))
    
    
    bbox_inner = [-12,18,-8,16]
    
    # make sure that all arrays will be same shape
    xshape = (bbox_inner[1]-bbox_inner[0])/hspace
    yshape = (bbox_inner[3]-bbox_inner[2])/hspace
    # print(xshape,yshape)
    xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox_inner[0],
                                        x_center+bbox_inner[1])))[0]
    ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox_inner[2],
                                        y_center+bbox_inner[3])))[0]
    if xtest != xshape:
        bbox_inner[1] += (xshape - xtest)*hspace
        xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox_inner[0],
                                            x_center+bbox_inner[1])))[0]
    if ytest != yshape:
        bbox_inner[3] += (yshape - ytest)*hspace
        ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox_inner[2],
                                            y_center+bbox_inner[3])))[0]
    
    w_inner = ds.winterp.sel(zh=heights,
                             yh=slice(y_center+bbox_inner[2],y_center+bbox_inner[3]),
                             xh=slice(x_center+bbox_inner[0],x_center+bbox_inner[1]))
    
    updraft = w_inner.where(w_inner>0, w_inner, np.nan)
    
    max_updraft_prof = np.nanmax(updraft, axis=(1,2))
    
    ds.close()
    gc.collect()
        
    return max_updraft_prof,max_downdraft_prof,time,heights


def make_plot(fig,axs,heights,
              tmean_updraft_prof,tmean_downdraft_prof,
              folder,indir):

    if 'mm' in folder:
        color='#005AB5'
        style = 'solid'
        label='Moist PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
        order=0
    elif 'md' in folder:
        color='#005AB5'
        style='dashed'
        label='Moist PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
        order=1
    elif 'dm' in folder:
        color='#DC3220'
        style='solid'
        label='Dry PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
        order=2
    elif 'dd' in folder:
        color='#DC3220'
        style='dashed'
        label='Dry PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
        order=3
    else:
        pass
    
    updraft_plot = axs.plot(tmean_updraft_prof,heights,
                            color=color,linewidth=2.5,
                            linestyle=style,label=label)
    
    axs.plot(tmean_downdraft_prof,heights,
             color=color,linewidth=2.5,
             linestyle=style,label=label)
    
    axs.axvline(x=0, color='k', linestyle='--')

    return updraft_plot,order


###############################################################################
###############################################################################

# Core set of simulations
indir = '/t1/topping/runs/2500/'

# CAPE sensitivity
# indir = '/t1/topping/runs/1500/'
# indir = '/t1/topping/runs/3500/'

# Microphysics sensitivity
# indir = '/t1/topping/runs/2500_morrison/'
# indir = '/strm4/topping/runs/nssl3/'

# Surface drag sensitivity
# indir = '/t1/topping/runs/freeslip/'

# Shear sensitivity
# indir = '/t1/topping/runs/sigtor/'
# indir = '/t1/topping/runs/sigtor2/'

# Random temperature perturbations
# indir = '/t1/topping/runs/ensemble/'
# indir = '/strm4/topping/runs/ensemble/'

###############################################################################

runs = ['mm','md','dm','dd']
member = '0' # ensemble member number for random temperature perturbations

HODO = 'QT'
CAPE = '2500'
MP = 'NSSL'
# MP = 'MORRISON'

st = 90    # start time
et = 180    # end time

ft = 45   # first time after initialization
ff = 2    # number of first file after initialization
dt = 1    # large timestep (minutes)

# file numbers based on start and end times
sf = ((st-ft)/dt)+ff 
ef = ((et-ft)/dt)+ff


fig,axs = plt.subplots(figsize=(10,6),layout='constrained')

# axs.set_title('Time Averaged Vertical Profiles of wmax (60-150 min)',
#               fontsize=16,fontweight='bold',y=1)

plot_lines = []
orders = []

for folder in os.listdir(indir):

    updraft_profs = []
    downdraft_profs = []
    times = []

    if os.path.isdir(os.path.join(indir,folder)) and folder in runs:
        
        print(folder[:2]+' -----')
        plot = True
        
        if int(member) != 0:
            run = indir+folder+'/'+folder[:2]+member+'/run/'
            outpath = indir+'figures/member'+member+'/'
        else:
            run = indir+folder+'/run/'
            outpath = indir+'figures/'
        
        pos_df = pd.read_csv(run+'rm_tracking.csv')
        x_locs = np.asarray(pos_df['x_smooth'])
        y_locs = np.asarray(pos_df['y_smooth'])
        locs = (x_locs,y_locs)
         
        i=0      
        print('\tGetting Data:')   
        for file in sorted(os.listdir(run)):
            if os.path.isfile(os.path.join(run,file)) and 'cm1out_000' in file\
            and (sf <= int(file[-6:-3]) <= ef):
                f = file
                
                cx = locs[0][st-ft+i]
                cy = locs[1][st-ft+i]
                
                updraft_prof,downdraft_prof,time,heights = get_data(run,f,cx,cy)

                updraft_profs.append(updraft_prof)
                downdraft_profs.append(downdraft_prof)
                times.append(time)
                
                i+=1

            else:
                pass
            
            
        tmean_updraft_prof = np.nanmean(updraft_profs,axis=0)
        tmean_downdraft_prof = np.nanmean(downdraft_profs,axis=0)

        plot_line = make_plot(fig,axs,heights,
                              tmean_updraft_prof,tmean_downdraft_prof,
                              folder,indir)
        
        plot_lines.append(plot_line[0][0])
        orders.append(plot_line[1])

        #axs.set_xticks(-0.01,0)
        axs.tick_params(axis='both', which='major', labelsize=14)
        
        axs.set_xlabel('Vertical Velocity (m $\mathregular{s^{-1}}$)', fontsize=16)
        axs.set_ylabel('Height (km)', fontsize=16)

        axs.set_xticks(np.linspace(-30,60,10))
        axs.set_xlim(-30,60)
        axs.set_ylim(0,6)

    else:
        pass
    
    
plot_lines_ordered = [None,None,None,None]
for i in range(len(orders)):
    plot_lines_ordered[orders[i]] = plot_lines[i]

axs.legend(handles=plot_lines_ordered, loc='best', fontsize=16)


if int(member) != 0:
    plt.savefig(outpath+'pdf/new/'+'member'+member+ '_w_vertical_prof'+'.pdf',bbox_inches='tight')
    plt.savefig(outpath+'png/new/'+'member'+member+ '_w_vertical_prof'+'.png',dpi=300,bbox_inches='tight')
else:
    plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_w_vertical_prof2'+'.pdf',bbox_inches='tight')
    plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_w_vertical_prof2'+'.png',dpi=300,bbox_inches='tight')


