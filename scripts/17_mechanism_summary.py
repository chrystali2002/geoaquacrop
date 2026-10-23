#!/usr/bin/env python

import pandas as pd
import numpy as np

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

experiments = {
    "Control":
    "control_2015",

    "Early Recovery":
    "early_recovery_2015_v2",

    "Late Stress":
    "late_stress_2015_v5",

    "Dual Stress":
    "dual_stress_2015_v2"
}

rows = []

for label, exp in experiments.items():

    summary = pd.read_pickle(
        f"{BASE}/{exp}/outputs/summary_results.pkl"
    )

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    s = summary[0]

    water = daily[0]["water_flux"].copy()
    growth = daily[0]["crop_growth"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    final_biomass = float(
        growth["biomass"].max()
    )

    final_hi = float(
        growth["harvest_index_adj"].max()
    )

    rows.append({

        "trajectory": label,

        "yield_t_ha":
        round(
            float(
                s["Dry yield (tonne/ha)"].iloc[0]
            ),
            2
        ),

        "yield_potential_t_ha":
        round(
            float(
                s["Yield potential (tonne/ha)"].iloc[0]
            ),
            2
        ),

        "yield_gap_pct":
        round(
            100 *
            (
                1 -
                float(
                    s["Dry yield (tonne/ha)"].iloc[0]
                )
                /
                float(
                    s["Yield potential (tonne/ha)"].iloc[0]
                )
            ),
            1
        ),

        "mean_Wr":
        round(
            water["Wr"].mean(),
            1
        ),

        "mean_Tr_fraction":
        round(
            water["Tr_fraction"].mean(),
            3
        ),

        "seasonal_transpiration_mm":
        round(
            float(
                s["seasonal_transpiration_mm"].iloc[0]
            ),
            1
        ),

        "final_biomass":
        round(
            final_biomass,
            1
        ),

        "max_harvest_index":
        round(
            final_hi,
            3
        )
    })

df = pd.DataFrame(rows)

print("\n")
print("=" * 100)
print("MECHANISTIC SUMMARY")
print("=" * 100)
print(df.to_string(index=False))
