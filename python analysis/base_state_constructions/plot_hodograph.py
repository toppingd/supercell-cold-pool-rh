# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 15:56:43 2023

@author: dtopping
"""

import numpy as np
import metpy.calc as mcalc
from metpy.units import units
# import os
import matplotlib.pyplot as plt

# import matplotlib.patches as patches


# infile = 'D:/cold_pool_mwr/soundings/shear_profiles/qt_sharppy'
# infile = 'D:/cold_pool_mwr/soundings/shear_profiles/sigtor_sharppy'
infile = 'D:/cold_pool_mwr/soundings/final/sharppy/sigtor_203050504_mkl_moistPBL_moistFT_moderateCAPE_qt_sharppy'


sndg = open(infile, 'r')

data = sndg.readlines()[6:-1]
for i in range(len(data)):
    data[i] = data[i].split(',')
    for j in range(len(data[i])):
        data[i][j] = float(data[i][j].strip())

heights = []
levels = []
wind_dirs = []
wind_spds = []

lev = 1
for line in data:
    level, height, t, td, wind_dir, wind_spd = (float(line[0]),
                                                float(line[1]),
                                                float(line[2]),
                                                float(line[3]),
                                                float(line[4]),
                                                float(line[5]))

    heights.append(height)
    levels.append(level)
    wind_dirs.append(wind_dir)
    wind_spds.append(wind_spd * 0.514444)

sndg.close()

fig, ax = plt.subplots(1, 1, figsize=(5, 5))

heights = np.array(heights)
levels = np.array(levels)
wind_dirs = np.array(wind_dirs)
wind_spds = np.array(wind_spds)

target_heights = [0, 500, 1000, 3000, 6000, 9000, 12000]
height_indices = []
for h in target_heights:
    _diff = np.abs(heights - h)
    hi = np.where(_diff == np.min(_diff))[0][0]
    height_indices.append(hi)

plot_heights = heights[height_indices]

u = np.empty_like(wind_dirs)
v = np.empty_like(wind_dirs)
for i in range(len(wind_dirs)):
    adjusted_wind_dir = np.deg2rad(270 - wind_dirs[i])
    u[i] = wind_spds[i] * np.cos(adjusted_wind_dir)
    v[i] = wind_spds[i] * np.sin(adjusted_wind_dir)

ax.plot(u[:height_indices[1] + 1],
        v[:height_indices[1] + 1],
        c='purple', linewidth=3, zorder=0)

ax.plot(u[height_indices[1]:height_indices[3] + 1],
        v[height_indices[1]:height_indices[3] + 1],
        c='r', linewidth=3, zorder=0)

ax.plot(u[height_indices[3]:height_indices[4] + 1],
        v[height_indices[3]:height_indices[4] + 1],
        c='lime', linewidth=3, zorder=0)

ax.plot(u[height_indices[4]:height_indices[5] + 1],
        v[height_indices[4]:height_indices[5] + 1],
        c='y', linewidth=3, zorder=0)

ax.plot(u[height_indices[5]:height_indices[6] + 1],
        v[height_indices[5]:height_indices[6] + 1],
        c='cyan', linewidth=3, zorder=0)


# ax.plot((u[120],u[120]),
#         (v[120],v[120]+0.3),
#         c='cyan', linewidth=3, zorder=0)

# ax.plot(u[120:160+1],
#         v[120:160+1]+0.3,
#         c='cyan', linewidth=3, zorder=0)

# ax.scatter(u[height_indices],v[height_indices], c='r', zorder=1)


# 0-6 kmmean wind
_diff = np.abs(heights - 6000)
i6000 = np.where(_diff == np.min(_diff))[0][0]

bottom = (levels[0]) * units('hPa')
depth = -(levels[i6000 + 1] - levels[0]) * units('hPa')

mean_u6 = mcalc.mean_pressure_weighted(levels * units('hPa'),
                                       u * units('m/s'),
                                       bottom=bottom,
                                       depth=depth)[0].magnitude

mean_v6 = mcalc.mean_pressure_weighted(levels * units('hPa'),
                                       v * units('m/s'),
                                       bottom=bottom,
                                       depth=depth)[0].magnitude

mean_spd6 = np.sqrt(mean_u6 ** 2 + mean_v6 ** 2)

# ax.arrow(0, 0, mean_u6,mean_v6, shape='full', length_includes_head=True,
#          overhang=0.25, head_width=0.5, color='orange', )
# ax.plot(mean_u6,mean_v6, marker='o',
#                          markersize=8,
#                          markerfacecolor='orange',
#                          markeredgewidth=1,
#                          markeredgecolor='k')

# 0-6 km bulk wind difference
bwd6 = np.sqrt((u[i6000] - u[0]) ** 2 \
               + (v[i6000] - v[0]) ** 2)

# Bunkers method
_diff = np.abs(heights - 500)
i500 = np.where(_diff == np.min(_diff))[0][0]
_diff = np.abs(heights - 5500)
i5500 = np.where(_diff == np.min(_diff))[0][0]

u_mean_0_500 = np.mean(u[list(range(0, i500 + 1))])
u_mean_5500_6000 = np.mean(u[list(range(i5500, i6000 + 1))])

v_mean_0_500 = np.mean(v[list(range(0, i500 + 1))])
v_mean_5500_6000 = np.mean(v[list(range(i5500, i6000 + 1))])

# ax.plot([u_mean_0_500,u_mean_5500_6000],[v_mean_0_500,v_mean_5500_6000], c='b',
#         linewidth=1,linestyle='dotted',alpha=0.75)

slope = (v_mean_5500_6000 - v_mean_0_500) / (u_mean_5500_6000 - u_mean_0_500)
b1 = -(slope * u_mean_5500_6000 - v_mean_5500_6000)
orthog_slope = - 1 / slope
b2 = -(orthog_slope * mean_u6 - mean_v6)
orthog_y = [0, 20]
orthog_x = []
for y in orthog_y:
    orthog_x.append((y - b2) / orthog_slope)

# ax.plot(orthog_x, orthog_y, c='b',
#         linewidth=1,linestyle='dotted',alpha=0.75)


# right moving storm motion
ul = None
vl = None
min_diff = 1000000
for u_inc in np.arange(mean_u6, (mean_u6 * 5) + 0.01, 0.01):
    v_inc = orthog_slope * u_inc + b2
    diff_spd = np.sqrt((u_inc - mean_u6) ** 2 + (v_inc - mean_v6) ** 2)
    diff2 = np.abs(7.5 - diff_spd)
    if diff2 < min_diff:
        ul = u_inc
        vl = v_inc
        min_diff = diff2
if ul == None:
    ul = mean_u6
    vl = mean_v6 + 7.5

ax.plot(ul,vl, marker='*',
        markersize=12,
        markerfacecolor='purple',
        markeredgewidth=1,
        markeredgecolor='k')

# left moving storm motion
ur = None
vr = None
min_diff = 1000000
for u_inc in np.arange(-mean_u6 * 5, mean_u6 + 0.01, 0.01):
    v_inc = orthog_slope * u_inc + b2
    diff_spd = np.sqrt((u_inc - mean_u6) ** 2 + (v_inc - mean_v6) ** 2)
    diff2 = np.abs(7.5 - diff_spd)
    if diff2 < min_diff:
        ur = u_inc
        vr = v_inc
        min_diff = diff2
if ur == None:
    ur = mean_u6
    vr = mean_v6 - 7.5

# ax.plot(ur, vr, marker='*',
#         markersize=12,
#         markerfacecolor='purple',
#         markeredgewidth=1,
#         markeredgecolor='k')

# SRH
srh_o = 0  # ordinary cell
srh_l = 0  # left-mover
srh_r = 0  # right-mover
for i in range(len(u[:height_indices[3] + 1]) - 1):
    srh_o += ((u[i + 1] - mean_u6) * (v[i] - mean_v6)) - ((u[i] - mean_u6) * (v[i + 1] - mean_v6))
    srh_l += ((u[i + 1] - ul) * (v[i] - vl)) - ((u[i] - ul) * (v[i + 1] - vl))
    srh_r += ((u[i + 1] - ur) * (v[i] - vr)) - ((u[i] - ur) * (v[i + 1] - vr))

ax.axhline(y=0, c='gray', linewidth=2, alpha=0.25, linestyle='--')
ax.axvline(x=0, c='gray', linewidth=2, alpha=0.25, linestyle='--')
for th in np.arange(15, 180, 15):
    s = np.tan(np.deg2rad(th))
    ax.plot([-100, 100], [-100 * s, 100 * s], c='gray', linewidth=1, alpha=0.25, linestyle='--')
for r in np.arange(5, 90, 5):
    circ = plt.Circle((0, 0), r,
                      edgecolor='gray', fill=False, linewidth=1, alpha=0.25)
    ax.add_patch(circ)
ax.set_xlim(-10, 65)
ax.set_xlabel('u wind (m $s^{-1}$)', fontsize=14)
ax.set_ylim(-25, 50)
ax.set_ylabel('v wind (m $s^{-1}$)', fontsize=14)

u0_1 = np.mean(u[height_indices[:2]])
v0_1 = np.mean(v[height_indices[:2]])
sru0_1 = u0_1 - ul
srv0_1 = v0_1 - vl
sr_0_1_mag = np.sqrt(sru0_1 ** 2 + srv0_1 ** 2)

# ax.plot(u0_1,v0_1, marker='o',
#         markersize=12,
#         markerfacecolor='gold',
#         markeredgewidth=1,
#         markeredgecolor='k')

# ax.plot([u0_1,ul],[v0_1,vl])

# print(sr_0_1_mag)

# outpath = ''
# plt.savefig(outpath + 'pdf/' + 'sigtor_translated_hodo' + '.pdf', bbox_inches='tight')
# plt.savefig(outpath + 'png/' + 'sigtor_translated_hodo' + '.png', dpi=300, bbox_inches='tight')
plt.show()

