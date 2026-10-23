#!/usr/bin/env python

# Purpose:
# Compare v1-v5 side-by-side for a given trajectory.
#
# Examples:
# python 13_compare_versions.py late_stress
# python 13_compare_versions.py early_recovery
# python 13_compare_versions.py dual_stress

import sys
from pathlib import Path

import pandas as pd
import numpy as np

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

trajectory = sys.argv[1]

versions = ["v1", "v2", "v3", "v4", "v5"]

rows = []

for v in versions:

    exp = f"{trajectory}_2015_{v}"

    summary_file = Path(
        f"{BASE}/{exp}/outputs/summary_results.pkl"
    )

    daily_file = Path(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    if not summary_file.exists():

        print(
            f"Skipping {exp} "
            f"(summary_results.pkl not found)"
        )

        continue

    if not daily_file.exists():

        print(
            f"Skipping {exp} "
            f"(daily_results.pkl not found)"
        )

        continue

    summary = pd.read_pickle(summary_file)

    daily = pd.read_pickle(daily_file)

    s = summary[0]

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    yield_actual = float(
        s["Dry yield (tonne/ha)"].iloc[0]
    )

    yield_potential = float(
        s["Yield potential (tonne/ha)"].iloc[0]
    )

    rows.append({

        "version": v,

        "yield_t_ha":
        round(yield_actual, 2),

        "yield_potential_t_ha":
        round(yield_potential, 2),

        "yield_gap_pct":
        round(
            100 *
            (
                1 -
                yield_actual / yield_potential
            ),
            1
        ),

        "seasonal_precip_mm":
        round(
            float(
                s["seasonal_precip_mm"].iloc[0]
            ),
            1
        ),

        "seasonal_transpiration_mm":
        round(
            float(
                s["seasonal_transpiration_mm"].iloc[0]
            ),
            1
        ),

        "mean_Wr":
        round(
            float(
                water["Wr"].mean()
            ),
            1
        ),

        "mean_Tr_fraction":
        round(
            float(
                water["Tr_fraction"].mean()
            ),
            3
        ),

        "wp_et_kg_per_m3":
        round(
            float(
                s["wp_et_kg_per_m3"].iloc[0]
            ),
            3
        )
    })

df = pd.DataFrame(rows)

print("\n")
print("=" * 90)
print(f"{trajectory.upper()} VERSION COMPARISON")
print("=" * 90)

print(df.to_string(index=False))










