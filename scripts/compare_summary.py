# compare_summary.py

import pandas as pd

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

experiments = [
    "control",
    "early_recovery",
    "late_stress",
    "dual_stress"
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

        "wp_et_kg_per_m3":
        float(
            s["wp_et_kg_per_m3"].iloc[0]
        )
    })

df = pd.DataFrame(rows)

print(df)

