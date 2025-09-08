#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 17:23:50 2024

@author: dtopping
"""


import xarray as xr
# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import gc
import csv
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
    
    
    return retained_cp


def cp_data(run,ds0,f,cx_in,cy_in):

    ds = xr.open_dataset(run+f, decode_times=True)
    time = ds.time.dt.seconds.values[0]/60

    print('\t\t--> '+f+'\t'+str(time))
    
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
    
    
    # if bbox_sel != bbox:

    #     sel_shape = np.shape(b)
    #     new_b = np.full((int(yshape),int(xshape)),np.nan)
    #     new_b[:sel_shape[0],:sel_shape[1]] = b
    #     b = new_b
        
    #     sel_shape = np.shape(lh)
    #     sel_shape = np.shape(lh)
    #     new_lh = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
    #     new_lh[:sel_shape[0],:sel_shape[1]] = lh
    #     lh = new_lh
        
    #     sel_shape = np.shape(lcl)
    #     new_lcl = np.full((int(yshape),int(xshape)),np.nan)
    #     new_lcl[:sel_shape[0],:sel_shape[1]] = lcl
    #     lcl = new_lcl
    
       
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
        cp_isolated = np.full_like(b, np.nan)

    
    cp_mean = np.nanmean(cp_isolated)

    
    ds_outflow.close()
    ds.close()
    gc.collect()

    return cp_mean, time


# def make_plot(fig,axs,times,neg_tseries,folder,indir):
    
#     if 'mm' in folder:
#         color='#005AB5'
#         style = 'solid'
#         label='Moist PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
#         order=0
#     elif 'md' in folder:
#         color='#005AB5'
#         style='dashed'
#         label='Moist PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
#         order=1
#     elif 'dm' in folder:
#         color='#DC3220'
#         style='solid'
#         label='Dry PBL / Moist FT'#'-' + CAPE + '-' + HODO + '-' + MP
#         order=2
#     elif 'dd' in folder:
#         color='#DC3220'
#         style='dashed'
#         label='Dry PBL / Dry FT'#'-' + CAPE + '-' + HODO + '-' + MP
#         order=3
#     else:
#         pass
    
    
#     neg_plot = axs.plot(times, neg_tseries,
#                         label=label, color=color, linestyle=style)
    
    
#     return neg_plot, order
    

###############################################################################
###############################################################################

# Core set of simulations
# indir = '/t1/topping/runs/2500/'

# CAPE sensitivity
# indir = '/t1/topping/runs/1500/'
# indir = '/t1/topping/runs/3500/'

# Microphysics sensitivity
# indir = '/t1/topping/runs/morrison/'
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

# simulations = ['/t1/topping/runs/2500/',
#                '/t1/topping/runs/1500/',
#                '/t1/topping/runs/3500/',
#                '/t1/topping/runs/morrison/',
#                '/strm4/topping/runs/nssl3/',
#                '/t1/topping/runs/freeslip/',
simulations = [
                '/t1/topping/runs/sigtor/',
                '/t1/topping/runs/ensemble/',
                '/strm4/topping/runs/ensemble/',
                '/strm4/topping/runs/ensemble/',
                '/strm4/topping/runs/ensemble/',
                '/strm4/topping/runs/ensemble/']

member = '0' # ensemble member number for random temperature perturbations

for indir in simulations:

    sim_name = indir.split('/')[-2]
    
    if sim_name == 'ensemble':
        member = str(int(member)+1)
        
    runs = ['mm','md','dm','dd']
    # runs = ['md']

    # HODO = 'QT'
    # CAPE = '2500'
    # MP = 'NSSL'
    # MP = 'MORRISON'
    
    st = 90   # start time
    et = 180    # end time
    
    ft = 45   # first time after initialization
    ff = 2    # number of first file after initialization
    dt = 1    # large timestep (minutes)
    
    # file numbers based on start and end times
    sf = ((st-ft)/dt)+ff 
    ef = ((et-ft)/dt)+ff
    
    
    # fig,axs = plt.subplots(1,1,figsize=(12,6))#, sharex=True)
    
    neg_plot_lines = []
    orders = []
    
    all_data = []
    
    for folder in os.listdir(indir):
    
        times = []
        neg_tseries = []
    
        if os.path.isdir(os.path.join(indir,folder)) and folder in runs:
            
            print(sim_name+' --> '+folder[:2]+' -----')
            plot = True
            
            if int(member) != 0:
                run = indir+folder+'/'+folder[:2]+member+'/run/'
                outpath = indir+'figures/member'+member+'/'
            else:
                run = indir+folder+'/run/'
                outpath = indir+'figures/'
    
            ds0 = xr.open_dataset(run+'/cm1out_000001.nc',
                                  decode_times=True)
            
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
                    
                    neg_intensity, time = cp_data(run,ds0,f,cx,cy)
                        
                    neg_tseries.append(neg_intensity.flatten())
                    all_data.append(neg_intensity.flatten())
                    times.append(time)
                    
                    i+=1
                    
            # plot = make_plot(fig,axs,times,neg_tseries,folder,indir)
            # neg_plot_lines.append(plot[0][0])
            # orders.append(plot[1])
            
            ds0.close()
            
            
            if int(member) != 0:
                mem = member
            else:
                mem = ''
            
            intensity_concat = np.concatenate(neg_tseries)
            
            # cp_intensity_median = np.round(np.nanpercentile(intensity_concat,50),4)
            
            # csv_data = [[sim_name+mem,folder,cp_intensity_median]]
            
            # csv_path = '/t1/topping/point_data/median_cp_intensity_points.csv'
            # with open(csv_path, 'a', newline='') as file:
            #     writer = csv.writer(file)
            #     writer.writerows(csv_data)
                
            cp_intensity_mean = np.round(np.nanmean(intensity_concat),4)
            
            csv_data = [[sim_name+mem,folder,cp_intensity_mean]]
            
            csv_path = '/strm4/topping/revised_figs/mean_cp_intensity_points.csv'
            with open(csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(csv_data)
    
        else:
            pass
        
    all_concat = np.concatenate(all_data)
    
    # overall_median = np.round(np.nanpercentile(all_concat,50),4)
    
    # csv_data = [[sim_name+mem,'overall',overall_median],['----------------------']]
    
    # csv_path = '/t1/topping/point_data/median_cp_intensity_points.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerows(csv_data)
    
    overall_mean = np.round(np.nanmean(all_concat),4)
    
    csv_data = [[sim_name+mem,'overall',overall_mean],['----------------------']]

    csv_path = mean_cp_intensity_points.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    
# plot_lines_ordered = list(np.full_like(neg_plot_lines,None))
# for i in range(len(orders)):
#     plot_lines_ordered[orders[i]] = neg_plot_lines[i]
    

# axs.set_xlabel('Time (min)', fontsize=18)
# axs.tick_params(axis='x', which='major', labelsize=14)

# # axs.set_ylabel('Mean cold pool buoyancy (m $s^{-2}$)', fontsize=18)
# axs.set_ylabel('$90^{th}$ percentile buoyancy (m $s^{-2}$)', fontsize=18)
# axs.tick_params(axis='y', which='major', labelsize=14)

# axs.tick_params(axis='both', which='major', length=8, width=2)


# plt.subplots_adjust(wspace=0.08, hspace=0.2)

# axs.legend(handles=plot_lines_ordered,ncols=2, loc='best', fontsize=18)

# axs.set_xlim(90,180)
# axs.set_ylim(-0.2,-0.01)
# # axs.invert_yaxis()


# # if int(member) != 0:
# #     plt.savefig(outpath+'pdf/new/'+'member'+member+ '_ts_mean_b'+'.pdf',bbox_inches='tight')
# #     plt.savefig(outpath+'png/new/'+'member'+member+ '_ts_mean_b'+'.png',dpi=300,bbox_inches='tight')
# # else:
# #     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_ts_mean_b'+'.pdf',bbox_inches='tight')
# #     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_ts_mean_b'+'.png',dpi=300,bbox_inches='tight')
    
# if int(member) != 0:
#     plt.savefig(outpath+'pdf/new/'+'member'+member+ '_ts_90p_b'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+'member'+member+ '_ts_90p_b'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_ts_90p_b'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_ts_90p_b'+'.png',dpi=300,bbox_inches='tight')
