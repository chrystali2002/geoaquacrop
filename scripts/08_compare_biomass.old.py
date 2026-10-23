#!/usr/bin/env python

import pandas as pd
import matplotlib.pyplot as plt

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"
FIG_DIR = "/mnt/scratch/olusegu3/geoaquacrop/figures"

experiments = [
    "control_2015",
    "early_recovery_2015",
    "late_stress_2015",
    "dual_stress_2015"
]

fig, ax = plt.subplots(figsize=(10,6))

for exp in experiments:

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    growth = daily[0]["crop_growth"]

    ax.plot(
        growth["dap"],
        growth["biomass"],
        lw=2,
        label=exp
    )

ax.axvline(
    72,
    color="black",
    ls="--",
    label="Reproductive onset"
)

ax.set_xlabel("Days After Planting (DAP)")
ax.set_ylabel("Biomass")
ax.set_title("Biomass Accumulation")

ax.legend()

plt.tight_layout()

outfile = f"{FIG_DIR}/compare_biomass_2015.png"

plt.savefig(
    outfile,
    dpi=300,
    bbox_inches="tight"
)

print(outfile)
