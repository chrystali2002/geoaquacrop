#!/usr/bin/env python

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"
FIG_DIR = "/mnt/scratch/olusegu3/geoaquacrop/figures"

experiments = {
    "Control":
    "control_2015",

    "Early Recovery":
    "early_recovery_2015_v2",

    "Late Stress":
    "late_stress_2015_v5",

    "Dual Stress":
    "dual_stress_2015_v4"
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

    rows.append({

        "Trajectory": label,

        "Mean Wr":
        water["Wr"].mean(),

        "Mean Tr/TrPot":
        water["Tr_fraction"].mean(),

        "Final Biomass":
        growth["biomass"].max(),

        "Harvest Index":
        growth["harvest_index_adj"].max(),

        "Yield":
        float(
            s["Dry yield (tonne/ha)"].iloc[0]
        )
    })

df = pd.DataFrame(rows)

# ---------------------------------------------
# Normalize to Control
# ---------------------------------------------

for col in [
    "Mean Wr",
    "Mean Tr/TrPot",
    "Final Biomass",
    "Harvest Index",
    "Yield"
]:

    control = (
        df.loc[
            df["Trajectory"] == "Control",
            col
        ]
        .iloc[0]
    )

    df[col] = 100 * df[col] / control

# ---------------------------------------------
# Plot
# ---------------------------------------------

fig, ax = plt.subplots(
    figsize=(12,6)
)

xlabels = [
    "Root Zone\nWater",
    "Transpiration",
    "Biomass",
    "Harvest\nIndex",
    "Yield"
]

for _, row in df.iterrows():

    ax.plot(
        xlabels,
        [
            row["Mean Wr"],
            row["Mean Tr/TrPot"],
            row["Final Biomass"],
            row["Harvest Index"],
            row["Yield"]
        ],
        lw=2,
        marker="o",
        label=row["Trajectory"]
    )

ax.axhline(
    100,
    color="black",
    ls="--"
)

ax.set_ylabel(
    "% of Control"
)

ax.set_title(
    "Mechanistic Pathway from Water Availability to Yield"
)

ax.legend()

plt.tight_layout()

outfile = (
    f"{FIG_DIR}/mechanistic_pathway_2015.png"
)

plt.savefig(
    outfile,
    dpi=300,
    bbox_inches="tight"
)

print(outfile)

