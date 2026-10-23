#!/usr/bin/env python

import xarray as xr

late = xr.open_dataset(
    "/mnt/scratch/olusegu3/geoaquacrop/experiments/"
    "late_stress_2015_v5/processed/"
    "Precipitation20152015.nc"
)

dual = xr.open_dataset(
    "/mnt/scratch/olusegu3/geoaquacrop/experiments/"
    "dual_stress_2015_v4/processed/"
    "Precipitation20152015.nc"
)

print(
    "Identical precipitation:",
    late["Precipitation"].equals(
        dual["Precipitation"]
    )
)

diff = (
    late["Precipitation"]
    -
    dual["Precipitation"]
)

print(
    "Maximum absolute difference:",
    float(abs(diff).max())
)
