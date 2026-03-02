# -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 13:20:29 2023

@author: dtopping
"""

import os
import numpy as np
from metpy.units import units
import metpy.calc as mcalc


def sharpp_to_cm1(indir, filename, outdir):

    infile = f'{indir}/{filename}'
    sndg = open(infile, 'r')

    if 'sharppy' in filename:
        filename_cm1 = filename.replace('_sharppy', '')
    sndg_cm1 = open(f'{outdir}/{filename_cm1}_cm1', 'w')

    # Store sounding data in arrays
    data = sndg.readlines()[6:-1]
    for i in range(len(data)):
        data[i] = data[i].split(',')
        for j in range(len(data[i])):
            data[i][j] = float(data[i][j].strip())

    sfc_data = data[0]

    sfcprs, sfct, sfcdwpt = (float(sfc_data[0]),
                             float(sfc_data[2]),
                             float(sfc_data[3]))

    sfcth = (sfct + 273.15) * ((1000 / sfcprs) ** (287 / 1004))
    # print(filename, str(sfcth))

    c1 = 611.12  # reference pressure [Pa]
    c2 = 2.5008e6  # latent heat of vaporization [J/kg]
    c3 = 461.2  # gas constant for water vapor [K]
    c4 = 273.16  # reference temperature [k]

    sfce = c1 * np.exp((c2 / c3) * ((1 / c4) - (1 / (c4 + sfcdwpt))))  # [Pa]
    sfcqv = 621.97 * (sfce / ((sfcprs * 100) - sfce))  # [g/kg]

    print('%3.5f \t%3.5f \t%3.5f' % (sfcprs, sfcth, sfcqv),
          file=sndg_cm1)

    for line in data:
        prs, height, t, dwpt, wdir, wspd = (float(line[0]),
                                            float(line[1]),
                                            float(line[2]),
                                            float(line[3]),
                                            float(line[4]),
                                            float(line[5]))

        th = (t + 273.15) * ((1000 / prs) ** (2 / 7))

        e = c1 * np.exp((c2 / c3) * ((1 / c4) - (1 / (c4 + dwpt))))  # [Pa]
        qv = 621.97 * (e / ((prs * 100) - e))  # [g/kg]

        wdir = wdir * units('degrees')
        wspd = (wspd * units('knots')).to(units('m/s'))

        # print(wdir,wspd)

        u, v = mcalc.wind_components(wspd, wdir)
        # print(u,v)

        print('%3.5f \t%3.5f \t%3.5f \t%3.5f \t%3.5f' % (height,
                                                         th,
                                                         qv,
                                                         u.magnitude,
                                                         v.magnitude),
              file=sndg_cm1)

    sndg_cm1.close()
    sndg.close()


cape_options = ('lowCAPE', 'moderateCAPE', 'highCAPE')
cape_choice = cape_options[0]

indir = f'D:/cold_pool_mwr/soundings/final/sharppy/{cape_choice}'
outdir = f'D:/cold_pool_mwr/soundings/final/cm1/{cape_choice}'

for filename in os.listdir(indir):
    sharppy_file = f'{indir}/{filename}'
    if os.path.isfile(sharppy_file) and '_sharppy' in filename:
        # print(filename)
        sharpp_to_cm1(indir,filename,outdir)
