#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 14:56:47 2025

@author: dtopping
"""


import sharppy.sharptab.profile as profile
import sharppy.sharptab.params as params

import numpy as np
from io import StringIO


# infile = '/t1/topping/soundings/2500CAPE/mm_extended_sharppy'
# infile = '/t1/topping/soundings/2500CAPE/md_extended_sharppy'
# infile = '/t1/topping/soundings/2500CAPE/dm_extended_sharppy'
# infile = '/t1/topping/soundings/2500CAPE/dd_extended_sharppy'

# infile = '/t1/topping/soundings/1500CAPE/mm_qt_extended_sharppy'
# infile = '/t1/topping/soundings/1500CAPE/md_qt_extended_sharppy'
# infile = '/t1/topping/soundings/1500CAPE/dm_qt_extended_sharppy'
# infile = '/t1/topping/soundings/1500CAPE/dd_qt_extended_sharppy'

# infile = '/t1/topping/soundings/3500CAPE/mm_qt_extended_sharppy'
# infile = '/t1/topping/soundings/3500CAPE/md_qt_extended_sharppy'
# infile = '/t1/topping/soundings/3500CAPE/dm_qt_extended_sharppy'
# infile = '/t1/topping/soundings/3500CAPE/dd_qt_extended_sharppy'

###########
###########

CAPE = '3500'

# infile = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/mm_'+CAPE+'_extended_sharppy'
# infile = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/md_'+CAPE+'_extended_sharppy'
# infile = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dm_'+CAPE+'_extended_sharppy'
infile = 'C:/Users/dtopp/OneDrive/Desktop/revised_figs/soundings/'+CAPE+'/dd_'+CAPE+'_extended_sharppy'


spc_file = open(infile, 'r').read()

def parseSPC(spc_file):

    ## read in the file
    data = np.array([l.strip() for l in spc_file.split('\n')])

    ## necessary index points
    start_idx = np.where(data=='%RAW%')[0][0]+1
    finish_idx = np.where(data=='%END%')[0][0]

    ## put it all together for StringIO
    full_data = '\n'.join(data[start_idx:finish_idx][:])
    sound_data = StringIO(full_data)

    ## read the data into arrays
    p,h,t,td,wdir,wspd = np.genfromtxt(sound_data,delimiter=',',comments="%",\
                                       unpack=True )

    return p,h,t,td,wdir,wspd

pres,hght,tmpc,dwpc,wdir,wspd = parseSPC(spc_file)

prof = profile.create_profile(profile='default',pres=pres,hght=hght,tmpc=tmpc, \
                              dwpc=dwpc,wspd=wspd,wdir=wdir,\
                              missing=-9999,strictQC=True)
    
      
sfcpcl = params.parcelx(prof, flag=1) # Surface Parcel
mupcl = params.parcelx(prof, flag=3) # Most-Unstable Parcel
mlpcl = params.parcelx(prof, flag=4) # 100 mb Mean Layer Parcel


###############################################################################
# Thermodynamics
###############################################################################

# mean RH (%)
pbl_mean_rh = params.mean_relh(prof, mlpcl.pres, mlpcl.lfcpres)
ft_mean_rh = params.mean_relh(prof, mlpcl.lfcpres, mlpcl.elpres)
rh_lcl_700 = params.mean_relh(prof, mlpcl.lclpres, 700)
rh_700_500 = params.mean_relh(prof, 700, 500)
rh_500_300 = params.mean_relh(prof, 500, 300)


# PWAT (inches)
pwat = params.precip_water(prof, mlpcl.pres,300)

print(pwat)


# LCL and LFC
ml_lcl = mlpcl.lclhght # m AGL
ml_lfc = mlpcl.lfchght # m AGL
ml_lcl_to_lfc = ml_lfc - ml_lcl # m


# CAPE and CIN (J/kg)
sfc_cape = sfcpcl.bplus
sfc_cin = sfcpcl.bminus
sfc_3cape = sfcpcl.b3km

mu_cape = mupcl.bplus
mu_cin = mupcl.bminus
mu_3cape = mupcl.b3km

ml_cape = mlpcl.bplus
ml_cin = mlpcl.bminus
ml_3cape = mlpcl.b3km


# DCAPE
dcape,dpcl_ttrace,dpcl_ptrace = params.dcape(prof) # J/kg
dpcl_min_temp = np.min(dpcl_ttrace) # deg C


# Lapse rates (K/km)
lr_sfc_850mb = params.lapse_rate(prof, mlpcl.pres,850,pres=True)
lr_0_3km = params.lapse_rate(prof, 0,3000,pres=False)
lr_3_6km = params.lapse_rate(prof, 3000,6000,pres=False)
lr_850_500mb = params.lapse_rate(prof, 850,500,pres=True)
lr_700_500mb = params.lapse_rate(prof, 700,500,pres=True)


###############################################################################
# Kinematics
###############################################################################

# shear



# near-ground storm-relative motion





