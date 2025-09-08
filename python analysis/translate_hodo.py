# -*- coding: utf-8 -*-
"""
Created on Fri Nov 1, 2024

@author: dtopping
"""


import numpy as np
import metpy.calc as mcalc
from metpy.units import units
import os


def get_sfc_wind(infile): 

    sndg = open(infile,'r')
 
    data = sndg.readlines()[5]
    data = data.split(',')
    for i in range(len(data)):
        data[i] = float(data[i].strip())

    spd0 = data[6]*units('m/s') # sfc wind magnitude
    dir0 = data[7] # sfc wind from direction
    
    u,v = mcalc.wind_components(spd0.to('knots'),dir0*units('degrees'))
    
    sndg.close()
    
    return u.magnitude, v.magnitude


def translate_hodo(sfc_u_mean,sfc_v_mean,hodo_file,outfile): 

    og_hodo = open(hodo_file,'r')
    data = og_hodo.readlines()[6:-1]
    new_hodo = open(outfile,'w')
    
    print('%s' % ('%TITLE%'),
          file=new_hodo)
    print(' %s\t%s\n' % ('IDEAL', '010101/1200'),
          file=new_hodo)
    print('   %s\t%s\t%s\t%s\t%s\t%s' % ('LEVEL', 'HGHT', 'TEMP', 'DWPT', 'WDIR', 'WSPD'),
          file=new_hodo)
    print('%s' % ('------------------------------------------------------------------'),
          file=new_hodo)
    print('%s' % ('%RAW%'),
          file=new_hodo)    
    
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            data[i][j] = float(data[i][j].strip())

         
    for i in range(len(data)):
        prs = data[i][0]
        height = data[i][1]
        temp = data[i][2]
        td = data[i][3]
        wind_dir = data[i][4]
        wind_spd = data[i][5]
        
        u_wind,v_wind = mcalc.wind_components(wind_spd*units('knots'),
                                              wind_dir*units('degrees'))
        
        u_translated = u_wind + sfc_u_mean*units('knots')
        v_translated = v_wind + sfc_v_mean*units('knots')
        
        new_spd = mcalc.wind_speed(u_translated,v_translated).magnitude
        new_dir = mcalc.wind_direction(u_translated,v_translated).magnitude
    
        print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
              (prs,height,temp,td,new_dir,new_spd),
              file=new_hodo)
        
    print('%s' % ('%END%'), file=new_hodo)  
        
    
    og_hodo.close()
    new_hodo.close()
 
    
indir = '/t1/topping/soundings/original_all/sigtor/'

sfc_u_li = []
sfc_v_li = []
for filename in os.listdir(indir):
    if os.path.isfile(indir+filename):
        infile = indir+filename
        
        sfc_u,sfc_v = get_sfc_wind(infile) # get surface wind components (knots)
        
    sfc_u_li.append(sfc_u)
    sfc_v_li.append(sfc_v)
    
sfc_u_mean = np.mean(sfc_u_li)
sfc_v_mean = np.mean(sfc_v_li)

mean_spd = mcalc.wind_speed(sfc_u_mean*units('knots'),
                            sfc_v_mean*units('knots')).magnitude

mean_dir = mcalc.wind_direction(sfc_u_mean*units('knots'),
                                sfc_v_mean*units('knots')).magnitude


hodo_file = '/t1/topping/soundings/hodographs/sigtor_shear_sharppy' #sharppy file
outfile = '/t1/topping/soundings/hodographs/sigtor_translated_sharppy'

translate_hodo(sfc_u_mean,sfc_v_mean,hodo_file,outfile)

