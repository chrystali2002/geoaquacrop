#Build the precipitation modifier 50% precipitation reduction
#during vegetative period only


#python modify_precip.py early_recovery
#This will create:50% rainfall reduction
#during vegetative growth only
#which corresponds to:Early stress
#+
#Recovery before reproductive growth and is directly analogous to the early-recovery trajectory in your manuscript.
#python modify_precip.py late_stress
#python modify_precip.py dual_stress

#!/usr/bin/env python

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

REDUCTION_FACTOR = 0.50

experiment = sys.argv[1]

BASE = (
    "/mnt/scratch/olusegu3/geoaquacrop/"
    f"experiments/{experiment}/processed"
)

infile = (
    f"{BASE}/Precipitation20122012.nc"
)

# --------------------------------------------------
# LOAD
# --------------------------------------------------

ppt = xr.open_dataset(infile)

# load into memory and release file lock
ppt.load()
ppt.close()

ppt_mod = ppt.copy()

# --------------------------------------------------
# CROP CALENDAR
# --------------------------------------------------

planting = pd.Timestamp("2012-05-13")

# harvest index begins >0 at DAP = 72
reproductive_start = planting + pd.Timedelta(days=72)

# harvest at DAP = 137
harvest = planting + pd.Timedelta(days=137)

print("\n===================================")
print("Experiment:", experiment)
print("Planting:", planting.date())
print("Reproductive onset:", reproductive_start.date())
print("Harvest:", harvest.date())
print("Reduction factor:", REDUCTION_FACTOR)
print("===================================\n")

# --------------------------------------------------
# BUILD MASKS
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
# APPLY TREATMENT
# --------------------------------------------------

if experiment == "early_recovery":

    mask = veg_mask

elif experiment == "late_stress":

    mask = rep_mask

elif experiment == "dual_stress":

    mask = veg_mask | rep_mask

else:

    raise ValueError(
        f"Unknown experiment: {experiment}"
    )

# rainfall before modification
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

# rainfall after modification
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

# --------------------------------------------------
# WRITE
# --------------------------------------------------

tmpfile = infile.replace(
    ".nc",
    "_modified.nc"
)

ppt_mod.to_netcdf(tmpfile)

# replace original
Path(tmpfile).replace(infile)

print(
    f"\nUpdated file:\n{infile}"
)









