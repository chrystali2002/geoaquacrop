#This is the first figure that can directly address your manuscript question:

#Why does recovery appear under a soil-moisture perspective?

#because it lets you evaluate:


#Wr recovers
#↓
#Tr/TrPot recovers
#↓
#Biomass recovers
#↓
#Yield largely recovers

#for the Early Recovery treatment relative to Late Stress and Dual Stress.

#!/usr/bin/env python

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"
FIG_DIR = "/mnt/scratch/olusegu3/geoaquacrop/figures"

# --------------------------------------------------
# Candidate experiment set
# --------------------------------------------------

experiments = {
    "Control":
    "control_2015",

    "Early Recovery":
    "early_recovery_2015_v2",

    "Late Stress":
    "late_stress_2015_v3",

    "Dual Stress":
    "dual_stress_2015_v2"
}

colors = {
    "Control": "black",
    "Early Recovery": "orange",
    "Late Stress": "green",
    "Dual Stress": "red"
}

# --------------------------------------------------
# Multi-panel figure
# --------------------------------------------------

fig, axes = plt.subplots(
    2,
    2,
    figsize=(14,10)
)

# ==================================================
# PANEL A
# Root-zone Water
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
# PANEL B
# Transpiration Fraction
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
ax.set_ylabel("Tr / TrPot")

# ==================================================
# PANEL C
# Biomass
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
# PANEL D
# Yield
# ==================================================

ax = axes[1,1]

yields = []

labels = []

for label, exp in experiments.items():

    summary = pd.read_pickle(
        f"{BASE}/{exp}/outputs/summary_results.pkl"
    )

    s = summary[0]

    yields.append(
        float(
            s["Dry yield (tonne/ha)"].iloc[0]
        )
    )

    labels.append(label)

ax.bar(
    labels,
    yields,
    color=[colors[x] for x in labels]
)

ax.set_title("D. Final Yield")
ax.set_ylabel("Yield (t ha⁻¹)")

for i, y in enumerate(yields):

    ax.text(
        i,
        y,
        f"{y:.2f}",
        ha="center",
        va="bottom"
    )

# ==================================================

plt.tight_layout()

outfile = (
    f"{FIG_DIR}/compare_trajectories.png"
)

plt.savefig(
    outfile,
    dpi=300,
    bbox_inches="tight"
)

print(f"\nSaved:\n{outfile}")
