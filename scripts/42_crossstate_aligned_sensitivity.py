#!/usr/bin/env python
"""
42_crossstate_aligned_sensitivity.py   (EXPLORATORY, post hoc; see docs/crossstate_amendment1.md)

Why: 03 writes one planting date per county (the first cell's) to phenology.csv and 04 builds one
calendar window from it. In counties whose cells have different crop-calendar planting dates, the
treatment window is misaligned for cells whose planting date differs from the county row date.

What: recompute each county's early-only loss using ONLY cells whose planting_date equals the county
row planting date (so window and cell agree), then repeat the state-level test exactly as in
40_crossstate_summary.py (state mean, Spearman, one-sided exact permutation p). No model rerun:
cell yields come from the existing experiments/<site>/<exp>/outputs/summary_results.pkl.
Same ratio-of-means definition as the primary: loss = 100 - 100 * mean(treated dry yield) / mean(control dry yield),
over the same (aligned) set of cells in treated and control.

Usage: python 42_crossstate_aligned_sensitivity.py
Outputs (results/crossstate/): crossstate_aligned_county.csv, crossstate_aligned_state.csv,
crossstate_aligned_test.json. Reported alongside the primary, whatever it shows.
"""
import itertools
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
CONFIG, OUT = ROOT / "config", ROOT / "results" / "crossstate"
YCOL = "Dry yield (tonne/ha)"
EXPS = {"v025": "g_v025_r100", "v050": "g_v050_r100", "v000": "g_v000_r100"}
ABBR = {"IA": "Iowa", "IL": "Illinois", "IN": "Indiana", "MI": "Michigan", "MN": "Minnesota",
        "MO": "Missouri", "OH": "Ohio", "SD": "South Dakota", "WI": "Wisconsin"}


def cells(site, exp):
    p = ROOT / "experiments" / site / exp / "outputs" / "summary_results.pkl"
    return pd.concat(pd.read_pickle(p), ignore_index=True)


def exact_perm_p(x, y):
    n = len(x); rx, ry = rankdata(x), rankdata(y)
    if np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return np.nan, np.nan
    zx = (rx - rx.mean()) / rx.std(); zy = (ry - ry.mean()) / ry.std()
    obs = float(zx @ zy / n)
    perms = np.array(list(itertools.permutations(range(n))), dtype=np.int8)
    return obs, float(np.mean((zy[perms] @ zx) / n >= obs - 1e-12))


sites = pd.read_csv(CONFIG / "crossstate_sites.csv", dtype={"fips": str})
pheno = pd.read_csv(CONFIG / "phenology.csv").set_index("site_id")
primary = pd.read_csv(OUT / "crossstate_county_loss.csv")
obs = pd.read_csv(CONFIG / "observed_state_coefficients.csv")
obs = obs[obs["in_primary"].astype(str).str.lower() == "true"].copy()
obs["observed_penalty"] = -obs["ssmi_cellB_coef_bu_ac"]

rows, worst = [], 0.0
for r in sites.itertuples():
    md = pd.Timestamp(pheno.loc[r.site_id, "planting_date"]).strftime("%m/%d")
    ctrl = cells(r.site_id, "control_2015")
    mc = ctrl["planting_date"].astype(str) == md
    row = dict(state=r.state, county=r.county, site_id=r.site_id, row_planting=md,
               n_cells=len(ctrl), n_aligned=int(mc.sum()),
               distinct_planting_dates=int(ctrl["planting_date"].nunique()))
    if mc.sum() == 0:
        sys.exit(f"{r.site_id}: no cell has the row planting date {md}")
    for k, exp in EXPS.items():
        tr = cells(r.site_id, exp)
        mt = tr["planting_date"].astype(str) == md
        row[f"loss_{k}_aligned"] = 100 - 100 * tr.loc[mt, YCOL].mean() / ctrl.loc[mc, YCOL].mean()
        all_loss = 100 - 100 * tr[YCOL].mean() / ctrl[YCOL].mean()
        row[f"loss_{k}_allcells"] = all_loss
        ref = primary.loc[primary.site_id == r.site_id, f"loss_{'v025' if k == 'v025' else ('v050' if k == 'v050' else 'v000')}"].iloc[0]
        worst = max(worst, abs(all_loss - ref))
    rows.append(row)
cty = pd.DataFrame(rows)
cty.to_csv(OUT / "crossstate_aligned_county.csv", index=False)
print(f"Consistency: max |all-cell loss recomputed here - loss in crossstate_county_loss.csv| = {worst:.3f} pp")
if worst > 0.5:
    print("WARNING: recomputed all-cell losses differ from the primary table by > 0.5 pp; check before interpreting.")

st = cty.groupby("state")[[c for c in cty.columns if c.endswith("_aligned") or c.endswith("_allcells")]].mean().reset_index()
st["state_name"] = st.state.map(ABBR)
st = st.merge(obs[["state", "observed_penalty"]].rename(columns={"state": "state_name"}), on="state_name")
st.to_csv(OUT / "crossstate_aligned_state.csv", index=False)

res = {}
for col in ("loss_v025_aligned", "loss_v050_aligned", "loss_v000_aligned", "loss_v025_allcells"):
    rho, p = exact_perm_p(st[col].values, st["observed_penalty"].values)
    res[col] = dict(rho=rho, p_one_sided=p, n=len(st))
(OUT / "crossstate_aligned_test.json").write_text(json.dumps(res, indent=2))

pd.set_option("display.width", 200)
print("\nCounties with cells that disagree on planting date (aligned = cells whose date equals the county row date):")
d = cty[cty.distinct_planting_dates > 1]
print(d[["state", "county", "row_planting", "n_cells", "n_aligned", "loss_v025_allcells", "loss_v025_aligned"]].round(2).to_string(index=False))
print("\nState values (veg 0.25, rep 1.00 loss, pp):")
print(st[["state", "loss_v025_allcells", "loss_v025_aligned", "observed_penalty"]].round(2)
      .sort_values("loss_v025_aligned", ascending=False).to_string(index=False))
print("\nEXPLORATORY (post hoc). One-sided exact permutation, n = 9:")
for k, v in res.items():
    print(f"  {k:<20} rho = {v['rho']:.3f}  p = {v['p_one_sided']:.6f}")
print("Primary (pre-specified, all cells) for comparison: rho = 0.033, p = 0.474")
