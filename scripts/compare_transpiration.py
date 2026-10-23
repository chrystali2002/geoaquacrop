# compare_transpiration.py

import pandas as pd
import numpy as np
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

ax.set_xlabel("DAP")
ax.set_ylabel("Tr / TrPot")

ax.set_title(
    "Transpiration Stress Through the Season"
)

ax.legend()

plt.tight_layout()

plt.savefig(
    f"{BASE}/../figures/transpiration_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

