#!/usr/bin/env python

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = (
    "/mnt/scratch/olusegu3/geoaquacrop/"
    "experiments/control_2015/outputs"
)

summary = pd.read_pickle(
    f"{BASE}/summary_results.pkl"
)

daily = pd.read_pickle(
    f"{BASE}/daily_results.pkl"
)

summary0 = summary[0]

water = daily[0]["water_flux"].copy()
growth = daily[0]["crop_growth"].copy()

water["Tr_fraction"] = np.where(
    water["TrPot"] > 0,
    water["Tr"] / water["TrPot"],
    np.nan
)

print("\n==============================")
print("CROP CALENDAR")
print("==============================")

print(
    "Planting date:",
    summary0["planting_date"].iloc[0]
)

print(
    "Season length:",
    summary0["season_length_days"].iloc[0]
)

print("\n==============================")
print("PEAK CANOPY")
print("==============================")

print(
    growth.loc[
        growth["canopy_cover"].idxmax()
    ]
)

print("\n==============================")
print("REPRODUCTIVE ONSET")
print("==============================")

print(
    growth[growth["harvest_index"] > 0]
    .head(1)
)

print("\n==============================")
print("MAXIMUM TRANSPIRATION")
print("==============================")

print(
    water.loc[
        water["Tr"].idxmax()
    ]
)

print("\n==============================")
print("MINIMUM Tr/TrPot")
print("==============================")

print(
    water.loc[
        water["Tr_fraction"].idxmin()
    ]
)

# --------------------------------
# Figure 1 Canopy Cover
# --------------------------------

fig, ax = plt.subplots(figsize=(10,5))

ax.plot(
    growth["dap"],
    growth["canopy_cover"],
    lw=2
)

ax.set_title("Canopy Cover")

plt.tight_layout()

plt.savefig(
    f"{BASE}/fig01_canopy_cover.png",
    dpi=300
)

# --------------------------------
# Figure 2 Harvest Index
# --------------------------------

fig, ax = plt.subplots(figsize=(10,5))

ax.plot(
    growth["dap"],
    growth["harvest_index"],
    lw=2
)

ax.set_title("Harvest Index")

plt.tight_layout()

plt.savefig(
    f"{BASE}/fig02_harvest_index.png",
    dpi=300
)

# --------------------------------
# Figure 3 Root-zone Water
# --------------------------------

fig, ax = plt.subplots(figsize=(10,5))

ax.plot(
    water["dap"],
    water["Wr"],
    lw=2
)

ax.set_title("Root-zone Water")

plt.tight_layout()

plt.savefig(
    f"{BASE}/fig03_root_zone_water.png",
    dpi=300
)

# --------------------------------
# Figure 4 Tr/TrPot
# --------------------------------

fig, ax = plt.subplots(figsize=(10,5))

ax.plot(
    water["dap"],
    water["Tr_fraction"],
    lw=2
)

ax.set_title("Transpiration Fraction")

plt.tight_layout()

plt.savefig(
    f"{BASE}/fig04_tr_fraction.png",
    dpi=300
)

print("\nDone.")
