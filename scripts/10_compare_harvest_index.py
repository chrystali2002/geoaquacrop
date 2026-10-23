#python 10_compare_harvest_index.py v1
#python 10_compare_harvest_index.py v2
#python 10_compare_harvest_index.py v3

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
        growth["harvest_index_adj"],
        lw=2,
        label=exp
    )

ax.axvline(
    72,
    color="black",
    ls="--",
    label="Reproductive onset"
)

ax.set_xlabel("DAP")
ax.set_ylabel("Adjusted Harvest Index")

ax.set_title("Harvest Index Development")

ax.legend()

plt.tight_layout()

plt.savefig(
    f"{FIG_DIR}/compare_harvest_index_2015_{version}.png",
    dpi=300,
    bbox_inches="tight"
)


