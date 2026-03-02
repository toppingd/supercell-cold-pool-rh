# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 15:54:46 2023

@author: dtopping
"""


def combine_sharppy(thermo_file, shear_file, outfile):
    thermo = open(thermo_file, 'r')
    shear = open(shear_file, 'r')

    final_comp = open(outfile, 'w')

    print('%s' % ('%TITLE%'),
          file=final_comp)
    print(' %s\t%s\n' % ('IDEAL', '010101/1200'),
          file=final_comp)
    print('   %s\t%s\t%s\t%s\t%s\t%s' % ('LEVEL', 'HGHT', 'TEMP', 'DWPT', 'WDIR', 'WSPD'),
          file=final_comp)
    print('%s' % ('------------------------------------------------------------------'),
          file=final_comp)
    print('%s' % ('%RAW%'),
          file=final_comp)

    thermo_data = thermo.readlines()[6:-1]
    shear_data = shear.readlines()[6:-1]

    for i in range(len(thermo_data)):
        thermo_data[i] = thermo_data[i].split(',')
        for j in range(len(thermo_data[i])):
            thermo_data[i][j] = float(thermo_data[i][j].strip())

    for i in range(len(shear_data)):
        shear_data[i] = shear_data[i].split(',')
        for j in range(len(shear_data[i])):
            shear_data[i][j] = float(shear_data[i][j].strip())

    for i in range(len(thermo_data)):
        prs = thermo_data[i][0]
        height = thermo_data[i][1]
        temp = thermo_data[i][2]
        td = thermo_data[i][3]

        if i < len(shear_data):
            wind_dir = shear_data[i][4]
            wind_spd = shear_data[i][5]
        else:
            wind_dir = shear_data[-1][4]
            wind_spd = shear_data[-1][5]

        print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
              (prs, height, temp, td, wind_dir, wind_spd),
              file=final_comp)

    print('%s' % ('%END%'), file=final_comp)

    final_comp.close()
    shear.close()
    thermo.close()


rh_options = ('moistPBL_moistFT', 'moistPBL_dryFT', 'dryPBL_moistFT', 'dryPBL_dryFT')
cape_options = ('lowCAPE', 'moderateCAPE', 'highCAPE')
hodo_options = ('qt', 'sigtor')

rh_choice = rh_options[3]
cape_choice = cape_options[0]
hodo_choice = hodo_options[0]

sounding_choice = 'nontor_199072922_fvx'

thermo_file = f'D:/cold_pool_mwr/soundings/supercell_sharppy/adjusted_soundings/{rh_choice}/{cape_choice}/{sounding_choice}_sharppy_extended_adjusted'
shear_file = f'D:/cold_pool_mwr/soundings/shear_profiles/{hodo_choice}_sharppy'

outfile = f'D:/cold_pool_mwr/soundings/final/sharppy/{cape_choice}/{rh_choice}_{cape_choice}_{hodo_choice}Hodo_{sounding_choice}_sharppy'

combine_sharppy(thermo_file, shear_file, outfile)