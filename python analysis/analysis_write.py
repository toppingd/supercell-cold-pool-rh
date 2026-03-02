

import argparse
import os
import numpy as np
import pandas as pd
import xarray as xr
import dask
from pathlib import Path

from scipy.ndimage import distance_transform_edt
from skimage.filters import gaussian, sobel
from skimage.morphology import opening, closing, dilation, disk, remove_small_objects
from skimage.segmentation import watershed

from zarr.codecs.numcodecs import Blosc
from dask.diagnostics import ProgressBar

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='zarr')


# Dask config
dask.config.set({'array.chunk-size': '128MiB'})
os.environ.setdefault('DASK_TEMPORARY_DIRECTORY', '/storm/topping/tmp/dask-tmp')


VARS_NEEDED = ['th', 'qv', 'qc', 'qr', 'qi', 'qs', 'qg', 'qhl', 'buoyancy', 'dbz', 'uh', 'ptb_mp', 'rho', 'lcl', 'prate', 'winterp']
FINAL_KEEP = ['prate', 'uh', 'lcl', 'dbz', 'buoyancy', 'b2', 'winterp', 'cp_clean', 'cp_depth', 'total_hydro_mass', 'ptb_mp', 'lh_norm']


def create_file_list(sim_dir, sf, ef):

    sim_dir = Path(sim_dir)
    all_files = sorted(sim_dir.glob('cm1out_000*.nc'))

    if not all_files:
        raise RuntimeError(f'No CM1out files in {sim_dir}')

    selected_files = []
    for f in all_files:
        try:
            num = int(f.stem.split('_')[-1])
        except ValueError:
            continue
        if sf <= num <= ef:
            selected_files.append(f)

    if not selected_files:
        raise RuntimeError(f'No files found in range {sf}–{ef}')

    return selected_files


def get_vars_to_drop(nc_file):

    ds_inspect = xr.open_dataset(nc_file, decode_times=False)
    all_vars = set(ds_inspect.data_vars)
    coords = set(ds_inspect.coords)
    ds_inspect.close()

    keep = set(VARS_NEEDED) | coords
    drop_vars = list(all_vars - keep)

    return drop_vars


def get_storm_locs(sim_dir, i_start, i_end):
    pos_df = pd.read_csv(sim_dir / 'rm_tracking.csv')
    cxs = pos_df['x_smooth'].values[i_start:i_end + 1]
    cys = pos_df['y_smooth'].values[i_start:i_end + 1]

    return cxs, cys


def coords_km_to_indices(x_axis, y_axis, x_km, y_km):

    x_axis = np.asarray(x_axis)
    y_axis = np.asarray(y_axis)
    x_km   = np.asarray(x_km)
    y_km   = np.asarray(y_km)

    # position where x_km should be inserted to keep order, then snap to nearest neighbor
    ix = np.searchsorted(x_axis, x_km)
    ix = np.clip(ix, 1, len(x_axis) - 1)
    cx = ix - (x_km < (x_axis[ix] + x_axis[ix-1]) / 2.0)

    iy = np.searchsorted(y_axis, y_km)
    iy = np.clip(iy, 1, len(y_axis) - 1)
    cy = iy - (y_km < (y_axis[iy] + y_axis[iy-1]) / 2.0)

    return cx.astype(int), cy.astype(int)


def storm_subset(ds, icx, icy, bbox):

    west, east, south, north = bbox

    x = ds['xh'].values
    y = ds['yh'].values
    dx = float(np.diff(x).mean())
    dy = float(np.diff(y).mean())

    # index offsets
    ix0 = int(np.floor(west / dx))
    ix1 = int(np.ceil(east / dx))
    iy0 = int(np.floor(south / dy))
    iy1 = int(np.ceil(north / dy))

    # final index window
    ixs = icx + ix0
    ixe = icx + ix1
    iys = icy + iy0
    iye = icy + iy1

    ds_subset = ds.isel(yh=slice(iys, iye + 1),
                        xh=slice(ixs, ixe + 1))

    icx_local = icx - ixs
    icy_local = icy - iys

    return icy_local, icx_local, ds_subset


# def calc_reference_th_rho(initial_file, drop_vars, morrison):
#     # using initial base state as the reference
#     with xr.open_dataset(initial_file,
#                          engine='h5netcdf',
#                          decode_times=False,
#                          mask_and_scale=False,
#                          decode_coords=False,
#                          cache=False,
#                          lock=False,
#                          drop_variables=drop_vars) as ds_initial:
#
#         yh_vals = ds_initial['yh'].values
#         xh_vals = ds_initial['xh'].values
#         iy = int(np.argmin(np.abs(yh_vals - 100)))
#         ix = int(np.argmin(np.abs(xh_vals - 10)))
#         sel0 = {'yh': iy, 'xh': ix}
#
#         if morrison:
#
#             vars_needed= ['th', 'qv', 'qc', 'qr', 'qi', 'qs', 'qg']
#             ds0_slice = ds_initial[vars_needed].isel(time=0, **sel0)
#
#             ds0_slice = ds0_slice.load()
#
#             th_rho0 = (
#                     ds0_slice.th *
#                     (1 + 0.608 * ds0_slice.qv
#                     - ds0_slice.qc - ds0_slice.qr
#                     - ds0_slice.qi - ds0_slice.qs
#                     - ds0_slice.qg)
#             ).squeeze()
#
#         else:
#
#             vars_needed= ['th', 'qv', 'qc', 'qr', 'qi', 'qs', 'qg', 'qhl']
#             ds0_slice = ds_initial[vars_needed].isel(time=0, **sel0)
#
#             ds0_slice = ds0_slice.load()
#
#             th_rho0 = (
#                     ds0_slice.th *
#                     (1 + 0.608 * ds0_slice.qv
#                     - ds0_slice.qc - ds0_slice.qr
#                     - ds0_slice.qi - ds0_slice.qs
#                     - ds0_slice.qg - ds0_slice.qhl)
#             ).squeeze()
#
#     return th_rho0


def calc_reference_th_rho(ds, morrison):

    # time varying reference state
    # southeast corner (far enough away from storm and boundaries)
    sel0 = {'yh': slice(100, 140), 'xh': slice(500, 540)}

    if morrison:
        print('Morrison buoyancy calc')
        vars_needed = ['th', 'qv', 'qc', 'qr', 'qi', 'qs', 'qg']
        ds0_slice = ds[vars_needed].isel(time=0, **sel0)

        ds0_slice = ds0_slice.load()

        th_rho0 = (
                ds0_slice.th *
                (1 + 0.608 * ds0_slice.qv
                 - ds0_slice.qc - ds0_slice.qr
                 - ds0_slice.qi - ds0_slice.qs
                 - ds0_slice.qg)
        ).squeeze()

    else:
        print('Regular buoyancy calc')
        vars_needed = ['th', 'qv', 'qc', 'qr', 'qi', 'qs', 'qg', 'qhl']
        ds0_slice = ds[vars_needed].isel(time=0, **sel0)

        ds0_slice = ds0_slice.load()

        th_rho0 = (
                ds0_slice.th *
                (1 + 0.608 * ds0_slice.qv
                 - ds0_slice.qc - ds0_slice.qr
                 - ds0_slice.qi - ds0_slice.qs
                 - ds0_slice.qg - ds0_slice.qhl)
        ).squeeze()

    th_rho0_mean = th_rho0.mean(dim=('yh', 'xh'), skipna=True)

    return th_rho0_mean


def calc_buoyancy(reference_th_rho, ds, morrison):

    if morrison:
        th_rho = (
            ds.th *
            (1 + 0.608 * ds.qv
            - ds.qc - ds.qr
            - ds.qi - ds.qs
            - ds.qg)
        )

    else:
        th_rho = (
            ds.th *
            (1 + 0.608 * ds.qv
            - ds.qc - ds.qr
            - ds.qi - ds.qs
            - ds.qg - ds.qhl)
        )

    th_rho_pert = th_rho - reference_th_rho
    b2 = 9.81 * (th_rho_pert / reference_th_rho)

    return th_rho, b2


def isolate_cp_watershed(
    b_sfc,                      # 2D (yh, xh): buoyancy at ~125 m
    dbz_sfc,                    # 2D (yh, xh): reflectivity (dBZ) at ~125 m
    cp_mask,                    # 2D (yh, xh): strict candidate cold-pool mask (boolean)
    w,                          # 3D (nz, yh, xh): vertical motion (m/s)
    center_ixy,                 # (icx, icy): pixel coords for the target right-mover
    zh,
    w_dbz=0.2, w_b=8, w_edge=0.1, # elevation recipe
    dbz_clip=(20, 65),
    b_clip=(-0.3, -0.03),
    smooth_sigma=2.0,
    # Updraft layer range
    zh_mean_range=(2, 5),
    wmean_sigma=1.0,            # smoothing for w-mean before competitor selection
    # Marker settings
    main_seed_radius=1,         # px
    move_max_radius=80,         # px; allow main seed to move without letting it seed a different storm
    competitor_w_thresh=20.0,   # m/s threshold on mean w for competitor markers
    competitor_buffer_px=200,   # px exclusion around main seed (40 px = 10 km)
    competitor_buffer_dir=[(270, 5, 130)],
    competitor_min_distance=20, # px spacing between competitors
    competitor_kmax=2,          # max competitor seeds
    competitor_edge_margin_px=10,   # px: don't allow competitors within this many pixels of the domain edge
    # Masks & watershed knobs
    mask_open_radius=-1,         # px: break hairline bridges in cp_mask
    mask_link_px=20,            # px: geometrically combine broken cold pool regions 10 px = 2.5 km)
    compactness=0.005,
    connectivity=1,
    watershed_line=True,
    # Post-processing
    min_keep_area_px=-1,
    # Debug
    return_debug=True
):

    # -----------------------------
    # Helpers
    # -----------------------------
    def _normalize_clip(x, lo, hi):
        x = np.clip(x, lo, hi)
        return (x - lo) / max(1e-6, hi - lo)

    def _build_elev(b2d, z2d, mask):
        # Normalize (0..1); higher => stronger signal
        b_neg = np.clip(-b2d, -b_clip[0], -b_clip[1]) / max(1e-6, -b_clip[0])  # stronger negative buoyancy -> 1
        z_nm  = _normalize_clip(z2d, *dbz_clip)                          # stronger dbz -> 1

        # Smooth for stable gradients
        b_sm = gaussian(b_neg, sigma=smooth_sigma, preserve_range=True)
        z_sm = gaussian(z_nm,  sigma=smooth_sigma, preserve_range=True)

        # Edge term (ridges/gaps)
        edge = 0.5 * sobel(b_sm) + 0.5 * sobel(z_sm)
        edge = np.clip(edge, 0, None)

        # Elevation: interior low, ridges high
        elev = w_dbz * (1.0 - z_sm) + w_b * (1.0 - b_sm) + w_edge * edge
        elev = np.where(mask, elev, np.nan)

        # Normalize to [0,1] within mask for stable scaling (single percentile pass)
        vals = elev[np.isfinite(elev)]
        if vals.size > 0:
            lo, hi = np.percentile(vals, [2, 98])
            elev = (elev - lo) / max(1e-6, hi - lo)
            elev = np.clip(elev, 0, 1)

            barrier = (elev >= 1.0 - 0.08)
            elev[barrier] = np.inf

        else:
            elev = np.zeros_like(mask, dtype=float)

        return elev

    def _zh_indices(nz, zh_levels, rng):
        zmin_m = float(rng[0])
        zmax_m = float(rng[1])
        z0i = int(np.argmin(np.abs(zh_levels - zmin_m)))
        z1i = int(np.argmin(np.abs(zh_levels - zmax_m)))

        z0i = max(0, min(nz - 1, z0i))
        z1i = max(0, min(nz - 1, z1i))

        return z0i, z1i

    def _select_competitors_topk(wmean, zone, kmax, min_dist):
        H, W = wmean.shape
        cand = wmean.copy()
        cand[~zone] = -np.inf

        # Get up to kmax top indices via argpartition (fast)
        flat = cand.ravel()
        k = min(kmax, np.count_nonzero(np.isfinite(flat)))
        if k == 0:
            return []
        idxs = np.argpartition(flat, -k)[-k:]
        idxs = idxs[np.argsort(flat[idxs])[::-1]]  # sort descending

        peaks = []
        for idx in idxs:
            y = idx // W
            x = idx % W
            if not np.isfinite(cand[y, x]) or cand[y, x] == -np.inf:
                continue
            peaks.append((y, x))
            # Non-maximum suppression in a disk of 'min_dist' px
            rr = int(min_dist)
            y0, y1 = max(0, y - rr), min(H, y + rr + 1)
            x0, x1 = max(0, x - rr), min(W, x + rr + 1)
            yy, xx = np.ogrid[y0:y1, x0:x1]
            mask_nms = (yy - y) ** 2 + (xx - x) ** 2 <= rr * rr
            cand[y0:y1, x0:x1][mask_nms] = -np.inf
        return peaks

    # -----------------------------
    # Preprocess & masks
    # -----------------------------
    cp_mask_orig = cp_mask.astype(bool).copy() # Keep a copy of the original cold pool mask for final trimming

    H, W = cp_mask.shape
    icx, icy = map(int, center_ixy)
    icx = np.clip(icx, 0, W - 1)
    icy = np.clip(icy, 0, H - 1)

    # Strict mask for final flooding domain
    cp_mask_strict = cp_mask.astype(bool)
    if mask_open_radius and mask_open_radius > 0:
        cp_mask_strict = opening(cp_mask_strict, disk(int(mask_open_radius)))
    if mask_link_px and mask_link_px > 0:
        r_close = max(1, mask_link_px // 2)
        cp_mask_strict = closing(cp_mask_strict, disk(r_close))

    # -----------------------------
    # Elevation
    # -----------------------------
    elev = _build_elev(b_sfc, dbz_sfc, cp_mask_strict)
    allowed = cp_mask_strict & np.isfinite(elev)

    # -----------------------------
    # Markers (main + competitors)
    # -----------------------------
    markers = np.zeros((H, W), dtype=np.int32)

    # Main seed: one pixel at center (or nearest cp pixel)
    main_seed = np.zeros((H, W), dtype=bool)
    if cp_mask_strict[icy, icx]:
        main_seed[icy, icx] = True
    else:
        yy, xx = np.nonzero(cp_mask_strict)
        if yy.size == 0:
            target = np.zeros_like(cp_mask_strict, dtype=bool)
            return (target, {"reason": "no_cp_pixels"}) if return_debug else target
        k0 = np.argmin((yy - icy) ** 2 + (xx - icx) ** 2)
        main_seed[yy[k0], xx[k0]] = True

    # ALWAYS MOVE: lowest-elevation allowed pixel WITHIN the radius
    cand_mask = allowed & np.isfinite(elev)
    if cand_mask.any():
        # Distance map from the requested storm center (icy, icx)
        H, W = allowed.shape
        yy, xx = np.indices((H, W))
        d2 = (yy - icy)**2 + (xx - icx)**2
        in_radius = d2 <= (move_max_radius**2)

        cand_mask &= in_radius
        if not cand_mask.any():
            # Optional: fallback — loosen to nearest allowed pixel inside radius cap
            # (Here, we expand radius gradually; see Option C below if you want that.)
            # For a simple fallback, just keep the original center pixel as seed:
            cand_mask = allowed & np.isfinite(elev)  # (or skip moving)

        if cand_mask.any():
            # Slight tie-breaker by (normalized) distance to keep moves local
            d2_norm = d2 / (d2.max() + 1e-6)
            score = np.where(cand_mask, elev + 1e-3*d2_norm, np.inf)

            iy_new, ix_new = np.unravel_index(np.argmin(score), score.shape)
            main_seed[:] = False
            main_seed[iy_new, ix_new] = True
            markers[:] = 0
            markers[iy_new, ix_new] = 1

            # Dilate AFTER moving (unchanged from your pipeline)
            if main_seed_radius and main_seed_radius > 0:
                main_seed = dilation(main_seed, disk(int(main_seed_radius)))
                markers[:] = 0
                markers[main_seed] = 1

    # Competitor seeds from mean w in zh range
    nz = zh.size
    z0i, z1i = _zh_indices(nz, zh, zh_mean_range)
    wmean = np.nanmean(w[z0i:(z1i + 1)], axis=0)
    if wmean_sigma and wmean_sigma > 0:
        wmean = gaussian(wmean, sigma=wmean_sigma, preserve_range=True)

    # -----------------------------
    # Direction-aware competitor buffer
    # -----------------------------
    dist_to_seed = distance_transform_edt(~main_seed).astype(float)  # px

    # Angle map relative to the main seed centroid
    ys, xs = np.nonzero(main_seed)
    if ys.size == 0:
        seed_yc, seed_xc = float(icy), float(icx)
    else:
        seed_yc, seed_xc = ys.mean(), xs.mean()

    yy, xx = np.indices((H, W))
    dx = xx - seed_xc          # +x to the right (same in image & math)
    dy = yy - seed_yc          # +y downward in image coordinates

    # arctan2(x, y) gives 0° at +y (north), increasing clockwise (east=90°).
    ang_deg = (np.degrees(np.arctan2(dx, dy)) + 360.0) % 360.0
    buf_r = np.full((H, W), float(competitor_buffer_px), dtype=float)
    if competitor_buffer_dir:
        for amin, amax, r in competitor_buffer_dir:
            amin = float(amin) % 360.0
            amax = float(amax) % 360.0
            r = float(r)
            if amin <= amax:
                sel = (ang_deg >= amin) & (ang_deg <= amax)
            else:
                # Wrap-around across 0° (e.g., 330°..20°)
                sel = (ang_deg >= amin) | (ang_deg <= amax)
            buf_r[sel] = r

    # -------------------------------------------------
    # Edge margin: disallow competitors near domain edge
    # -------------------------------------------------
    m = int(competitor_edge_margin_px)
    if m > 0:
        interior = np.zeros_like(cp_mask_strict, dtype=bool)
        if H > 2*m and W > 2*m:
            interior[m:H-m, m:W-m] = True
        # If the margin exceeds half the dimension, interior stays all False (no competitors allowed)
    else:
        interior = np.ones_like(cp_mask_strict, dtype=bool)

    comp_zone = (
        cp_mask_strict &
        interior &
        (dist_to_seed >= buf_r) &
        np.isfinite(wmean) &
        (wmean >= competitor_w_thresh)
    )

    peaks = _select_competitors_topk(
        wmean=wmean, zone=comp_zone,
        kmax=int(competitor_kmax), min_dist=int(competitor_min_distance)
    )
    for i, (y, x) in enumerate(peaks, start=2):
        markers[y, x] = i

    # -----------------------------
    # Main speed boost (local bias to help the target flood a little farther)
    # -----------------------------
    # seed_boost_px   = 3     # radius (px) around the main seed to bias (typical 1–3)
    # seed_boost_gain = 0.5  # how much to lower elev in that ring (typical 0.04–0.10)
    # if seed_boost_px > 0 and seed_boost_gain > 0:
    #     seed_zone = dilation(main_seed, disk(int(seed_boost_px))) & allowed
    #     if seed_zone.any():
    #         elev = elev.copy()
    #         elev[seed_zone] = np.clip(elev[seed_zone] - float(seed_boost_gain), 0.0, 1.0)

    # -----------------------------
    # Watershed
    # -----------------------------
    elev_w = elev.copy()
    elev_w[~allowed] = np.inf

    labels = watershed(
        elev_w,
        markers=markers,
        mask=allowed,
        connectivity=connectivity,
        compactness=compactness,
        watershed_line=watershed_line
    )
    target = (labels == 1)

    target = (target & cp_mask_orig)

    # -----------------------------
    # Post-processing
    # -----------------------------
    if min_keep_area_px and min_keep_area_px > 0 and target.any():
        target = remove_small_objects(target, min_size=int(min_keep_area_px))

    if return_debug:
        dbg = {
            "elev": elev,
            "markers": markers,
            "labels": labels,
            "allowed": allowed,
            "main_seed": main_seed,
            "wmean": wmean,
            "comp_zone": comp_zone,
            "angs": ang_deg,
            "peaks": peaks,
            "interior":interior
        }
        return target, dbg
    else:
        return target


def filter_cp(ds, center_xy, zmax=5):

    b = ds['b2'].isel(time=0).sel(zh=slice(0,zmax)).values
    lh = ds['ptb_mp'].isel(time=0).sel(zh=slice(0,zmax)).values
    w = ds['winterp'].isel(time=0).sel(zh=slice(0,zmax)).values
    dbz = ds['dbz'].isel(time=0).sel(zh=slice(0, zmax)).values

    zh = ds['zh'].values
    z = ds['zh'].sel(zh=slice(0,zmax)).values
    lcl = ds['lcl'].isel(time=0).values

    z_3d = z[:, None, None]
    lcl_3d = lcl[None, :, :]
    lcl_mask = (z_3d <= lcl_3d)  # cap lcl height at zmax (5 km)

    # mean subcloud latent heating
    lh_subcloud = np.nanmedian(np.where(lcl_mask, lh, np.nan), axis=0)

    # filter out where buoyancy is greater that -0.01 m2 s-2
    b_sfc = b[0, :, :]
    dbz_sfc = dbz[0, :, :]

    b_condition = (b_sfc <= -0.01)
    lh_condition = (lh_subcloud != 0)
    cp_mask = (b_condition & lh_condition)  # active cold pool

    if np.any(cp_mask):
        cp_isolated_mask, debug = isolate_cp_watershed(b_sfc,
                                                       dbz_sfc,
                                                       cp_mask,
                                                       w,
                                                       center_xy,
                                                       zh)

        cp_isolated_mask_3d = cp_isolated_mask[None, :, :].repeat(b.shape[0], axis=0)  # (zh, yh, xh)
        cp_isolated = np.where(cp_isolated_mask_3d, b, np.nan)  # (zh, yh, xh)

    else:
        cp_isolated = np.full_like(b, np.nan)

    padding_size = ds.zh.size - cp_isolated.shape[0]
    padding = ((0, padding_size), (0, 0), (0, 0))

    cp_isolated = np.pad(
        cp_isolated,
        pad_width=padding,
        mode='constant',
        constant_values=np.nan
    )

    cp_isolated_4d = cp_isolated[None,:,:,:]

    cp_isolated_padded = xr.DataArray(
        data = cp_isolated_4d,
        coords = {
            'time':ds.time,
            'zh':ds.zh,
            'yh':ds.yh,
            'xh':ds.xh
        },
        dims = ['time', 'zh', 'yh', 'xh']
    )

    ds_cp = xr.Dataset({'cp_clean':cp_isolated_padded})

    ds_cp['cp_clean'].attrs.update({
        'long_name': 'isolated cold pool',
        'units': 'm s-2',
    })

    return ds_cp


def calc_cp_depth(ds):
    cp = ds['cp_clean']
    cp_mask = cp <= -0.01
    valid = xr.where(cp_mask, np.isfinite(cp), False)
    valid_np = valid.values.astype(bool)
    T, Z, Y, X = valid_np.shape

    bad = ~valid_np
    bad_int = bad.astype(np.int16)

    # Compute consecutive-bad run length by scanning upward.
    run_bad = np.zeros_like(bad_int, dtype=np.int16)
    run_bad[:, 0, :, :] = bad_int[:, 0, :, :]

    for k in range(1, Z):
        curr_bad = bad_int[:, k, :, :]  # 1 if bad, 0 if good
        prev_bad = bad_int[:, k - 1, :, :]  # 1 if previous level bad

        # extend where current bad and previous bad
        extend = (curr_bad == 1) & (prev_bad == 1)
        # new sequence where current bad and previous good
        newseq = (curr_bad == 1) & (prev_bad == 0)

        run_bad[:, k, :, :] = 0
        run_bad[:, k, :, :][extend] = run_bad[:, k - 1, :, :][extend] + 1
        run_bad[:, k, :, :][newseq] = 1

    breaker = run_bad > 2  # set int to desired gap depth

    any_break = np.any(breaker, axis=1)  # (T, Y, X)
    first_break_idx = np.argmax(breaker, axis=1)

    last_valid_index = np.where(
        any_break,
        first_break_idx - 1,  # just before first breaker
        Z - 1  # no breaker -> full column allowed
    )

    last_valid_index = np.where(last_valid_index < 0, -1, last_valid_index)

    runlen = np.where(last_valid_index >= 0, last_valid_index + 1, 0).astype(np.int32)  # (T, Y, X)

    zh_vals = cp['zh'].values
    depth = np.zeros((T, Y, X), dtype=zh_vals.dtype)

    mask_pos = runlen > 0
    idx = np.maximum(runlen - 1, 0)  # safe index

    flat_mask = mask_pos.ravel()
    flat_idx = idx.ravel()
    depth_flat = depth.ravel()
    depth_flat[flat_mask] = zh_vals[flat_idx[flat_mask]]
    depth = depth_flat.reshape((T, Y, X))

    da_depth = xr.DataArray(
        depth,
        dims=('time', 'yh', 'xh'),
        coords={'time': cp['time'], 'yh': cp['yh'], 'xh': cp['xh']},
        name='cp_depth',
    )

    # Carry units from zh if present
    zh_units = cp['zh'].attrs.get('units', '')
    da_depth.attrs.update({
        'long_name': 'cold pool depth',
        'units': zh_units,
        'description': 'contiguous cold-pool depth from surface'
    })

    ds_cpd = xr.Dataset({'cp_depth': da_depth})

    return ds_cpd


def calc_latent_heating(
    ds,
    *,
    zmax_km = 10.5,
    w_thresh= 1.0,
    density_var = 'rho',
    q_names = ('qc', 'qr', 'qi', 'qs', 'qg', 'qhl')
):

    sub = ds.sel(zh=slice(0, zmax_km))

    x_km = sub['xh'].values
    y_km = sub['yh'].values
    dx_m = float(np.diff(x_km).mean()) * 1000.0
    dy_m = float(np.diff(y_km).mean()) * 1000.0

    zf = ds['zf']
    dz_m = (zf.diff('zf') * 1000.0) \
        .rename({'zf': 'zh'}) \
        .assign_coords(zh=ds['zh']) \
        .sel(zh=sub['zh'])

    dz = dz_m.values

    # Cell volume per (zh,yh,xh)
    vol3d = (dx_m * dy_m) * dz[:, None, None]

    # total hydrometeor mass
    q_list = [name for name in q_names if name in sub.data_vars]
    qtotal = None # kg/kg
    for qn in q_list:
        qv = sub[qn].data.astype(np.float32, copy=False)
        qtotal = qv if qtotal is None else (qtotal + qv)

    rho = sub[density_var].data.astype(np.float32, copy=False) # kg/m^3
    lh  = sub['ptb_mp'].data.astype(np.float32, copy=False) # K/s
    w   = sub['winterp'].data.astype(np.float32, copy=False) # m/s

    total_mass = qtotal * rho * vol3d # kg

    safe = (total_mass > 0 + 1e-6) & (w < w_thresh) # only want values outside the updraft

    lh_norm = np.full_like(lh, np.nan, dtype=np.float32)
    np.divide(lh, total_mass, out=lh_norm, where=safe)

    ds_out = xr.Dataset(
        {
            'total_hydro_mass': xr.DataArray(
                total_mass.astype(np.float32, copy=False),
                dims=sub[density_var].dims,
                coords=sub[density_var].coords,
            ),
            'lh_norm2': xr.DataArray(
                lh_norm,
                dims=sub['ptb_mp'].dims,
                coords=sub['ptb_mp'].coords,
            ),
        }
    )

    ds_out['total_hydro_mass'].attrs.update({
        'long_name': 'total hydrometeor mass',
        'units': 'kg',
        'note': f"q sum = {','.join(q_list)}; density = {density_var}; volume from dx*dy*dz"
    })

    ds_out['lh_norm2'].attrs.update({
        'long_name': 'latent heating normalized by hydrometeor mass',
        'units': 'K s-1 kg-1'
    })

    return ds_out


def calculations(reference_th_rho, center_ixy, ds, morrison):

    th_rho, b2 = calc_buoyancy(reference_th_rho, ds, morrison)

    ds_b = xr.Dataset({'th_rho': th_rho, 'b2': b2})

    ds_b['th_rho'].attrs.update({
        'long_name': 'density potential temperature',
        'units': 'K',
    })
    ds_b['b2'].attrs.update({
        'long_name': 'buoyancy based on current time step',
        'units': 'm s-2',
    })

    ds = ds.merge(ds_b)

    ##############################################

    ds_cp = filter_cp(ds, center_ixy, zmax=5)
    ds = ds.merge(ds_cp)

    ###############################################

    ds_cpd = calc_cp_depth(ds)
    ds = ds.merge(ds_cpd)

    ###############################################

    ds_lh = calc_latent_heating(ds)
    ds = ds.merge(ds_lh)


    return ds


def build_zarr_v3_encoding(ds):

    compressor = Blosc(cname='zstd', clevel=3, shuffle=1)
    enc = {}

    all_vars = {**ds.data_vars, **ds.coords}

    for name, da in all_vars.items():
        e = {'compressor': compressor}
        has_dask_chunks = getattr(da.data, 'chunks', None) is not None

        if not has_dask_chunks and da.ndim >= 1:
            # One chunk spanning the full axis along each dimension is fine for coords
            e['chunks'] = tuple(int(s) for s in da.shape)

        # 0-D scalars (rare for coords) don’t need chunks
        enc[name] = e

    return enc


def write_output(ds_out, outdir, outfile, write_zarr=True):
    outdir.mkdir(parents=True, exist_ok=True)

    if write_zarr:
        outpath = f'{outdir}/{outfile}.zarr'

        encoding = build_zarr_v3_encoding(ds_out)
        delayed = ds_out.to_zarr(
            outpath,
            mode='w',
            encoding=encoding,
            compute=False,
            zarr_version=3,
            consolidated=False,
        )

    else:
        outpath = f'{outdir}/{outfile}.nc'

        encoding = {
            var: {
                'zlib': True,
                'complevel': 3,
                'shuffle': True,
                'dtype': 'float32',
                'chunksizes': (1, 20, 250, 250),
                '_FillValue': np.nan
                }
            for var in ds_out.data_vars
            }
        delayed = ds_out.to_netcdf(outpath,
                                    mode='w',
                                    engine='netcdf4',
                                    encoding=encoding
                                    )

    with ProgressBar():
        dask.compute(delayed)

    return


def main(sim_dir, st=90, et=180, morrison=False):
# def main():
#     morrison=False
#     sim_dir = '/storm/topping/cold_pools/runs/2500_core/dm'

    sim_dir = Path(sim_dir)
    print(f'Simulation directory: {sim_dir}')

    # bbox = [-25.0, 65.0, -15.0, 57.0]  # west, east, south, north (km)
    bbox = [-35.0, 65.0, -15.0, 60.0]

    # st = 90  # start time
    # et = 180  # end time

    ft = 45  # first time after initialization
    ff = 2  # number of first file after initialization
    dt = 1  # large timestep (minutes)
    i1 = int((st - ft) / dt)
    i2 = int((et - ft) / dt)
    sf = i1 + ff
    ef = i2 + ff

    regimes = ['mm','md','dm','dd']

    for regime in regimes:
        print(f'\tRegime: {regime}')
        run_dir = sim_dir / regime / 'run'
        outdir = sim_dir / regime / 'derived_vars'

        initial_file = run_dir / 'cm1out_000001.nc'


        file_list = create_file_list(run_dir, sf, ef)
        drop_vars = get_vars_to_drop(initial_file)

        print('\t\tGetting tracks...')
        track_x, track_y = get_storm_locs(sim_dir / regime, i1, i2)

        # print('Calculating reference density potential temperature...')
        # th_rho0 = calc_reference_th_rho(initial_file, drop_vars, morrison)

        for i, f in enumerate(file_list):
            print(f'\t\tProcessing {f}...')

            outfile = str(f.stem).replace('cm1out', 'derived_vars')

            ds_t = xr.open_dataset(
                    f,
                    engine='h5netcdf',
                    decode_times=False,
                    mask_and_scale=False,
                    decode_coords=False,
                    drop_variables=drop_vars
            )

            th_rho0 = calc_reference_th_rho(ds_t, morrison)

            icx, icy = coords_km_to_indices(ds_t['xh'], ds_t['yh'], track_x[i], track_y[i])
            icy_sub, icx_sub, ds_sub = storm_subset(ds_t, icx, icy, bbox)
            ds_sub = ds_sub.compute()

            ds_t.close()

            ds_new = calculations(th_rho0, (icx_sub, icy_sub), ds_sub, morrison)

            ds_keep = ds_new[FINAL_KEEP]

            print(f'writing to {outfile}')

            write_output(ds_keep, outdir, outfile, write_zarr=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process CM1 outputs and write derived variables.'
    )
    parser.add_argument(
        '--sim_dir',
        type=str,
        required=True,
        help='Path to the simulation directory containing "run"'
    )
    parser.add_argument(
        '--st',
        type=int,
        required=True,
        help='Start time (minutes)'
    )
    parser.add_argument(
        '--et',
        type=int,
        required=True,
        help='End time (minutes)'
    )
    parser.add_argument(
        '--morrison',
        action='store_true',
        help='Morrison microphysics scheme'
    )

    args = parser.parse_args()
    main(args.sim_dir, args.st, args.et, args.morrison)
    # main()