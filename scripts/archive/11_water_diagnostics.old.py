import pandas as pd

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

experiments = [
    "control_2015",
    "early_recovery_2015",
    "late_stress_2015",
    "dual_stress_2015"
]

target_daps = [60, 72, 90, 110, 130]

for exp in experiments:

    daily = pd.read_pickle(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    water = daily[0]["water_flux"]

    subset = water.loc[
        water["dap"].isin(target_daps),
        ["dap", "Wr", "Tr", "TrPot"]
    ]

    print("\n================================")
    print(exp)
    print("================================")
    print(subset)
