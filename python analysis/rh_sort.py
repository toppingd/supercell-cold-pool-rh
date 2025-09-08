# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 14:57:22 2023

@author: dtopping
"""

########################


import os
import numpy as np
from io import StringIO
import sharppy.sharptab.profile as profile
import sharppy.sharptab.params as params
import metpy.calc as mcalc
from metpy.units import units
import shutil
import tkinter as tk
from tkinter import filedialog


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

    #return mlpcl.lfchght,mlpcl.elhght
    return mlpcl.lfcpres,mlpcl.elpres


def get_rh(f,sf):

    # open, read, and reformat the file into indexable/usable values
    file = open(f,'r')
    data = file.readlines()
    file.close()
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            if data[i][j].strip().replace('.','').replace('-','').isdecimal():
                data[i][j] = float(data[i][j].strip())
            else:
                data[i][j] = data[i][j].strip()

    sfc_data = data[0]
    # all other variables from the surface to 16km
    level_data = data[5:]


    # get LFC and EL heights
    # lfc_h,el_h = calc_lfc(sf)
    lfc_p,el_p = calc_lfc(sf)

    # h = np.array([line[0] for line in level_data])
    p = np.array([line[1] for line in level_data])

    # lfc_hdiff = abs(lfc_h - h)
    # lfc_hi = np.where(lfc_hdiff == min(lfc_hdiff))[0][0]
    # el_hdiff = abs(el_h - h)
    # el_hi = np.where(el_hdiff == min(el_hdiff))[0][0]
    lfc_pdiff = abs(lfc_p - p)
    lfc_pi = np.where(lfc_pdiff == min(lfc_pdiff))[0][0]
    el_pdiff = abs(el_p - p)
    el_pi = np.where(el_pdiff == min(el_pdiff))[0][0]

    # pbl_data = level_data[:lfc_hi+1]
    # ft_data = level_data[lfc_hi+1:el_hi+1]
    pbl_data = level_data[:lfc_pi+1]
    ft_data = level_data[lfc_pi+1:el_pi+1]

    pbl_rh = []
    sfc=True
    for level in pbl_data:
        if sfc:
            sfc_t = (sfc_data[6]-32)*(5/9)*units('degC')
            sfc_td = (sfc_data[7]-32)*(5/9)*units('degC')
            sfc_rh = mcalc.relative_humidity_from_dewpoint(sfc_t,sfc_td).to('percent')
            pbl_rh.append(sfc_rh)
            sfc=False
        else:
            pbl_rh.append(level[23])
    mean_pbl_rh = np.mean(pbl_rh)

    ft_rh = []
    for level in ft_data:
        ft_rh.append(level[23])
    mean_ft_rh = np.mean(ft_rh)

    return (f,mean_pbl_rh,mean_ft_rh,sfc_rh)


def calc_quantiles(pbl_rh_li,ft_rh_li,sfc_rh_li):

    #quartiles = [0.25,0.5,0.75]
    tertiles = [0.33333,0.66666]

    pbl_q = np.quantile(pbl_rh_li,tertiles,method='median_unbiased')
    ft_q = np.quantile(ft_rh_li,tertiles,method='median_unbiased')
    sfc_q = np.quantile(sfc_rh_li,tertiles,method='median_unbiased')

    return (pbl_q,ft_q,sfc_q)


def sort_rh(indir,outdir,f_rh,pbl_q,ft_q,sfc_q):

    outdir+='/'

    if len(pbl_q)==2:
        b1 = [] # low PBL RH, low FT RH
        b2 = [] # low PBL RH, high FT RH
        b3 = [] # high PBL RH, low FT RH
        b4 = [] # high PBL RH, high FT RH
        # for f in f_rh:
        #     if pbl_q[0] < f[1] <= pbl_q[1] and ft_q[0] < f[2] <= ft_q[1]:
        #         if sfc_q[0] < f[3] <= sfc_q[1]:
        #             b1.append(f[0])

        #     elif pbl_q[0] < f[1] <= pbl_q[1] and f[2] > ft_q[1]:
        #         if sfc_q[0] < f[3] <= sfc_q[1]:
        #             b2.append(f[0])

        #     elif f[1] > pbl_q[1] and ft_q[0] < f[2] <= ft_q[1]:
        #         if f[3] > sfc_q[1]:
        #             b3.append(f[0])

        #     elif f[1] > pbl_q[1] and f[2] > ft_q[1]:
        #         if f[3] > sfc_q[1]:
        #             b4.append(f[0])
        
        
        
        # determine mean relative humidity for each regime layer
        moistPBL_bin,dryPBL_bin,moistFT_bin,dryFT_bin = ([],[],[],[])
        for f in f_rh:
            if f[1] >= pbl_q[1]:
                if f[3] >= sfc_q[1]:
                    moistPBL_bin.append(f[1])
            elif f[1] < pbl_q[1]:
                if f[3] < sfc_q[1]:
                    dryPBL_bin.append(f[1])
            else:
                pass

            if f[2] >= ft_q[1]:
                moistFT_bin.append(f[2])
            elif f[2] < ft_q[1]:
                dryFT_bin.append(f[2])
            else:
                pass
        moistPBL_mean = np.mean(moistPBL_bin)
        dryPBL_mean = np.mean(dryPBL_bin)
        moistFT_mean = np.mean(moistFT_bin)
        dryFT_mean = np.mean(dryFT_bin)
        print('moistPBL mean RH: '+str(moistPBL_mean)+'\n'
              'dryPBL mean RH: '+str(dryPBL_mean)+'\n'
              'moistFT mean RH: '+str(moistFT_mean)+'\n'
              'dryFT mean RH: '+str(dryFT_mean)+'\n')
        
        
        for f in f_rh:
            if f[1] < pbl_q[1] and f[2] < ft_q[1]:
                if f[3] < sfc_q[1]:
                    b1.append(f[0])

            elif f[1] < pbl_q[1] and f[2] >= ft_q[1]:
                if f[3] < sfc_q[1]:
                    b2.append(f[0])

            elif f[1] >= pbl_q[1] and f[2] < ft_q[1]:
                if f[3] >= sfc_q[1]:
                    b3.append(f[0])

            elif f[1] >= pbl_q[1] and f[2] >= ft_q[1]:
                if f[3] >= sfc_q[1]:
                    b4.append(f[0])

            else:
                pass


    elif len(pbl_q)==3:
        b1 = [] # low PBL RH, low FT RH
        b2 = [] # low PBL RH, high FT RH
        b3 = [] # high PBL RH, low FT RH
        b4 = [] # high PBL RH, high FT RH
        for f in f_rh:
            if pbl_q[0] < f[1] <= pbl_q[1] and ft_q[0] < f[2] <= ft_q[1]:
                if sfc_q[0] < f[3] <= sfc_q[1]:
                    b1.append(f[0])

            elif pbl_q[0] < f[1] <= pbl_q[1] and f[2] > ft_q[2]:
                if sfc_q[0] < f[3] <= sfc_q[1]:
                    b2.append(f[0])

            elif f[1] > pbl_q[2] and ft_q[0] < f[2] <= ft_q[1]:
                if f[3] > sfc_q[2]:
                    b3.append(f[0])

            elif f[1] > pbl_q[2] and f[2] > ft_q[2]:
                if f[3] > sfc_q[2]:
                    b4.append(f[0])

            else:
                pass

    else:
        print('Need to alter code if other than quartiles or thirds')


    # bins = (b1,b2,b3,b4)
    # bin_names = ('dryPBL_dryFT','dryPBL_moistFT','moistPBL_dryFT','moistPBL_moistFT')
    # for i in range(len(bins)):
    #     for j in bins[i]:
    #         jparts = list(j.split('/'))
    #         infile = j
    #         outpath = outdir+bin_names[i]+'/'
    #         if not os.path.isdir(outpath):
    #             os.mkdir(outpath)
    #         outfile = outpath+j[-13:-4]+'_'+j[-3:]+'_'+jparts[-2]
            # shutil.copy(infile,outfile)


#########################
#########################


root = tk.Tk()
ogdir = filedialog.askdirectory(parent=root, initialdir='C:/',
                                title='Select an input directory')
root.destroy()

root = tk.Tk()
outdir = filedialog.askdirectory(parent=root, initialdir='C:/',
                                title='Select an output directory')
root.destroy()

indir = ogdir+'/'
cats = ['nontor','wektor','sigtor']
files = []
sfiles = []

for cat in cats:
    folder = indir+cat+'/'
    sharppy_folder = folder+'sharppy_soundings/'
    for file, sharppy_file in zip(os.listdir(folder),os.listdir(sharppy_folder)):
        files.append(folder+file)
        sfiles.append(sharppy_folder+sharppy_file)

lfc_li = []
for f, sf in zip(files, sfiles):
    if os.path.isfile(f) and os.path.isfile(sf):
        lfc_plev,el_plev = calc_lfc(sf)
        if isinstance(lfc_plev,float) and isinstance(el_plev,float):
            lfc_li.append((f,sf,lfc_plev))
    else:
        print('no file with name: '+f+' ** or ** '+sf)

lfc_plevs = []
[lfc_plevs.append(x[2]) for x in lfc_li]
mean_lfc_plev = np.mean(lfc_plevs)
lfc_plev_std = np.std(lfc_plevs)

new_files = []
new_sfiles = []
for item in lfc_li:
    if mean_lfc_plev - lfc_plev_std < item[2] < mean_lfc_plev + lfc_plev_std:
        new_files.append(item[0])
        new_sfiles.append(item[1])

f_rh = []
pbl_rh_li = []
ft_rh_li = []
sfc_rh_li = []

for f, sf in zip(new_files, new_sfiles):
    if os.path.isfile(f) and os.path.isfile(sf):
        mean_rh = get_rh(f,sf)
        f_rh.append(mean_rh)
        pbl_rh_li.append(mean_rh[1])
        ft_rh_li.append(mean_rh[2])
        sfc_rh_li.append(mean_rh[3])

pbl_q,ft_q,sfc_q = calc_quantiles(pbl_rh_li,ft_rh_li,sfc_rh_li)

# sort based on relative humidity
sort_rh(ogdir,outdir,f_rh,pbl_q,ft_q,sfc_q)
