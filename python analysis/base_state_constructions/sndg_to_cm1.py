# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 11:22:59 2023

@author: dtopping
"""

import tkinter as tk
from tkinter import filedialog
from itertools import islice
import numpy as np
import os

root = tk.Tk()
indir = filedialog.askdirectory(parent=root, initialdir='C:/',
                                title='Select a directory')
root.destroy()


def convert_cm1(inpath, filename, outpath):
    infile = inpath + filename

    sndg = open(infile, 'r')
    sndg_cm1 = open(outpath + filename + '_cm1', 'w')

    c1 = 611.12  # reference pressure [Pa]
    c2 = 2.5008e6  # latent heat of vaporization [J/kg]
    c3 = 461.2  # gas constant for water vapor [K]
    c4 = 273.16  # reference temperature [k]

    for l in islice(sndg, 5, 6):
        l.replace(' ', '')
        l.replace('\t', '')
        line = l.split(',')
        sfcprs, sfcth, sfcdwpt = (float(line[1]),
                                  float(line[19]),
                                  float(line[3]))

        sfce = c1 * np.exp((c2 / c3) * ((1 / c4) - (1 / (c4 + sfcdwpt))))  # [Pa]
        sfcqv = 621.97 * (sfce / ((sfcprs * 100) - sfce))  # [g/kg]

        print('%3.5f \t%3.5f \t%3.5f' % (sfcprs, sfcth, sfcqv),
              file=sndg_cm1)

    for l in islice(sndg, 0, None):
        l.replace(' ', '')
        l.replace('\t', '')
        line = l.split(',')
        height, th, prs, dwpt, u, v = (float(line[0]),
                                       float(line[19]),
                                       float(line[1]),
                                       float(line[3]),
                                       float(line[4]),
                                       float(line[5]))

        e = c1 * np.exp((c2 / c3) * ((1 / c4) - (1 / (c4 + dwpt))))  # [Pa]
        qv = 621.97 * (e / ((prs * 100) - e))  # [g/kg]

        print('%3.5f \t%3.5f \t%3.5f \t%3.5f \t%3.5f' % (height, th, qv, u, v),
              file=sndg_cm1)

    sndg_cm1.close()
    sndg.close()


inpath = indir + '/'
outpath = inpath + 'cm1_soundings/'
if not os.path.isdir(outpath):
    os.mkdir(outpath)

for filename in os.listdir(inpath):
    infile = inpath + filename
    if os.path.isfile(infile):
        convert_cm1(inpath, filename, outpath)
