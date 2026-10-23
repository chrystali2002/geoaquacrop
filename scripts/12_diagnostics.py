#Purpose:

#Provide one consolidated summary for all experiments.
#python 12_diagnostics.py v1
#python 12_diagnostics.py v2
#python 12_diagnostics.py v3
#What we're trying to learn

#The central mechanistic question remains:

#Plain Text
#Wr recovers
#↓
#Tr recovers
#↓
#Yield recovers

#If this pathway consistently appears in:

#Plain Text
#early_recovery

#but not in:

#Plain Text
#late_stress
#dual_stress


#then GeoAquaCrop begins to provide process-based support for your manuscript's most novel finding:

#Recovery was supported under the soil-moisture-based representation (SSMI), whereas alternative drought representations suggested ongoing stress.

#That is the key test I'd focus on next before adding new locations or additional years.

#!/usr/bin/env python

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

rows = []

for exp in experiments:

    summary_file = Path(
        f"{BASE}/{exp}/outputs/summary_results.pkl"
    )

    daily_file = Path(
        f"{BASE}/{exp}/outputs/daily_results.pkl"
    )

    if not summary_file.exists():

        print(
            f"Skipping {exp} "
            f"(summary_results.pkl not found)"
        )

        continue

    if not daily_file.exists():

        print(
            f"Skipping {exp} "
            f"(daily_results.pkl not found)"
        )

        continue

    summary = pd.read_pickle(summary_file)

    daily = pd.read_pickle(daily_file)

    s = summary[0]

    water = daily[0]["water_flux"].copy()

    water["Tr_fraction"] = np.where(
        water["TrPot"] > 0,
        water["Tr"] / water["TrPot"],
        np.nan
    )

    yield_actual = float(
        s["Dry yield (tonne/ha)"].iloc[0]
    )

    yield_potential = float(
        s["Yield potential (tonne/ha)"].iloc[0]
    )

    rows.append({

        "experiment": exp,

        "yield_t_ha":
        round(
            yield_actual,
            2
        ),

        "yield_potential_t_ha":
        round(
            yield_potential,
            2
        ),

        "yield_gap_pct":
        round(
            100 *
            (
                1 -
                yield_actual /
                yield_potential
            ),
            1
        ),

        "seasonal_precip_mm":
        round(
            float(
                s["seasonal_precip_mm"].iloc[0]
            ),
            1
        ),

        "seasonal_transpiration_mm":
        round(
            float(
                s["seasonal_transpiration_mm"].iloc[0]
            ),
            1
        ),

        "mean_Wr":
        round(
            float(
                water["Wr"].mean()
            ),
            1
        ),

        "mean_Tr_fraction":
        round(
            float(
                water["Tr_fraction"].mean()
            ),
            3
        ),

        "water_productivity":
        round(
            float(
                s["wp_et_kg_per_m3"].iloc[0]
            ),
            3
        )
    })

df = pd.DataFrame(rows)

print("\n")
print("=" * 90)
print(f"DIAGNOSTICS ({version})")
print("=" * 90)

if len(df) == 0:

    print("\nNo experiments found.")

else:

    print(df.to_string(index=False))
