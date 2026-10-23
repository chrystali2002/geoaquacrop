#!/usr/bin/env python

#python 08_compare_biomass.py v1
#python 08_compare_biomass.py v2
#python 08_compare_biomass.py v3
import sys
import pandas as pd
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

outfile = f"{FIG_DIR}/compare_biomass_2015_{version}.png"

plt.savefig(
    outfile,
    dpi=300,
    bbox_inches="tight"
)

print(outfile)
