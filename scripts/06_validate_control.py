#!/usr/bin/env python
"""
06_validate_control.py   (integrity gate 3)

Compare a site's control run with USDA NASS before trusting it.

Usage
-----
python 06_validate_control.py SITE [SITE ...] --nass-csv QuickStats.csv
        [--moisture 0.155]
        [--planted-50 YYYY-MM-DD] [--silking-50 YYYY-MM-DD] [--harvested-50 YYYY-MM-DD]

NASS yield: county corn-for-grain yield, bu/ac (Quick Stats CSV download).
Unit conversion (assumption, stated so you can challenge it):
    model 'Dry yield' is dry matter, t/ha.
    wet yield at standard moisture = dry / (1 - moisture)   (default 15.5 %)
    1 bu/ac of corn = 56 lb/bu = 0.062770 t/ha
The optional dates are STATE-level Crop Progress 50 % dates for that site's
state (give them only when validating one site; run once per site).

It prints differences only. It sets no pass/fail limit: write the tolerance in
docs/champaign_experiment_plan.md BEFORE looking at the result.
Unweighted mean over simulated cells (not weighted by maize area).
"""
import argparse, os, sys
from pathlib import Path
import pandas as pd

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
CONFIG = ROOT / "config"
T_HA_PER_BU_AC = 0.062770

p = argparse.ArgumentParser()
p.add_argument("sites", nargs="+")
p.add_argument("--nass-csv", required=True)
p.add_argument("--moisture", type=float, default=0.155)
p.add_argument("--reference", default="story2015", help="site whose R the others are compared with")
p.add_argument("--tol", type=float, default=0.20, help="pre-specified gate 3 tolerance on |R_site - R_reference|")
p.add_argument("--planted-50"); p.add_argument("--silking-50"); p.add_argument("--mature-50"); p.add_argument("--harvested-50")
a = p.parse_args()

if len(a.sites) > 1 and (a.planted_50 or a.silking_50 or a.mature_50 or a.harvested_50):
    sys.exit("State dates differ by state: give them for one site per run.")

counties = pd.read_csv(CONFIG / "counties.csv", dtype={"geoid": str})
pheno = pd.read_csv(CONFIG / "phenology.csv")
nass = pd.read_csv(a.nass_csv, dtype=str)
need = {"Year", "Data Item", "Value", "State ANSI", "County ANSI"}
if not need <= set(nass.columns):
    sys.exit(f"NASS CSV lacks columns {sorted(need - set(nass.columns))}; has {list(nass.columns)}")

rows = []
for site in a.sites:
    m = counties.loc[counties["site_id"] == site]
    if len(m) != 1:
        sys.exit(f"{site} not found exactly once in counties.csv")
    geoid = m.iloc[0]["geoid"].zfill(5); year = int(m.iloc[0]["year"])
    ph = pheno.loc[pheno["site_id"] == site]
    if ph.empty:
        sys.exit(f"{site} not in phenology.csv; run 03 first")
    ph = ph.iloc[0]

    exp = ROOT / "experiments" / (f"control_{year}" if site == "story2015" else f"{site}/control_{year}")
    summ = pd.concat(pd.read_pickle(exp / "outputs" / "summary_results.pkl"), ignore_index=True)
    dry = summ["Dry yield (tonne/ha)"].mean()
    model_bu = dry / (1 - a.moisture) / T_HA_PER_BU_AC

    sel = nass[(nass["Year"] == str(year))
               & (nass["State ANSI"].str.zfill(2) == geoid[:2])
               & (nass["County ANSI"].str.zfill(3) == geoid[2:])
               & nass["Data Item"].str.upper().str.contains("CORN, GRAIN - YIELD, MEASURED IN BU / ACRE", regex=False)]
    if sel.empty:
        print(f"{site}: no NASS county yield row for {year} (county may be suppressed).")
        nass_bu = float("nan")
    else:
        nass_bu = float(sel.iloc[0]["Value"].replace(",", ""))
    rows.append({"site": site, "model_dry_t_ha": round(dry, 2),
                 "model_bu_ac": round(model_bu, 1), "nass_bu_ac": nass_bu,
                 "R_model_over_nass": round(model_bu / nass_bu, 3),
                 "model_minus_nass_pct": round(100 * (model_bu / nass_bu - 1), 1),
                 "n_cells": len(summ)})

    print(f"\n=== {site} (GEOID {geoid}) ===")
    for lab, mod, ref in (("planting", ph["planting_date"], a.planted_50),
                          ("silking / reproductive onset", ph["reproductive_date"], a.silking_50),
                          ("model harvest (= maturity) vs state % mature", ph["harvest_date"], a.mature_50),
                          ("model harvest vs state % harvested (expected later)", ph["harvest_date"], a.harvested_50)):
        if ref:
            d = (pd.Timestamp(mod) - pd.Timestamp(ref)).days
            print(f"{lab}: model {mod}, state 50% {ref}, difference {d:+d} days")
        else:
            print(f"{lab}: model {mod} (no state date given)")

out = pd.DataFrame(rows)
print("\n", out.to_string(index=False))

# Gate 3 (pre-specified): |R_site - R_reference| <= tol
if a.reference in set(out["site"]) and len(out) > 1:
    r_ref = float(out.loc[out["site"] == a.reference, "R_model_over_nass"].iloc[0])
    print(f"\nGate 3: |R_site - R_{a.reference}| <= {a.tol}   (R_{a.reference} = {r_ref})")
    for _, r in out[out["site"] != a.reference].iterrows():
        d = abs(float(r["R_model_over_nass"]) - r_ref)
        print(f"  {r['site']}: R = {r['R_model_over_nass']}  |diff| = {d:.3f}  ->  {'PASS' if d <= a.tol else 'FAIL'}")
res = ROOT / "results"; res.mkdir(exist_ok=True)
out.to_csv(res / ("control_validation_" + "_".join(a.sites) + ".csv"), index=False)
