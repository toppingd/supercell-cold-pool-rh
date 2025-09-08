# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 15:54:46 2023

@author: dtopping
"""


import numpy as np
import metpy.calc as mcalc
from metpy.units import units



H1 = 2500 # bottom of layer to adjust (m)
H2 = 11500 # top of layer to adjust (m)

T_ADD = -1.5 # constant RH (%) for method=0


inpath = '/t1/topping/soundings/rh_sort/dryPBL_moistFT/sharppy_soundings/'
# f_sharppy = inpath + 'dd_high_cin_sharppy'
f_sharppy = inpath + 'dm_option3_mot_sharppy'

# outpath = inpath
# regime = f_sharppy.split('/')[-1][:2] 
outfile = f_sharppy + '_tadd'

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

# layer to adjust        
z = np.array([line[1] for line in data])
diff1 = np.array(abs(z-H1))
zi1 = np.where(diff1==min(diff1))[0][0]
z1 = z[zi1]
diff2 = np.array(abs(z-H2))
zi2 = np.where(diff2==min(diff2))[0][0]
z2 = z[zi2]

for level in data:
    prs = level[0]
    height = level[1]
    temp = level[2]
    td = level[3]
    wind_dir = level[4]
    wind_spd = level[5]
    
    if z1 <= height <= z2:
        
        rh = mcalc.relative_humidity_from_dewpoint(temp*units('degC'),
                                                   td*units('degC'))
        
        temp += T_ADD
        
        td = mcalc.dewpoint_from_relative_humidity(temp*units('degC'),
                                                   rh)
            
        td = td.magnitude
    
    print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
          (prs,height,temp,td,wind_dir,wind_spd),
          file=out)
    
print('%s' % ('%END%'), file=out)  
    
out.close()
sndg.close()
