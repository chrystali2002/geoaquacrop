# 23_inspect_pickles.py

import pandas as pd

daily = pd.read_pickle(
    "/mnt/scratch/olusegu3/geoaquacrop/experiments/"
    "early_recovery_2015_v2/outputs/"
    "daily_results.pkl"
)

print(type(daily))
print(len(daily))

for k in daily[0]:
    print(k)
