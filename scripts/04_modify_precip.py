#!/usr/bin/env python
#before running ensure 
#cp -r \
#/mnt/scratch/olusegu3/geoaquacrop/story2015/processed \
#/mnt/scratch/olusegu3/geoaquacrop/experiments/early_recovery_2015_v1/processed/

#cp -r \
#/mnt/scratch/olusegu3/geoaquacrop/story2015/processed \
#/mnt/scratch/olusegu3/geoaquacrop/experiments/late_stress_2015_v1/processed/

#cp -r \
#/mnt/scratch/olusegu3/geoaquacrop/story2015/processed \
#/mnt/scratch/olusegu3/geoaquacrop/experiments/dual_stress_2015_v1/processed/

# Examples:
# python 04_modify_precip.py early_recovery_2015_v1
# python 04_modify_precip.py late_stress_2015_v2
# python 04_modify_precip.py dual_stress_2015_v3

import sys
from pathlib import Path

import pandas as pd
import xarray as xr

# --------------------------------------------------
# Experiment
# --------------------------------------------------

experiment = sys.argv[1]

BASE = (
    "/mnt/scratch/olusegu3/geoaquacrop/"
    f"experiments/{experiment}/processed"
)

infile = (
    f"{BASE}/Precipitation20152015.nc"
)

# --------------------------------------------------
# Read precipitation
# --------------------------------------------------

ppt = xr.open_dataset(infile)

ppt.load()
ppt.close()

ppt_mod = ppt.copy()

# --------------------------------------------------
# Crop calendar derived from diagnostics
# --------------------------------------------------

planting = pd.Timestamp("2015-05-13")

reproductive_start = (
    planting + pd.Timedelta(days=72)
)

harvest = (
    planting + pd.Timedelta(days=137)
)

print("\n===================================")
print("Experiment:", experiment)
print("Planting:", planting.date())
print("Reproductive onset:",
      reproductive_start.date())
print("Harvest:", harvest.date())
print("===================================\n")

# --------------------------------------------------
# Drought windows
# --------------------------------------------------

veg_mask = (
    (ppt_mod.time >= planting)
    &
    (ppt_mod.time < reproductive_start)
)

rep_mask = (
    (ppt_mod.time >= reproductive_start)
    &
    (ppt_mod.time <= harvest)
)

# --------------------------------------------------
# Save baseline rainfall totals
# --------------------------------------------------

before = (
    ppt["Precipitation"]
    .mean(dim=["y", "x"], skipna=True)
)

# --------------------------------------------------
# APPLY TREATMENTS
# --------------------------------------------------

# ==============================
# EARLY RECOVERY
# ==============================

if experiment == "early_recovery_2015_v1":

    # 50% reduction
    diag_mask = veg_mask

    ppt_mod["Precipitation"] = xr.where(
        veg_mask,
        ppt_mod["Precipitation"] * 0.50,
        ppt_mod["Precipitation"]
    )

elif experiment == "early_recovery_2015_v2":

    # 85% reduction
    diag_mask = veg_mask

    ppt_mod["Precipitation"] = xr.where(
        veg_mask,
        ppt_mod["Precipitation"] * 0.15,
        ppt_mod["Precipitation"]
    )

elif experiment == "early_recovery_2015_v3":

    # 100% removal
    diag_mask = veg_mask

    ppt_mod["Precipitation"] = xr.where(
        veg_mask,
        0.0,
        ppt_mod["Precipitation"]
    )

# ==============================
# LATE STRESS
# ==============================

elif experiment == "late_stress_2015_v1":

    # 50% reduction
    diag_mask = rep_mask

    ppt_mod["Precipitation"] = xr.where(
        rep_mask,
        ppt_mod["Precipitation"] * 0.50,
        ppt_mod["Precipitation"]
    )

elif experiment == "late_stress_2015_v2":

    # 100% removal in reproductive period
    diag_mask = rep_mask

    ppt_mod["Precipitation"] = xr.where(
        rep_mask,
        0.0,
        ppt_mod["Precipitation"]
    )

elif experiment == "late_stress_2015_v3":

    # Reduce vegetative water
    ppt_mod["Precipitation"] = xr.where(
        veg_mask,
        ppt_mod["Precipitation"] * 0.50,
        ppt_mod["Precipitation"]
    )

    # Remove reproductive rainfall
    ppt_mod["Precipitation"] = xr.where(
        rep_mask,
        0.0,
        ppt_mod["Precipitation"]
    )

    diag_mask = veg_mask | rep_mask

# ==============================
# LATE STRESS v4
# ==============================

elif experiment == "late_stress_2015_v4":

    # moderate reduction before reproductive onset
    ppt_mod["Precipitation"] = xr.where(
        veg_mask,
        ppt_mod["Precipitation"] * 0.50,
        ppt_mod["Precipitation"]
    )

    # remove all reproductive rainfall
    ppt_mod["Precipitation"] = xr.where(
        rep_mask,
        0.0,
        ppt_mod["Precipitation"]
    )

    diag_mask = veg_mask | rep_mask

# ==============================
# LATE STRESS v5
# ==============================

elif experiment == "late_stress_2015_v5":

    # stronger antecedent drying
    ppt_mod["Precipitation"] = xr.where(
        veg_mask,
        ppt_mod["Precipitation"] * 0.25,
        ppt_mod["Precipitation"]
    )

    # no rainfall during reproductive period
    ppt_mod["Precipitation"] = xr.where(
        rep_mask,
        0.0,
        ppt_mod["Precipitation"]
    )

    diag_mask = veg_mask | rep_mask

# ==============================
# DUAL STRESS
# ==============================

elif experiment == "dual_stress_2015_v1":

    diag_mask = veg_mask | rep_mask

    ppt_mod["Precipitation"] = xr.where(
        veg_mask | rep_mask,
        ppt_mod["Precipitation"] * 0.50,
        ppt_mod["Precipitation"]
    )

elif experiment == "dual_stress_2015_v2":

    diag_mask = veg_mask | rep_mask

    ppt_mod["Precipitation"] = xr.where(
        veg_mask | rep_mask,
        ppt_mod["Precipitation"] * 0.15,
        ppt_mod["Precipitation"]
    )

elif experiment == "dual_stress_2015_v3":

    diag_mask = veg_mask | rep_mask

    ppt_mod["Precipitation"] = xr.where(
        veg_mask | rep_mask,
        0.0,
        ppt_mod["Precipitation"]
    )

# ==============================
# DUAL STRESS v4
# ==============================

elif experiment == "dual_stress_2015_v4":

    # Reduce vegetative rainfall by 75%
    ppt_mod["Precipitation"] = xr.where(
        veg_mask,
        ppt_mod["Precipitation"] * 0.25,
        ppt_mod["Precipitation"]
    )

    # Remove all reproductive rainfall
    ppt_mod["Precipitation"] = xr.where(
        rep_mask,
        0.0,
        ppt_mod["Precipitation"]
    )

    diag_mask = veg_mask | rep_mask



# ==============================
# DUAL STRESS v5
# ==============================
elif experiment == "dual_stress_2015_v5":

    ppt_mod["Precipitation"] = (
        ppt_mod["Precipitation"] * 0.0
    )

    diag_mask = (
        veg_mask | rep_mask
    )

else:

    raise ValueError(
        f"Unknown experiment: {experiment}"
    )

# --------------------------------------------------
# Diagnostics
# --------------------------------------------------

after = (
    ppt_mod["Precipitation"]
    .mean(dim=["y", "x"], skipna=True)
)

before_total = float(
    before.where(diag_mask).sum()
)

after_total = float(
    after.where(diag_mask).sum()
)

removed = before_total - after_total

print(
    f"Rainfall before: {before_total:.2f} mm"
)

print(
    f"Rainfall after : {after_total:.2f} mm"
)

print(
    f"Removed        : {removed:.2f} mm"
)

# --------------------------------------------------
# Write modified NetCDF
# --------------------------------------------------

tmpfile = infile.replace(
    ".nc",
    "_modified.nc"
)

ppt_mod.to_netcdf(tmpfile)

Path(tmpfile).replace(infile)

print(
    f"\nUpdated:\n{infile}"
)
