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
    "late_stress_2015_v3",

    "Dual Stress":
    "dual_stress_2015_v5"
}

colors = {
    "Control": "black",
    "Early Recovery": "orange",
    "Late Stress": "green",
    "Dual Stress": "red"
}

fig, axes = plt.subplots(
    2,
    2,
    figsize=(14,10)
)

# ==================================================
# A. Root-zone Water
# ==================================================

ax = axes[0,0]

for label, exp in experiments.items():

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    water = daily[0]["water_flux"]

    ax.plot(
        water["dap"],
        water["Wr"],
        lw=2,
        label=label,
        color=colors[label]
    )

ax.axvline(
    72,
    color="black",
    ls="--"
)

ax.set_title("A. Root-zone Water")
ax.set_xlabel("DAP")
ax.set_ylabel("Wr (mm)")
ax.legend()

# ==================================================
# B. Transpiration Fraction
# ==================================================

ax = axes[0,1]

for label, exp in experiments.items():

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    ax.plot(
        water["dap"],
        water["Tr_fraction"],
        lw=2,
        label=label,
        color=colors[label]
    )

ax.axvline(
    72,
    color="black",
    ls="--"
)

ax.set_title("B. Transpiration Fraction")
ax.set_xlabel("DAP")
ax.set_ylabel("Tr/TrPot")

# ==================================================
# C. Biomass
# ==================================================

ax = axes[1,0]

for label, exp in experiments.items():

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    growth = daily[0]["crop_growth"]

    ax.plot(
        growth["dap"],
        growth["biomass"],
        lw=2,
        label=label,
        color=colors[label]
    )

ax.axvline(
    72,
    color="black",
    ls="--"
)

ax.set_title("C. Biomass")
ax.set_xlabel("DAP")
ax.set_ylabel("Biomass")

# ==================================================
# D. Yield
# ==================================================

ax = axes[1,1]

labels = []
yields = []

for label, exp in experiments.items():

    summary = pd.read_pickle(
        f"{BASE}/{exp}/outputs/summary_results.pkl"
    )

    s = summary[0]

    labels.append(label)

    yields.append(
        float(
            s["Dry yield (tonne/ha)"].iloc[0]
        )
    )

ax.bar(
    labels,
    yields,
    color=[colors[x] for x in labels]
)

for i, y in enumerate(yields):

    ax.text(
        i,
        y,
        f"{y:.2f}",
        ha="center"
    )

ax.set_title("D. Final Yield")
ax.set_ylabel("Yield (t ha⁻¹)")

plt.tight_layout()

outfile = (
    f"{FIG_DIR}/compare_trajectories_best.png"
)

plt.savefig(
    outfile,
    dpi=300,
    bbox_inches="tight"
)

print(outfile)
