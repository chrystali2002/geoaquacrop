#!/usr/bin/env python
"""
22_evaluate_hypotheses.py

Applies the criteria frozen in docs/champaign_experiment_plan.md (tag
champaign_plan_frozen) to the two sites' grid results from
21_resilience_metrics.py --grid. Nothing here is a free parameter: the constants
below are the plan's numbers. Change them only by amending the plan first.

Usage
-----
python 22_evaluate_hypotheses.py [--reference story2015] [--site champaign2015] [--dir DIR]

Reads  <dir>/<site>_grid_resilience.csv   (default dir: <root>/results)
Writes <dir>/cross_site_cells.csv and <dir>/hypothesis_evaluation.json
"""
import argparse, json, math, os, sys
from pathlib import Path
import pandas as pd

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))

# ---- constants frozen in the plan ----
H1_MIN_YIELD_RECOVERY = 95.0          # %, and State must be Tolerant
H1_CELLS = [(1.00, 0.25), (1.00, 0.00)]   # every one must pass
H2_VEG_LEVELS = [0.25, 0.00]
H2_MIN_GAIN_PP = 20.0                 # YR(rep=1.00) - YR(rep=0.00)
H3_MAX_DIFF_PP = 10.0
H3_MIN_FRACTION = 0.80
N_GRID = 24
# --------------------------------------

p = argparse.ArgumentParser()
p.add_argument("--reference", default="story2015")
p.add_argument("--site", default="champaign2015")
p.add_argument("--dir", default=str(ROOT / "results"))
a = p.parse_args()
d = Path(a.dir)


def load(site):
    f = d / f"{site}_grid_resilience.csv"
    if not f.exists():
        sys.exit(f"{f} not found. Run: python 21_resilience_metrics.py {site} --grid --out {f}")
    df = pd.read_csv(f)
    for c in ("veg_mult", "rep_mult", "YieldRecoveryPct", "State"):
        if c not in df.columns:
            sys.exit(f"{f} lacks column {c}; was it made with --grid?")
    df["veg_mult"] = df["veg_mult"].round(2)
    df["rep_mult"] = df["rep_mult"].round(2)
    df = df.set_index(["veg_mult", "rep_mult"])
    if df.index.duplicated().any():
        sys.exit(f"{f}: duplicate (veg_mult, rep_mult) rows")
    if len(df) != N_GRID + 1:
        sys.exit(f"{f}: expected {N_GRID + 1} rows (control + grid), found {len(df)}")
    return df


def cell(df, v, r):
    key = (round(v, 2), round(r, 2))
    if key not in df.index:
        sys.exit(f"cell veg={v} rep={r} missing")
    return df.loc[key]


def h1(df):
    rows, ok = [], True
    for v, r in H1_CELLS:
        c = cell(df, v, r)
        passed = bool(c["YieldRecoveryPct"] >= H1_MIN_YIELD_RECOVERY and c["State"] == "Tolerant")
        ok &= passed
        rows.append({"veg": v, "rep": r, "yield_recovery_pct": float(c["YieldRecoveryPct"]),
                     "state": c["State"], "pass": passed})
    return ("Supported" if ok else "Not supported"), rows


def h2(df):
    rows, evaluable_ok, n_eval = [], True, 0
    for v in H2_VEG_LEVELS:
        c1, c0 = cell(df, v, 1.00), cell(df, v, 0.00)
        row = {"veg": v, "state_rep1": c1["State"],
               "yr_rep1": float(c1["YieldRecoveryPct"]), "yr_rep0": float(c0["YieldRecoveryPct"])}
        if c1["State"] == "Tolerant":
            row.update(evaluable=False, note="excluded: rep=1.00 run had no sustained stress")
        else:
            gain = row["yr_rep1"] - row["yr_rep0"]
            passed = bool(gain >= H2_MIN_GAIN_PP and c1["State"] == "Recovered")
            n_eval += 1
            evaluable_ok &= passed
            row.update(evaluable=True, gain_pp=gain, **{"pass": passed})
        rows.append(row)
    if n_eval == 0:
        outcome = "Not evaluable"
    else:
        outcome = "Supported" if evaluable_ok else "Not supported"
    return outcome, rows


ref, site = load(a.reference), load(a.site)
res = {"reference": a.reference, "site": a.site}
for name, df in ((a.reference, ref), (a.site, site)):
    o1, r1 = h1(df); o2, r2 = h2(df)
    res[name] = {"H1": o1, "H1_cells": r1, "H2": o2, "H2_levels": r2}

# H3: matched grid cells (everything except the control cell)
common = [k for k in ref.index if k != (1.0, 1.0) and k in site.index]
if len(common) != N_GRID:
    sys.exit(f"expected {N_GRID} matched grid cells, found {len(common)}")
cells = pd.DataFrame({
    "veg_mult": [k[0] for k in common], "rep_mult": [k[1] for k in common],
    f"yr_{a.reference}": [float(ref.loc[k, "YieldRecoveryPct"]) for k in common],
    f"yr_{a.site}": [float(site.loc[k, "YieldRecoveryPct"]) for k in common],
    f"state_{a.reference}": [ref.loc[k, "State"] for k in common],
    f"state_{a.site}": [site.loc[k, "State"] for k in common]})
cells["abs_diff_pp"] = (cells[f"yr_{a.reference}"] - cells[f"yr_{a.site}"]).abs()
cells["within_limit"] = cells["abs_diff_pp"] <= H3_MAX_DIFF_PP
n_ok = int(cells["within_limit"].sum())
frac = n_ok / N_GRID
agree = frac >= H3_MIN_FRACTION

o = res
same_h1 = o[a.reference]["H1"] == o[a.site]["H1"]
h2_ref, h2_site = o[a.reference]["H2"], o[a.site]["H2"]
h2_evaluable = "Not evaluable" not in (h2_ref, h2_site)
same_h2 = h2_evaluable and h2_ref == h2_site

inconsistent = (not same_h1) or (h2_evaluable and h2_ref != h2_site) or (not agree)
if not h2_evaluable:
    h3 = ("Recovery component not evaluable; no cross-site recovery claim. "
          f"Cell agreement {'met' if agree else 'NOT met'}; H1 {'same' if same_h1 else 'DIFFERENT'}.")
else:
    h3 = "Supported" if (agree and same_h1 and same_h2) else "Not supported"

res["H3"] = {"cells_within_limit": n_ok, "of": N_GRID, "fraction": frac,
             "cell_agreement_met": agree, "H1_same_outcome": same_h1,
             "H2_same_outcome": same_h2, "H2_evaluable_at_both": h2_evaluable,
             "outcome": h3, "inconsistent_per_plan": bool(inconsistent)}

cells.to_csv(d / "cross_site_cells.csv", index=False)
(d / "hypothesis_evaluation.json").write_text(json.dumps(res, indent=2, default=str))

print("=" * 72); print("HYPOTHESIS EVALUATION (criteria from champaign_plan_frozen)"); print("=" * 72)
for name in (a.reference, a.site):
    print(f"\n{name}\n  H1 (buffering): {res[name]['H1']}")
    for c in res[name]["H1_cells"]:
        print(f"      veg={c['veg']:.2f} rep={c['rep']:.2f}  YR={c['yield_recovery_pct']:.1f}%  {c['state']}  -> {'pass' if c['pass'] else 'FAIL'}")
    print(f"  H2 (recovery):  {res[name]['H2']}")
    for c in res[name]["H2_levels"]:
        if c["evaluable"]:
            print(f"      veg={c['veg']:.2f}  gain={c['gain_pp']:.1f} pp  rep=1.00 state={c['state_rep1']}  -> {'pass' if c['pass'] else 'FAIL'}")
        else:
            print(f"      veg={c['veg']:.2f}  {c['note']} (YR={c['yr_rep1']:.1f}%, {c['state_rep1']})")
print(f"\nH3 (cross-site): {n_ok}/{N_GRID} cells within {H3_MAX_DIFF_PP:.0f} pp ({frac:.0%}; need {H3_MIN_FRACTION:.0%})")
print(f"  H1 same outcome: {same_h1}   H2 same outcome: {same_h2 if h2_evaluable else 'n/a (not evaluable)'}")
print(f"  Outcome: {h3}")
print(f"  Inconsistent per plan: {inconsistent}")
print(f"\nWrote {d / 'cross_site_cells.csv'} and {d / 'hypothesis_evaluation.json'}")
