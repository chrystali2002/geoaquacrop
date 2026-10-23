#!/usr/bin/env python

import pandas as pd
import numpy as np

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

experiments = [
    "control_2015",
    "early_recovery_2015_v1",
    "late_stress_2015_v2",
    "dual_stress_2015_v1"
]

target_daps = [60, 72, 90, 110, 130]

print("\n")
print("=" * 80)
print("SUMMARY DIAGNOSTICS")
print("=" * 80)

all_rows = []

for exp in experiments:

    summary = pd.read_pickle(
        f"{BASE}/{exp}/outputs/summary_results.pkl"
    )

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

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

    yield_gap_pct = (
        100.0 *
        (
            1.0 -
            yield_actual / yield_potential
        )
    )

    all_rows.append({

        "experiment": exp,

        "yield_t_ha": round(
            yield_actual,
            2
        ),

        "yield_potential_t_ha": round(
            yield_potential,
            2
        ),

        "yield_gap_pct": round(
            yield_gap_pct,
            1
        ),

        "seasonal_precip_mm": round(
            float(
                s["seasonal_precip_mm"].iloc[0]
            ),
            1
        ),

        "seasonal_transpiration_mm": round(
            float(
                s["seasonal_transpiration_mm"].iloc[0]
            ),
            1
        ),

        "wp_et_kg_per_m3": round(
            float(
                s["wp_et_kg_per_m3"].iloc[0]
            ),
            3
        )
    })

summary_df = pd.DataFrame(all_rows)

print("\n")
print(summary_df)

# ==================================================
# ROOT-ZONE WATER AND TRANSPIRATION CHECKPOINTS
# ==================================================

print("\n")
print("=" * 80)
print("ROOT-ZONE WATER AND TRANSPIRATION CHECKPOINTS")
print("=" * 80)

for exp in experiments:

    print("\n")
    print("-" * 40)
    print(exp)
    print("-" * 40)

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    subset = water.loc[
        water["dap"].isin(target_daps),
        [
            "dap",
            "Wr",
            "Tr",
            "TrPot",
            "Tr_fraction"
        ]
    ]

    print(subset.round(3))

# ==================================================
# MEAN PROCESS METRICS
# ==================================================

print("\n")
print("=" * 80)
print("MEAN PROCESS METRICS")
print("=" * 80)

for exp in experiments:

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    print("\n")
    print(exp)

    print(
        "Mean Wr:",
        round(
            water["Wr"].mean(),
            2
        )
    )

    print(
        "Mean Tr:",
        round(
            water["Tr"].mean(),
            2
        )
    )

    print(
        "Mean Tr/TrPot:",
        round(
            water["Tr_fraction"].mean(),
            3
        )
    )

# ==================================================
# RECOVERY RELATIVE TO CONTROL
# ==================================================

control_yield = summary_df.loc[
    summary_df["experiment"] == experiments[0],
    "yield_t_ha"
].iloc[0]

summary_df["yield_pct_of_control"] = (
    summary_df["yield_t_ha"] /
    control_yield
) * 100

print("\n")
print("=" * 80)
print("YIELD RELATIVE TO CONTROL")
print("=" * 80)

print(
    summary_df[
        [
            "experiment",
            "yield_t_ha",
            "yield_pct_of_control"
        ]
    ].round(1)
)
