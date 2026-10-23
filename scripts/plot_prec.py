import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

ppt = xr.open_dataset(
    "/mnt/scratch/olusegu3/geoaquacrop/story2012/processed/Precipitation20122012.nc"
)

ppt_mean = (
    ppt["Precipitation"]
    .mean(dim=["y", "x"], skipna=True)
    .to_pandas()
)

fig, ax = plt.subplots(figsize=(12,5))

ppt_mean.plot(ax=ax)

ax.set_title(
    "Story County Mean Daily Precipitation (2012)"
)

ax.set_ylabel("Precipitation (mm/day)")
ax.set_xlabel("Date")

plt.tight_layout()

outfile = (
    "/mnt/scratch/olusegu3/geoaquacrop/story2012/outputs/"
    "precipitation_2012.png"
)

plt.savefig(outfile, dpi=300)

print(outfile)

