#This is the first script aimed directly at your manuscript question:

#Does recovery occur when root-zone water and transpiration recover?

#!/usr/bin/env python

#python 14_recovery_metrics.py

import pandas as pd
import numpy as np

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

control_summary = pd.read_pickle(
    f"{BASE}/control_2015/outputs/summary_results.pkl"
)

control_daily = pd.read_pickle(
    f"{BASE}/control_2015/outputs/daily_results.pkl"
)

control_yield = float(
    control_summary[0]["Dry yield (tonne/ha)"].iloc[0]
)

control_water = control_daily[0]["water_flux"].copy()

control_water["Tr_fraction"] = np.where(
    control_water["TrPot"] > 0,
    control_water["Tr"] /
    control_water["TrPot"],
    np.nan
)

for experiment in [
    "early_recovery_2015_v1",
    "early_recovery_2015_v2",
    "early_recovery_2015_v3"
]:

    summary = pd.read_pickle(
        f"{BASE}/{experiment}/outputs/summary_results.pkl"
    )

    daily = pd.read_pickle(
        f"{BASE}/{experiment}/outputs/daily_results.pkl"
    )

    yield_exp = float(
        summary[0]["Dry yield (tonne/ha)"].iloc[0]
    )

    recovery_pct = (
        yield_exp /
        control_yield
    ) * 100

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] /
        water["TrPot"],
        np.nan
    )

    print("\n")
    print(experiment)

    print(
        "Yield Recovery (%):",
        round(recovery_pct, 1)
    )

    print(
        "Mean Tr/TrPot:",
        round(
            water["Tr_fraction"].mean(),
            3
        )
    )

    print(
        "Mean Wr:",
        round(
            water["Wr"].mean(),
            1
        )
    )
