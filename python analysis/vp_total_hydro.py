#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 12:53:11 2024

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import gc
import csv


def get_data(run,ds0,f,cx_in,cy_in):

    ds = xr.open_dataset(run+f, decode_times=True)
    time = ds.time.dt.seconds.values[0]/60
    
    filenum = f[-9:]
    # ds_hydro = xr.open_dataset(run+'hydro_'+filenum)

    print('\t\t--> '+file+'\t'+str(time))
    
    
    x_center = ds.xh.sel(xh=cx_in, method='nearest')
    y_center = ds.yh.sel(yh=cy_in, method='nearest')
    
    zmax = ds.zh.sel(zh=10.5, method='nearest')
    
    
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
    

    z = ds.zh.sel(zh=slice(0,zmax))
    
    
    # total_hydro_mass = ds_hydro.total_hydro_mass.sel(zh=slice(0,zmax))
    # total_hydro_mass2 = total_hydro_mass.where(total_hydro_mass>0)
    

    # rh = ds_hydro.rh
    
    w = ds.winterp.sel(zh=slice(0,zmax), 
                        xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                        yh=slice(y_center+bbox[2],
                                y_center+bbox[3])).squeeze(('time'))
    
    
    qr = ds.qr.sel(zh=slice(0,zmax), 
                   xh=slice(x_center+bbox[0],
                            x_center+bbox[1]),
                   yh=slice(y_center+bbox[2],
                            y_center+bbox[3])).squeeze(('time'))
    
    qc = ds.qc.sel(zh=slice(0,zmax), 
                   xh=slice(x_center+bbox[0],
                            x_center+bbox[1]),
                   yh=slice(y_center+bbox[2],
                            y_center+bbox[3])).squeeze(('time'))
    
    liquid_hydro = (qc+qr)*1000#*rhod*vol3d
    
    # if bbox_sel != bbox:

    #    sel_shape = np.shape(w)

    #    new_w = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
    #    new_w[:sel_shape[0],:sel_shape[1]] = w
    #    w = new_w
       
    #    sel_shape = np.shape(liquid_hydro)
    
    #    new_liquid_hydro = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
    #    new_liquid_hydro[:sel_shape[0],:sel_shape[1]] = liquid_hydro
    #    liquid_hydro = new_liquid_hydro
    
    
    qs = ds.qs.sel(zh=slice(0,zmax), 
                   xh=slice(x_center+bbox[0],
                            x_center+bbox[1]),
                   yh=slice(y_center+bbox[2],
                            y_center+bbox[3])).squeeze(('time'))
    
    qi = ds.qi.sel(zh=slice(0,zmax), 
                   xh=slice(x_center+bbox[0],
                            x_center+bbox[1]),
                   yh=slice(y_center+bbox[2],
                            y_center+bbox[3])).squeeze(('time'))
    
    if MP == 'NSSL':
    
        qg = ds.qg.sel(zh=slice(0,zmax), 
                       xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                       yh=slice(y_center+bbox[2],
                                y_center+bbox[3])).squeeze(('time'))
        
        qhl = ds.qhl.sel(zh=slice(0,zmax), 
                         xh=slice(x_center+bbox[0],
                                  x_center+bbox[1]),
                         yh=slice(y_center+bbox[2],
                                  y_center+bbox[3])).squeeze(('time'))
        
        frozen_hydro = (qs+qi+qg+qhl)*1000#*rhod*vol3d
        
    else:
        
        qg = ds.qg.sel(zh=slice(0,zmax), 
                       xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                       yh=slice(y_center+bbox[2],
                                y_center+bbox[3])).squeeze(('time'))
        
        frozen_hydro = (qs+qi+qg)*1000#*rhod*vol3d
    
    
    # if bbox_sel != bbox:

    #    sel_shape = np.shape(w)

    #    new_w = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
    #    new_w[:sel_shape[0],:sel_shape[1]] = w
    #    w = new_w
       
    #    sel_shape = np.shape(frozen_hydro)
    
    #    new_frozen_hydro = np.full((sel_shape[0],int(yshape),int(xshape)),np.nan)
    #    new_frozen_hydro[:sel_shape[0],:sel_shape[1]] = frozen_hydro
    #    frozen_hydro = new_frozen_hydro



    total_hydro = liquid_hydro + frozen_hydro
    
    thresh = np.quantile(total_hydro,0.1)
    
    hydro_outside = np.where(((total_hydro>thresh) & (w<1)), total_hydro, np.nan)
    
    sum_hydro = np.nanmedian(hydro_outside)
    

    # ds_hydro.close()
    ds.close()
    gc.collect()
    
    # return hydro_outside,z
    return sum_hydro,z


def make_plot(fig,heights,tmean_prof,folder,indir):

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
    
    # if fig.number==1:
    #     plt.figure(1)
    # elif fig.number==2:
    #     plt.figure(2)
    # elif fig.number==3:
    #     plt.figure(3)
    # else:
    #     pass
        
    ax = plt.gca()
    mean_plot = ax.plot(tmean_prof,heights,color=color,linewidth=2.5,
                         linestyle=style,label=label)
    
    ax.set_ylabel('Height (km)', fontsize=18, labelpad=10)

    ax.set_xlabel('Total hydrometeor mixing ratio (g $kg^{-1}$)', fontsize=18, labelpad = 10)

    ax.set_ylim(0,10.5)
    
    ax.set_yticks(np.arange(0,11,1))
    labels = [str(label) for label in np.arange(0,11,1)]
    ax.set_yticklabels(labels, fontsize=14)

    return mean_plot, order


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
        
    if sim_name == 'morrison':
        MP = 'MORRISON'
    else:
        MP = 'NSSL'
    
    
    runs = ['mm','md','dm','dd']

    HODO = 'QT'
    CAPE = '2500'
    
    
    st = 90     # start time
    et = 180    # end time
    
    ft = 45   # first time after initialization
    ff = 2    # number of first file after initialization
    dt = 1    # large timestep (minutes)
    
    # file numbers based on start and end times
    sf = ((st-ft)/dt)+ff 
    ef = ((et-ft)/dt)+ff
    
        
    # # fig1 = plt.figure(1,figsize=(15,10))
    # # fig2 = plt.figure(2,figsize=(15,10))
    # fig3 = plt.figure(3,figsize=(8,8))
    
    # # plot1_lines=[]
    # # plot2_lines=[]
    # plot3_lines=[]
    
    # # orders1 = []
    # # orders2 = []
    # orders3 = []
    
    all_data = []
    
    for folder in os.listdir(indir):
    
        # hydro_storm_tseries = []
        # hydro_within_tseries = []
        hydro_outside_tseries = [] 
    
        if os.path.isdir(os.path.join(indir,folder)) and folder in runs:
            
            print(folder[:2]+' -----')
            plot = True
            
            if int(member) != 0:
                run = indir+folder+'/'+folder[:2]+member+'/run/'
                outpath = indir+'figures/member'+member+'/'
            else:
                run = indir+folder+'/run/'
                outpath = indir+'figures/'
            
            ds0 = xr.open_dataset(run+'/cm1out_000001.nc', decode_times=True)
            
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
                    
                    hydro_outside, heights = get_data(run,ds0,f,cx,cy)
    
                    # hydro_storm_tseries.append(hydro_storm)
                    # hydro_within_tseries.append(hydro_within)
                    hydro_outside_tseries.append(hydro_outside)
                    all_data.append(hydro_outside)
                    
                    i+=1
    
                else:
                    pass
                
            ds0.close()
            
            # # storm_xr = xr.concat(hydro_storm_tseries, dim='whoop')
            # # within_xr = xr.concat(hydro_within_tseries, dim='whoop')
            # # outside_xr = xr.concat(hydro_outside_tseries, dim='whoop')
            
            # # tmean_storm = storm_xr.mean(dim='whoop',skipna=True)
            # # tmean_within = within_xr.mean(dim='whoop',skipna=True)
            # # tmean_outside = outside_xr.mean(dim='whoop',skipna=True)
            
            # # tmean_storm_prof = tmean_storm.mean(dim=['xh','yh'], skipna=True)
            # # tmean_within_prof = tmean_within.mean(dim=['xh','yh'], skipna=True)
            # # tmean_outside_prof = tmean_outside.mean(dim=['xh','yh'], skipna=True)
            
            # tmean_outside_prof = np.nanmean(hydro_outside_tseries, axis=(0,2,3))
    
        
            # # plot1_line = make_plot(fig1,heights,tmean_storm_prof,folder,indir)
            # # plot1_lines.append(plot1_line[0][0])
            # # orders1.append(plot1_line[1])
        
            # # plot2_line = make_plot(fig2,heights,tmean_within_prof,folder,indir)
            # # plot2_lines.append(plot2_line[0][0])
            # # orders2.append(plot2_line[1])
            
            # plot3_line = make_plot(fig3,heights,tmean_outside_prof,folder,indir)
            # plot3_lines.append(plot3_line[0][0])
            # orders3.append(plot3_line[1])
    
    
            if int(member) != 0:
                mem = member
            else:
                mem = ''

            hydro_mass_median = np.nanpercentile(hydro_outside_tseries,50)
            
            csv_data = [[sim_name+mem,folder,hydro_mass_median]]
            
            csv_path = '/t1/topping/point_data/median_hydro_points.csv'
            with open(csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(csv_data)
            
            # hydro_mass_mean = np.nanmean(hydro_outside_tseries)
            
            # csv_data = [[sim_name+mem,folder,hydro_mass_mean]]
            
            # csv_path = '/t1/topping/point_data/mean_hydro_points.csv'
            # with open(csv_path, 'a', newline='') as file:
            #     writer = csv.writer(file)
            #     writer.writerows(csv_data)
    
        else:
            pass
        
    overall_median = np.nanpercentile(all_data,50)
    
    csv_data = [[sim_name+mem,'overall',overall_median],['----------------------']]
    
    csv_path = '/t1/topping/point_data/median_hydro_points.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    
    # overall_mean = np.nanmean(all_data)
    
    # csv_data = [[sim_name+mem,'overall',overall_mean],['----------------------']]
    
    # csv_path = '/t1/topping/point_data/mean_hydro_points.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerows(csv_data)
    
    
# # plot_lines_ordered1 = list(np.full_like(plot1_lines,None))
# # for i in range(len(orders1)):
# #     plot_lines_ordered1[orders1[i]] = plot1_lines[i]
    
# # plot_lines_ordered2 = list(np.full_like(plot2_lines,None))
# # for i in range(len(orders2)):
# #     plot_lines_ordered2[orders2[i]] = plot2_lines[i]
    
# plot_lines_ordered3 = list(np.full_like(plot3_lines,None))
# for i in range(len(orders3)):
#     plot_lines_ordered3[orders3[i]] = plot3_lines[i]


# # plt.figure(1)
# # ax = plt.gca()
# # # ax.set_xticks(np.arange(-5,0.5,0.5))
# # # labels = [str(label) for label in np.arange(-5,0.5,0.5)]
# # # ax.set_xticklabels(labels, fontsize=14)
# # ax.legend(handles=plot_lines_ordered1, loc='best', fontsize=16)

# # outpath = indir+'figures/'
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_hydro_mass_storm'+'.pdf',bbox_inches='tight')
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_hydro_mass_storm'+'.png',dpi=300,bbox_inches='tight')


# # plt.figure(2)
# # ax = plt.gca()
# # # ax.set_xticks([np.round(i,3) for i in np.arange(-0.25,0.025,0.025)])
# # # labels = [str(np.round(i,3)) for i in np.arange(-0.25,0.025,0.025)]
# # # ax.set_xticklabels(labels, fontsize=14)
# # ax.legend(handles=plot_lines_ordered2, loc='best', fontsize=16)

# # outpath = indir+'figures/'
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_hydro_mass_within'+'.pdf',bbox_inches='tight')
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_hydro_mass_within'+'.png',dpi=300,bbox_inches='tight')


# plt.figure(3)
# ax = plt.gca()
# # ax.set_xticks([np.round(i,3) for i in np.arange(-0.25,0.025,0.025)])
# # labels = [str(np.round(i,3)) for i in np.arange(-0.25,0.025,0.025)]
# # ax.set_xticklabels(labels, fontsize=14)
# ax.tick_params(axis='both', which='major', labelsize=14)
# ax.legend(handles=plot_lines_ordered3, loc='best', fontsize=16)


# if int(member) != 0:
#     plt.savefig(outpath+'pdf/new/'+'member'+member+ '_vp_hydro'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+'member'+member+ '_vp_hydro'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_vp_hydro'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_vp_hydro'+'.png',dpi=300,bbox_inches='tight')

