#!/usr/bin/env python
"""
02_run_control.py

Run the unmodified control simulation for a registered site.

Usage
-----
python 02_run_control.py --site champaign2015 [--irrigation rainfed] [--force]

Reads  <root>/<site_id>/processed        (baseline from 01; copied, not edited)
Writes <exp_root>/control_<year>/{processed,outputs}
  exp_root = <root>/experiments for story2015 (legacy layout, frozen),
             <root>/experiments/<site_id> for every other site.

Refuses to overwrite existing control outputs unless --force is given, and
refuses to run if the control's precipitation differs from the baseline.
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
parser.add_argument("--site", required=True)
parser.add_argument("--irrigation", default="rainfed")
parser.add_argument("--force", action="store_true")
args = parser.parse_args()

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

baseline = ROOT / SITE / "processed"
control = EXPERIMENTS / f"control_{YEAR}"
DATA_PATH = control / "processed"
OUTPUT_DIR = control / "outputs"

fname = f"Precipitation{YEAR}{YEAR}.nc"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


if not baseline.exists():
    sys.exit(f"{baseline} not found. Run 01_run_preprocess.py --site {SITE}")

summary_target = OUTPUT_DIR / "summary_results.pkl"
daily_target = OUTPUT_DIR / "daily_results.pkl"

if summary_target.exists() and not args.force:
    sys.exit(
        f"{summary_target} already exists; control outputs are not "
        "overwritten without --force."
    )

if not DATA_PATH.exists():
    shutil.copytree(baseline, DATA_PATH)
    print(f"Copied baseline inputs -> {DATA_PATH}")

if (baseline / fname).exists() and (DATA_PATH / fname).exists():
    if sha256(baseline / fname) != sha256(DATA_PATH / fname):
        sys.exit(
            "Control precipitation differs from the baseline "
            f"({DATA_PATH / fname}); a control must be unmodified."
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

print("Original outputs:")
print(summary_file)
print(daily_file)

shutil.copy2(summary_file, summary_target)
shutil.copy2(daily_file, daily_target)

print("\nStandardized outputs:")
print(summary_target)
print(daily_target)

record = {
    "site_id": SITE,
    "experiment": f"control_{YEAR}",
    "year": YEAR,
    "crop": CROP,
    "irrigation": args.irrigation,
    "precipitation_sha256": (
        sha256(DATA_PATH / fname) if (DATA_PATH / fname).exists() else None
    ),
    "geoaquacrop_version": getattr(gac, "__version__", "unknown"),
    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
}

(control / "run_record.json").write_text(json.dumps(record, indent=2))

print(f"\nNext: python 03_growth_stage_diagnostics.py {SITE}")
