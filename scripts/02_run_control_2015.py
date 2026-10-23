#!/usr/bin/env python

#before running
#mkdir -p /mnt/scratch/olusegu3/geoaquacrop/experiments/control_2015

#mkdir -p \
#/mnt/scratch/olusegu3/geoaquacrop/experiments/early_recovery_2015

#mkdir -p \
#/mnt/scratch/olusegu3/geoaquacrop/experiments/late_stress_2015

#mkdir -p \
#/mnt/scratch/olusegu3/geoaquacrop/experiments/dual_stress_2015

#cp -r \
#/mnt/scratch/olusegu3/geoaquacrop/story2015/processed \
#/mnt/scratch/olusegu3/geoaquacrop/experiments/control_2015/

#cp -r story2015/processed \
#      experiments/early_recovery_2015/

#cp -r story2015/processed \
#      experiments/late_stress_2015/

#cp -r story2015/processed \
#      experiments/dual_stress_2015/



import os
import shutil
import geoaquacrop as gac

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

DATA_PATH = (
    "/mnt/scratch/olusegu3/geoaquacrop/"
    "experiments/control_2015/processed"
)

OUTPUT_DIR = (
    "/mnt/scratch/olusegu3/geoaquacrop/"
    "experiments/control_2015/outputs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# RUN GEoAquaCrop
# --------------------------------------------------

summary_file, daily_file = gac.simulate.run(
    data_path=DATA_PATH,
    start_date="2015/01/01",
    end_date="2015/12/31",
    crop="Maize",
    irrigation="rainfed",
    output_dir=OUTPUT_DIR
)

print("Original outputs:")
print(summary_file)
print(daily_file)

# --------------------------------------------------
# STANDARDIZE FILENAMES
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
