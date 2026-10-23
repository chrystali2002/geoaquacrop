
#!/usr/bin/env python

# Purpose:
# Check specific DAP checkpoints
# Inspect root-zone water recovery
# Inspect transpiration recovery
#
# Examples:
# python 11_water_diagnostics.py v1
# python 11_water_diagnostics.py v2
# python 11_water_diagnostics.py v3
# python 11_water_diagnostics.py v4
#python 11_water_diagnostics.py v5

import sys
from pathlib import Path

import pandas as pd
import numpy as np

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

version = sys.argv[1]

experiments = [
    "control_2015",
    f"early_recovery_2015_{version}",
    f"late_stress_2015_{version}",
    f"dual_stress_2015_{version}"
]

target_daps = [60, 72, 90, 110, 130]

for exp in experiments:

    pkl_file = Path(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    if not pkl_file.exists():

        print("\n================================")
        print(exp)
        print("================================")
        print(f"SKIPPED: {pkl_file} not found")
        continue

    daily = pd.read_pickle(pkl_file)

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    print("\n================================")
    print(exp)
    print("================================")

    subset = water.loc[
        water["dap"].isin(target_daps),
        [
            "dap",
            "Wr",
            "Tr",
            "TrPot",
            "Tr_fraction"
        ]
    ]

    print(subset.round(3))


