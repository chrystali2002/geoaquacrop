"""
check_esi_time_bounds.py
Settle whether the SPoRT/SERVIR 4-week ESI time stamp is the START, CENTRE or END of the
4-week composite, by reading `time` and `time_bnds` from the NetCDF aggregation.

    python check_esi_time_bounds.py

Needs: xarray, netCDF4 (OPeNDAP support), requests.
If the HPC cannot reach the host, run the same script on a laptop with internet access.

Host and dataset path come from the file's own metadata (cdmremote CDL):
  https://threddsx.servirglobal.net/thredds/cdmremote/Agg/sport-esi_global_0.05deg_4wk.nc4
The OPeNDAP address below is the standard THREDDS equivalent and is UNVERIFIED; the script
tries a few variants and prints what it finds.
"""
import sys

import numpy as np
import requests

HOST = "https://threddsx.servirglobal.net/thredds"
CDL = f"{HOST}/cdmremote/Agg/sport-esi_global_0.05deg_4wk.nc4?req=cdl"
CANDIDATES = [
    f"{HOST}/dodsC/Agg/sport-esi_global_0.05deg_4wk.nc4",
    f"{HOST}/dodsC/Agg/sport-esi_global_0.05deg_4wk.nc",
]

print("1. Reachability")
for url in (f"{HOST}/catalog.html", CDL):
    try:
        r = requests.get(url, timeout=30)
        print(f"   {r.status_code}  {url}")
    except Exception as exc:
        print(f"   FAILED  {url}\n           {exc}")
        print("   -> Host not reachable from here. Run this script on a machine with internet access.")
        sys.exit(1)

print("\n2. Open via OPeNDAP")
ds = None
for url in CANDIDATES:
    try:
        import xarray as xr
        ds = xr.open_dataset(url)
        print(f"   opened {url}")
        break
    except Exception as exc:
        print(f"   could not open {url}\n      {str(exc)[:200]}")
if ds is None:
    print("   -> Open the THREDDS catalog page in a browser (HOST/catalog.html), find the dataset's")
    print("      OPeNDAP access URL, and put it in CANDIDATES.")
    sys.exit(1)

print("\n3. time vs time_bnds")
print("   variables:", list(ds.variables))
if "time_bnds" not in ds.variables:
    print("   no time_bnds in this file; check the attributes below.")
    print(ds.attrs)
    sys.exit(1)

t = ds["time"].values[-6:]
b = ds["time_bnds"].values[-6:]
for ti, bi in zip(t, b):
    print(f"   time {str(ti)[:10]}   bounds {str(bi[0])[:10]} -> {str(bi[1])[:10]}")

same_start = np.all(t == b[:, 0])
same_end = np.all(t == b[:, 1])
mid = np.all(np.abs((b[:, 0] + (b[:, 1] - b[:, 0]) / 2) - t) < np.timedelta64(2, "D"))
span_days = (b[:, 1] - b[:, 0]).astype("timedelta64[D]").astype(int)
print(f"\n   bounds span (days): {sorted(set(span_days))}")
if same_end:
    print("   RESULT: time stamp = END of the composite -> use --center-offset 14 (centre = stamp - 14 d)")
elif same_start:
    print("   RESULT: time stamp = START of the composite -> use --center-offset -14 (centre = stamp + 14 d)")
elif mid:
    print("   RESULT: time stamp = CENTRE of the composite -> use --center-offset 0")
else:
    print("   RESULT: no simple match; inspect the printed values.")
print("\nNote: GeoTIFF file DOY and the NetCDF time stamp are assumed to be the same date convention; "
      "confirm by matching one GeoTIFF date to a NetCDF time value if the dates overlap.")
