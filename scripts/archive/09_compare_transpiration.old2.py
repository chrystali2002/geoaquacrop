#!/usr/bin/env python


#python 09_compare_transpiration.py v1
#python 09_compare_transpiration.py v2
#python 09_compare_transpiration.py v3

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"
FIG_DIR = "/mnt/scratch/olusegu3/geoaquacrop/figures"


version = sys.argv[1]

experiments = [
    "control_2015",
    f"early_recovery_2015_{version}",
    f"late_stress_2015_{version}",
    f"dual_stress_2015_{version}"
]


fig, ax = plt.subplots(figsize=(10,6))

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

    ax.plot(
        water["dap"],
        water["Tr_fraction"],
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
ax.set_ylabel("Tr / TrPot")
ax.set_title("Transpiration Stress Through Time")

ax.legend()

plt.tight_layout()

outfile = f"{FIG_DIR}/compare_transpiration_2015_{version}.png"

plt.savefig(
    outfile,
    dpi=300,
    bbox_inches="tight"
)

print(outfile)
