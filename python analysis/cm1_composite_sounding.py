# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 11:22:59 2023

@author: dtopping
"""

import tkinter as tk
from tkinter import filedialog
import pandas as pd
import xarray as xr
import os


root = tk.Tk()
seldir = filedialog.askdirectory(parent=root, initialdir='C:/', 
                                title='Select cm1 directory')
root.destroy()

indir = seldir

sfc_data = []
agl_data = []

for filename in os.listdir(indir):
    inpath = indir+'/'
    
    if os.path.isfile(inpath+filename) and 'cm1_comp' not in filename:
    
        file = open(inpath+filename)
        data = file.readlines()
        file.close

        for i in range(len(data)):
            data[i] = data[i].split('\t')
            for j in range(len(data[i])):
                data[i][j] = float(data[i][j].strip())
                
        sfc = data[0]
        df_sfc = pd.DataFrame(sfc)
            
        agl = data[1:]
        df = pd.DataFrame(agl)
        
    
        ds_sfc = xr.Dataset.from_dataframe(df_sfc)
        sfc_data.append(ds_sfc)
        
        ds = xr.Dataset.from_dataframe(df)
        agl_data.append(ds)
    

ds_sfc = xr.concat(sfc_data, dim='event')
ds = xr.concat(agl_data, dim='event')


# mean sounding
sfc_mean = ds_sfc.mean(dim='event')
agl_mean = ds.mean(dim='event')

outfile = inpath+'cm1_comp'
composite = open(outfile,'w')

sfcprs,sfcth,sfcqv = (sfc_mean[0].values[0],
                      sfc_mean[0].values[1],
                      sfc_mean[0].values[2])
print('%3.5f \t%3.5f \t%3.5f' % (sfcprs,sfcth,sfcqv),
      file=composite)

for i in range(len(agl_mean[0])):
    height = agl_mean[0].values[i]
    th = agl_mean[1].values[i]
    qv = agl_mean[2].values[i]
    u = agl_mean[3].values[i]
    v = agl_mean[4].values[i]
    
    print('%3.5f \t%3.5f \t%3.5f \t%3.5f \t%3.5f' % (height,th,qv,u,v),
          file=composite)

composite.close()
