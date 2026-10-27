#!/usr/bin/env python
"""
05_run_experiment.py

Run one experiment prepared by 04_modify_precip.py.

Usage
-----
python 05_run_experiment.py EXPERIMENT [--site story2015] [--force]
                            [--allow-no-record] [--irrigation rainfed]

Safety checks
-------------
- the experiment's treatment_record.json (written by 04) must exist, and its
  recorded precipitation checksum must match the forcing file now on disk,
  so a run can never silently use forcing that was changed after 04;
- existing outputs are not overwritten unless --force is given.
  (--allow-no-record is only for legacy Story experiments made before 04
  wrote records.)
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import geoaquacrop as gac

ROOT = Path(
    os.environ.get(
        "GEOAQUACROP_ROOT",
        "/mnt/scratch/olusegu3/geoaquacrop"
    )
)

CONFIG = ROOT / "config"

parser = argparse.ArgumentParser()
parser.add_argument("experiment")
parser.add_argument("--site", default="story2015")
parser.add_argument("--irrigation", default="rainfed")
parser.add_argument("--force", action="store_true")
parser.add_argument("--allow-no-record", action="store_true")
args = parser.parse_args()

experiment = args.experiment
SITE = args.site

counties = pd.read_csv(CONFIG / "counties.csv")
match = counties.loc[counties["site_id"] == SITE]

if len(match) != 1:
    sys.exit(f"{SITE} must appear exactly once in {CONFIG / 'counties.csv'}")

YEAR = int(match.iloc[0]["year"])
CROP = str(match.iloc[0]["crop"]).strip().capitalize()

EXPERIMENTS = (
    ROOT / "experiments"
    if SITE == "story2015"
    else ROOT / "experiments" / SITE
)

exp_dir = EXPERIMENTS / experiment
DATA_PATH = exp_dir / "processed"
OUTPUT_DIR = exp_dir / "outputs"

fname = f"Precipitation{YEAR}{YEAR}.nc"
precip = DATA_PATH / fname


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


if not precip.exists():
    sys.exit(
        f"{precip} not found. Run: python 04_modify_precip.py "
        f"{experiment} --site {SITE}"
    )

record_file = exp_dir / "treatment_record.json"

if record_file.exists():

    rec = json.loads(record_file.read_text())

    if sha256(precip) != rec.get("output_sha256"):
        sys.exit(
            "Forcing file changed since 04_modify_precip.py recorded it "
            f"({precip}). Re-run 04 (or --check) before running the model."
        )

elif not args.allow_no_record:

    sys.exit(
        f"No treatment_record.json in {exp_dir}. Run 04_modify_precip.py "
        "first (legacy experiments: --allow-no-record)."
    )

summary_target = OUTPUT_DIR / "summary_results.pkl"
daily_target = OUTPUT_DIR / "daily_results.pkl"

if summary_target.exists() and not args.force:
    sys.exit(
        f"{summary_target} already exists; outputs are not overwritten "
        "without --force. Back them up first if you intend to rerun."
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

summary_file, daily_file = gac.simulate.run(
    data_path=str(DATA_PATH),
    start_date=f"{YEAR}/01/01",
    end_date=f"{YEAR}/12/31",
    crop=CROP,
    irrigation=args.irrigation,
    output_dir=str(OUTPUT_DIR)
)

print("\nOriginal outputs:")
print(summary_file)
print(daily_file)

shutil.copy2(summary_file, summary_target)
shutil.copy2(daily_file, daily_target)

print("\nStandardized outputs:")
print(summary_target)
print(daily_target)

run_record = {
    "site_id": SITE,
    "experiment": experiment,
    "year": YEAR,
    "crop": CROP,
    "irrigation": args.irrigation,
    "forcing_sha256": sha256(precip),
    "geoaquacrop_version": getattr(gac, "__version__", "unknown"),
    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
}

(exp_dir / "run_record.json").write_text(json.dumps(run_record, indent=2))

print(f"\nCompleted experiment: {experiment}")
