# compare_wr.py

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

    water = daily[0]["water_flux"]

    ax.plot(
        water["dap"],
        water["Wr"],
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
ax.set_ylabel("Root-zone Water (mm)")
ax.set_title("Root-zone Water Dynamics")

ax.legend()

plt.tight_layout()

plt.savefig(
    f"{BASE}/../figures/wr_comparison.png",
    dpi=300,
    bbox_inches="tight"
)
