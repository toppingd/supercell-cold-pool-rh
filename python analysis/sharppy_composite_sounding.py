# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 17:37:31 2023

@author: dtopping
"""

import tkinter as tk
from tkinter import filedialog
import metpy.calc as calc
from metpy.units import units
import pandas as pd
import xarray as xr
import os


root = tk.Tk()
seldir = filedialog.askdirectory(parent=root, initialdir='C:/', 
                                title='Select sharppy directory')
root.destroy()

indir = seldir
mode = os.path.basename(seldir)

agl_data = []
for filename in os.listdir(indir):
    inpath = indir+'/'
    if os.path.isfile(inpath+filename) and 'sharppy_comp' not in filename:
        file = open(inpath+filename)
      
        lines = file.readlines()
        _agl = lines[6:-1]
        agl = []
        for i in range(len(_agl)):
            row = []
            _agl[i] = _agl[i].split(', ')
            for item in _agl[i]:
                item.strip(' ')
                row.append(float(item.strip('\n')))
            agl.append(row)
        df = pd.DataFrame(agl)
            
        file.close
            
        ds = xr.Dataset.from_dataframe(df)
        agl_data.append(ds)
    
ds = xr.concat(agl_data, dim='event')

ds = ds.rename(name_dict={0:'level',1:'height',2:'t',3:'td',4:'winddir',5:'windspd'})
u,v = calc.wind_components(ds.windspd*units('m/s'),
                           ds.winddir*units('degrees'))

ds = ds.assign(u = u)
ds = ds.assign(v = v)

# mean sounding
agl_mean = ds.mean(dim='event')

agl_mean = agl_mean.assign(winddir = calc.wind_direction(agl_mean.u, agl_mean.v))
agl_mean = agl_mean.assign(windspd = calc.wind_speed(agl_mean.u, agl_mean.v))

outfile1 = inpath+'sharppy_comp'
composite1 = open(outfile1,'w')

print('%s' % ('%TITLE%'),
      file=composite1)
print(' %s\t%s\n' % ('IDEAL', '010101/1200'),
      file=composite1)
print('   %s\t%s\t%s\t%s\t%s\t%s' % ('LEVEL', 'HGHT', 'TEMP', 'DWPT', 'WDIR', 'WSPD'),
      file=composite1)
print('%s' % ('------------------------------------------------------------------'),
      file=composite1)
print('%s' % ('%RAW%'),
      file=composite1)

for i in range(len(agl_mean.level)):
    level = agl_mean.level.values[i]
    height = agl_mean.height.values[i]
    temp = agl_mean.t.values[i]
    dwpt = agl_mean.td.values[i]
    wind_dir = agl_mean.winddir.values[i]
    wind_spd = agl_mean.windspd.values[i]
    
    
    
    print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
          (level,height,temp,dwpt,wind_dir,wind_spd),
          file=composite1)

print('%s' % ('%END%'), file=composite1)  

composite1.close()
