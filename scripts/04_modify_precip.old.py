#python 04_modify_precip.py early_recovery_2015
#python 04_modify_precip.py late_stress_2015
#python 04_modify_precip.py dual_stress_2015


#!/usr/bin/env python

import sys
from pathlib import Path

import pandas as pd
import xarray as xr

REDUCTION_FACTOR = 0.15  #50% rainfall reduction is 0.5 but85% reduction is 0.15

experiment = sys.argv[1]

BASE = (
    "/mnt/scratch/olusegu3/geoaquacrop/"
    f"experiments/{experiment}/processed"
)

infile = (
    f"{BASE}/Precipitation20152015.nc"
)

ppt = xr.open_dataset(infile)

ppt.load()
ppt.close()

ppt_mod = ppt.copy()

# --------------------------------------------------
# Crop calendar derived from diagnostics
# --------------------------------------------------

planting = pd.Timestamp("2015-05-13")

reproductive_start = planting + pd.Timedelta(days=72)

harvest = planting + pd.Timedelta(days=137)

print("\n===================================")
print("Experiment:", experiment)
print("Planting:", planting.date())
print("Reproductive onset:", reproductive_start.date())
print("Harvest:", harvest.date())
print("Reduction factor:", REDUCTION_FACTOR)
print("===================================\n")

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
# Apply treatment
# --------------------------------------------------

if "early_recovery" in experiment:

    mask = veg_mask

elif "late_stress" in experiment:

    mask = rep_mask

elif "dual_stress" in experiment:

    mask = veg_mask | rep_mask

else:

    raise ValueError(
        f"Unknown experiment: {experiment}"
    )

before = (
    ppt_mod["Precipitation"]
    .mean(dim=["y", "x"], skipna=True)
)

before_total = float(
    before.where(mask).sum()
)

ppt_mod["Precipitation"] = xr.where(
    mask,
    ppt_mod["Precipitation"] * REDUCTION_FACTOR,
    ppt_mod["Precipitation"]
)

after = (
    ppt_mod["Precipitation"]
    .mean(dim=["y", "x"], skipna=True)
)

after_total = float(
    after.where(mask).sum()
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

tmpfile = infile.replace(
    ".nc",
    "_modified.nc"
)

ppt_mod.to_netcdf(tmpfile)

Path(tmpfile).replace(infile)

print(
    f"\nUpdated:\n{infile}"
)
