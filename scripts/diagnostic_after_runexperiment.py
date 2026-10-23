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

    row = {
        "experiment": exp,
        "yield_t_ha": float(
            s["Dry yield (tonne/ha)"].iloc[0]
        ),
        "yield_potential_t_ha": float(
            s["Yield potential (tonne/ha)"].iloc[0]
        ),
        "seasonal_precip_mm": float(
            s["seasonal_precip_mm"].iloc[0]
        ),
        "seasonal_et_mm": float(
            s["seasonal_et_mm"].iloc[0]
        ),
        "seasonal_transpiration_mm": float(
            s["seasonal_transpiration_mm"].iloc[0]
        ),
        "water_productivity": float(
            s["wp_et_kg_per_m3"].iloc[0]
        ),
        "rainfall_use_efficiency": float(
            s["rainfall_use_efficiency_kg_per_m3"].iloc[0]
        )
    }

    rows.append(row)

df = pd.DataFrame(rows)

print("\n==============================")
print("SUMMARY COMPARISON")
print("==============================\n")

print(df)

# ---------------------------------------------------
# Yield recovery relative to control
# ---------------------------------------------------

control_yield = df.loc[
    df["experiment"] == "control",
    "yield_t_ha"
].iloc[0]

df["yield_pct_of_control"] = (
    df["yield_t_ha"] /
    control_yield
) * 100

print("\n==============================")
print("YIELD RELATIVE TO CONTROL")
print("==============================\n")

print(
    df[
        [
            "experiment",
            "yield_t_ha",
            "yield_pct_of_control"
        ]
    ]
)
