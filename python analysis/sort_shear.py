# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 14:53:14 2023

@author: dtopping
"""

########################


import os
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units
import shutil


########################
########################


def calc_srh(level_data):

    prs,u,v,h = ([],
                 [],
                 [],
                 [])

    depth = (1000 * units('m'),3000 * units('m'))
    bottom = 0 * units('m')

    for level in level_data:
        prs.append(level[1])
        u.append(level[4])
        v.append(level[5])
        h.append(level[0])

    # Metpy requires value to have units attached
    prs = prs * units('hPa')
    u = u * units('m/s')
    v = v * units('m/s')
    h = h * units('m')

    # bunkers right storm motion
    bunkers = mpcalc.bunkers_storm_motion(prs,u,v,h)
    right_mover = bunkers[0]

    # 0-1km Storm Relative Helicity
    srh1 = mpcalc.storm_relative_helicity(h[:11],u[:11],v[:11],depth[0],
                                          bottom=bottom,
                                          storm_u=right_mover[0],
                                          storm_v=right_mover[1])

    # 0-3km Storm Relative Helicity
    srh3 =  mpcalc.storm_relative_helicity(h[:31],u[:31],v[:31],depth[1],
                                           bottom=bottom,
                                           storm_u=right_mover[0],
                                           storm_v=right_mover[1])

    return (srh1[2],srh3[2])


def calc_bulk_shear(level_data):

    prs,u,v,h = ([],
                 [],
                 [],
                 [])

    for level in level_data:
        prs.append(level[1])
        u.append(level[4])
        v.append(level[5])
        h.append(level[0])

    depth = 6000 * units('m')
    bottom = 0 * units('m')

    # Metpy requires value to have units attached
    prs = prs * units('hPa')
    u = u * units('m/s')
    v = v * units('m/s')
    h = h * units('m')

    shear_comp = mpcalc.bulk_shear(prs[:61],u[:61],v[:61],height=h[:61],
                                   bottom=bottom,depth=depth)

    u_shear = shear_comp[0].to(units('knots')).magnitude
    v_shear = shear_comp[1].to(units('knots')).magnitude

    shear_mag = np.sqrt(u_shear**2 + v_shear**2)

    return shear_mag


def get_shear(indir,filename):

    ogfilename = filename
    if filename[0]=='.':
        filename = filename[1:14]
    else:
        filename = filename[:13]
    inpath = indir+filename

    # open, read, and reformat the file into indexable/usable values
    f = open(inpath,'r')
    data = f.readlines()
    f.close()
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            if data[i][j].strip().replace('.','').replace('-','').isdecimal():
                data[i][j] = float(data[i][j].strip())
            else:
                data[i][j] = data[i][j].strip()

    # all other variables from the surface to 16km
    level_data = data[5:]

    srh = calc_srh(level_data)
    srh1,srh3 = (srh[0].magnitude,srh[1].magnitude)
    deep_shear = calc_bulk_shear(level_data)

    return (ogfilename,srh1,deep_shear)


def calc_quantiles(f_shear,srh,deep_shear):

    # normalize srh and deep_shear
    s_index = []
    for i in range(len(srh)):
        srh_norm = (srh[i]-np.min(srh))/(np.max(srh)-np.min(srh))
        shear_norm = (deep_shear[i]-np.min(deep_shear))/(np.max(deep_shear)-np.min(deep_shear))
        s_val = srh_norm + shear_norm
        s_index.append(s_val)
        f_shear[i].append(s_val)


    #quartiles = [0.25,0.5,0.75]
    thirds = [0.33333,0.66666]

    quantiles = np.quantile(s_index,thirds,method='median_unbiased')

    return (quantiles)


def sort_shear(ogdir,f_shear,quantiles):

    outdir = ogdir + 'shear_sort/'

    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    if len(quantiles)==2:
        b1 = [] # bin up to lower third
        b2 = [] # bin from lower third to upper third
        b3 = [] # bin from upper third up
        for f in f_shear:

            if f[2] <= quantiles[0]:
                # original filename, new filename with nontor/sigtor designation
                b1.append((f[0][0],f[0][0].replace('.','_')+'_'+f[1]))
            elif quantiles[0] < f[2] <= quantiles[1]:
                b2.append((f[0][0],f[0][0].replace('.','_')+'_'+f[1]))
            else:
                b3.append((f[0][0],f[0][0].replace('.','_')+'_'+f[1]))

        bins = (b1,b2,b3)
        bin_names = ['lower_third','middle_third','upper_third']
        for i in range(len(bins)):
            for j in bins[i]:
                infile = ogdir+j[1][-6:]+'/'+j[0]
                outpath = outdir+bin_names[i]+'/'+j[1][-6:]+'/'
                if not os.path.isdir(outpath[:-7]):
                    os.mkdir(outpath[:-7])
                if not os.path.isdir(outpath):
                    os.mkdir(outpath)
                outfile = outpath+j[1]
                shutil.copy(infile,outfile)


    elif len(quantiles)==3:
        b1 = [] # bin up to lower quatile
        b2 = [] # bin from lower quartile and median
        b3 = [] # bin from median and upper quartile
        b4 = [] # bin from upper quartile up
        for f in f_shear:
            if f[2] <= quantiles[0]:
                b1.append((f[0][0],f[0][0].replace('.','_')+'_'+f[1]))
            elif quantiles[0] < f[2] <= quantiles[1]:
                b2.append((f[0][0],f[0][0].replace('.','_')+'_'+f[1]))
            elif quantiles[1] < f[2] <= quantiles[2]:
                b3.append((f[0][0],f[0][0].replace('.','_')+'_'+f[1]))
            else:
                b4.append((f[0][0],f[0][0].replace('.','_')+'_'+f[1]))


        bins = (b1,b2,b3,b4)
        bin_names = ['q1','q2','q3','q4']
        for i in range(len(bins)):
            for j in bins[i]:
                infile = ogdir+j[1][-6:]+'/'+j[0]
                outpath = outdir+bin_names[i]+'/'+j[1][-6:]+'/'
                if not os.path.isdir(outpath[:-7]):
                    os.mkdir(outpath[:-7])
                if not os.path.isdir(outpath):
                    os.mkdir(outpath)
                outfile = outpath+j[1]
                shutil.copy(infile,outfile)

    else:
        print('Need to alter code if other than quartiles or thirds')


#########################
#########################


# directory containing original soundings
ogdir = '/t1/topping/soundings/original_all/'
# only interested in nontornadic vs tornadic supercells
foci = ['nontor','wektor','sigtor']

f_shear = []
srh = []
deep_shear = []
for focus in foci:
    indir = ogdir+focus+'/'
    for filename in os.listdir(indir):
        infile = indir+filename
        if os.path.isfile(infile):
            shear = get_shear(indir,filename)
            f_shear.append([shear,focus])
            srh.append(shear[1])
            deep_shear.append(shear[2])


q = calc_quantiles(f_shear,srh,deep_shear)

# sort based on storm relative helicity quantiles
sort_shear(ogdir,f_shear,q)
