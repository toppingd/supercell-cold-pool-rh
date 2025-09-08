# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 15:54:46 2023

@author: dtopping
"""


import metpy.calc as mcalc
from metpy.units import units


# regime = 'mm'
# wind_profile = 'sigtor_t'
z_trop = 14400 # height of tropopause (m)

ztop = 20000 # top of sounding (m)
dz = 100 # distance between levels (m)

# inpath = '/t1/topping/soundings/1500CAPE/'
# inpath = '/t1/topping/soundings/2500CAPE/'
# inpath = '/t1/topping/soundings/3500CAPE/'

# f_sharppy = inpath + regime + '_' + wind_profile +'_sharppy'
f_sharppy = '/t1/topping/soundings/hodographs/sigtor_translated_sharppy'

outfile = f_sharppy[:-7] + 'extended_sharppy'

sndg = open(f_sharppy,'r')
out = open(outfile,'w')


print('%s' % ('%TITLE%'),
      file=out)
print(' %s\t%s\n' % ('IDEAL', '010101/1200'),
      file=out)
print('   %s\t%s\t%s\t%s\t%s\t%s' % ('LEVEL', 'HGHT', 'TEMP', 'DWPT', 'WDIR', 'WSPD'),
      file=out)
print('%s' % ('------------------------------------------------------------------'),
      file=out)
print('%s' % ('%RAW%'),
      file=out)


data = sndg.readlines()[6:-1]

for i in range(len(data)):
    data[i] = data[i].split(',')
    for j in range(len(data[i])):
        data[i][j] = float(data[i][j].strip())
        
        
for level in data:
    prs = level[0]
    height = level[1]
    temp = level[2]
    td = level[3]
    wind_dir = level[4]
    wind_spd = level[5]
    
    if height == z_trop:
        t_trop = temp
        td_trop = td
        
    if height > z_trop:
        temp = t_trop
        td = td_trop
    
    print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
          (prs,height,temp,td,wind_dir,wind_spd),
          file=out)
    
    
while height < ztop:
    
    prs = mcalc.add_height_to_pressure(prs*units('hPa'),dz*units('m')).magnitude
    
    height += dz
    
    print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
          (prs,height,t_trop,td_trop,wind_dir,wind_spd),
          file=out)

    
print('%s' % ('%END%'), file=out)  

    
out.close()
sndg.close()

