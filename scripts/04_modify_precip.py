#!/usr/bin/env python
"""
04_modify_precip.py

Build an experiment's precipitation forcing from the PRISTINE baseline file.

Usage
-----
python 04_modify_precip.py EXPERIMENT [--site story2015]
                           [--baseline-dir DIR] [--experiments-dir DIR]
                           [--check]

    EXPERIMENT       a row of config/treatments.csv, e.g. late_stress_2015_v2
    --site           row in config/counties.csv / config/phenology.csv
    --baseline-dir   default <root>/<site_id>/processed (never modified)
    --experiments-dir  default <root>/experiments for story2015 (legacy
                     layout), else <root>/experiments/<site_id>
    --check          do not write; compare the experiment's EXISTING
                     precipitation file with a single and a double
                     application of the treatment

Why this differs from the previous version
-------------------------------------------
The old script read the experiment's own precipitation file and replaced it
in place, so running it twice applied the treatment twice (x0.5 -> x0.25).
This version always starts from the baseline, so reruns give identical
files, and it writes treatment_record.json next to the experiment.

Windows (same definition as before)
-----------------------------------
vegetative   : planting <= date < planting + reproductive_dap
reproductive : planting + reproductive_dap <= date <= planting + harvest_dap
Phenology comes from config/phenology.csv (written by 03).

scope "windows": multipliers apply inside those windows only.
scope "year"   : legacy dual_stress_2015_v5 -- scales the ENTIRE year,
                 including days before planting.
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
import xarray as xr

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
parser.add_argument("--baseline-dir", default=None)
parser.add_argument("--experiments-dir", default=None)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()

experiment = args.experiment
SITE = args.site

# --------------------------------------------------
# Site, phenology, treatment (all from config/)
# --------------------------------------------------

counties = pd.read_csv(CONFIG / "counties.csv")
match = counties.loc[counties["site_id"] == SITE]

if len(match) != 1:
    sys.exit(f"{SITE} must appear exactly once in {CONFIG / 'counties.csv'}")

YEAR = int(match.iloc[0]["year"])

pheno_file = CONFIG / "phenology.csv"

if not pheno_file.exists():
    sys.exit(
        f"{pheno_file} not found. Run "
        f"03_growth_stage_diagnostics.py {SITE} first."
    )

pheno = pd.read_csv(pheno_file)
pheno = pheno.loc[pheno["site_id"] == SITE]

if len(pheno) != 1:
    sys.exit(
        f"phenology.csv needs exactly one row for {SITE}; found "
        f"{len(pheno)}. Run 03_growth_stage_diagnostics.py {SITE}."
    )

prow = pheno.iloc[0]


def phenology_dap(row, dap_col, date_col):
    """DAP from the model's dap column; else from dates (planting + DAP days)."""

    if dap_col in row.index and pd.notna(row[dap_col]):
        return int(row[dap_col])

    if (
        date_col in row.index
        and "planting_date" in row.index
        and pd.notna(row[date_col])
    ):
        return int(
            (
                pd.to_datetime(row[date_col])
                - pd.to_datetime(row["planting_date"])
            ).days
        )

    sys.exit(
        f"phenology.csv row for {SITE} has neither '{dap_col}' nor "
        f"'{date_col}' with 'planting_date'. Columns found: "
        f"{list(row.index)}. Run 03_growth_stage_diagnostics.py {SITE}."
    )


if "planting_date" not in prow.index or pd.isna(prow["planting_date"]):
    sys.exit("phenology.csv has no planting_date for " + SITE)

planting = pd.Timestamp(prow["planting_date"])
reproductive_dap = phenology_dap(prow, "reproductive_dap", "reproductive_date")
harvest_dap = phenology_dap(prow, "harvest_dap", "harvest_date")

reproductive_start = planting + pd.Timedelta(days=reproductive_dap)
harvest = planting + pd.Timedelta(days=harvest_dap)

treat = pd.read_csv(CONFIG / "treatments.csv")
trow = treat.loc[treat["experiment"] == experiment]

if len(trow) != 1:
    sys.exit(
        f"{experiment} must appear exactly once in "
        f"{CONFIG / 'treatments.csv'}"
    )

veg_mult = float(trow.iloc[0]["veg_mult"])
rep_mult = float(trow.iloc[0]["rep_mult"])
scope = str(trow.iloc[0]["scope"])

if scope not in ("windows", "year"):
    sys.exit(f"scope must be 'windows' or 'year'; got {scope!r}")

if scope == "year" and veg_mult != rep_mult:
    sys.exit("scope 'year' needs veg_mult == rep_mult")

# --------------------------------------------------
# Paths
# --------------------------------------------------

baseline_dir = (
    Path(args.baseline_dir)
    if args.baseline_dir
    else ROOT / SITE / "processed"
)

if args.experiments_dir:
    experiments_root = Path(args.experiments_dir)
elif SITE == "story2015":
    experiments_root = ROOT / "experiments"      # legacy layout (frozen)
else:
    experiments_root = ROOT / "experiments" / SITE

fname = f"Precipitation{YEAR}{YEAR}.nc"

infile = baseline_dir / fname
exp_dir = experiments_root / experiment
exp_processed = exp_dir / "processed"
outfile = exp_processed / fname

if not infile.exists():
    sys.exit(f"Baseline precipitation not found: {infile}")

# --------------------------------------------------
# Read the baseline (never written)
# --------------------------------------------------

ppt = xr.open_dataset(infile)
ppt.load()
ppt.close()

print("\n===================================")
print("Site:", SITE)
print("Experiment:", experiment)
print("Planting:", planting.date())
print("Reproductive onset:", reproductive_start.date(),
      f"(DAP {reproductive_dap})")
print("Harvest:", harvest.date(), f"(DAP {harvest_dap})")
print(f"veg x{veg_mult:g}  rep x{rep_mult:g}  scope={scope}")
print("===================================\n")

veg_mask = (
    (ppt.time >= planting)
    &
    (ppt.time < reproductive_start)
)

rep_mask = (
    (ppt.time >= reproductive_start)
    &
    (ppt.time <= harvest)
)


def apply_treatment(ds):
    """One application of the treatment (same operations as the old script)."""

    out = ds.copy()

    if scope == "year":
        out["Precipitation"] = out["Precipitation"] * veg_mult
        return out

    for mask, mult in ((veg_mask, veg_mult), (rep_mask, rep_mult)):

        if mult == 1:
            continue

        if mult == 0:
            out["Precipitation"] = xr.where(
                mask,
                0.0,
                out["Precipitation"]
            )
        else:
            out["Precipitation"] = xr.where(
                mask,
                out["Precipitation"] * mult,
                out["Precipitation"]
            )

    return out


def window_totals(ds):
    """Spatial-mean rainfall (mm) in each window and over the whole year."""

    series = ds["Precipitation"].mean(dim=["y", "x"], skipna=True)

    return {
        "vegetative": float(series.where(veg_mask).sum()),
        "reproductive": float(series.where(rep_mask).sum()),
        "whole_year": float(series.sum()),
    }


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --------------------------------------------------
# --check : compare the EXISTING experiment file
# --------------------------------------------------

if args.check:

    if not outfile.exists():
        sys.exit(f"Nothing to check: {outfile} does not exist")

    existing = xr.open_dataset(outfile)
    existing.load()
    existing.close()

    single = apply_treatment(ppt)
    double = apply_treatment(single)

    print(f"Checking {outfile}\n")
    print(f"{'compared with':<22}{'identical':<11}{'max |diff| mm/d':<17}"
          f"{'veg mm':>9}{'rep mm':>9}{'year mm':>10}")

    results = {}

    for label, ds in (
        ("baseline (untouched)", ppt),
        ("1 application", single),
        ("2 applications", double),
        ("EXISTING file", existing),
    ):
        t = window_totals(ds)
        if label == "EXISTING file":
            same, diff = "", ""
        else:
            a = existing["Precipitation"]
            b = ds["Precipitation"]
            same = str(bool(a.equals(b)))
            diff = f"{float(abs(a - b).max(skipna=True)):.6g}"
            results[label] = same == "True"
        print(f"{label:<22}{same:<11}{diff:<17}"
              f"{t['vegetative']:>9.1f}{t['reproductive']:>9.1f}"
              f"{t['whole_year']:>10.1f}")

    if results["1 application"]:
        verdict = "EXISTING file = one application of the treatment (as defined)."
    elif results["2 applications"]:
        verdict = ("EXISTING file = TWO applications of the treatment: the "
                   "effective multipliers are the squares of the defined ones.")
    elif results["baseline (untouched)"]:
        verdict = "EXISTING file is unmodified baseline rainfall."
    else:
        verdict = "EXISTING file matches none of these; investigate."

    print("\n" + verdict)
    sys.exit(0)

# --------------------------------------------------
# Write
# --------------------------------------------------

mod = apply_treatment(ppt)

before = window_totals(ppt)
after = window_totals(mod)

for name in ("vegetative", "reproductive", "whole_year"):
    print(
        f"{name:<13} before {before[name]:8.2f} mm   "
        f"after {after[name]:8.2f} mm   "
        f"removed {before[name] - after[name]:8.2f} mm"
    )

if not exp_processed.exists():
    shutil.copytree(baseline_dir, exp_processed)
    print(f"\nCopied baseline inputs -> {exp_processed}")

tmpfile = outfile.with_name(outfile.stem + "_modified.nc")

mod.to_netcdf(tmpfile)

tmpfile.replace(outfile)

record = {
    "experiment": experiment,
    "site_id": SITE,
    "year": YEAR,
    "veg_mult": veg_mult,
    "rep_mult": rep_mult,
    "scope": scope,
    "applications": 1,
    "planting_date": planting.strftime("%Y-%m-%d"),
    "reproductive_dap": reproductive_dap,
    "harvest_dap": harvest_dap,
    "baseline_file": str(infile),
    "baseline_sha256": sha256(infile),
    "output_sha256": sha256(outfile),
    "rainfall_mm_before": before,
    "rainfall_mm_after": after,
    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
}

(exp_dir / "treatment_record.json").write_text(
    json.dumps(record, indent=2)
)

print(f"\nUpdated:\n{outfile}")
print(f"Record:\n{exp_dir / 'treatment_record.json'}")
