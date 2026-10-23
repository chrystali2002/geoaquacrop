#!/usr/bin/env python
"""
03_growth_stage_diagnostics.py

Growth-stage diagnostics for a county control run, and (new) writes /
updates that county's row in config/phenology.csv, which
21_resilience_metrics.py (and, later, 04_modify_precip.py) read.

Usage
-----
python 03_growth_stage_diagnostics.py [site_id] [--control-dir DIR]

    site_id        row in config/counties.csv (default: story2015)
    --control-dir  folder holding the control run's summary_results.pkl and
                   daily_results.pkl. Default:
                   <root>/experiments/control_<year>/outputs

DAP convention: the model's own `dap` column. Dates written to
phenology.csv are planting_date + DAP days (same convention as the
Story README: DAP 72 -> 2015-07-24, DAP 137 -> 2015-09-27).
"""

import argparse
import os
import re
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(
    os.environ.get(
        "GEOAQUACROP_ROOT",
        "/mnt/scratch/olusegu3/geoaquacrop"
    )
)

CONFIG = ROOT / "config"

parser = argparse.ArgumentParser()
parser.add_argument("site", nargs="?", default="story2015")
parser.add_argument("--control-dir", default=None)
args = parser.parse_args()

SITE = args.site

counties = pd.read_csv(CONFIG / "counties.csv")
match = counties.loc[counties["site_id"] == SITE]

if len(match) != 1:
    sys.exit(f"{SITE} must appear exactly once in {CONFIG / 'counties.csv'}")

YEAR = int(match.iloc[0]["year"])

BASE = (
    Path(args.control_dir)
    if args.control_dir
    else ROOT / "experiments" / f"control_{YEAR}" / "outputs"
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

# --------------------------------
# Phenology metadata -> config/phenology.csv
# --------------------------------

print("\n==============================")
print("PHENOLOGY METADATA")
print("==============================")


def first_hi_dap(cell):
    """First DAP with harvest_index > 0 (reproductive onset)."""
    g = cell["crop_growth"]
    pos = g.loc[g["harvest_index"] > 0, "dap"]
    return int(pos.iloc[0]) if len(pos) else None


onsets = [first_hi_dap(c) for c in daily]

if onsets[0] is None:
    sys.exit(
        "No harvest_index > 0 found in the reference cell; "
        "phenology.csv not updated."
    )

# reference = first cell (same definition as the Story README);
# record whether all cells agree
reproductive_dap = onsets[0]
cells_agree = len(set(onsets)) == 1

if not cells_agree:
    print(
        "WARNING: reproductive onset differs among cells "
        f"(min {min(o for o in onsets if o is not None)}, "
        f"max {max(o for o in onsets if o is not None)}, "
        f"missing {sum(o is None for o in onsets)}); "
        "using cell 0."
    )

def parse_planting(value, year):
    """
    summary_results stores planting_date as text 'MM/DD' with no year
    (e.g. '05/13'); attach the site year from counties.csv. A full date is
    accepted only if its year matches the site year.
    """

    if isinstance(value, str) and re.fullmatch(r"\s*\d{1,2}/\d{1,2}\s*", value):
        month, day = (int(x) for x in value.split("/"))
        return pd.Timestamp(year=year, month=month, day=day)

    ts = pd.to_datetime(value)

    if ts.year != year:
        sys.exit(
            f"planting_date {value!r} parses to year {ts.year}, but "
            f"counties.csv gives {year} for {SITE}."
        )

    return ts


planting = parse_planting(summary0["planting_date"].iloc[0], YEAR)
harvest_dap = int(summary0["season_length_days"].iloc[0])

harvest_model = pd.to_datetime(
    summary0["Harvest Date (YYYY/MM/DD)"].iloc[0]
)

if (harvest_model - planting).days != harvest_dap:
    print(
        "WARNING: season_length_days "
        f"({harvest_dap}) != harvest date - planting date "
        f"({(harvest_model - planting).days}); using season_length_days. "
        "Check the planting_date format (parsed as MM/DD)."
    )

row = {
    "site_id": SITE,
    "planting_date": planting.strftime("%Y-%m-%d"),
    "reproductive_dap": reproductive_dap,
    "harvest_dap": harvest_dap,
    "reproductive_date": (
        planting + pd.Timedelta(days=reproductive_dap)
    ).strftime("%Y-%m-%d"),
    "harvest_date": (
        planting + pd.Timedelta(days=harvest_dap)
    ).strftime("%Y-%m-%d"),
    "cells_agree": cells_agree,
    "source": str(BASE),
}

pheno_file = CONFIG / "phenology.csv"

if pheno_file.exists():
    pheno = pd.read_csv(pheno_file)

    if "site_id" not in pheno.columns:
        sys.exit(
            f"{pheno_file} has no 'site_id' column "
            f"(columns: {list(pheno.columns)}); fix or remove it."
        )

    pheno = pheno.loc[pheno["site_id"] != SITE]
    pheno = pd.concat(
        [pheno, pd.DataFrame([row])],
        ignore_index=True
    )
else:
    CONFIG.mkdir(parents=True, exist_ok=True)
    pheno = pd.DataFrame([row])

pheno = pheno.sort_values("site_id")

# DAP columns as integers (not 72.0) when written
for c in ("reproductive_dap", "harvest_dap"):
    pheno[c] = pheno[c].astype("Int64")

# canonical column order first; keep any extra columns at the end
canonical = list(row.keys())
pheno = pheno[
    canonical + [c for c in pheno.columns if c not in canonical]
]

pheno.to_csv(
    pheno_file,
    index=False
)

for k, v in row.items():
    print(f"{k}: {v}")

print(f"\nWrote {pheno_file}")

print("\nDone.")
