import os

from sharppy.sharptab import winds, utils, params, thermo, interp, profile
from metpy.units import units
from metpy.calc import relative_humidity_from_dewpoint
from metpy.calc import dewpoint_from_relative_humidity
import numpy as np
from scipy.signal.windows import tukey


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

        # Create a profile object for SHARPpy
        prof = profile.create_profile(pres=prs.magnitude,
                                      hght=heights.magnitude,
                                      tmpc=temperature.magnitude,
                                      dwpc=dewpoint.magnitude,
                                      wdir=wdir.magnitude,
                                      wspd=wspd.magnitude)

        mlparcel = params.parcelx(prof, flag=4)
        mllfc_prs = mlparcel.lfcpres #* units('hectopascal')

    return prs, heights, temperature, dewpoint, wdir, wspd, mllfc_prs


def clamped_slice(i0, i1, n_total, pad):
    start = max(0, i0 - pad)
    end = min(n_total - 1, i1 + pad)
    if end < start:
        return None, 0
    return slice(start, end + 1), end - start + 1, start, end


def one_sided_cosine_weights(L, near_core_at_left: bool, gamma):
    """
    Raised-cosine ramp in [0,1] across length L.
    - If near_core_at_left=True: weight=1 at left (near core), 0 at right (far edge).
    - If near_core_at_left=False: weight=0 at left (far edge), 1 at right (near core).
     gamma < 0: steeper taper
     gamma > 0: more gradual taper
    """
    if L <= 0:
        return np.zeros(0, dtype=float)
    x = np.linspace(0.0, 1.0, L)
    xg = x**gamma
    if near_core_at_left:
        # 1 → 0 ramp: w = 0.5 * (1 + cos(pi*x))
        w = 0.5 * (1.0 + np.cos(np.pi * xg))
    else:
        # 0 → 1 ramp: w = 0.5 * (1 - cos(pi*x))
        w = 0.5 * (1.0 - np.cos(np.pi * xg))
    return w


def blend_padded_regions_to_threshold(working_arr, thresh_arr,
                                      i0, i1, n_total, taper_pad, gamma):
    # Upper padding: [i1+1 .. i1+pad]
    up_start = i1 + 1
    up_end   = min(n_total - 1, i1 + taper_pad)
    if up_start <= up_end:
        L_up = up_end - up_start + 1
        w_up = one_sided_cosine_weights(L_up, near_core_at_left=True, gamma=gamma)
        sl_up = slice(up_start, up_end + 1)
        delta_up = thresh_arr[sl_up] - working_arr[sl_up]
        working_arr[sl_up] = working_arr[sl_up] + delta_up * w_up

    # Lower padding: [i0-pad .. i0-1]
    low_start = max(0, i0 - taper_pad)
    low_end   = i0 - 1
    if low_start <= low_end:
        L_low = low_end - low_start + 1
        w_low = one_sided_cosine_weights(L_low, near_core_at_left=False, gamma=gamma)
        sl_low = slice(low_start, low_end + 1)
        delta_low = thresh_arr[sl_low] - working_arr[sl_low]
        working_arr[sl_low] = working_arr[sl_low] + delta_low * w_low


def adjust_thermo(prs, heights, temperature, dewpoint, mllfc_prs, taper_pad=2, gamma=1.5, max_sup_iter=5):
    sup_ad = -0.0098 * units('kelvin / meter')  # super adiabatic lapse rate (C/m)
    alpha = 0.98  # percentage of the adiabatic lapse rate
    rh_thresh = 0.95 # RH to be considered too close to saturation
    dry_thresh = 0.40 # RH too dry (
    lfc_pad = 75 # hPa layer above or below the LFC when considering dry layers near LFC)

    n_total = len(prs)

    working_temp = temperature.to('kelvin').copy()
    working_dwpt = dewpoint.to('kelvin').copy()

    for _ in range(max_sup_iter):
        changed = False
        sup_levs = []
        for lev in range(n_total-1):
            lapse_rate = (working_temp[lev + 1] - working_temp[lev]) / (heights[lev + 1] - heights[lev])
            if lapse_rate <= sup_ad:
                sup_levs.append(lev)
            if sup_levs and lev not in sup_levs:
                for sup_lev in sup_levs:
                    if sup_lev == 0:
                        working_temp[sup_lev] = working_temp[sup_lev + 1] - alpha * sup_ad * (
                                heights[sup_lev + 1] - heights[sup_lev])
                    else:
                        working_temp[sup_lev + 1] = working_temp[sup_lev] + alpha * sup_ad * (
                                heights[sup_lev + 1] - heights[sup_lev])
                sup_levs = []
                changed = True

        # Flush any remaining open segment at end
        if sup_levs:
            for sup_lev in sup_levs:
                if sup_lev == 0:
                    working_temp[sup_lev] = working_temp[sup_lev + 1] - alpha * sup_ad * (
                            heights[sup_lev + 1] - heights[sup_lev])
                else:
                    working_temp[sup_lev + 1] = working_temp[sup_lev] + alpha * sup_ad * (
                            heights[sup_lev + 1] - heights[sup_lev])
            sup_levs = []
            changed = True

        if not changed:
            break


    # don't make changes to dewpoint below the LFC
    ft_mask = np.where(prs.magnitude<=mllfc_prs)[0]
    sat_levs = []
    for lev in ft_mask:
        rh = relative_humidity_from_dewpoint(working_temp[lev], working_dwpt[lev]).magnitude
        if rh > rh_thresh:
            sat_levs.append(lev)
        if sat_levs and lev not in sat_levs:
            for sat_lev in sat_levs:
                working_dwpt[sat_lev] = dewpoint_from_relative_humidity(working_temp[sat_lev], rh_thresh).to('kelvin')

            dwpt_thresh_arr = dewpoint_from_relative_humidity(working_temp, rh_thresh).to('kelvin')
            blend_padded_regions_to_threshold(
                working_arr=working_dwpt,
                thresh_arr=dwpt_thresh_arr,
                i0=sat_levs[0], i1=sat_levs[-1], n_total=n_total,
                taper_pad=taper_pad, gamma=gamma)
            sat_levs = []

    # Flush any remaining open segment
    if sat_levs:
        for sat_lev in sat_levs:
            working_dwpt[sat_lev] = dewpoint_from_relative_humidity(working_temp[sat_lev], rh_thresh).to('kelvin')

        dwpt_thresh_arr = dewpoint_from_relative_humidity(working_temp, rh_thresh).to('kelvin')
        blend_padded_regions_to_threshold(
            working_arr=working_dwpt,
            thresh_arr=dwpt_thresh_arr,
            i0=sat_levs[0], i1=sat_levs[-1], n_total=n_total,
            taper_pad=taper_pad, gamma=gamma)
        sat_levs = []


    dry_levs = []
    for lev in range(n_total):
        rh = relative_humidity_from_dewpoint(working_temp[lev], working_dwpt[lev]).magnitude
        if (mllfc_prs-lfc_pad <= prs[lev].magnitude <= mllfc_prs+lfc_pad) and rh < dry_thresh:
            dry_levs.append(lev)
        if dry_levs and lev not in dry_levs:
            for dry_lev in dry_levs:
                working_dwpt[dry_lev] = dewpoint_from_relative_humidity(working_temp[dry_lev], dry_thresh).to('kelvin')

            dwpt_dry_arr = dewpoint_from_relative_humidity(working_temp, dry_thresh).to('kelvin')
            blend_padded_regions_to_threshold(
                working_arr=working_dwpt,
                thresh_arr=dwpt_dry_arr,
                i0=dry_levs[0], i1=dry_levs[-1], n_total=n_total,
                taper_pad=taper_pad, gamma=gamma)
            dry_levs = []

    # Flush any remaining open segment
    if dry_levs:
        for dry_lev in dry_levs:
            working_dwpt[dry_lev] = dewpoint_from_relative_humidity(working_temp[dry_lev], dry_thresh).to('kelvin')
        dwpt_dry_arr = dewpoint_from_relative_humidity(working_temp, dry_thresh).to('kelvin')

        blend_padded_regions_to_threshold(
            working_arr=working_dwpt,
            thresh_arr=dwpt_dry_arr,
            i0=dry_levs[0], i1=dry_levs[-1], n_total=n_total,
            taper_pad=taper_pad, gamma=gamma)
        dry_levs = []

    return working_temp.to('degC'), working_dwpt.to('degC')


def write_new_file(outfile, prs, heights, adjusted_temp, adjusted_dwpt, wdir, wspd):
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
                   adjusted_temp[i].magnitude,
                   adjusted_dwpt[i].magnitude,
                   wdir[i].magnitude,
                   wspd[i].magnitude),
                  file=sndg_sharppy)

        print('%s' % ('%END%'), file=sndg_sharppy)


def main():
    indir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/extended_soundings'
    outdir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/adjusted_soundings'
    # indir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/extended_test'
    # outdir = 'D:/cold_pool_mwr/soundings/supercell_sharppy/adjusted_test'

    os.makedirs(outdir, exist_ok=True)

    for filename in os.listdir(indir):
        outfile = f'{outdir}/{filename}_adjusted'
        if os.path.isfile(os.path.join(indir, filename)) and not os.path.exists(outfile):
            print(filename)
            sounding_file = os.path.join(indir, filename)
            prs, heights, temperature, dewpoint, wdir, wspd, mllfc_prs = get_profile(sounding_file)
            adjusted_temp, adjusted_dwpt = adjust_thermo(prs, heights, temperature, dewpoint, mllfc_prs,
                                                         taper_pad=5, gamma=1.3, max_sup_iter=10)
            write_new_file(outfile, prs, heights, adjusted_temp, adjusted_dwpt, wdir, wspd)


if __name__ == '__main__':
    main()