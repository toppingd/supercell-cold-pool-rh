# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 11:22:59 2023

@author: dtopping
"""

import os


def convert_sharppy(inpath, folder, filename, outpath):
    infile = f'{indir}/{filename}'

    sndg = open(infile, 'r')
    data = sndg.readlines()
    outfile = f'{outpath}/{folder}_{filename.replace(".","_")}_sharppy'
    sndg_sharppy = open(outfile, 'w')

    print('%s' % ('%TITLE%'),
          file=sndg_sharppy)
    print(' %s\t%s\n' % ('IDEAL', '010101/1200'),
          file=sndg_sharppy)
    print('   %s\t%s\t%s\t%s\t%s\t%s' % ('LEVEL', 'HGHT', 'TEMP', 'DWPT', 'WDIR', 'WSPD'),
          file=sndg_sharppy)
    print('%s' % ('------------------------------------------------------------------'),
          file=sndg_sharppy)
    print('%s' % ('%RAW%'),
          file=sndg_sharppy)

    for i in range(len(data)):
        data[i].replace(' ', '')
        data[i].replace('\t', '')
        data[i] = data[i].split(',')

    sfc_t = (float(data[0][6]) - 32) * (5 / 9)
    sfc_td = (float(data[0][7]) - 32) * (5 / 9)
    level_data = data[5:]

    sfc = True
    for line in level_data:
        if sfc:
            level, height, temp, dwpt, wind_dir, wind_spd = (float(line[1]),
                                                             float(line[0]),
                                                             sfc_t,
                                                             sfc_td,
                                                             float(line[7]),
                                                             float(line[6]))
            sfc = False

        else:
            level, height, temp, dwpt, wind_dir, wind_spd = (float(line[1]),
                                                             float(line[0]),
                                                             float(line[2]),
                                                             float(line[3]),
                                                             float(line[7]),
                                                             float(line[6]))

        print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
              (level, height, temp, dwpt, wind_dir, wind_spd * 1.94384),
              file=sndg_sharppy)

        ####  ^^^^  convert wind magnitude from m/s to knots  ^^^^  ####

    print('%s' % ('%END%'), file=sndg_sharppy)

    sndg_sharppy.close()
    sndg.close()


sounding_dir = 'D:/cold_pool_mwr/soundings/original_all'

for folder in os.listdir(sounding_dir):
    if folder in ('nontor','wektor','sigtor'):
        indir = f'{sounding_dir}/{folder}'
        outpath =  'D:/cold_pool_mwr/soundings/supercell_sharppy'

        os.makedirs(outpath, exist_ok=True)

        for filename in os.listdir(indir):
            infile = f'{indir}/{filename}'
            if os.path.isfile(infile):
                convert_sharppy(indir, folder, filename, outpath)
