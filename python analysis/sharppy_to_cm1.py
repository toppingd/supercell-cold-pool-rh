# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 13:20:29 2023

@author: dtopping
"""

import numpy as np
# import tkinter as tk
# from tkinter import filedialog
# import os
from metpy.units import units
import metpy.calc as mcalc


def sharpp_to_cm1(inpath,filename,outpath):
    
    infile = inpath+filename
    
    sndg = open(infile,'r')
    
    if 'sharppy' in filename:
        filename2 = filename.replace('sharppy','')
    sndg_cm1 = open(outpath+filename2+'cm1','w')
    
    # Store sounding data in arrays
    data = sndg.readlines()[6:-1]
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            data[i][j] = float(data[i][j].strip())
    
    sfc_data = data[0]
    
    sfcprs,sfct,sfcdwpt = (float(sfc_data[0]),
                           float(sfc_data[2]),
                           float(sfc_data[3]))
    
    sfcth = (sfct + 273.15)*((1000/sfcprs)**(287/1004))
    # print(filename, str(sfcth))
    
    c1 = 611.12      # reference pressure [Pa]
    c2 = 2.5008e6    # latent heat of vaporization [J/kg]
    c3 = 461.2       # gas constant for water vapor [K]
    c4 = 273.16      # reference temperature [k]
    
    sfce = c1*np.exp((c2/c3)*((1/c4)-(1/(c4+sfcdwpt))))     # [Pa]
    sfcqv = 621.97*(sfce/((sfcprs*100)-sfce))          # [g/kg]
    
    print('%3.5f \t%3.5f \t%3.5f' % (sfcprs,sfcth,sfcqv),
          file=sndg_cm1)
    
    for line in data:
        prs,height,t,dwpt,wdir,wspd = (float(line[0]),
                                       float(line[1]),
                                       float(line[2]),
                                       float(line[3]),                                                                
                                       float(line[4]),
                                       float(line[5]))
        
        th = (t + 273.15)*((1000/prs)**(2/7))
        
        e = c1*np.exp((c2/c3)*((1/c4)-(1/(c4+dwpt))))     # [Pa]
        qv = 621.97*(e/((prs*100)-e))                # [g/kg]
        
        wdir = wdir * units('degrees')
        wspd = (wspd * units('knots')).to(units('m/s'))
        
        # print(wdir,wspd)
        
        u,v = mcalc.wind_components(wspd,wdir)
        # print(u,v)
      
        print('%3.5f \t%3.5f \t%3.5f \t%3.5f \t%3.5f' % (height,
                                                         th,
                                                         qv,
                                                         u.magnitude,
                                                         v.magnitude),
                                                         file=sndg_cm1)
    
    sndg_cm1.close()
    sndg.close()


# root = tk.Tk()
# indir = filedialog.askdirectory(parent=root, initialdir='C:/', 
#                                 title='Select input directory')
# root.destroy()


# inpath = indir+'/'

# for conversion of entire directory
#outpath = indir +'/cm1_soundings/'
# if not os.path.isdir(outpath):
#     os.mkdir(outpath)

# inpath = '/t1/topping/soundings/1500CAPE/'
# inpath = '/t1/topping/soundings/2500CAPE/'
inpath =  '/t1/topping/soundings/2500CAPE/sigtor/'
filename = 'dd_sigtor_sharppy'
outpath = inpath
sharpp_to_cm1(inpath,filename,outpath)

# for filename in os.listdir(inpath):
#     sharppfile = inpath+filename
#     if os.path.isfile(sharppfile) and 'extended_sharppy' in filename:
#         sharpp_to_cm1(inpath,filename,outpath)
