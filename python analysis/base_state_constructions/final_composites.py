# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 15:54:46 2023

@author: dtopping
"""


# def combine_cm1(thermo_file,shear_file,outpath): 
   
    # thermo = open(thermo_file,'r')
    # shear = open(shear_file, 'r')
    
    # outfile = outpath+regime+'_qt_cm1'
    # final_comp = open(outfile,'w')
    
    # thermo_data = thermo.readlines()
    # shear_data = shear.readlines()[1:]
    
    # for i in range(len(thermo_data)):
    #     thermo_data[i] = thermo_data[i].split('\t')
    #     for j in range(len(thermo_data[i])):
    #         thermo_data[i][j] = float(thermo_data[i][j].strip())
            
    # for i in range(len(shear_data)):
    #     shear_data[i] = shear_data[i].split('\t')
    #     for j in range(len(shear_data[i])):
    #         shear_data[i][j] = float(shear_data[i][j].strip())    
    
    
    # thermo_data_sfc = thermo_data[0]
    # sfcprs,sfcth,sfcqv = (thermo_data_sfc[0],
    #                       thermo_data_sfc[1],
    #                       thermo_data_sfc[2])
    
    # print('%3.5f \t%3.5f \t%3.5f' % (sfcprs,sfcth,sfcqv),
    #       file=final_comp)
    
    
    # thermo_data_agl = thermo_data[1:]
    # for i in range(len(thermo_data_agl)):
    #     height = thermo_data_agl[i][0]
    #     th = thermo_data_agl[i][1]
    #     qv = thermo_data_agl[i][2]
    #     u = shear_data[i][3]
    #     v = shear_data[i][4]

    #     print('%3.5f \t%3.5f \t%3.5f \t%3.5f \t%3.5f' % (height,th,qv,u,v),
    #           file=final_comp)
           
           
    # final_comp.close()
    # shear.close()
    # thermo.close()
    

def combine_sharppy(thermo_file,shear_file,outpath): 

    thermo = open(thermo_file,'r')
    shear = open(shear_file, 'r')
    
    outfile = outpath+regime+'_sigtor_translated_sharppy'
    final_comp = open(outfile,'w')
    
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
              (prs,height,temp,td,wind_dir,wind_spd),
              file=final_comp)
        
    print('%s' % ('%END%'), file=final_comp)  
        
    final_comp.close()
    shear.close()
    thermo.close()
    

regime = 'dd'

# thermo_file1 = '/t1/topping/soundings/1500CAPE/'+regime+'_extended_cm1'
# shear_file1 = '/t1/topping/soundings/hodographs/quarter_turn_cm1'
thermo_file2 = '/t1/topping/soundings/2500CAPE/'+regime+'_extended_sharppy'
shear_file2 = '/t1/topping/soundings/hodographs/sigtor_sharppy'
outdir = '/t1/topping/soundings/2500CAPE/sigtor'

outpath = outdir+'/'

# combine_cm1(thermo_file1,shear_file1,outpath)
combine_sharppy(thermo_file2,shear_file2,outpath)