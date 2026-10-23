#!/usr/bin/env python




#python 06_compare_summary.py v1 > results/summary_v1.txt

#python 06_compare_summary.py v2 > results/summary_v2.txt

#python 06_compare_summary.py v3 > results/summary_v3.txt

import sys
import pandas as pd

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

version = sys.argv[1]

experiments = [
    "control_2015",
    f"early_recovery_2015_{version}",
    f"late_stress_2015_{version}",
    f"dual_stress_2015_{version}",
]

rows = []

for exp in experiments:

    summary = pd.read_pickle(
        f"{BASE}/{exp}/outputs/summary_results.pkl"
    )

    s = summary[0]

    rows.append({

        "experiment": exp,

        "yield_t_ha":
        float(
            s["Dry yield (tonne/ha)"].iloc[0]
        ),

        "yield_potential_t_ha":
        float(
            s["Yield potential (tonne/ha)"].iloc[0]
        ),

        "seasonal_precip_mm":
        float(
            s["seasonal_precip_mm"].iloc[0]
        ),

        "seasonal_transpiration_mm":
        float(
            s["seasonal_transpiration_mm"].iloc[0]
        ),

        "water_productivity":
        float(
            s["wp_et_kg_per_m3"].iloc[0]
        )
    })

df = pd.DataFrame(rows)

# Yield gap

df["yield_gap_pct"] = (
    100 *
    (
        1 -
        df["yield_t_ha"] /
        df["yield_potential_t_ha"]
    )
)

print("\n==============================")
print(f"SUMMARY ({version})")
print("==============================\n")

print(df.round(3))
