#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 17:23:50 2024

@author: dtopping
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import gc
import csv


def cp_data(run,ds0,f,cx_in,cy_in):

    ds = xr.open_dataset(run+f, decode_times=True)
    time = ds.time.dt.seconds.values[0]/60

    print('\t\t--> '+file+'\t'+str(time))
    
    x_center = ds.xh.sel(xh=cx_in, method='nearest')
    y_center = ds.yh.sel(yh=cy_in, method='nearest')
    

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
    

    rain = ds.prate.sel(xh=slice(x_center+bbox[0],x_center+bbox[1]),
                        yh=slice(y_center+bbox[2],y_center+bbox[3])).squeeze(('time'))
    
    # if bbox_sel != bbox:

    #     sel_shape = np.shape(rain)

    #     new_rain = np.full((int(yshape),int(xshape)),np.nan)
        
    #     if (sel_shape[0]<yshape) or (sel_shape[1]<xshape):
    #        new_rain[:sel_shape[0],:sel_shape[1]] = \
    #            rain[:sel_shape[0],:sel_shape[1]]
    #     else:
    #         sel_diff = (int(sel_shape[0]-yshape),int(sel_shape[1]-xshape))
    #         new_rain[:sel_shape[0]-sel_diff[0],:sel_shape[1]-sel_diff[1]] = \
    #             rain[:sel_shape[0]-sel_diff[0],:sel_shape[1]-sel_diff[1]]
        
    #     rain = new_rain

    
    # non zero values
    # mean_rain = np.nanmean(np.where(np.round(rain,3)>0, rain, np.nan))
    nonzero_rain = np.where(np.round(rain,3)>0,rain,np.nan)
    
    
    ds.close()
    gc.collect()

    # return mean_rain,time
    return nonzero_rain,time


def make_plot(fig,ax,times,rain_tseries,folder,indir):
    
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
    
    plot = ax.plot(times, rain_tseries,
                   label=label, color=color, linestyle=style,
                   linewidth=2)

    
    return plot, order
    

###############################################################################
###############################################################################

# Core set of simulations
# indir = '/t1/topping/runs/2500/'

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

simulations = ['/t1/topping/runs/2500/',
                '/t1/topping/runs/1500/',
                '/t1/topping/runs/3500/',
                '/t1/topping/runs/morrison/',
                '/strm4/topping/runs/nssl3/',
                '/t1/topping/runs/freeslip/',
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
        print
        
    runs = ['mm','md','dm','dd']
    
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
    
        
    # fig,ax = plt.subplots(1,1,figsize=(12,6), sharex=True)
    
    plot_lines = []
    orders = []
    all_data = []
    
    for folder in os.listdir(indir):
    
        times = []
        rain_tseries = []
    
        if os.path.isdir(os.path.join(indir,folder)) and folder in runs:
            
            print(folder[:2]+' -----')
            plot = True
            
            if int(member) != 0:
                run = indir+folder+'/'+folder[:2]+member+'/run/'
                outpath = indir+'figures/member'+member+'/'
            else:
                run = indir+folder+'/run/'
                outpath = indir+'figures/'
    
            ds0 = xr.open_dataset(run+'/cm1out_000001.nc',decode_times=True)
            
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
                    
                    rain,time = cp_data(run,ds0,f,cx,cy)
                        
                    rain_tseries.append(rain.flatten())
                    all_data.append(rain.flatten())
                    times.append(time)
                    
                    i+=1
                    
            # plot = make_plot(fig,ax,times,rain_tseries,folder,indir)
            # plot_lines.append(plot[0][0])
            # orders.append(plot[1])
            
            
            if int(member) != 0:
                mem = member
            else:
                mem = ''
            
            rain_concat = np.concatenate(rain_tseries)
            
            # rain_median = np.round(np.nanpercentile(rain_concat,50),4)
                      
            # csv_data = [[sim_name+mem,folder,rain_median]]
            
            # csv_path = '/t1/topping/point_data/median_rain_points.csv'
            # with open(csv_path, 'a', newline='') as file:
            #     writer = csv.writer(file)
            #     writer.writerows(csv_data)
            
            rain_mean = np.round(np.nanpercentile(rain_concat,50),4)
                      
            csv_data = [[sim_name+mem,folder,rain_mean]]
            
            csv_path = '/t1/topping/point_data/mean_rain_points.csv'
            with open(csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(csv_data)
    
        else:
            pass
        
    all_concat = np.concatenate(all_data)
    # overall_median = np.round(np.nanpercentile(all_concat,50),4)
    
    # csv_data = [[sim_name+mem,'overall',overall_median],['----------------------']]
    
    # csv_path = '/t1/topping/point_data/median_rain_points.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerows(csv_data)
    
    overall_mean = np.round(np.nanmean(all_concat),4)
    
    csv_data = [[sim_name+mem,'overall',overall_mean],['----------------------']]
    
    csv_path = '/t1/topping/point_data/mean_rain_points.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    
# plot_lines_ordered = list(np.full_like(plot_lines,None))
# for i in range(len(orders)):
#     plot_lines_ordered[orders[i]] = plot_lines[i]
    

# ax.set_xlabel('Time (min)', fontsize=18)
# ax.tick_params(axis='x', which='major', labelsize=14)
# ax.set_ylabel('Surface rain rate (kg $m^{-2}$ $s^{-1}$)', fontsize=18)
# ax.tick_params(axis='y', which='major', labelsize=14)
# ax.tick_params(axis='both', which='major', length=8, width=2)

# ax.legend(handles=plot_lines_ordered,ncols=2, loc='best', fontsize=16)

# ax.set_yticks(np.arange(0,0.014,0.002))
# ax.set_xticks(np.arange(60,190,10))

# ax.set_xlim(st,et)
# ax.set_ylim(0,0.012)


# if int(member) != 0:
#     plt.savefig(outpath+'pdf/new/'+'member'+member+ '_sfc_rain'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+'member'+member+ '_sfc_rain'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_sfc_rain'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_sfc_rain'+'.png',dpi=300,bbox_inches='tight')

