# diagnostic_processes.py

import pandas as pd
import numpy as np

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

for exp in [
    "control",
    "early_recovery",
    "late_stress",
    "dual_stress"
]:

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    print("\n================================")
    print(exp)
    print("================================")

    print(
        "Mean Wr:",
        round(water["Wr"].mean(),2)
    )

    print(
        "Mean Tr:",
        round(water["Tr"].mean(),2)
    )

    print(
        "Mean Tr/TrPot:",
        round(
            water["Tr_fraction"].mean(),
            3
        )
    )
