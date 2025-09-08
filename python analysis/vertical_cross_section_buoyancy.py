# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Created on Fri Apr  5 13:39:22 2024

# @author: dtopping
# """

# # import tkinter as tk
# # from tkinter import filedialog
# import xarray as xr
# import matplotlib.pyplot as plt
# import matplotlib.colors as colors
# import numpy as np
# import os


# G = 9.81


# def centroid(arr):
#     a = arr
#     points = np.where(a>=150) # uh >= 750 m^2/s^2
#     grid = np.meshgrid(points[0],points[1], indexing='ij')
#     xq3,xq1 = np.percentile(points[0], [75, 25])
#     yq3,yq1 = np.percentile(points[1], [75, 25])
#     xiqr = xq3-xq1
#     yiqr = yq3-yq1
#     c_points = np.where( ((xq1-1*xiqr)<grid[0]) & (grid[0]<(xq3+1*xiqr))\
#                         & ((yq1-1*yiqr)<grid[1]) & (grid[1]<(yq3+1*yiqr)) )
#     npoints = c_points[0].shape[0]
#     i_cx750 = int(np.sum(c_points[0])/npoints)
#     i_cy750 = int(np.sum(c_points[1])/npoints)
#     i_cy = points[0][i_cx750]
#     i_cx = points[1][i_cy750]
#     return i_cx,i_cy


# # indir = '/t1/topping/paper_runs/1500/'
# # indir = '/t1/topping/paper_runs/2500/'
# # indir = '/t1/topping/paper_runs/3500/'

# indir = '/t1/topping/paper_runs/2500_morrison/'


# ######################!!!!!!!###########################
# ########################################################
# folder = 'mm' + '/'               # Regime [mm,md,dm,dd]
# time = 120               # Time between 60 and 180 min
# num = 2
# cs_sp = (6,30)   # Cross section start point (x,y) km (10,10)
# cs_ep = (35,5)   # Cross section start point (x,y) km  (17,6)
# ########################################################
# ######################!!!!!!!###########################
# cs_xvector = np.array([cs_sp[0],cs_ep[0]])
# cs_yvector = np.array([cs_sp[1],cs_ep[1]])

# time-=43
# base = 'cm1out_0000'
# if time < 10:
#     filename = base+'0'+str(time)+'.nc'
# else:
#     filename = base+str(time)+'.nc'

# file = indir+folder+'run/'+filename
# if os.path.isfile(os.path.join(indir+folder+'run/',filename)):
    
#     ds0 = xr.open_dataset(indir+folder+'/run/cm1out_000001.nc',
#                           decode_times=True)
#     ds = xr.open_dataset(file, decode_times=True)
    
#     filenum = file[-9:]
#     ds_outflow = xr.open_dataset(indir+folder+'/run/outflow_'+filenum)
    
#     # center of max updraft
#     uh = ds.uh.values[0]
#     i_x_center, i_y_center = centroid(uh)
#     x_center = ds.xh.values[i_x_center]
#     y_center = ds.yh.values[i_y_center]

#     # index for top of cross section
#     diff = np.array(abs(ds.zh.values-5))    #################### adjust height
#     iz = np.where(diff==min(diff))[0][0]+1

#     bbox = [-25.0,65.0,-15.0,57.0]
#     # indices for subset x bounds
#     diff = abs(ds.xh.values-(x_center+bbox[0]))
#     ix1 = np.where(diff==min(diff))[0][0]
#     diff = abs(ds.xh.values-(x_center+bbox[1]))
#     ix2 = np.where(diff==min(diff))[0][0]+1

#     # indices for subset y bounds
#     diff = abs(ds.yh.values-(y_center+bbox[2]))
#     iy1 = np.where(diff==min(diff))[0][0]
#     diff = abs(ds.yh.values-(y_center+bbox[3]))
#     iy2 = np.where(diff==min(diff))[0][0]+1
    
    
#     # cross section x and y indices
#     x = ds.xh.values[ix1:ix2]-ds.xh.values[ix1]
#     _diff = abs(x-cs_sp[0])
#     sp_xi = np.where(_diff==min(_diff))[0][0]
#     _diff = abs(x-cs_ep[0])
#     ep_xi = np.where(_diff==min(_diff))[0][0]+1
    
#     y = ds.yh.values[iy1:iy2]-ds.yh.values[iy1]
#     _diff = abs(x-cs_sp[1])
#     sp_yi = np.where(_diff==min(_diff))[0][0]
#     _diff = abs(x-cs_ep[1])
#     ep_yi = np.where(_diff==min(_diff))[0][0]+1
    
#     cs_xi = []
#     cs_yi = []
#     greater_axis = np.argmax((len(x[sp_xi:ep_xi]),len(y[sp_yi:ep_yi])))
#     if greater_axis == 1: # dy larger
#         cs_slope = (cs_ep[0] - cs_sp[0]) / (cs_ep[1] - cs_sp[1])
#         for i in range(len(y[sp_yi:ep_yi])):
#             x_calc = y[i] * cs_slope + cs_sp[0]
#             _diff = abs(x-x_calc)
#             _xi = np.where(_diff==min(_diff))[0][0]
#             cs_xi.append(_xi)
            
#             _diff = abs(y-y[sp_yi:ep_yi][i])
#             _yi = np.where(_diff==min(_diff))[0][0]
#             cs_yi.append(_yi)
            
#     else:    # dx larger
#         cs_slope = (cs_ep[1] - cs_sp[1]) / (cs_ep[0] - cs_sp[0])
#         for i in range(len(x[sp_xi:ep_xi])):
#             y_calc = x[i] * cs_slope + cs_sp[1]
#             _diff = abs(y-y_calc)
#             _yi = np.where(_diff==min(_diff))[0][0]
#             cs_yi.append(_yi)
            
#             _diff = abs(x-x[sp_xi:ep_xi][i])
#             _xi = np.where(_diff==min(_diff))[0][0]
#             cs_xi.append(_xi)

#     x_cs = x[cs_xi]
#     y_cs = y[cs_yi]

#     lcl_cs = ds.lcl.values[0][iy1:iy2,ix1:ix2][cs_yi,cs_xi]/1000   
#     w_cs = ds.winterp.values[0][:iz,iy1:iy2,ix1:ix2][:,cs_yi,cs_xi]
#     zvort_cs = ds.zvort.values[0][:iz,iy1:iy2,ix1:ix2][:,cs_yi,cs_xi]
#     th_cs = ds.th.values[0][:iz,iy1:iy2,ix1:ix2][:,cs_yi,cs_xi]
#     prs_cs = ds.prs.values[0][:iz,iy1:iy2,ix1:ix2][:,cs_yi,cs_xi]
#     # buoy = ds.buoyancy.values[0][:iz,iy1:iy2,ix1:ix2][:,cs_yi,cs_xi]

#     # # qr0 = ds.qr.values[0][:,181:281,:361]
#     # # qv0 = ds.qv.values[0][:,181:281,:361]
#     # # qc0 = ds.qc.values[0][:,181:281,:361]
#     # # qi0 = ds.qi.values[0][:,181:281,:361]
#     # # qs0 = ds.qs.values[0][:,181:281,:361]
#     # # qg0 = ds.qg.values[0][:,181:281,:361]
#     # # qhl0 = ds.qhl.values[0][:,181:281,:361]
#     # # th0 = ds.th.values[0][:,181:281,:361]
#     # # th_rho0 = np.mean(th0*(1+0.608*qv0-qc0-qr0-qi0-qs0-qg0-qhl0), axis=(1,2))
    
#     # qr0 = ds0.qr.values[0][:,0,0]
#     # qv0 = ds0.qv.values[0][:,0,0]
#     # qc0 = ds0.qc.values[0][:,0,0]
#     # qi0 = ds0.qi.values[0][:,0,0]
#     # qs0 = ds0.qs.values[0][:,0,0]
#     # qg0 = ds0.qg.values[0][:,0,0]
#     # qhl0 = ds0.qhl.values[0][:,0,0]
#     # th0 = ds0.th.values[0][:,0,0]
#     # th_rho0 = th0*(1+0.608*qv0-qc0-qr0-qi0-qs0-qhl0-qg0)

#     # qr = ds.qr.values[0][:,iy1:iy2,ix1:ix2]
#     # qv = ds.qv.values[0][:,iy1:iy2,ix1:ix2]
#     # qc = ds.qc.values[0][:,iy1:iy2,ix1:ix2]
#     # qi = ds.qi.values[0][:,iy1:iy2,ix1:ix2]
#     # qs = ds.qs.values[0][:,iy1:iy2,ix1:ix2]
#     # qg = ds.qg.values[0][:,iy1:iy2,ix1:ix2]
#     # qhl = ds.qhl.values[0][:,iy1:iy2,ix1:ix2]
#     # th = ds.th.values[0][:,iy1:iy2,ix1:ix2]
#     # # qr = ds.qr.values[0]
#     # # qv = ds.qv.values[0]
#     # # qc = ds.qc.values[0]
#     # # qi = ds.qi.values[0]
#     # # qs = ds.qs.values[0]
#     # # qg = ds.qg.values[0]
#     # # qhl = ds.qhl.values[0]
#     # # th = ds.th.values[0]
#     # th_rho = th*(1+0.608*qv-qc-qr-qi-qs-qg-qhl)

#     # th_rho_pert = th_rho - th_rho0[:,None,None]
    
#     # buoyancy = G * (th_rho_pert / th_rho0[:,None,None])
#     buoyancy = ds_outflow.buoyancy2.sel( 
#                                         xh=slice(x_center+bbox[0],
#                                                  x_center+bbox[1]),
#                                         yh=slice(y_center+bbox[2],
#                                                  y_center+bbox[3])).squeeze(('time'))
#     buoyancy_cs = np.array(buoyancy)[:iz,cs_yi,cs_xi] 
    
#     # qv_cs = qv[:,cs_yi,cs_xi]*1000
#     # qh_cs = (qr[:,cs_yi,cs_xi]+qi[:,cs_yi,cs_xi]+qs[:,cs_yi,cs_xi]\
#     #         +qg[:,cs_yi,cs_xi]+qhl[:,cs_yi,cs_xi])*1000
       

#     fig, axs = plt.subplots(1,2, figsize=(17,6),
#                             gridspec_kw={'width_ratios': [1, 1.5]})
#     fig.tight_layout()

#     axs[1].set_ylabel('Height (km)',fontsize=12,labelpad=5)
#     z = ds.zh.values[:iz]
    
#     axs[1].set_xlabel('Cross-sectional distance (km)',fontsize=12,labelpad=5)
#     cs_dist = np.sqrt((x_cs[-1]-x_cs[0])**2+(y_cs[-1]-y_cs[0])**2)
#     x_cs_trans = []
#     if greater_axis == 1:
#         for i in range(len(y_cs)):
#             _x = (y_cs[i]-y_cs[0])*(cs_dist/(y_cs[-1]-y_cs[0]))
#             x_cs_trans.append(_x)
#     else:
#         for i in range(len(x_cs)):
#             _x = (x_cs[i]-x_cs[0])*(cs_dist/(x_cs[-1]-x_cs[0]))
#             x_cs_trans.append(_x)
    
#     cs_max = round(np.max(x_cs_trans))
#     if cs_max%2!=0:
#         cs_max+=1
#     zmax = round(z.max())
#     axs[1].set_xticks(np.linspace(0,cs_max,(cs_max)+1))
#     # axs[1].set_xticks(np.linspace(0,cs_max,(cs_max*2)+1))
#     axs[1].set_yticks(np.linspace(0,zmax,zmax+1))


#     # negative vertical velocity
#     levs = list(np.arange(np.min(w_cs)-np.min(w_cs)%3,0,3))
#     contour1 = axs[1].contour(x_cs_trans,z,w_cs,levels=levs,
#                               colors='k',linestyles='dashed',linewidths=2,zorder=2)

#     # positive vertical velocity
#     levs = list(np.arange(5,(np.max(w_cs)-np.max(w_cs)%5)+5,5))
#     contour2 = axs[1].contour(x_cs_trans,z,w_cs,levels=levs,
#                               colors='k',linestyles='solid',linewidths=2,zorder=2)
    
#     # # negative vertical vorticity
#     # levs = list(np.arange(np.min(zvort_cs)-np.min(zvort_cs)%0.02,0,0.02))
#     # contour3 = axs[1].contour(x_cs_trans,z,zvort_cs,levels=levs,
#     #                           colors='magenta',linestyles='dashed',linewidths=2,zorder=2)

#     # positive vertical vorticity
#     # levs = list(np.arange(0.02,(np.max(zvort_cs)-np.max(zvort_cs)%0.04)+0.04,0.04))
#     # contour4 = axs[1].contour(x_cs_trans,z,zvort_cs,levels=levs,
#     #                           colors='magenta',linestyles='solid',linewidths=2,zorder=2)
    
#     # levs = [0.1]
#     # levs2 = list(np.arange(2,(np.max(qh_cs)-np.max(qh_cs)%2)+2,2))
#     # [levs.append(l) for l in levs2]
#     # contour3 = axs[1].contour(x_cs_trans,z,qh_cs,levels=levs,
#     #                           colors='violet',linestyles='solid',linewidths=2,zorder=2)
    
#     # levs = list(np.arange(2,(np.max(qv_cs)-np.max(qv_cs)%2)+2,2))
#     # contour4 = axs[1].contour(x_cs_trans,z,qv_cs,levels=levs,
#     #                           colors='g',linestyles='solid',linewidths=2,zorder=2)
    
#     axs[1].contour(x_cs_trans,z,buoyancy_cs,[-0.01], colors='purple',linestyles='solid',
#                     linewidths=1,zorder=2)


#     # storm relative wind vectors
#     v_cs = ds.vinterp.values[0][:iz,iy1:iy2,ix1:ix2][:,cs_yi,cs_xi]
#     u_cs = ds.uinterp.values[0][:iz,iy1:iy2,ix1:ix2][:,cs_yi,cs_xi]
#     # project sr wind vectors onto cross sectional axis
#     wind_mag = np.sqrt(u_cs**2 + v_cs**2)
#     wind_dir = np.mod(180+(180/np.pi)*np.arctan2(v_cs,u_cs), 360)
    
#     x_unit_vector = cs_xvector / np.linalg.norm(cs_xvector)
#     y_unit_vector = cs_yvector / np.linalg.norm(cs_yvector)
#     _kdata = []
#     for k in range(u_cs.shape[0]):
#         _idata = []
#         for i in range(u_cs.shape[1]):
#             _udot = np.dot(u_cs[k,i],x_unit_vector)
#             _idata.append(_udot)
#         _kdata.append(_idata)
#     udot = _kdata
        
#     _kdata = []
#     for k in range(v_cs.shape[0]):
#         _idata = []
#         for i in range(v_cs.shape[1]):
#             _vdot = np.dot(v_cs[k,i],y_unit_vector)
#             _idata.append(_udot)
#     _kdata.append(_idata)
                     
#     vdot = _kdata
    
#     proj_wind = udot + vdot
#     proj_wind = np.array(proj_wind)
#     proj_wind_mag = proj_wind[:,:,1] - proj_wind[:,:,0]
    
#     grid = np.meshgrid(x_cs_trans[::2],z[::6])
#     u_grid = proj_wind_mag[::6,::2]
#     w_grid = w_cs[::6,::2]
#     quiver = axs[1].quiver(grid[0],grid[1], u_grid,w_grid,
#                            scale=500, width=0.002, zorder=1)
    
#     temp_cs = th_cs/((100000/prs_cs)**(287.05/1005))-273.15
    
#     lcl_plot = axs[1].plot(x_cs_trans,lcl_cs, c='g',linestyle='dotted',linewidth=2)
#     freeze_plot = axs[1].contour(x_cs_trans,z, temp_cs, [0],
#                                  colors='purple',linestyles='dotted',linewidths=2)

#     plt.clabel(contour1, fontsize=10,inline_spacing=3)
#     plt.clabel(contour2, fontsize=10,inline_spacing=3)
#     # plt.clabel(contour3, fontsize=10,inline_spacing=3)
#     # plt.clabel(contour4, fontsize=10,inline_spacing=3)

#     axs[1].set_title('Cross-section', fontsize='x-large')
    
#     axs[1].set_ylim(0.025)

# ##############################################################################
# ##############################################################################
    
#     x_pv = ds.xh.values[ix1:ix2] - ds.xh.values[ix1]
#     y_pv = ds.yh.values[iy1:iy2] - ds.yh.values[iy1]

#     u_pv = ds.uinterp.values[0]
#     v_pv = ds.vinterp.values[0]

#     grid2 = np.meshgrid(x_pv[::4],y_pv[::4])
#     u_grid2 = u_pv[0,iy1:iy2:4,ix1:ix2:4]
#     v_grid2 = v_pv[0,iy1:iy2:4,ix1:ix2:4]
#     axs[0].quiver(grid2[0],grid2[1], u_grid2,v_grid2, width=0.002)
    
#     # th_rho_pert_h_pv = th_rho_pert[0,:,:]
#     dbz_pv = ds.dbz.values[0][0,iy1:iy2,ix1:ix2]
#     uh_pv = uh[iy1:iy2,ix1:ix2]
#     buoyancy_pv = buoyancy[0,:,:]

    
#     ##########
#     # TLV Criteria
#     ##########
    
#     # vertical vorticity at surface greater than 0.15 /s
#     crit1 = ds.zvort.values[0][0,iy1:iy2,ix1:ix2]>=0.1
    
#     # pressure pertubation less than or equal to -10 hPa
#     diff = np.array(abs(ds.zh.values-1))
#     i1 = np.where(diff==min(diff))[0][0]+1
#     crit2 = np.mean(ds.prspert.values[0][:i1,iy1:iy2,ix1:ix2],axis=0)<=-10
    
#     # instantaneous wind speed at surface greater than or equal to 30 m/s
#     uinterp = ds.uinterp.values[0][0,iy1:iy2,ix1:ix2]
#     vinterp = ds.vinterp.values[0][0,iy1:iy2,ix1:ix2]
    
#     crit3 = np.sqrt(uinterp**2 + vinterp**2)>=25
    
#     all_crit = crit1*crit2*crit3
    
#     check_tlv = all_crit.flatten()
#     vort = ds.zvort.values[0][0,iy1:iy2,ix1:ix2].flatten()
#     tlv_vort = []
#     is_tlv = False
#     for i in range(len(check_tlv)):
#         if check_tlv[i] == True:
#             print('\t\t\thit')
#             tlv_vort.append(vort[i])
#             is_tlv = True
#         else:
#             pass
        
#     if is_tlv:
#         zvort = ds.zvort.values[0][0,iy1:iy2,ix1:ix2]
#         tlv_loc = np.where(zvort==np.max(zvort))
#         tlv_x = x_pv[tlv_loc[1]]
#         tlv_y = y_pv[tlv_loc[0]]
#     else:
#         tlv_loc = None
        
#     ##########
#     ##########
    
#     axs[0].plot(x_cs,y_cs, color='limegreen',linestyle='dashed',linewidth=4)
    
#     cs_min_val = np.round(np.min(buoyancy_cs),0)
#     cs_max_val = np.round(np.max(buoyancy_cs),0)
#     pv_min_val = np.round(np.min(buoyancy_pv),0)
#     pv_max_val = np.round(np.max(buoyancy_pv),0)
#     absmax = int(max(abs(cs_min_val),abs(cs_max_val),abs(pv_min_val),abs(pv_max_val)))
#     absmax = 0.2
#     cmap = 'seismic'
#     norm = colors.Normalize(vmin=-absmax, vmax=absmax)
    
#     cp_plot = axs[0].pcolormesh(x_pv[:-1],y_pv[:-1],buoyancy_pv, shading='gouraud',
#                                 cmap='seismic',norm=norm,zorder=0)
#     cb1 = plt.colorbar(cp_plot ,aspect=30, extend='both',ax=axs[0])
#     cb1.ax.set_title('Buoyancy (m $s^{-2}$)',fontsize=12)
    
#     color_plot = axs[1].pcolormesh(x_cs_trans,z,buoyancy_cs,
#                                    cmap=cmap,norm=norm,
#                                    zorder=0,shading='gouraud')
#     cb2 = plt.colorbar(color_plot, aspect=30,extend='both',ax=axs[1])
#     cb2.ax.set_title('Buoyancy (m $s^{-2}$)',fontsize=12)
    
#     axs[0].contour(x_pv[:-1],y_pv[:-1],buoyancy_pv,[-0.01], colors='purple',linestyles='solid',
#                     linewidths=1,zorder=2)
    
#     axs[0].contour(x_pv,y_pv,dbz_pv,[10], colors='k',linewidths=2,zorder=1)
    
#     axs[0].contour(x_pv,y_pv,uh_pv,[600], colors='magenta',linewidths=2,zorder=2)

    
#     if is_tlv:
#         axs[0].plot(tlv_x,tlv_y, marker='*',
#                     markersize=16,
#                     markerfacecolor='gold',
#                     markeredgewidth=1,
#                     markeredgecolor='k')

#     axs[0].set_title('Plan view', fontsize='x-large')
#     axs[0].set_xlabel('West-to-East distance (km)',fontsize=12,labelpad=5)
#     axs[0].set_ylabel('South-to-North distance (km)',fontsize=12,labelpad=5)
#     xmax2 = round(x_pv.max())
#     xmin2 = round(x_pv.min())
#     ymax2 = round(y_pv.max())
#     ymin2 = round(y_pv.min())
#     axs[0].set_xticks(np.linspace(xmin2,xmax2,15))
#     axs[0].set_yticks(np.linspace(ymin2,ymax2,15))
    
#     ts = str(int(ds.time.dt.seconds.values[0]/60))
#     axs[1].text(0.65, 0.075, 't = '+ts+' min',
#                 transform=axs[0].transAxes,fontstyle='italic',
#                 fontsize=16,backgroundcolor='white')
    
#     plt.subplots_adjust(wspace=0.02)
    
#     plt.show()
#     # outpath = '/t1/topping/python_scripts/figures/2500CAPE/'+\
#     #             'vertical_cross_sections/md_tlv_1/'
                
#     # plt.savefig(outpath+'vcs'+str(num)+'_ql_'+ts+'min.png',bbox_inches='tight',dpi=300)
    
# else:
#     print('No file found with name: ' + file)
    


import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import cmasher as cmr
import pandas as pd
import numpy as np
import os


def cp_data(run,f,cx_in,cy_in):

    ds = xr.open_dataset(run+f, decode_times=True)
    time = ds.time.dt.seconds.values[0]/60

    print('\t\t--> '+file+'\t'+str(time))
    
    x_center = ds.xh.sel(xh=cx_in, method='nearest')
    y_center = ds.yh.sel(yh=cy_in, method='nearest')
    
    z = ds.zh.values
    
    zmax = 5

    global bbox, bbox_sel, hspace
    bbox = [-25.0,65.0,-15.0,57.0]
    
    hspace = round(ds.xh.values[1]-ds.xh.values[0],2)
    
    # make sure that all arrays will be same shape
    global xshape,yshape
    xshape = (bbox[1]-bbox[0])/hspace
    yshape = (bbox[3]-bbox[2])/hspace
    xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox[0],
                                        x_center+bbox[1])))[0]
    ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox[2],
                                        y_center+bbox[3])))[0]
    if xtest != xshape:
        bbox[1] += (xshape - xtest)*hspace
        xtest = np.shape(ds.xh.sel(xh=slice(x_center+bbox[0],
                                            x_center+bbox[1])))[0]
    if ytest != yshape:
        bbox[3] += (yshape - ytest)*hspace
        ytest = np.shape(ds.yh.sel(yh=slice(y_center+bbox[2],
                                            y_center+bbox[3])))[0]
    
    xsel = ds.xh.sel(xh=slice((x_center+bbox[0]),
                              (x_center+bbox[1])))
    
    ysel = ds.yh.sel(yh=slice((y_center+bbox[2]),
                              (y_center+bbox[3])))

    x1diff = np.round(xsel.values[0] - x_center, 2)
    x2diff = np.round(xsel.values[-1]- x_center, 2)
    y1diff = np.round(ysel.values[0]- y_center, 2)
    y2diff = np.round(ysel.values[-1] - y_center, 2)
    bbox_sel = [x1diff,x2diff,y1diff,y2diff]
    
    # b = ds.buoyancy.sel(zh=slice(0,zmax), 
    #                     xh=slice(x_center+bbox[0],
    #                              x_center+bbox[1]),
    #                     yh=slice(y_center+bbox[2],
    #                              y_center+bbox[3])).squeeze(('time'))
    
    b = ds.buoyancy.sel(zh=slice(0,zmax), 
                        xh=slice(x_center+bbox[0],
                                 x_center+bbox[1]),
                        yh=y_center+25).squeeze(('time'))
    
    w = ds.winterp.sel(zh=slice(0,zmax),
                       xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                       yh=y_center+25).squeeze(('time'))
    
    lh = ds.ptb_mp.sel(zh=slice(0,zmax),
                       xh=slice(x_center+bbox[0],
                                x_center+bbox[1]),
                       yh=y_center+25).squeeze(('time'))
    
    
    cp_condition = np.where(((b>-0.01) | (np.abs(w>2)) | (lh>-1e-5)), 0, b)
       
    # b_mean = np.nanmean(b, axis=1)
    
    # outflow = np.where(b<-0.01, b, np.nan)
    # b_mean = np.nanmean(outflow, axis=1)
   
    # ds.close()

    # return b_mean
    
    cpd_i = np.argmax(cp_condition, axis=0)


    ds.close()

    return cp_condition, cpd_i


def make_plot(fig,axs,cp_comp,cpd_comp,folder):
    
    if 'mm' in folder:
        i=0
        title='  (a)  Moist PBL / Moist FT'#-' + HODO + '-' + CAPE
    elif 'md' in folder:
        i=1
        title='  (b)  Moist PBL / Dry FT'#-' + HODO + '-' + CAPE
    elif 'dm' in folder:
        i=2
        title='  (c)  Dry PBL / Moist FT'#-' + HODO + '-' + CAPE
    elif 'dd' in folder:
        i=3
        title='  (d)  Dry PBL / Dry FT'#-' + HODO + '-' + CAPE
        
        
    plotx = range(0,np.shape(cp_comp)[1])
    plotz = range(0,np.shape(cp_comp)[0])  

    
    axs[i].set_title(title,fontsize=20,loc='left')
    
    cp_mask = np.ma.masked_greater(cp_comp,-0.01)
    norm = colors.Normalize(vmin=-0.12, vmax=-0.01)
    cmap = cmr.voltage
    # cp_mask = np.ma.masked_inside(cp_comp,-0.001, 0.001)
    # norm = colors.Normalize(vmin=-0.2, vmax=0.2)
    # cmap = 'seismic'
    cp_plot = axs[i].pcolormesh(plotx,plotz,cp_mask, 
                                shading='gouraud',cmap=cmap,norm=norm,
                                zorder=0)
    
    axs[i].plot(plotx, cpd_comp,
                color='k',linestyle='dashed',linewidth=2, 
                zorder=1)
    
    
    return cp_plot
    

###############################################################################
###############################################################################

# Core set of simulations
indir = '/t1/topping/runs/2500/'

# CAPE sensitivity
# indir = '/t1/topping/runs/1500/'
# indir = '/t1/topping/runs/3500/'

# Microphysics sensitivity
indir = '/t1/topping/runs/morrison/'
# indir = '/strm4/topping/runs/nssl3/'

# Surface drag sensitivity
# indir = '/t1/topping/runs/freeslip/'

# Shear sensitivity
# indir = '/t1/topping/runs/sigtor/'
# indir = '/t1/topping/runs/sigtor2/'

# Random temperature perturbations
# indir = '/strm4/topping/runs/ensemble/'
# indir = '/t1/topping/runs/ensemble/'

###############################################################################

runs = ['mm','md','dm','dd']
member = '0'

HODO = 'QT'
CAPE = '2500'
MP = 'NSSL'

st = 90   # start time
et = 90    # end time

ft = 45   # first time after initialization
ff = 2    # number of first file after initialization
dt = 1    # large timestep (minutes)

# file numbers based on start and end times
sf = ((st-ft)/dt)+ff 
ef = ((et-ft)/dt)+ff


fig,axs = plt.subplots(2,2,figsize=(16,11.5))
axs = axs.flatten()

for folder in os.listdir(indir):

    neg_tseries = []
    cpd_tseries = []

    if os.path.isdir(os.path.join(indir,folder)) and folder in runs:
        
        print(folder[:2]+' -----')
        plot = True
        
        if int(member) != 0:
            run = indir+folder+'/'+folder[:2]+member+'/run/'
            outpath = indir+'figures/member'+member+'/'
        else:
            run = indir+folder+'/run/'
            outpath = indir+'figures/'
        
        pos_df = pd.read_csv(run+'rm_tracking.csv')
        x_locs = np.asarray(pos_df['x_smooth'])
        y_locs = np.asarray(pos_df['y_smooth'])
        locs = (x_locs,y_locs)
                    
        i=0      
        print('\tGetting Data:')
        for file in sorted(os.listdir(run)):
            if os.path.isfile(os.path.join(run,file)) and 'cm1out_000' in file\
            and (sf <= int(file[-6:-3]) <= ef):
                f = file
                
                cx = locs[0][st-ft+i]
                cy = locs[1][st-ft+i]
                
                neg_intensity, cpd = cp_data(run,f,cx,cy)
                    
                neg_tseries.append(neg_intensity)
                cpd_tseries.append(cpd)

                i+=1
                
        cp_comp = np.nanmean(neg_tseries, axis=0)
        cpd_comp = np.nanmean(cpd_tseries, axis=0)
        cp_plot = make_plot(fig,axs,cp_comp,cpd_comp,folder)

    else:
        pass
    

axs[2].set_xlabel('x-distance (km)', fontsize=18)
axs[3].set_xlabel('x-distance (km)', fontsize=18)
axs[3].tick_params(axis='x', which='major', labelsize=14)

axs[0].set_ylabel('height (km)', fontsize=18)
axs[0].tick_params(axis='y', which='major', labelsize=14)
axs[2].set_ylabel('height (km)', fontsize=18)
axs[2].tick_params(axis='both', which='major', labelsize=14)

axs[0].tick_params(axis='x', which='major', labelcolor='white')
axs[1].tick_params(axis='both', which='major', labelcolor='white')
axs[3].tick_params(axis='y', which='major', labelcolor='white')

axs[0].tick_params(axis='both', which='major', length=8, width=2)
axs[1].tick_params(axis='both', which='major', length=8, width=2)
axs[2].tick_params(axis='both', which='major', length=8, width=2)
axs[3].tick_params(axis='both', which='major', length=8, width=2)


fig.subplots_adjust(right=0.8, hspace=0.26, wspace=0.25)
cbar_ax = fig.add_axes([0.82, 0.15, 0.01, 0.7])
cb = plt.colorbar(cp_plot,cax=cbar_ax, extend='min')
cb.set_label(label='Mean Buoyancy (m $s^{-2}$)',fontsize=18)
cb.ax.tick_params(labelsize=14) 

plt.subplots_adjust(wspace=0.08, hspace=0.2)






