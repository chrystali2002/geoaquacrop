# compare_biomass.py

import pandas as pd
import matplotlib.pyplot as plt

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

experiments = [
    "control",
    "early_recovery",
    "late_stress",
    "dual_stress"
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

plt.savefig(
    f"{BASE}/../figures/biomass_comparison.png",
    dpi=300,
    bbox_inches="tight"
)
