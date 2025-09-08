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

import tkinter as tk
from tkinter import filedialog

import itertools
import time


#############################
#############################

start = time.time()

PARCEL = 2 # 1 = Surface based; 2 = Mixed Layer
MIN_CAPE = 2000
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

    return infile,SBCAPE,SBCIN,MLCAPE,MLCIN


root = tk.Tk()
indir = filedialog.askdirectory(parent=root, initialdir='C:/',
                                title='Select input directory')
root.destroy()

inpath = indir+'/'

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

all_cats = [hh,hl,lh,ll]

combs = list(itertools.product(*all_cats))
comb_errs = []
filter_combs = []
for comb in combs:
    cape = []
    cin = []
    ncape = []
    ncin = []
    for ccase in comb:
        if PARCEL==1:
            cape.append(ccase[1])
            cin.append(ccase[2])
            ncape.append(ccase[1]/5000)
            ncin.append(ccase[2]/-100)
        elif PARCEL==2:
            cape.append(ccase[3])
            cin.append(ccase[4])
            ncape.append(ccase[3]/5000)
            ncin.append(ccase[4]/-100)
    cape_err = [abs(c1-c2) for c1,c2 in itertools.combinations(cape, 2)]
    cin_err = [abs(c1-c2) for c1,c2 in itertools.combinations(cin, 2)]
    ncape_err = [abs(c1-c2) for c1,c2 in itertools.combinations(ncape, 2)]
    ncin_err = [abs(c1-c2) for c1,c2 in itertools.combinations(ncin, 2)]
    err = []
    check1=0
    check2=0
    for c in cape:
        if c>=MIN_CAPE:
            check1+=1
    for i in range(len(cape_err)):
        if cape_err[i]<=CAPE_THRESH and cin_err[i]<=CIN_THRESH:
            check2+=1
    if check1==4 and check2==6:
        for i in range(len(cape_err)):
            err.append(ncape_err[i] + ncin_err[i])
        filter_combs.append(comb)
        comb_errs.append(np.max(err))

i_min = sorted(range(len(comb_errs)), key=lambda sub: comb_errs[sub])
comb_min = []
for loc in i_min:
    comb_min.append(filter_combs[loc])



if PARCEL==1:
    outfile = inpath+'sb_filtered.txt'
elif PARCEL==2:
    outfile = inpath+'ml_filtered.txt'
else:
    print('choose appropriate value for parcel type')

output = open(outfile,'w')

for j in comb_min:
    for k in j:
        filename = k[0][-23:-8]
        if PARCEL==1:
            output.write(('{} \t{} \t{} \n').format(filename,k[1],k[2]))
        elif PARCEL==2:
            output.write(('{} \t{} \t{} \n').format(filename,k[3],k[4]))
    output.write('\n\n')

output.close()

end = time.time()

print('Finished in: '+str(end-start)+' seconds')
