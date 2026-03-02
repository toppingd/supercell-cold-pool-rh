import glob

output_file = '/storm/topping/cold_pools/sim_means/buoyancy_means_const_thresh.csv'

with open(output_file, 'w') as outfile:
    for fname in glob.glob('/storm/topping/cold_pools/sim_means/*_buoyancy_means_const_thresh.csv'):
        with open(fname, 'r') as infile:
            outfile.writelines(infile.readlines())