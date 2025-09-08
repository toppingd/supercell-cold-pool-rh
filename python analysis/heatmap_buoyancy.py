#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 14:01:12 2024

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.patheffects as path_effects
import cmasher as cmr
import numpy as np
import pandas as pd
import os
import gc
from sklearn.cluster import KMeans


def isolate_cp(cold_pool, n_cluster=100, xthresh=20, ythresh=250):
    
    mask = cold_pool!=0
    coords = np.argwhere(mask)
    values = cold_pool[mask]
          
    weights = 1 - 0.5 * (np.abs(values) / np.max(np.abs(values)))
    weighted_coords = coords * weights[:, np.newaxis]
    
    X = np.hstack((weighted_coords, values.reshape(-1,1)))
    
    kmeans = KMeans(n_clusters=n_cluster, random_state=42)
    labels = kmeans.fit_predict(X)

    remove_clusters = []
    for cluster_id in range(n_cluster):
        cluster_points = coords[labels == cluster_id]
        centroid = cluster_points.mean(axis=0)
        
        if centroid[1] < xthresh:
            remove_clusters.append(cluster_id)
        
        if centroid[0] > ythresh:
            remove_clusters.append(cluster_id)
      
    retained_mask = np.zeros_like(cold_pool, dtype=bool)
    for idx, (i, j) in enumerate(coords):
        if labels[idx] not in remove_clusters:
            retained_mask[i, j] = True

    retained_cp = np.full_like(cold_pool, 0)
    retained_cp[retained_mask] = cold_pool[retained_mask]
    
    return retained_cp


def cp_data(run,ds0,f,cx_in,cy_in):

    ds = xr.open_dataset(run+f, decode_times=True)
    timestep = ds.time.dt.seconds.values[0]/60

    print('\t\t--> '+f+'\t'+str(timestep))
    
    filenum = f[-9:]
    ds_outflow = xr.open_dataset(run+'outflow_'+filenum)
    
    x_center = ds.xh.sel(xh=cx_in, method='nearest').values
    y_center = ds.yh.sel(yh=cy_in, method='nearest').values
    
    zmax = ds.zh.sel(zh=5, method='nearest')
    lml = ds.zh.sel(zh=0, method='nearest')
    
    global bbox, hspace
    bbox = [-25.0,65.0,-15.0,57.0]
    
    hspace = round(ds.xh.values[1]-ds.xh.values[0],2)
    
    # make sure that all arrays will be same shape
    xshape = (bbox[1]-bbox[0])/hspace
    yshape = (bbox[3]-bbox[2])/hspace
    
    xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox[0],
                                        x_center+bbox[1])))[0]
    ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox[2],
                                        y_center+bbox[3])))[0]
    if xtest != xshape:
        bbox[1] += (xshape - xtest)*hspace
        xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox[0],
                                            x_center+bbox[1])))[0]
    if ytest != yshape:
        bbox[3] += (yshape - ytest)*hspace
        ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox[2],
                                            y_center+bbox[3])))[0]
    
    xsel = ds.xh.sel(xh=slice((x_center+bbox[0]),
                              (x_center+bbox[1])))
    
    ysel = ds.yh.sel(yh=slice((y_center+bbox[2]),
                              (y_center+bbox[3])))

    x1diff = np.round(xsel.values[0] - x_center, 2)
    x2diff = np.round(xsel.values[-1]- x_center, 2)
    y1diff = np.round(ysel.values[0]- y_center, 2)
    y2diff = np.round(ysel.values[-1] - y_center, 2)
    bbox_sel = [x1diff,x2diff,y1diff,y2diff]

    
    b = ds_outflow.buoyancy2.sel(zh=lml,
                                 xh=slice(x_center+bbox[0],
                                          x_center+bbox[1]),
                                 yh=slice(y_center+bbox[2],
                                          y_center+bbox[3])).squeeze(('time')) 
    
    lh = ds.ptb_mp.sel(zh=slice(0,zmax),
                       xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                       yh=slice(y_center+bbox[2],
                                y_center+bbox[3])).squeeze(('time'))
    
    lcl = ds.lcl.sel(xh=slice(x_center+bbox[0],
                              x_center+bbox[1]),
                     yh=slice(y_center+bbox[2],
                              y_center+bbox[3])).squeeze(('time'))/1000
    
    
    if bbox_sel != bbox:

       sel_shape = np.shape(b)
       new_b = np.full((int(yshape),int(xshape)),np.nan)
       new_b[:sel_shape[0],:sel_shape[1]] = b
       b = new_b
       
       sel_shape = np.shape(lh)
       sel_shape = np.shape(lh)
       new_lh = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
       new_lh[:sel_shape[0],:sel_shape[1]] = lh
       lh = new_lh
       
       sel_shape = np.shape(lcl)
       new_lcl = np.full((int(yshape),int(xshape)),np.nan)
       new_lcl[:sel_shape[0],:sel_shape[1]] = lcl
       lcl = new_lcl
       
       
    z = ds.zh.sel(zh=slice(0,zmax)).values
    lcl_3d = lcl[None,:,:]
    z_3d = z[:,None,None]
    lcl_mask = z_3d <= lcl_3d
        
    lh_subcloud = np.nanmean(np.where(lcl_mask, lh, np.nan), axis=0)
       
    b_condition = np.where(b<=-0.01, b, 0)
    cp_condition = np.where(lh_subcloud<-8e-6, b_condition, 0)
    
    cp_isolated = isolate_cp(cp_condition,
                          n_cluster=100, xthresh=20, ythresh=250)
    
    cp_isolated[cp_isolated==0] = np.nan

    cp_hist = np.histogram(cp_isolated,50,range=(-0.25,-0.0))
    # cp_hist = np.histogram(cp_isolated,80,range=(-0.4,-0.0))
    bins = cp_hist[1][:-1]
    
    cp_mean = np.nanmean(cp_isolated)

    
    ds_outflow.close()
    ds.close()
    gc.collect()

    return cp_hist[0],bins, cp_mean, timestep


def make_plot(fig,ax,times,hist_tseries,bins,mean_tseries,folder,indir):    

    if 'mm' in folder:
        label='Moist PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=0
    elif 'md' in folder:
        label='Moist PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=1
    elif 'dm' in folder:
        label='Dry PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=2
    elif 'dd' in folder:
        label='Dry PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
        i=3
    else:
        pass
    
    axs[i].set_title(label,fontsize=22,loc='left')
    
    cp_grid = np.asarray(hist_tseries).transpose()
    
    norm = colors.Normalize(vmin=0,vmax=1800)
    # cmap = cmr.fall_r
    cmap = cmr.gothic_r
    cp_plot = axs[i].pcolormesh(times,bins,cp_grid, 
                                shading='gouraud',cmap=cmap,norm=norm,
                                zorder=0)
    
    axs[i].plot(times, mean_tseries,
                color='w', linestyle='solid', linewidth=5)
    
    axs[i].plot(times, mean_tseries,
                color='k', linestyle='dashed', linewidth=3)
    
    # shadow_effect = path_effects.withStroke(linestyle='solid', linewidth=8, foreground='white')
    # line.set_path_effects([shadow_effect])
    
    axs[i].set_xlim(min(times),max(times))
    axs[i].set_ylim(np.min(bins),-0.01)    
    
    return cp_plot  
    

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
# runs = ['dm']
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


fig,axs = plt.subplots(4,1,figsize=(15,20))#, sharex=True, sharey=True)
axs = axs.flatten()

plot=False
# fig,axs = plt.subplots(1,1,figsize=(10,7.2))

for folder in os.listdir(indir):

    hist_tseries = []
    mean_tseries = []
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

        ds0 = xr.open_dataset(run+'cm1out_000001.nc', decode_times=True)
        
        pos_df = pd.read_csv(run+'rm_tracking.csv')
        x_locs = np.asarray(pos_df['x_smooth'])
        y_locs = np.asarray(pos_df['y_smooth'])
        locs = (x_locs,y_locs)
        
        i=0
        # i -= st-ft
        print('\tGetting Data:')
        for file in sorted(os.listdir(run)):
            if os.path.isfile(os.path.join(run,file)) and 'cm1out_000' in file\
            and (sf <= int(file[-6:-3]) <= ef):
                plot=True

                f = file
                
                cx = locs[0][st-ft+i]
                cy = locs[1][st-ft+i]
                
                cp_hist, bins, cp_mean, timestep = cp_data(run,ds0,f,cx,cy)
                    
                hist_tseries.append(cp_hist)
                mean_tseries.append(cp_mean)
                times.append(timestep)
                
                i+=1

        ds0.close()
        
        if plot:
            cp_plot = make_plot(fig,axs,times,hist_tseries,bins,mean_tseries,folder,indir)

    else:
        pass
    

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


# if int(member) != 0:
#     plt.savefig(outpath+'pdf/new/'+'member'+member+ '_b_heatmap'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+'member'+member+ '_b_heatmap'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_b_heatmap2'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_b_heatmap2'+'.png',dpi=300,bbox_inches='tight')

outpath = '/strm4/topping/revised_figs/cp_heatmap_2500.pdf'
plt.savefig(outpath, bbox_inches='tight')
