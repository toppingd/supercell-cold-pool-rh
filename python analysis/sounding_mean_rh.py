# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 14:57:22 2023

@author: dtopping
"""

########################

import numpy as np
from io import StringIO
import sharppy.sharptab.profile as profile
import sharppy.sharptab.params as params
import metpy.calc as mcalc
from metpy.units import units

########################
########################


def calc_lfc(sf):

    sndg = open(sf,'r').read()

    ## read in the file
    data = np.array([l.strip() for l in sndg.split('\n')])

    ## necessary index points
    start_idx = np.where(data=='%RAW%')[0][0]+1
    finish_idx = np.where(data=='%END%')[0][0]

    ## put it all together for StringIO
    full_data = '\n'.join(data[start_idx:finish_idx][:])
    sound_data = StringIO(full_data)

    ## read the data into arrays
    p, h, T, Td, wdir, wspd = np.genfromtxt(sound_data,delimiter=',',comments="%",unpack=True )

    prof = profile.create_profile(profile='default',pres=p,hght=h,
                                  tmpc=T,dwpc=Td,wspd=wspd,wdir=wdir,
                                  missing=-9999,strictQC=True)

    mlpcl = params.parcelx(prof,flag=4)

    return mlpcl.lfcpres,mlpcl.elpres,mlpcl.lfchght,mlpcl.elhght


def get_rh(f): 

    # open, read, and reformat the file into indexable/usable values
    sndg = open(f,'r')
    
    # Store sounding data in arrays   
    data = sndg.readlines()[6:-1]
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            data[i][j] = float(data[i][j].strip())


    # get LFC and EL heights
    lfc_p,el_p,lfc_h,el_h = calc_lfc(f)

    p = np.array([line[0] for line in data])

    lfc_pdiff = abs(lfc_p - p)
    lfc_pi = np.where(lfc_pdiff == min(lfc_pdiff))[0][0]
    el_pdiff = abs(el_p - p)
    el_pi = np.where(el_pdiff == min(el_pdiff))[0][0]

    pbl_data = data[:lfc_pi+1]
    ft_data = data[lfc_pi+1:el_pi+1]

    pbl_rh = []
    # print('--PBL--')
    for level in pbl_data:
        t,td = (float(level[2])*units('degC'),
                float(level[3])*units('degC'))
        rh = mcalc.relative_humidity_from_dewpoint(t,td).to('percent').magnitude
        pbl_rh.append(rh)
        # print(rh)
        
    mean_pbl_rh = np.mean(pbl_rh)

    ft_rh = []
    # print('--FT--')
    for level in ft_data:
        t,td = (float(level[2])*units('degC'),
                float(level[3])*units('degC'))
        rh = mcalc.relative_humidity_from_dewpoint(t,td).to('percent').magnitude
        ft_rh.append(rh)
        # print(rh)
        
    mean_ft_rh = np.mean(ft_rh)


    return mean_pbl_rh,mean_ft_rh


infile = '/t1/topping/soundings/2500CAPE/dd_hodo4_sharppy'

lfc_p,el_p,lfc_h,el_h = calc_lfc(infile)
mean_pbl_rh,mean_ft_rh = get_rh(infile)

print('ML Parcel LFC (height): '+str(int(lfc_h))+' m\n'
      'ML Parcel EL (height): '+str(int(el_h))+' m')

print('mean PBL RH: '+str(int(mean_pbl_rh))+'%\n'
      'mean FT RH: '+str(int(mean_ft_rh))+'%')

