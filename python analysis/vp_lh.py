#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 13:22:21 2024

@author: dtopping
"""


import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
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
    
    zmax = float(ds.zh.sel(zh=10.5, method='nearest').values)
    
    z = ds.zh.sel(zh=slice(0,zmax))
    
    
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

    
    # rh = ds_hydro.rh#.sel(zh=slice(0,zmax))
    
    w = ds.winterp.sel(zh=slice(0,zmax), 
                       xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                       yh=slice(y_center+bbox[2],
                                y_center+bbox[3])).squeeze(('time'))
    
    
    latent_heat = ds.ptb_mp.sel(zh=slice(0,zmax), 
                       xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                       yh=slice(y_center+bbox[2],
                                y_center+bbox[3])).squeeze(('time')) # K s^-1
    
    # hydro_mass = ds_hydro.total_hydro_mass
    
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
    
    hydro_mass = liquid_hydro + frozen_hydro
    
    # if bbox_sel != bbox:

    #    sel_shape1 = np.shape(latent_heat)

    #    new_latent_heat = np.full((sel_shape1[0],int(yshape),int(xshape)),np.nan)
    #    new_latent_heat[:sel_shape1[0],:sel_shape1[1],:sel_shape1[2]] = latent_heat
    #    latent_heat = new_latent_heat
       
    #    sel_shape1 = np.shape(w)
       
    #    new_w = np.full((sel_shape1[0],int(yshape),int(xshape)),np.nan)
    #    new_w[:sel_shape1[0],:sel_shape1[1],:sel_shape1[2]] = w
    #    w = new_w
       
    #    sel_shape1 = np.shape(hydro_mass)
       
    #    new_hydro_mass = np.full((sel_shape1[0],int(yshape),int(xshape)),np.nan)
    #    new_hydro_mass[:sel_shape1[0],:sel_shape1[1],:sel_shape1[2]] = hydro_mass
    #    hydro_mass = new_hydro_mass
       
    
    hydro_mass = np.where(hydro_mass == 0, np.nan, hydro_mass)
    latent_heat = np.where(latent_heat == 0, np.nan, latent_heat)

     
    thresh_hydro = np.nanpercentile(hydro_mass,10)
    thresh_lh = np.nanpercentile(np.abs(latent_heat),10)
    
    lh = np.where(((np.abs(latent_heat)>thresh_lh) & (hydro_mass>thresh_hydro)),
                  latent_heat, np.nan)
    
    lh_storm = lh
     
    # lh_within = np.where(((w>=1) & (rh>=98)), lh_storm, np.nan)
    # lh_outside = np.where(((w<1) & (rh<98)), lh_storm, np.nan)
    lh_outside = np.where(((w<1)), lh_storm, np.nan)
    
    
    
    # ds_hydro.close()
    ds.close()
    gc.collect()
    
    # return lh_storm,lh_outside,z
    return lh_outside,z


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
    # # elif fig.number==2:
    # #     plt.figure(2)
    # elif fig.number==3:
    #     plt.figure(3)
    # else:
    #     pass
        
    ax = plt.gca()
    mean_plot = ax.plot(tmean_prof,heights,color=color,linewidth=2.5,
                         linestyle=style,label=label)
    
    ax.axvline(x=0, color = 'k', linestyle='dashed')
    
    ax.set_ylabel('Height (km)', fontsize=16)
    ax.set_xlabel('Latent heating rate (K $s^{-1}$)', fontsize=16)
    
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
        
    runs = ['mm','md','dm','dd']

    HODO = 'QT'
    CAPE = '2500'
    MP = 'NSSL'
    # MP = 'MORRISON'
    
    st = 90     # start time
    et = 180    # end time
    
    ft = 45   # first time after initialization
    ff = 2    # number of first file after initialization
    dt = 1    # large timestep (minutes)
    
    # file numbers based on start and end times
    sf = ((st-ft)/dt)+ff 
    ef = ((et-ft)/dt)+ff
    
    
    # # fig1 = plt.figure(1,figsize=(8,6))
    # # fig2 = plt.figure(2,figsize=(8,6))
    # fig3 = plt.figure(3,figsize=(8,6))
    
    # # plot1_lines=[]
    # # plot2_lines=[]
    # plot3_lines=[]
    
    # # orders1 = []
    # # orders2 = []
    # orders3 = []
    
    all_data = []
    
    for folder in os.listdir(indir):
    
        # storm_tseries = []
        # within_tseries = []
        outside_tseries = []
    
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
                    
                    outside, heights = get_data(run,ds0,f,cx,cy)
    
                    # storm_tseries.append(storm)
                    # within_tseries.append(within)
                    outside_tseries.append(outside.flatten())
                    all_data.append(outside.flatten())
                    
                    i+=1
    
                else:
                    pass
                
            ds0.close()
                
            
            # # tmean_storm_prof = np.nanmean(storm_tseries, axis=(0,2,3))
            # # tmean_within_prof = np.nanmean(within_tseries, axis=(0,2,3))
            # # tmean_outside_prof = np.nanmean(outside_tseries, axis=(0,2,3))
            # tmean_outside_prof = np.nanpercentile(outside_tseries,50, axis=(0,2,3))
        
            # # plot1_line = make_plot(fig1,heights,tmean_storm_prof,folder,indir)
            # # plot1_lines.append(plot1_line[0][0])
            # # orders1.append(plot1_line[1])
    
            # # plot2_line = make_plot(fig2,heights,tmean_within_prof,folder,indir)
            # # plot2_lines.append(plot2_line[0][0])
            # # orders2.append(plot2_line[1])
            
            # plot3_line = make_plot(fig3,heights,tmean_outside_prof,folder,indir)
            # plot3_lines.append(plot3_line[0][0])
            # orders3.append(plot3_line[1])
        
            lh_concat = np.concatenate(outside_tseries)
            lh_median = np.nanpercentile(lh_concat,50)
            
            if int(member) != 0:
                mem = member
            else:
                mem = ''
            csv_data = [[sim_name+mem,folder,lh_median]]
            
            csv_path = '/t1/topping/point_data/lh_points.csv'
            with open(csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(csv_data)
    
        else:
            pass
        
    all_concat = np.concatenate(all_data)
    overall_median = np.nanpercentile(all_concat,50)
    
    csv_data = [[sim_name+mem,'overall',overall_median],['----------------------']]
    
    csv_path = '/t1/topping/point_data/lh_points.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
    
    
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
# # ax.tick_params(axis='both', which='major', labelsize=14)
# # ax.set_xlim(-0.003,0.005)
# # ax.legend(handles=plot_lines_ordered1, loc='best', fontsize=16)

# # outpath = indir+'figures/'
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_lh_storm'+'.pdf',bbox_inches='tight')
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_lh_storm'+'.png',dpi=300,bbox_inches='tight')


# # plt.figure(2)
# # ax = plt.gca()
# # # ax.set_xticks([np.round(i,3) for i in np.arange(-0.25,0.025,0.025)])
# # # labels = [str(np.round(i,3)) for i in np.arange(-0.25,0.025,0.025)]
# # # ax.set_xticklabels(labels, fontsize=14)
# # ax.tick_params(axis='both', which='major', labelsize=14)
# # ax.legend(handles=plot_lines_ordered2, loc='best', fontsize=16)

# # outpath = indir+'figures/'
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_lh_within'+'.pdf',bbox_inches='tight')
# # plt.savefig(outpath+CAPE + '_' + HODO + '_' + MP + '_lh_within'+'.png',dpi=300,bbox_inches='tight')


# plt.figure(3)
# ax = plt.gca()
# # ax.set_xticks([np.round(i,3) for i in np.arange(-0.25,0.025,0.025)])
# # labels = [str(np.round(i,3)) for i in np.arange(-0.25,0.025,0.025)]
# # ax.set_xticklabels(labels, fontsize=14)
# ax.tick_params(axis='both', which='major', labelsize=14)

# formatter = ScalarFormatter()
# formatter.set_scientific(True)
# formatter.set_powerlimits((0, 0))

# ax.xaxis.set_major_formatter(formatter)

# # ax.set_xlim(-0.003,0)
# ax.legend(handles=plot_lines_ordered3, loc='best', fontsize=16)


# if int(member) != 0:
#     plt.savefig(outpath+'pdf/new/'+'member'+member+ '_vp_lh2'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+'member'+member+ '_vp_lh2'+'.png',dpi=300,bbox_inches='tight')
# else:
#     plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_vp_lh2'+'.pdf',bbox_inches='tight')
#     plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_vp_lh2'+'.png',dpi=300,bbox_inches='tight')

