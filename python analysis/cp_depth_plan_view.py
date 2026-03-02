#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 13:14:48 2024

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.colors import ListedColormap
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
    
    
    try:
        kmeans = KMeans(n_clusters=n_cluster, random_state=42)
        labels = kmeans.fit_predict(X)
    except:
        return cold_pool


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
    
    # plt.imshow(retained_cp, cmap='viridis', origin='lower') 
    
    return retained_cp


def cp_data(run,ds0,f,cx_in,cy_in):

    global ds
    ds = xr.open_dataset(run+f, decode_times=True)
    timestep = ds.time.dt.seconds.values[0]/60

    print('\t\t--> '+file+'\t'+str(timestep))
    
    filenum = f[-9:]
    ds_outflow = xr.open_dataset(run+'outflow_'+filenum)
    
    
    x_center = ds.xh.sel(xh=cx_in, method='nearest').values
    y_center = ds.yh.sel(yh=cy_in, method='nearest').values
    
    zmax = ds.zh.sel(zh=9, method='nearest')
    lml = ds.zh.sel(zh=0, method='nearest')
    # dz = ds.zh.values[1]-ds.zh.values[0]
    
    global bbox, hspace
    bbox = [-25.0,65.0,-15.0,57.0]
    # bbox=[ds.xh.values[0]-x_center,
    #       ds.xh.values[-1]-x_center,
    #       ds.yh.values[0]-y_center,
    #       ds.yh.values[-1]-y_center]
    
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

    
    # indicies for center
    global ixc,iyc
    diff = abs(ds.xh-x_center)
    ixc = np.where(diff==min(diff))[0][0]
    diff = abs(ds.xh-y_center)
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

    
    b = ds_outflow.buoyancy2.sel(zh=slice(0,zmax),
                                 xh=slice(x_center+bbox[0],
                                          x_center+bbox[1]),
                                 yh=slice(y_center+bbox[2],
                                          y_center+bbox[3])).squeeze(('time'))
    
    b_sfc = ds_outflow.buoyancy2.sel(zh=lml,
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
    
    # th_rho_pert = ds.ptb_mp.sel(zh=slice(0,zmax),
    #                     xh=slice(x_center+bbox[0],
    #                             x_center+bbox[1]),
    #                     yh=slice(y_center+bbox[2],
    #                             y_center+bbox[3])).squeeze(('time'))
    
    th_pert = ds.thpert.sel(zh=slice(0,zmax),
                            xh=slice(x_center+bbox[0],
                                     x_center+bbox[1]),
                            yh=slice(y_center+bbox[2],
                                     y_center+bbox[3])).squeeze(('time'))
    
    lcl = ds.lcl.sel(xh=slice(x_center+bbox[0],
                              x_center+bbox[1]),
                     yh=slice(y_center+bbox[2],
                              y_center+bbox[3])).squeeze(('time'))/1000
    
    
    if bbox_sel != bbox:
        
        sel_shape = np.shape(b_sfc)
        new_b_sfc = np.full((int(yshape),int(xshape)),np.nan)
        new_b_sfc[:sel_shape[0],:sel_shape[1]] = b_sfc
        b_sfc = new_b_sfc

        sel_shape = np.shape(b)
        new_b = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
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
        new_lh = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
        new_lh[:sel_shape[0],:sel_shape[1]] = lh
        lh = new_lh
        
        # sel_shape = np.shape(th_rho_pert)
        # new_th_rho_pert = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
        # new_th_rho_pert[:sel_shape[0],:sel_shape[1]] = th_rho_pert
        # th_rho_pert = new_th_rho_pert
        
        sel_shape = np.shape(th_pert)
        new_th_pert = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
        new_th_pert[:sel_shape[0],:sel_shape[1]] = th_pert
        th_pert = new_th_pert
        
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
        
    # mean subcloud (below LCL) latent heating rate
    lh_subcloud = np.nanmean(np.where(lcl_mask, lh, np.nan), axis=0)
       
    b_condition = np.where(b_sfc<=-0.01, b_sfc, 0)
    cp_condition = np.where(lh_subcloud<-8e-6, b_condition, 0)
    
    
    if (cp_condition.size!=0) & (cp_condition[cp_condition!=0].size!=0):
        cp_isolated = isolate_cp(cp_condition,
                                 n_cluster=100, xthresh=20, ythresh=250)
        
        # cp_isolated[cp_isolated==0] = np.nan
    
    else:
        cp_isolated = np.zeros_like(b_sfc)  
        
      
    cp_mask = cp_isolated==0
    cp_mask_3d = np.broadcast_to(cp_mask, np.shape(b))
    combined_mask = (b>-0.01)
    cpd_condition = cp_mask_3d | combined_mask

    cpd_i = np.argmax(cpd_condition, axis=0)
    zgrid = np.tile(z_3d, (1, np.shape(cpd_i)[0], np.shape(cpd_i)[1])) 
    yi, xi = np.meshgrid(np.arange(np.shape(cpd_i)[0]),
                         np.arange(np.shape(cpd_i)[1]),
                         indexing='ij')
    cpd = zgrid[cpd_i, yi, xi]*1000
    
    cpd_isolated = np.where(cp_isolated!=0, cpd, 0)
    
    #limit cold pool depth to the height of the LCL
    cpd_limited = np.where(cpd_isolated>lcl*1000, lcl*1000, cpd_isolated)


    ds_outflow.close()
    ds.close()
    gc.collect()
    
    # return b_sfc,cpd_isolated,dbz,uh,x,y,indices,timestep
    return b_sfc,cpd_limited,dbz,uh,x,y,indices,timestep


def make_plot(fig,ax,x,y,indices,cp_tseries,cpd_tseries,dbz_tseries,
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
    axs[i].contour(plotx,ploty, cp_comp,[-0.01],
                    colors='purple',linestyles='dashed',linewidths=1.5, 
                    zorder=1)
    
    cpd_comp = np.nanmean(cpd_tseries,axis=0)
    norm = colors.Normalize(vmin=50,vmax=2000)
    
    cmap = plt.cm.hot_r#cool
    cmaplist = [cmap(i) for i in range(cmap.N)]
    cmaplist[0] = (1.0, 1.0, 1.0, 1.0)  # Set the lowest value to white
    custom_cmap = ListedColormap(cmaplist)

    cpd_plot = axs[i].pcolormesh(plotx,ploty, cpd_comp, 
                                shading='gouraud',cmap=custom_cmap,norm=norm,
                                zorder=0)    
    
    dbz_comp = np.nanmean(dbz_tseries,axis=0)
    axs[i].contour(plotx,ploty, dbz_comp,[10],colors='darkgray',linestyles='solid',
                    linewidths=2,zorder=1)
    
    
    uh_comp = np.nanmean(uh_tseries,axis=0)
    axs[i].contour(plotx,ploty, uh_comp,[500],colors='k',
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
    
    
    return cpd_plot  
    

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

st = 100     # start time
et = 100    # end time

ft = 45   # first time after initialization
ff = 2    # number of first file after initialization
dt = 1    # large timestep (minutes)

# file numbers based on start and end times
sf = ((st-ft)/dt)+ff 
ef = ((et-ft)/dt)+ff


fig,axs = plt.subplots(2,2,figsize=(16,11.5))#, sharex=True, sharey=True)
axs = axs.flatten()

plot=False

# fig,axs = plt.subplots(1,1,figsize=(10,7.2))


for folder in os.listdir(indir):

    cp_tseries = []
    cpd_tseries = []
    dbz_tseries = []
    uh_tseries = []
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
            
                
                cp,cpd,dbz,uh,x,y,indices,timestep = cp_data(run,ds0,f,cx,cy)
                    
                cp_tseries.append(cp)
                cpd_tseries.append(cpd)
                dbz_tseries.append(dbz)
                uh_tseries.append(uh)
                times.append(timestep)
                
                i+=1

        ds0.close()
        
        if plot:
            cp_plot = make_plot(fig,axs,x,y,indices,cp_tseries,cpd_tseries,
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
cb = plt.colorbar(cp_plot,cax=cbar_ax, extend='max')
cb.set_label(label='Mean cold pool depth (m)',fontsize=18)
cb.ax.tick_params(labelsize=14) 

plt.subplots_adjust(wspace=0.08, hspace=0.2)


# if int(member) != 0:
#     plt.savefig(outpath+'pdf/new/'+'member'+member+ '_comp_cp_depth'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+'member'+member+ '_comp_cp_depth'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_comp_cp_depth'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_comp_cp_depth'+'.png',dpi=300,bbox_inches='tight')

outpath = '/strm4/topping/revised_figs/cp_depth_comp_2500_limited.pdf'
# plt.savefig(outpath, bbox_inches='tight')
