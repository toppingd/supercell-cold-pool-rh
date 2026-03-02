# -*- coding: utf-8 -*-
"""
Created on Thu May 16 16:54:54 2024

@author: dtopp
"""


ztop = 15750

str_bot = 5000
str_top = 12500

dz_bot = 50
dz_top = 250

nz = (str_bot / dz_bot) + (ztop - str_top) / dz_top\
      + (str_top - str_bot) / (0.5*(dz_bot + dz_top))
