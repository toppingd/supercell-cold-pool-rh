#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 14:02:49 2024

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import cmasher as cmr
import numpy as np
import pandas as pd
import os
from sklearn.cluster import KMeans


def isolate_cp(cold_pool, n_cluster=100, xthresh=20, ythresh=250):
    
    mask = cold_pool!=0
    coords = np.argwhere(mask)
    values = cold_pool[mask]
          
    weights = 1 - 0.5 * (np.abs(values) / np.max(np.abs(values)))
    weighted_coords = coords * weights[:, np.newaxis]
    
    X = np.hstack((weighted_coords, values.reshape(-1,1)))
    
    
    try:
        kmeans = KMeans(n_clusters=n_cluster, random_state=42)
        labels = kmeans.fit_predict(X)
    except:
        return cold_pool


    # centroids = []
    remove_clusters = []
    for cluster_id in range(n_cluster):
        cluster_points = coords[labels == cluster_id]
        centroid = cluster_points.mean(axis=0)
        
        if centroid[1] < xthresh:
            remove_clusters.append(cluster_id)
        
        if centroid[0] > ythresh:
            remove_clusters.append(cluster_id)
        # centroids.append(centroid)
    
    # storm_center = np.array(storm_center)
    # nw_corner = np.array([288,0])
    
    # distances = [np.linalg.norm(centroid - storm_center) for centroid in centroids]
    # distances = [np.linalg.norm(centroid - nw_corner) for centroid in centroids]
    
    # farthest_cluster = np.argmax(distances)
    # farthest_cluster = -1#np.argmin(distances)
    
    # label_map = -1 * np.ones_like(cold_pool, dtype=int)
    retained_mask = np.zeros_like(cold_pool, dtype=bool)
    for idx, (i, j) in enumerate(coords):
        if labels[idx] not in remove_clusters:#!= farthest_cluster:
            # label_map[i, j] = labels[idx]
            retained_mask[i, j] = True

    # plt.imshow(label_map, cmap='viridis', origin='lower')      

    retained_cp = np.full_like(cold_pool, 0)
    retained_cp[retained_mask] = cold_pool[retained_mask]
    
    return retained_cp


def cp_data(run,f,x_in,y_in):

    ds = xr.open_dataset(run+f, decode_times=True)
    timestep = ds.time.dt.seconds.values[0]/60

    print('\t\t--> '+f+'\t'+str(timestep))
    
    filenum = f[-9:]
    ds_outflow = xr.open_dataset(run+'outflow_'+filenum)
    
    x_center = ds.xh.sel(xh=x_in, method='nearest').values
    y_center = ds.yh.sel(yh=y_in, method='nearest').values
    
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
    
    
    diff = abs(ds.xh.sel(xh=slice(x_center+bbox[0],x_center+bbox[1]))-x_center)
    ixc = np.where(diff==min(diff))[0][0]
    diff = abs(ds.yh.sel(yh=slice(y_center+bbox[2],y_center+bbox[3]))-y_center)
    iyc = np.where(diff==min(diff))[0][0]+1
    
    # indices for subset x bounds
    diff = abs(ds.xh-(x_center+bbox[0]))
    ix1 = np.where(diff==min(diff))[0][0]
    diff = abs(ds.xh-(x_center+bbox[1]))
    ix2 = np.where(diff==min(diff))[0][0]+1

    # indices for subset y bounds
    diff = abs(ds.yh-(y_center+bbox[2]))
    iy1 = np.where(diff==min(diff))[0][0]
    diff = abs(ds.yh-(y_center+bbox[3]))
    iy2 = np.where(diff==min(diff))[0][0]+1
    
    indices = (ix1,ix2,iy1,iy2)
    
    x = ds.xh.values
    y = ds.yh.values

    
    b = ds_outflow.buoyancy2.sel(zh=lml,
                                 xh=slice(x_center+bbox[0],
                                          x_center+bbox[1]),
                                 yh=slice(y_center+bbox[2],
                                          y_center+bbox[3])).squeeze(('time'))
    
    dbz = ds.dbz.sel(zh=lml, 
                     xh=slice(x_center+bbox[0],
                              x_center+bbox[1]),
                     yh=slice(y_center+bbox[2],
                              y_center+bbox[3])).squeeze(('time'))
    
    uh = ds.uh.sel(xh=slice(x_center+bbox[0],
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
           
       sel_shape = np.shape(dbz)
       new_dbz = np.full((int(yshape),int(xshape)),np.nan)
       new_dbz[:sel_shape[0],:sel_shape[1]] = dbz
       dbz = new_dbz
           
       sel_shape = np.shape(uh)
       new_uh = np.full((int(yshape),int(xshape)),np.nan)
       new_uh[:sel_shape[0],:sel_shape[1]] = uh
       uh = new_uh
       
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
    try: 
        lcl_3d = lcl[None,:,:]
    except:
        lcl_3d = lcl.values[None,:,:]
    z_3d = z[:,None,None]
    lcl_mask = z_3d <= lcl_3d
        
    lh_subcloud = np.nanmean(np.where(lcl_mask, lh, np.nan), axis=0)
       
    b_condition = np.where(b<=-0.01, b, 0)
    cp_condition = np.where(lh_subcloud<-8e-6, b_condition, 0)
    

    if (cp_condition.size!=0) & (cp_condition[cp_condition!=0].size!=0):
        cp_isolated = isolate_cp(cp_condition,
                                 n_cluster=100, xthresh=20, ythresh=250)
        
        cp_isolated[cp_isolated==0] = np.nan

    else:
        cp_isolated = np.zeros_like(b)
    
    
    ds_outflow.close()
    ds.close()

    return b_condition, cp_isolated, dbz, uh, x, y, indices


def make_plot(fig,ax,x,y,indices,sfc_b_tseries,cp_tseries,dbz_tseries,
              uh_series,folder,indir):    

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
    
    ix1,ix2,iy1,iy2 = indices
    plotx = range(ix1,ix1 + np.shape(dbz_tseries)[2])
    ploty = range(iy1,iy1 + np.shape(dbz_tseries)[1])  
    
        
    cp_comp = np.nanmean(cp_tseries,axis=0)
    cp_mask = np.ma.masked_greater(cp_comp,-0.01)
    norm = colors.Normalize(vmin=-0.2, vmax=0)
    cmap = cmr.voltage
    cp_plot = axs[i].pcolormesh(plotx, ploty, cp_mask, 
                                shading='gouraud',cmap=cmap,norm=norm,
                                zorder=0)
    
    sfc_b_comp = np.nanmean(sfc_b_tseries,axis=0)
    axs[i].contour(plotx, ploty, sfc_b_comp,[-0.01],
                   colors='purple',linestyles='dashed',linewidths=2, 
                   zorder=1)
    
    ref_comp = np.nanmean(dbz_tseries,axis=0)
    axs[i].contour(plotx, ploty, ref_comp,[10],
                   colors='k',linestyles='solid',
                   linewidths=2,zorder=1)
    
    uh_comp = np.nanmean(uh_tseries,axis=0)
    axs[i].contour(plotx, ploty, uh_comp,[500],
                   colors='goldenrod',
                   linewidths=2,zorder=2) 
    
   
    axs[i].set_xlim(ix1,ix2-1)
    axs[i].set_ylim(iy1,iy2-1)
    
    interval = 10
    
    xticks = np.arange(ix1,ix2-1,round(interval/hspace))
    axs[i].set_xticks(xticks)
    xlabels = [x[i]-x[ix1] for i in xticks]
    axs[i].set_xticklabels([interval*round(int(l)/interval) for l in xlabels])
    
    yticks = np.arange(iy1,iy2-1,round(interval/hspace))
    axs[i].set_yticks(yticks)
    ylabels = [y[i]-y[iy1] for i in yticks]
    axs[i].set_yticklabels([interval*round(int(l)/interval) for l in ylabels])
    
    
    return cp_plot  


###############################################################################
###############################################################################

# Core set of simulations
# indir = '/t1/topping/runs/2500/'

# CAPE sensitivity
# indir = '/t1/topping/runs/1500/'
indir = '/t1/topping/runs/3500/'

# Microphysics sensitivity
# indir = '/t1/topping/runs/morrison/'
# indir = '/strm4/topping/runs/nssl3/'

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
# runs = ['md']
member = '0'

HODO = 'QT'
CAPE = '2500'
MP = 'NSSL'

st = 123     # start time
et = 124    # end time

ft = 45   # first time after initialization
ff = 2    # number of first file after initialization
dt = 1    # large timestep (minutes)

# file numbers based on start and end times
sf = ((st-ft)/dt)+ff 
ef = ((et-ft)/dt)+ff


fig,axs = plt.subplots(2,2,figsize=(16,11.5))
axs = axs.flatten()

plot=False

for folder in os.listdir(indir):

    sfc_b_tseries = []
    cp_tseries = []
    dbz_tseries = []
    uh_tseries = []

    if os.path.isdir(os.path.join(indir,folder)) and folder[:2] in runs:
       
        print(folder[:2]+' -----')
        
        if int(member) != 0:
            run = indir+folder+'/'+folder[:2]+member+'/run/'
            outpath = indir+'figures/member'+member+'/'
        else:
            run = indir+folder+'/run/'
            outpath = indir+'figures/'
        
        # comp_ds = xr.open_dataset(run+'basic_comps.nc', decode_times=True)

        
        # cp_comp = comp_ds.b_comp
        
        # ref_comp = comp_ds.ref_comp
        
        # uh_comp = comp_ds.uh_comp
        
        
        # comp_ds.close()
        
        
        # if 'mm' in folder:
        #     i=0
        #     title='  (a)  Moist PBL / Moist FT'#-' + HODO + '-' + CAPE
        # elif 'md' in folder:
        #     i=1
        #     title='  (b)  Moist PBL / Dry FT'#-' + HODO + '-' + CAPE
        # elif 'dm' in folder:
        #     i=2
        #     title='  (c)  Dry PBL / Moist FT'#-' + HODO + '-' + CAPE
        # elif 'dd' in folder:
        #     i=3
        #     title='  (d)  Dry PBL / Dry FT'#-' + HODO + '-' + CAPE

        
        # axs[i].set_title(title,fontsize=20,loc='left')
        
        
        # cp_mask = np.ma.masked_greater(cp_comp,-0.01)
        # norm = colors.Normalize(vmin=-0.18, vmax=0)
        # # cmap = 'BuPu_r'
        # cmap = cmr.voltage
        # cp_plot = axs[i].pcolormesh(cp_mask, 
        #                             shading='gouraud',cmap=cmap,norm=norm,
        #                             zorder=0)
        
        # axs[i].contour(cp_comp,[-0.01],
        #                colors='purple',linestyles='dashed',linewidths=2, 
        #                zorder=1)
        
        # axs[i].contour(ref_comp,[10],
        #                colors='k',linestyles='solid',
        #                linewidths=2,zorder=1)
        
        # axs[i].contour(uh_comp,[500],
        #                colors='goldenrod',
        #                linewidths=2,zorder=2)  
        
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
            
                
                sfc_b,cp,dbz,uh,x,y,indices = cp_data(run,f,cx,cy)
                    
                sfc_b_tseries.append(sfc_b)
                cp_tseries.append(cp)
                dbz_tseries.append(dbz)
                uh_tseries.append(uh)
                
                i+=1
        
        if plot:
            cp_plot = make_plot(fig,axs,x,y,indices,sfc_b_tseries,cp_tseries,
                                dbz_tseries,uh_tseries,folder,indir)

    else:
        pass
    

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
cb = plt.colorbar(cp_plot,cax=cbar_ax, extend='min')
cb.set_label(label='Mean Buoyancy (m $s^{-2}$)',fontsize=18)
cb.ax.tick_params(labelsize=14) 

plt.subplots_adjust(wspace=0.08, hspace=0.2)

# if int(member) != 0:
#     plt.savefig(outpath+'pdf/'+'member'+member+ '_90min_cp_comp'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/'+'member'+member+ '_90min_cp_comp'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + MP + '_90min_cp_comp'+'.pdf')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + MP + '_90min_cp_comp'+'.png',dpi=300)

outpath = '/strm4/topping/revised_figs/cp_comp_2500_2.pdf'
# plt.savefig(outpath, bbox_inches='tight')

