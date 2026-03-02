# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 15:56:43 2023

@author: dtopping
"""

#####################################
#####################################
'''AT SOME POINT, REDO USING METPY
TO GREATLY SIMPLIFY WIND COMPONENT
CALCULATIONS'''
#####################################
#####################################


import numpy as np
import tkinter as tk
from tkinter import filedialog
import os


def rotate_cm1(inpath,filename,outpath): 
    
    infile = inpath+filename

    sndg = open(infile,'r')
    sndg_cm1 = open(outpath+filename+'_rot','w')
    
    c1 = 611.12      # reference pressure [Pa]
    c2 = 2.5008e6    # latent heat of vaporization [J/kg]
    c3 = 461.2       # gas constant for water vapor [K]
    c4 = 273.16      # reference temperature [k]
    
    data = sndg.readlines()[5:]
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            data[i][j] = float(data[i][j].strip())
    
    sfc_data = data[0]
    h6km_data = data[60]
    level_data = data[1:]
    
    
    sfcprs,sfcth,sfcdwpt = (float(sfc_data[1]),
                            float(sfc_data[19]),
                            float(sfc_data[3]))
    
    sfce = c1*np.exp((c2/c3)*((1/c4)-(1/(c4+sfcdwpt))))     # [Pa]
    sfcqv = 621.97*(sfce/((sfcprs*100)-sfce))          # [g/kg]
    
    print('%3.5f \t%3.5f \t%3.5f' % (sfcprs,sfcth,sfcqv),
          file=sndg_cm1)

    dir0 = sfc_data[7] # sfc wind from direction
    spd0 = sfc_data[6] # sfc wind magnitude
    
    if 180 < dir0 <= 270:
        a0 = np.deg2rad(dir0 - 180) # angle from 0
        u0 = spd0*np.sin(a0) # sfc u component
        v0 = spd0*np.cos(a0) # sfc v component
    elif 90 < dir0 <= 180:
        a0 = -np.deg2rad(dir0 - 180) # angle from 0
        u0 = -spd0*np.sin(a0) # sfc u component
        v0 = spd0*np.cos(a0) # sfc v component
    elif 0 < dir0 <= 90:
        a0 = np.deg2rad(dir0) # angle from 0
        u0 = -spd0*np.sin(a0) # sfc u component
        v0 = -spd0*np.cos(a0) # sfc v component
    else:
        a0 = -np.deg2rad(dir0 - 360) # angle from 0
        u0 = spd0*np.sin(a0) # sfc u component
        v0 = -spd0*np.cos(a0) # sfc v component
        
    
    
    dir6 = h6km_data[7]# 6 km wind from direction
    spd6 = h6km_data[6] # 6 km wind magnitude   
    
    if 180 < dir6 <= 270:
        a6 = np.deg2rad(dir6 - 180) # angle from 0
        u6t = spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = spd6*np.cos(a6) - v0 # translated 6 km v wind
    elif 90 < dir6 <= 180:
        a6 = -np.deg2rad(dir6 - 180) # angle from 0
        u6t = -spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = spd6*np.cos(a6) - v0 # translated 6 km v wind
    elif 0 < dir6 <= 90:
        a6 = np.deg2rad(dir6) # angle from 0
        u6t = -spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = -spd6*np.cos(a6) - v0 # translated 6 km v wind
    else:
        a6 = -np.deg2rad(dir6 - 360) # angle from 0
        u6t = spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = -spd6*np.cos(a6) - v0 # translated 6 km v wind
      
    a0_6 = np.arctan((u6t)/(v6t))
    
    if u6t >= 0 and v6t > 0:
        rot = np.deg2rad(90) - a0_6
    elif u6t < 0 and v6t >= 0:
        rot = np.deg2rad(90) - a0_6
    elif u6t <= 0 and v6t < 0:
        rot = -(np.deg2rad(90) + a0_6)
    elif u6t > 0 and v6t <= 0:
        rot = -(np.deg2rad(90) + a0_6)
    else:
        rot = 0

     
    for level in level_data:
        height = level[0]
        th = level[19]
        prs = level[1]
        dwpt = level[3]
        wind_dir = level[7]
        wind_spd = level[6]
        
        e = c1*np.exp((c2/c3)*((1/c4)-(1/(c4+dwpt))))     # [Pa]
        qv = 621.97*(e/((prs*100)-e))                # [g/kg]
        
        # center hodograph origin at 0
        if 180 < wind_dir <= 270:
            a = np.deg2rad(wind_dir - 180) # angle from 0
            ut = wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = wind_spd*np.cos(a) - v0 # translated v component at level i
        elif 90 < wind_dir <= 180:
            a = -np.deg2rad(wind_dir - 180) # angle from 0
            ut = -wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = wind_spd*np.cos(a) - v0 # translated v component at level i
        elif 0 < wind_dir <= 90:
            a = np.deg2rad(wind_dir) # angle from 0
            ut = -wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = -wind_spd*np.cos(a) - v0 # translated v component at level i
        else:
            a = -np.deg2rad(wind_dir - 360) # angle from 0
            ut = wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = -wind_spd*np.cos(a) - v0 # translated v component at level i
        
        if ut==0 and vt==0:
            new_spd = 0
            at = 0
            a_diff = 0
            
            new_dir = wind_dir # from direction after translation and rotation
        else:
            new_spd = np.sqrt((ut**2)+(vt**2)) # wind magnitude after translation
            at = np.arctan(ut/vt)
        
            if ut >= 0 and vt > 0:
                dirt = at + np.deg2rad(180)
            elif ut < 0 and vt >= 0:
                dirt = at + np.deg2rad(180)
            elif ut <= 0 and vt < 0:
                dirt = at
            elif ut > 0 and vt <= 0:
                dirt = at + np.deg2rad(360)
            else:
                dirt = 0
                
            a_diff = dirt - np.deg2rad(wind_dir) # change in angle after translation
                
            # rotate hodograph so 0-6 km shear vector is parallel to x axis
            new_dir = wind_dir + np.rad2deg(a_diff) + np.rad2deg(rot) # from direction after translation and rotation
            
        if 180 < new_dir <= 270:
            new_a = np.deg2rad(new_dir - 180) # angle from 0
            new_u = new_spd*np.sin(new_a) # translated 6 km u wind
            new_v = new_spd*np.cos(new_a) # translated 6 km v wind
        elif 90 < new_dir <= 180:
            new_a = -np.deg2rad(new_dir - 180) # angle from 0
            new_u = -new_spd*np.sin(new_a) # translated 6 km u wind
            new_v = new_spd*np.cos(new_a) # translated 6 km v wind
        elif 0 < new_dir <= 90:
            new_a = np.deg2rad(new_dir) # angle from 0
            new_u = -new_spd*np.sin(new_a) # translated 6 km u wind
            new_v = -new_spd*np.cos(new_a) # translated 6 km v wind
        else:
            new_a = -np.deg2rad(new_dir - 360) # angle from 0
            new_u = new_spd*np.sin(new_a) # translated 6 km u wind
            new_v = -new_spd*np.cos(new_a) # translated 6 km v wind

        print('%3.5f \t%3.5f \t%3.5f \t%3.5f \t%3.5f' % (height,th,qv,new_u,new_v),
              file=sndg_cm1)

        
    sndg_cm1.close()
    sndg.close()

    
def rotate_sharppy(inpath,filename,outpath): 

    infile = inpath+filename

    sndg = open(infile,'r')
    sndg_sharppy = open(outpath+filename+'_rot','w')
    
    print('%s' % ('%TITLE%'),
          file=sndg_sharppy)
    print(' %s\t%s\n' % (filename[-3:], filename[1:7]+'/'+filename[7:9]+'00'),
          file=sndg_sharppy)
    print('   %s\t%s\t%s\t%s\t%s\t%s' % ('LEVEL', 'HGHT', 'TEMP', 'DWPT', 'WDIR', 'WSPD'),
          file=sndg_sharppy)
    print('%s' % ('------------------------------------------------------------------'),
          file=sndg_sharppy)
    print('%s' % ('%RAW%'),
          file=sndg_sharppy)    
    
    data = sndg.readlines()[6:-1]
    
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            data[i][j] = float(data[i][j].strip())
    

    dir0 = data[0][4] # sfc wind from direction
    spd0 = data[0][5] # sfc wind magnitude
    
    if 180 < dir0 <= 270:
        a0 = np.deg2rad(dir0 - 180) # angle from 0
        u0 = spd0*np.sin(a0) # sfc u component
        v0 = spd0*np.cos(a0) # sfc v component
    elif 90 < dir0 <= 180:
        a0 = -np.deg2rad(dir0 - 180) # angle from 0
        u0 = -spd0*np.sin(a0) # sfc u component
        v0 = spd0*np.cos(a0) # sfc v component
    elif 0 < dir0 <= 90:
        a0 = np.deg2rad(dir0) # angle from 0
        u0 = -spd0*np.sin(a0) # sfc u component
        v0 = -spd0*np.cos(a0) # sfc v component
    else:
        a0 = -np.deg2rad(dir0 - 360) # angle from 0
        u0 = spd0*np.sin(a0) # sfc u component
        v0 = -spd0*np.cos(a0) # sfc v component
        
        
    _heights = []
    for line in data:
        h = line[1]
        _heights.append(h)
    heights = np.array(_heights)
    diff = np.array(abs(heights-6000))
    i_nearest = np.where(diff==min(diff))[0][0]
    
    h6km_data = data[i_nearest]
       
    dir6 = h6km_data[4]# 6 km wind from direction
    spd6 = h6km_data[5] # 6 km wind magnitude   
    
    if 180 < dir6 <= 270:
        a6 = np.deg2rad(dir6 - 180) # angle from 0
        u6t = spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = spd6*np.cos(a6) - v0 # translated 6 km v wind
    elif 90 < dir6 <= 180:
        a6 = -np.deg2rad(dir6 - 180) # angle from 0
        u6t = -spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = spd6*np.cos(a6) - v0 # translated 6 km v wind
    elif 0 < dir6 <= 90:
        a6 = np.deg2rad(dir6) # angle from 0
        u6t = -spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = -spd6*np.cos(a6) - v0 # translated 6 km v wind
    else:
        a6 = -np.deg2rad(dir6 - 360) # angle from 0
        u6t = spd6*np.sin(a6) - u0 # translated 6 km u wind
        v6t = -spd6*np.cos(a6) - v0 # translated 6 km v wind
      
    
    a0_6 = np.arctan((u6t)/(v6t))
    
    if u6t >= 0 and v6t > 0:
        rot = np.deg2rad(90) - a0_6
    elif u6t < 0 and v6t >= 0:
        rot = np.deg2rad(90) - a0_6
    elif u6t <= 0 and v6t < 0:
        rot = -(np.deg2rad(90) + a0_6)
    elif u6t > 0 and v6t <= 0:
        rot = -(np.deg2rad(90) + a0_6)
    else:
        rot = 0

     
    for level in data:
        prs = level[0]
        height = level[1]
        temp = level[2]
        td = level[3]
        wind_dir = level[4]
        wind_spd = level[5]
        
        # center hodograph origin at 0
        if 180 < wind_dir <= 270:
            a = np.deg2rad(wind_dir - 180) # angle from 0
            ut = wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = wind_spd*np.cos(a) - v0 # translated v component at level i
        elif 90 < wind_dir <= 180:
            a = -np.deg2rad(wind_dir - 180) # angle from 0
            ut = -wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = wind_spd*np.cos(a) - v0 # translated v component at level i
        elif 0 < wind_dir <= 90:
            a = np.deg2rad(wind_dir) # angle from 0
            ut = -wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = -wind_spd*np.cos(a) - v0 # translated v component at level i
        else:
            a = -np.deg2rad(wind_dir - 360) # angle from 0
            ut = wind_spd*np.sin(a) - u0 # translated u component at level i
            vt = -wind_spd*np.cos(a) - v0 # translated v component at level i
        
        if ut==0 and vt==0:
            new_spd = 0
            at = 0
            a_diff = 0
            
            new_dir = wind_dir # from direction after translation and rotation
        else:
            new_spd = np.sqrt((ut**2)+(vt**2)) # wind magnitude after translation
            at = np.arctan(ut/vt)
        
            if ut >= 0 and vt > 0:
                dirt = at + np.deg2rad(180)
            elif ut < 0 and vt >= 0:
                dirt = at + np.deg2rad(180)
            elif ut <= 0 and vt < 0:
                dirt = at
            elif ut > 0 and vt <= 0:
                dirt = at + np.deg2rad(360)
            else:
                dirt = 0
                
            a_diff = dirt - np.deg2rad(wind_dir) # change in angle after translation
                
            # rotate hodograph so 0-6 km shear vector is parallel to x axis
            new_dir = wind_dir + np.rad2deg(a_diff) + np.rad2deg(rot) # from direction after translation and rotation

            # print(wind_dir, np.rad2deg(dirt), np.rad2deg(a_diff), np.rad2deg(rot), new_dir,new_spd)

        print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
              (prs,height,temp,td,new_dir,new_spd),
              file=sndg_sharppy)
        
    print('%s' % ('%END%'), file=sndg_sharppy)
        
    sndg_sharppy.close()
    sndg.close()


root = tk.Tk()
indir = filedialog.askdirectory(parent=root, initialdir='C:/', 
                                title='Select sharppy directory')
root.destroy()


# cm1path = indir+'/'

# outpath1 = cm1path +'rotated/'
# if not os.path.isdir(outpath1):
#     os.mkdir(outpath1)

# for filename in os.listdir(cm1path):
#     cm1file = cm1path+filename
#     if os.path.isfile(cm1file):
#         rotate_cm1(cm1path,filename,outpath1)


sharppypath = indir+'/'

outpath2 = sharppypath +'rotated/'
if not os.path.isdir(outpath2):
    os.mkdir(outpath2)

for filename in os.listdir(sharppypath):
    sharppyfile = sharppypath+filename
    if os.path.isfile(sharppyfile):
        rotate_sharppy(sharppypath,filename,outpath2)