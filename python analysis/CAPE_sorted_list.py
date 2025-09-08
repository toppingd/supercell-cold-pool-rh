# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 15:01:32 2023

@author: dtopping
"""


import os
import numpy as np

from io import StringIO
import sharppy.sharptab.profile as profile
import sharppy.sharptab.params as params

import itertools
import time


#############################
#############################

start = time.time()

PARCEL = 2 # 1 = Surface based; 2 = Mixed Layer
MIN_CAPE = 1000
CAPE_THRESH = 500 # max absolute error in CAPE
CIN_THRESH = 10 # max absolute error in CIN


def parseSNDG(sndg):
    """
        This function will read a SPC-style formatted observed sounding file,
        similar to that of the 14061619.OAX file included in the SHARPpy distribution.

        It will return the pressure, height, temperature, dewpoint, wind direction and wind speed data
        from that file.
    """
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

    return p, h, T, Td, wdir, wspd


def filter_sharppy(path,filename):

    infile = path+filename

    sndg = open(infile,'r').read()

    pres, hght, tmpc, dwpc, wdir, wspd = parseSNDG(sndg)

    prof = profile.create_profile(profile='default',pres=pres,hght=hght,
                                  tmpc=tmpc,dwpc=dwpc,wspd=wspd,wdir=wdir,
                                  missing=-9999,strictQC=True)

    sfcpcl = params.parcelx(prof,flag=1) # Surface Based Parcel
    mlpcl = params.parcelx(prof,flag=4) # 100 mb Mean Layer Parcel


    SBCAPE = sfcpcl.bplus
    SBCIN = sfcpcl.bminus
    MLCAPE = mlpcl.bplus
    MLCIN = mlpcl.bminus

    return infile,SBCAPE,MLCAPE,SBCIN,MLCIN


inpath = '/t1/topping/soundings/rh_sort/'
cats =['dryPBL_dryFT','dryPBL_moistFT','moistPBL_dryFT','moistPBL_moistFT']

hh = []
hl = []
lh = []
ll = []
for cat in cats:
    path = inpath+cat+'/sharppy_soundings/'
    for filename in os.listdir(path):
        infile = path+filename
        if os.path.isfile(infile):
            calc = filter_sharppy(path,filename)
            if cat==cats[0]:
                ll.append(calc)
            elif cat==cats[1]:
                lh.append(calc)
            elif cat==cats[2]:
                hl.append(calc)
            else:
                hh.append(calc)

all_cats = [('mm',hh),('md',hl),('dm',lh),('dd',ll)]
for cat in all_cats:
    cat_sort = sorted(cat[1], key=lambda x: x[PARCEL])
        
    if PARCEL==1:
        outfile = inpath+cat[0]+'_1500_sbcape_sorted.txt'
    elif PARCEL==2:
        outfile = inpath+cat[0]+'_1500_mlcape_sorted.txt'
    else:
        print('choose appropriate value for parcel type')

    output = open(outfile,'w')

    for i in cat_sort:
        filename = i[0][-28:-8]
        if PARCEL==1:
            output.write(('{} \t{} \t{} \n').format(filename,i[1],i[3]))
        elif PARCEL==2:
            output.write(('{} \t{} \t{} \n').format(filename,i[2],i[4]))
        # output.write('\n')

    output.close()


end = time.time()

print('Finished in: '+str(end-start)+' seconds')