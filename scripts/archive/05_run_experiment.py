#!/usr/bin/env python

#python 05_run_experiment.py early_recovery_2015_v1

#python 05_run_experiment.py late_stress_2015_v1

#python 05_run_experiment.py dual_stress_2015_v1

import os
import sys
import shutil
import geoaquacrop as gac

# --------------------------------------------------
# Experiment name
# --------------------------------------------------

experiment = sys.argv[1]

BASE = "/mnt/scratch/olusegu3/geoaquacrop"

DATA_PATH = (
    f"{BASE}/experiments/{experiment}/processed"
)

OUTPUT_DIR = (
    f"{BASE}/experiments/{experiment}/outputs"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

# --------------------------------------------------
# Run simulation
# --------------------------------------------------

summary_file, daily_file = gac.simulate.run(
    data_path=DATA_PATH,
    start_date="2015/01/01",
    end_date="2015/12/31",
    crop="Maize",
    irrigation="rainfed",
    output_dir=OUTPUT_DIR
)

print("\nOriginal outputs:")
print(summary_file)
print(daily_file)

# --------------------------------------------------
# Standardized filenames
# --------------------------------------------------

summary_target = os.path.join(
    OUTPUT_DIR,
    "summary_results.pkl"
)

daily_target = os.path.join(
    OUTPUT_DIR,
    "daily_results.pkl"
)

shutil.copy2(
    summary_file,
    summary_target
)

shutil.copy2(
    daily_file,
    daily_target
)

print("\nStandardized outputs:")
print(summary_target)
print(daily_target)

print(
    f"\nCompleted experiment: {experiment}"
)
