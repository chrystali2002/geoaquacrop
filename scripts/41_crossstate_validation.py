#!/usr/bin/env python
"""
41_crossstate_validation.py

Descriptive control validation for the 27 cross-state counties (docs/crossstate_validation_note.md):
no threshold, no county dropped. Runs 06_validate_control.py once per county with that
state's NASS Crop Progress 50 % dates, then combines the results.

Usage
-----
python 41_crossstate_validation.py [--dry-run]

Inputs
    config/crossstate_sites.csv              state, fips, county, tercile, site_id
    config/crossstate_counties.csv           yield_bu_ac = NASS 2015 county grain yield (frozen selection table)
    config/phenology.csv                     model phenology per site (from 03)
    results/nass_progress_50pct_2015_<states>.csv   from fetch_nass_progress.py (all nine states)
Writes
    results/crossstate/nass_county_yield_2015_crossstate.csv   Quick Stats-format yield table for 06
    results/logs/validation/<site>.txt                         06's printed output per county
    results/crossstate/crossstate_control_validation.csv       combined table (yield R + date differences)

The NASS yield table is a reformatting of yield_bu_ac in config/crossstate_counties.csv (the frozen
selection inputs), written in the column layout 06 expects. Gate 3 (story2015 reference) is not
invoked: the reference site is never passed to 06 here.
"""
import argparse
import glob
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
CONFIG, RESULTS = ROOT / "config", ROOT / "results"
OUT = RESULTS / "crossstate"
LOGDIR = RESULTS / "logs" / "validation"
SCRIPT06 = Path(__file__).resolve().parent / "06_validate_control.py"
ITEM = "CORN, GRAIN - YIELD, MEASURED IN BU / ACRE"

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
args = ap.parse_args()

sites = pd.read_csv(CONFIG / "crossstate_sites.csv", dtype={"fips": str})
sites["fips"] = sites["fips"].str.zfill(5)
sel = pd.read_csv(CONFIG / "crossstate_counties.csv", dtype={"fips": str})
sel["fips"] = sel["fips"].str.zfill(5)
pheno = pd.read_csv(CONFIG / "phenology.csv")

cands = sorted(glob.glob(str(RESULTS / "nass_progress_50pct_2015_*IL*MO*.csv")) or
               glob.glob(str(RESULTS / "nass_progress_50pct_2015_*.csv")))
if not cands:
    sys.exit("no results/nass_progress_50pct_2015_*.csv; run fetch_nass_progress.py first")
prog = pd.read_csv(max(cands, key=lambda p: len(pd.read_csv(p))), dtype=str)
dates = {(r.state, r.stage): r.date_50pct for r in prog.itertuples() if isinstance(r.date_50pct, str) and r.date_50pct}
for st in sites.state.unique():
    miss = [s for s in ("planted", "silking", "mature", "harvested") if (st, s) not in dates]
    if miss:
        sys.exit(f"{st}: missing state 50% dates for {miss}")

# Quick Stats-format yield table for 06
tab = sites.merge(sel[["fips", "yield_bu_ac"]], on="fips", how="left")
if tab.yield_bu_ac.isna().any():
    sys.exit("missing NASS yield for: " + ", ".join(tab[tab.yield_bu_ac.isna()].site_id))
qs = pd.DataFrame({"Year": "2015", "Data Item": ITEM, "Value": tab.yield_bu_ac.map(lambda v: f"{v:g}"),
                   "State ANSI": tab.fips.str[:2], "County ANSI": tab.fips.str[2:]})
OUT.mkdir(parents=True, exist_ok=True); LOGDIR.mkdir(parents=True, exist_ok=True)
nass_csv = OUT / "nass_county_yield_2015_crossstate.csv"
qs.to_csv(nass_csv, index=False)

failed = []
for r in sites.itertuples():
    cmd = [sys.executable, str(SCRIPT06), r.site_id, "--nass-csv", str(nass_csv),
           "--planted-50", dates[(r.state, "planted")], "--silking-50", dates[(r.state, "silking")],
           "--mature-50", dates[(r.state, "mature")], "--harvested-50", dates[(r.state, "harvested")]]
    if args.dry_run:
        print(" ".join(cmd)); continue
    p = subprocess.run(cmd, capture_output=True, text=True)
    (LOGDIR / f"{r.site_id}.txt").write_text(p.stdout + p.stderr)
    print(f"{r.site_id}: {'ok' if p.returncode == 0 else 'FAILED (see ' + str(LOGDIR / (r.site_id + '.txt')) + ')'}")
    if p.returncode != 0:
        failed.append(r.site_id)
if args.dry_run:
    sys.exit(0)
if failed:
    sys.exit(f"{len(failed)} counties failed: {failed}")

rows = []
for r in sites.itertuples():
    v = pd.read_csv(RESULTS / f"control_validation_{r.site_id}.csv").iloc[0].to_dict()
    ph = pheno[pheno.site_id == r.site_id].iloc[0]
    d = lambda a, b: (pd.Timestamp(a) - pd.Timestamp(b)).days
    v.update(state=r.state, county=r.county, tercile=r.tercile,
             planting_minus_state_days=d(ph.planting_date, dates[(r.state, "planted")]),
             silking_minus_state_days=d(ph.reproductive_date, dates[(r.state, "silking")]),
             harvest_minus_mature_days=d(ph.harvest_date, dates[(r.state, "mature")]),
             harvest_minus_harvested_days=d(ph.harvest_date, dates[(r.state, "harvested")]))
    rows.append(v)
c = pd.DataFrame(rows)
c = c[["state", "county", "tercile", "site", "model_bu_ac", "nass_bu_ac", "R_model_over_nass",
       "model_minus_nass_pct", "n_cells", "planting_minus_state_days", "silking_minus_state_days",
       "harvest_minus_mature_days", "harvest_minus_harvested_days"]]
c.to_csv(OUT / "crossstate_control_validation.csv", index=False)
pd.set_option("display.width", 200)
print("\n", c.round(3).to_string(index=False))
print("\nBy state (mean R, min, max):")
print(c.groupby("state").R_model_over_nass.agg(["mean", "min", "max"]).round(3).to_string())
print(f"\nAll 27: R mean {c.R_model_over_nass.mean():.3f}, range {c.R_model_over_nass.min():.3f}-{c.R_model_over_nass.max():.3f}")
print(f"Wrote {OUT / 'crossstate_control_validation.csv'}")
