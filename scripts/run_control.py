import os
import shutil
import glob
import geoaquacrop as gac

OUTPUT_DIR = (
    "/mnt/scratch/olusegu3/geoaquacrop/"
    "experiments/control/outputs"
)

summary_file, daily_file = gac.simulate.run(
    data_path="/mnt/scratch/olusegu3/geoaquacrop/experiments/control/processed",
    start_date="2012/01/01",
    end_date="2012/12/31",
    crop="Maize",
    irrigation="rainfed",
    output_dir=OUTPUT_DIR
)

print("Original outputs:")
print(summary_file)
print(daily_file)

# -------------------------------------------------
# Standardize filenames
# -------------------------------------------------

summary_target = os.path.join(
    OUTPUT_DIR,
    "summary_results.pkl"
)

daily_target = os.path.join(
    OUTPUT_DIR,
    "daily_results.pkl"
)

shutil.copy2(summary_file, summary_target)
shutil.copy2(daily_file, daily_target)

print("\nStandardized outputs:")
print(summary_target)
print(daily_target)
