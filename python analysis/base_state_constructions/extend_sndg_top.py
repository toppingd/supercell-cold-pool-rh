import os

from metpy.units import units
from metpy.calc import relative_humidity_from_dewpoint
from metpy.calc import dewpoint_from_relative_humidity
from metpy.calc import add_height_to_pressure
import numpy as np


def get_profile(sounding_file):

    with open(sounding_file, 'r') as f:
        data = f.readlines()[6:-1]
        for i in range(len(data)):
            data[i] = data[i].split(',')
            for j in range(len(data[i])):
                data[i][j] = float(data[i][j].strip())

        # Extract the necessary columns and convert to appropriate units
        prs = np.array([data[h][0] for h in range(len(data))]) * units('hPa')
        heights = np.array([data[h][1] for h in range(len(data))]) * units.meter
        temperature = np.array([data[h][2] for h in range(len(data))]) * units('degC')
        dewpoint = np.array([data[h][3] for h in range(len(data))]) * units('degC')
        wdir = np.array([data[h][4] for h in range(len(data))]) * units('degrees')
        wspd = np.array([data[h][5] for h in range(len(data))]) * units('knots')

    return prs, heights, temperature, dewpoint, wdir, wspd


def fill_nan_dwpt(prs, temperature, dewpoint):

    filled_dwpt = dewpoint.copy()
    prev_rh =  relative_humidity_from_dewpoint(temperature[0].to('kelvin'), dewpoint[0].to('kelvin')).magnitude
    for lev in range(len(prs)):
        if np.isnan(dewpoint[lev].magnitude):
            fill_dwpt = dewpoint_from_relative_humidity(temperature[lev].to('kelvin'), prev_rh)
            filled_dwpt[lev] = fill_dwpt
        else:
            prev_rh = relative_humidity_from_dewpoint(temperature[lev].to('kelvin'), dewpoint[lev].to('kelvin')).magnitude

    return filled_dwpt


def extend_sndg(prs, heights, temperature, dewpoint, wdir, wspd, num_levs=201):
    dz = (heights[1]-heights[0]).magnitude
    if len(heights) < num_levs:
        num_new_levs = num_levs - len(heights)
        new_heights = np.arange(heights[-1].magnitude + dz, heights[-1].magnitude + dz * (num_new_levs+1), dz)
        extended_heights = np.append(heights.magnitude, new_heights)*units('meters')

        temp_lapse_rate = (temperature[-1] - temperature[-2]) / dz
        append_temps = temperature[-1] + temp_lapse_rate * (new_heights-heights[-1].magnitude)
        extended_temp = np.append(temperature, append_temps)

        dwpt_lapse_rate = (dewpoint[-1] - dewpoint[-2]) / dz
        append_dwpts = dewpoint[-1] + dwpt_lapse_rate * (new_heights-heights[-1].magnitude)
        extended_dwpt = np.append(dewpoint, append_dwpts)

        append_prs = [add_height_to_pressure(prs[-1], (z*units('meters')-heights[-1])) for z in new_heights]
        extended_prs = np.append(prs, append_prs)

        append_wdir = [wdir[-1]]*(num_new_levs+1)
        extended_wdir = np.append(wdir, append_wdir)

        append_wspd = [wspd[-1]] * (num_new_levs + 1)
        extended_wspd = np.append(wspd, append_wspd)

        return extended_prs, extended_heights, extended_temp, extended_dwpt, extended_wdir, extended_wspd


def write_new_file(outfile, prs, heights, extended_temp, extended_dwpt, wdir, wspd):

        with open(outfile, 'w') as sndg_sharppy:

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

            for i in range(len(prs)):
                print('% 4.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f, % 5.2f' %
                      (prs[i].magnitude,
                       heights[i].magnitude,
                       extended_temp[i].magnitude,
                       extended_dwpt[i].magnitude,
                       wdir[i].magnitude,
                       wspd[i].magnitude),
                      file=sndg_sharppy)

            print('%s' % ('%END%'), file=sndg_sharppy)


def main():
    indir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/original_soundings'
    outdir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/extended_soundings'

    os.makedirs(outdir, exist_ok=True)

    for filename in os.listdir(indir):
        outfile = f'{outdir}/{filename}_extended'
        if os.path.isfile(os.path.join(indir, filename)) and not os.path.exists(outfile):
            print(filename)
            sounding_file = os.path.join(indir, filename)
            prs, heights, temperature, dewpoint, wdir, wspd = get_profile(sounding_file)
            filled_dwpt = fill_nan_dwpt(prs, temperature, dewpoint)
            extended_vars = extend_sndg(prs, heights, temperature, filled_dwpt, wdir, wspd, num_levs=201)
            extended_prs, extended_heights, extended_temp, extended_dwpt, extended_wdir, extended_wspd = extended_vars
            write_new_file(outfile, extended_prs, extended_heights, extended_temp, extended_dwpt, extended_wdir, extended_wspd)


if __name__ == '__main__':
    main()