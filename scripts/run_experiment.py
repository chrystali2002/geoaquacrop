#python run_experiment.py early_recovery

#python run_experiment.py late_stress

#python run_experiment.py dual_stress

import sys
import os
import shutil
import geoaquacrop as gac

experiment = sys.argv[1]

DATA_PATH = (
    f"/mnt/scratch/olusegu3/geoaquacrop/"
    f"experiments/{experiment}/processed"
)

OUTPUT_DIR = (
    f"/mnt/scratch/olusegu3/geoaquacrop/"
    f"experiments/{experiment}/outputs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

summary_file, daily_file = gac.simulate.run(
    data_path=DATA_PATH,
    start_date="2012/01/01",
    end_date="2012/12/31",
    crop="Maize",
    irrigation="rainfed",
    output_dir=OUTPUT_DIR
)

shutil.copy2(
    summary_file,
    f"{OUTPUT_DIR}/summary_results.pkl"
)

shutil.copy2(
    daily_file,
    f"{OUTPUT_DIR}/daily_results.pkl"
)

print(f"Completed: {experiment}")




