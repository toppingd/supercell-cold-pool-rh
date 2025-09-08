# -*- coding: utf-8 -*-
"""
Created on Thu Oct  5 16:06:09 2023

@author: dtopp
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
# import time
import gc
import csv
    

def cp_data(run,f,cx_in,cy_in):
    
    # start = time.time()

    ds = xr.open_dataset(run+f, decode_times=True)[['winterp','zvort']]
    timestep = ds.time.dt.seconds.values[0]/60
    
    print('\t\t--> '+file+'\t'+str(timestep))    

    x_center = ds.xh.sel(xh=cx_in, method='nearest')
    y_center = ds.yh.sel(yh=cy_in, method='nearest')
    
    lml = ds.zh.sel(zh=0, method='nearest')
    
    
    bbox_storm = [-25.0,65.0,-15.0,57.0]
   
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

    
    w_storm = ds.winterp.sel(zh=slice(0,3),
                             xh=slice(x_center+bbox_storm[0],
                                      x_center+bbox_storm[1]),
                             yh=slice(y_center+bbox_storm[2],
                                      y_center+bbox_storm[3]))
     

    wmin = w_storm.min()
    
    
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
    

    w_inner = ds.winterp.sel(xh=slice(x_center+bbox_inner[0],
                                      x_center+bbox_inner[1]),
                              yh=slice(y_center+bbox_inner[2],
                                      y_center+bbox_inner[3]),
                              zh=slice(0,6))


    wmax = w_inner.max()
    
    # wmax = w_storm.max()
    
    # zvort_inner = ds.zvort.sel(xh=slice(x_center+bbox_inner[0],
    #                                     x_center+bbox_inner[1]),
    #                             yh=slice(x_center+bbox_inner[2],
    #                                     x_center+bbox_inner[3]),
    #                             zh=lml)
    
    
    # zvort_storm = ds.zvort.sel(xh=slice(x_center+bbox_storm[0],
    #                                     x_center+bbox_storm[1]),
    #                             yh=slice(x_center+bbox_storm[2],
    #                                     x_center+bbox_storm[3]),
    #                             zh=lml)
    
    
    # zvort_max = zvort_inner.max()
    # zvort_max = zvort_storm.max())
    zvort_max=None
    
    
    # end = time.time()
    # elapsed_time = int(end-start)
    
    # print('\t\t--> '+f[-19:]+'\t'+str(timestep)+\
    #       '\t\t----- finished in: '+str(elapsed_time)+'seconds')
    
    ds.close()
    gc.collect()

    return wmax,wmin,zvort_max,timestep


def make_plot(fig,axs,times,wmax_ts,wmin_ts,zvort_max_ts,folder,indir):
    
    mean_down = int(np.round(np.mean(wmin_ts),0))
    mean_up = int(np.round(np.mean(wmax_ts),0))

    if 'mm' in folder:
        color='#005AB5'
        style = 'solid'
        label='Moist PBL / Moist FT ('+str(mean_up)+'/'+str(mean_down)+')'
        order=0
    elif 'md' in folder:
        color='#005AB5'
        style='dashed'
        label='Moist PBL / Dry FT ('+str(mean_up)+'/'+str(mean_down)+')'
        order=1
    elif 'dm' in folder:
        color='#DC3220'
        style='solid'
        label='Dry PBL / Moist FT ('+str(mean_up)+'/'+str(mean_down)+')'
        order=2
    elif 'dd' in folder:
        color='#DC3220'
        style='dashed'
        label='Dry PBL / Dry FT ('+str(mean_up)+'/'+str(mean_down)+')'
        order=3
    else:
        pass

    # wmin_plot = axs.plot(times,wmin_ts,color=color,linewidth=1.5,
    #                      linestyle=style,label=label)   

    # axs.plot(times,wmax_ts,color=color,linewidth=1.5,
    #          linestyle=style,label=label)
    
    # axs.set_yticks(np.arange(-40,90,10))
    # axs.set_ylim(ymin=-40,ymax=80)
    
    # axs.set_xticks(np.arange(np.min(times),np.max(times)+15,15))
    # axs.set_xlabel('Time (min)', fontsize=16)
    # axs.set_xlim(90,180)

    axs[0].set_title('(a) Maximum updraft velocity', fontsize=18, loc='left')
    axs[1].set_title('(b) Maximum downdraft velocity', fontsize=18, loc='left')
  

    max_plot = axs[0].plot(times,wmax_ts,color=color,linewidth=1.5,
                           linestyle=style,label=label)
    
    axs[1].plot(times,wmin_ts,color=color,linewidth=1.5,
                            linestyle=style,label=label) 
    
    # axs[2].plot(times,zvort_max_ts,color=color,linewidth=1.5,
    #             linestyle=style,label=label)
    
    
    # axs[0].fill_between([45,90],[-65],[0],color='lightgray',alpha=0.5)
    # axs[1].fill_between([45,90],[0],[80],color='lightgray',alpha=0.5)
    # axs[2].fill_between([45,90],[0],[0.2],color='lightgray',alpha=0.5)
    
    plot_line = (max_plot, order)
    
    
    axs[0].set_yticks(np.arange(25,65,5))
    axs[0].set_ylim(ymin=25,ymax=60)
        
    axs[1].set_yticks(np.arange(-28,-6,2))
    axs[1].set_ylim(ymin=-28,ymax=-8)
    
    # axs[2].set_yticks(np.arange(0,0.175,0.025))
    # axs[2].set_ylim(ymin=0,ymax=0.15)
    
    axs[0].set_ylabel('w (m $\mathregular{s^{-1}}$)',
                      fontsize=16)
    axs[1].set_ylabel('w (m $\mathregular{s^{-1}}$)',
                      fontsize=16)    
    # axs[2].set_ylabel('$ζ_{max}$ ($s^{-1}$)',
    #                   fontsize=12)
    
    
    axs[1].set_xticks(np.arange(np.min(times),np.max(times)+15,15))
    axs[1].set_xlabel('Time (min)', fontsize=16)
    axs[1].set_xlim(90,180)
    

    return plot_line


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

    st = 90    # start time
    et = 180    # end time
    
    ft = 45   # first time after initialization
    ff = 2    # number of first file after initialization
    dt = 1    # large timestep (minutes)
    
    # file numbers based on start and end times
    sf = ((st-ft)/dt)+ff 
    ef = ((et-ft)/dt)+ff
    
    
    # fig,axs = plt.subplots(2,1,figsize=(10,8), sharex=True)
    # axs = axs.flatten()
    
    plot_lines=[]
    orders=[]
    
    all_data_up = []
    all_data_down = []
    
    for folder in os.listdir(indir):
     
        wmax_ts = []
        wmin_ts = []
        zvort_max_ts = []
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
    
            ds0 = xr.open_dataset(run+'/cm1out_000001.nc',
                                  decode_times=True)
            
            pos_df = pd.read_csv(run+'rm_tracking.csv')
            x_locs = np.asarray(pos_df['x_smooth'])
            y_locs = np.asarray(pos_df['y_smooth'])
            locs = (x_locs,y_locs)
            
            i=0      
            print('\tGetting Data:')    
            for file in sorted(os.listdir(run)):
                if os.path.isfile(os.path.join(run,file)) and ('cm1out_000' in file)\
                and (sf <= int(file[-6:-3]) <= ef):
                    f = file
                    
                    cx = locs[0][st-ft+i]
                    cy = locs[1][st-ft+i]
                    
                    wmax,wmin,zvort_max,timestep = cp_data(run,f,cx,cy)
                    wmax_ts.append(wmax)
                    wmin_ts.append(wmin)
                    all_data_up.append(wmax)
                    all_data_down.append(wmin)
                    zvort_max_ts.append(zvort_max)
                    times.append(timestep)
                    
                    i+=1
                    
                ds0.close()
                
                
            if int(member) != 0:
                mem = member
            else:
                mem = ''
    
            # wmin_median = np.round(np.percentile(wmin_ts,50),4)
            # wmax_median = np.round(np.percentile(wmax_ts,50),4)
            
            # csv_data = [[sim_name+mem,folder,wmin_median,wmax_median]]
            
            # csv_path = '/t1/topping/point_data/median_w_points.csv'
            # with open(csv_path, 'a', newline='') as file:
            #     writer = csv.writer(file)
            #     writer.writerows(csv_data)
            
            wmin_mean = np.round(np.nanmean(wmin_ts),4)
            wmax_mean = np.round(np.nanmean(wmax_ts),4)
            
            csv_data = [[sim_name+mem,folder,wmin_mean,wmax_mean]]
            
            csv_path = '/t1/topping/point_data/mean_w_points.csv'
            with open(csv_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(csv_data)
                
                
    # overall_down_median = np.round(np.nanpercentile(all_data_down,50),4)
    # overall_up_median = np.round(np.nanpercentile(all_data_up,50),4)
    
    # csv_data = [[sim_name,'overall',overall_down_median,overall_up_median],
    #             ['----------------------']]
    
    # csv_path = '/t1/topping/point_data/median_w_points.csv'
    # with open(csv_path, 'a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerows(csv_data)
    
    overall_down_mean = np.round(np.nanmean(all_data_down),4)
    overall_up_mean = np.round(np.nanmean(all_data_up),4)
    
    csv_data = [[sim_name+mem,'overall',overall_down_mean,overall_up_mean],
                ['----------------------']]
    
    csv_path = '/t1/topping/point_data/mean_w_points.csv'
    with open(csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)
                       

#         plot_line = make_plot(fig,axs,times,wmax_ts,wmin_ts,zvort_max_ts,
#                               folder,indir)
        
#         plot_lines.append(plot_line[0][0])
#         orders.append(plot_line[1])
        

#     else:
#         pass


# plot_lines_ordered = [None,None,None,None]
# for i in range(len(orders)):
#     plot_lines_ordered[orders[i]] = plot_lines[i]
    

# # axs[0].invert_yaxis()
# # axs[0].legend(handles=plot_lines_ordered, ncols=2, loc='best', fontsize=16)
# plt.subplots_adjust(hspace=0.6)
# fig.legend(handles=plot_lines_ordered,
#            loc='center', bbox_to_anchor=(0.5, 0.52),
#            ncol=2, fontsize=16)


# outpath = indir+'figures/'
# plt.savefig(outpath+'pdf/new/'+CAPE + '_' + HODO + '_' + MP + '_ts_w2'+'.pdf',
#             bbox_inches='tight')
# plt.savefig(outpath+'png/new/'+CAPE + '_' + HODO + '_' + MP + '_ts_w2'+'.png',
#             dpi=300,bbox_inches='tight')
