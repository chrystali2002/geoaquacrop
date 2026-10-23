#!/usr/bin/env python

import geoaquacrop as gac

DATA_PATH = (
    "/mnt/scratch/olusegu3/geoaquacrop/story2012/processed"
)

OUTPUT_DIR = (
    "/mnt/scratch/olusegu3/geoaquacrop/story2012/outputs"
)

summary_file, daily_file = gac.simulate.run(
    data_path=DATA_PATH,
    start_date="2012/01/01",
    end_date="2012/12/31",
    crop="Maize",
    irrigation="rainfed",
    output_dir=OUTPUT_DIR
)

print("Summary:")
print(summary_file)

print("Daily:")
print(daily_file)
