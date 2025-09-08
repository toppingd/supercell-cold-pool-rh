#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 11:08:16 2024

@author: dtopping
"""


import xarray as xr
import pandas as pd
import numpy as np
import os
from scipy.signal import savgol_filter


def calc_center(prev_ix,prev_iy,points):
    grid = np.meshgrid(points[0],points[1], indexing='ij')
    xq3,xq1 = np.percentile(points[0], [75, 25])
    yq3,yq1 = np.percentile(points[1], [75, 25])
    xiqr = xq3-xq1
    yiqr = yq3-yq1
    c_points = np.where( ((xq1-1*xiqr)<grid[0]) & (grid[0]<(xq3+1*xiqr))\
                        & ((yq1-1*yiqr)<grid[1]) & (grid[1]<(yq3+1*yiqr)) )
    npoints = c_points[0].shape[0]
    if npoints==0:
        i_cx = prev_ix
        i_cy = prev_iy
    else:
        i_cx750 = int(np.sum(c_points[0])/npoints)
        i_cy750 = int(np.sum(c_points[1])/npoints)
        i_cy = points[0][i_cx750]
        i_cx = points[1][i_cy750]
    
    return i_cx,i_cy


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
indir = '/strm4/topping/runs/ensemble/'
# indir = '/t1/topping/runs/ensemble/'

###############################################################################

runs = ['mm','md','dm','dd']
member = '3'

st = 45    # start time
et = 180    # end time

ft = 45   # first time after initialization
ff = 2    # number of first file after initialization
dt = 1    # large timestep (minutes)

# file numbers based on start and end times
sf = ((st-ft)/dt)+ff 
ef = ((et-ft)/dt)+ff


for folder in os.listdir(indir):
    
    x_locs = []
    y_locs = []  
    times = []

    if os.path.isdir(os.path.join(indir,folder)) and folder[:2] in runs:
        
        print(folder[:2]+' -----')
        
        if int(member) != 0:
            run = indir+folder+'/'+folder[:2]+member+'/run/'
        else:
            run = indir+folder+'/run/'

        ds0 = xr.open_dataset(run+'cm1out_000001.nc', decode_times=True)
        
        i=0
        prev_ix = None
        prev_iy = None
        prevx = None
        prevy = None
        
        for file in sorted(os.listdir(run)):
            if os.path.isfile(os.path.join(run,file)) and 'cm1out_000' in file\
            and (sf <= int(file[-6:-3]) <= ef):

                f = file
                
                ds = xr.open_dataset(run+f, decode_times=True)
                timestep = ds.time.dt.seconds.values[0]/60

                print('\t\t--> '+file+'\t'+str(timestep))
                
                
                # find center of mid-level mesocyclone
                uh = ds.uh.squeeze('time')
                
                if i != 0:
                    uh = uh.where(((uh.xh>=(prevx-10)) & (uh.xh<=(prevx+10))) &\
                                  ((uh.yh>=(prevy-10)) & (uh.yh<=(prevy+10))),
                                  np.nan)

                points = np.where(uh>=600)
                
                # if storm uh less than 600, use 10 as new threshold
                if np.size(points)==0:
                    
                    points = np.where(uh>=10)
                    # if storm uh is less than 10, consider the storm dead 
                    # and keep storm center constant at the last location 
                    # with uh greater or equal to 10
                    if np.size(points)==0:
                        i_cx = prev_ix
                        i_cy = prev_iy
                    else:
                        i_cx,i_cy = calc_center(prev_ix,prev_iy,points)
                            
                else:
                    i_cx,i_cy = calc_center(prev_ix,prev_iy,points)
  
                
                x_center = ds.xh.values[i_cx]
                y_center = ds.yh.values[i_cy]
                
                
                prev_ix = i_cx
                prev_iy = i_cy

                prevx = x_center
                prevy = y_center
                
                
                x_locs.append(x_center)
                y_locs.append(y_center)
                times.append(timestep)
    
                
                ds.close()

                i+=1
                
            
        # calculate smoothed tracks for right moving supercells
        x_arr = np.array(x_locs)
        y_arr = np.array(y_locs)
        
        x_smooth = savgol_filter(x_arr, window_length=30,
                                 polyorder=1, mode='nearest').astype(float)
        y_smooth = savgol_filter(y_arr, window_length=30,
                                 polyorder=1, mode='nearest').astype(float)
    
                    
        centers_df = pd.DataFrame({'times':times,
                                   'x_center':x_locs,
                                   'y_center':y_locs,
                                   'x_smooth':x_smooth,
                                   'y_smooth':y_smooth})
        
        centers_df.to_csv(run+'rm_tracking.csv')
    
    
    