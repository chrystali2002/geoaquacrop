#!/usr/bin/env python
"""
40_crossstate_summary.py

Cross-state test of whether modelled buffering explains the observed SSMI early-only
(Cell B) result, exactly as pre-specified in docs/crossstate_plan.md
(tags crossstate_plan_frozen, crossstate_counties_selected).

Usage
-----
python 40_crossstate_summary.py [--out-dir results/crossstate]

Inputs (nothing is downloaded)
    config/crossstate_sites.csv            state, fips, county, tercile, site_id   (27 counties)
    config/crossstate_counties.csv         awc_cm per county (selection table)
    config/observed_state_coefficients.csv observed SSMI Cell B coefficients, in_primary flag
    results/crossstate/<site>_resilience_grid.csv   from 21_resilience_metrics.py --grid

Modelled metric (per county): early-only loss = 100 - YieldRecoveryPct at
    veg_mult = 0.25, rep_mult = 1.00         (primary)
    veg_mult = 0.50 and 0.00, rep_mult = 1.00  (sensitivity)
State value = mean of its counties (primary); median (sensitivity).
Observed early-only penalty = -(SSMI Cell B coefficient), bu/ac.

Test: Spearman rank correlation (average ranks for ties) between the state modelled loss
and the observed penalty over the primary states; one-sided exact permutation p-value
(all n! orderings); the plan passes if rho > 0 and p <= 0.05. Also leave-one-state-out and
a secondary county-level correlation of modelled loss with county AWC.

It refuses to run unless all 27 county files exist (no partial looks), and reports a null
result in the same format. Writes county, state and test tables plus crossstate_test.json.
"""
import argparse
import itertools
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
CONFIG = ROOT / "config"
ABBR = {"IA": "Iowa", "IL": "Illinois", "IN": "Indiana", "MI": "Michigan", "MN": "Minnesota",
        "MO": "Missouri", "OH": "Ohio", "SD": "South Dakota", "WI": "Wisconsin",
        "KS": "Kansas", "NE": "Nebraska"}
ALPHA = 0.05


def spearman(x, y):
    rx, ry = rankdata(x), rankdata(y)
    if np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return np.nan
    return float(np.corrcoef(rx, ry)[0, 1])


def exact_perm_p(x, y):
    """One-sided exact permutation p-value for rho > 0 (all n! orderings of y)."""
    n = len(x)
    rx, ry = rankdata(x), rankdata(y)
    if np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return np.nan, np.nan
    zx = (rx - rx.mean()) / rx.std()
    zy = (ry - ry.mean()) / ry.std()
    obs = float(zx @ zy / n)
    perms = np.array(list(itertools.permutations(range(n))), dtype=np.int8)
    rho = (zy[perms] @ zx) / n
    return obs, float(np.mean(rho >= obs - 1e-12))


def loss_at(df, veg, rep=1.0):
    m = df[np.isclose(df.veg_mult, veg) & np.isclose(df.rep_mult, rep)]
    if len(m) != 1:
        sys.exit(f"expected exactly one row for veg={veg}, rep={rep}, found {len(m)}")
    return 100.0 - float(m.YieldRecoveryPct.iloc[0])


ap = argparse.ArgumentParser()
ap.add_argument("--out-dir", default=str(ROOT / "results" / "crossstate"))
args = ap.parse_args()
OUT = Path(args.out_dir); OUT.mkdir(parents=True, exist_ok=True)

sites = pd.read_csv(CONFIG / "crossstate_sites.csv", dtype={"fips": str})
sites["fips"] = sites["fips"].str.zfill(5)
sel = pd.read_csv(CONFIG / "crossstate_counties.csv", dtype={"fips": str})
sel["fips"] = sel["fips"].str.zfill(5)
sites = sites.merge(sel[["fips", "awc_cm"]], on="fips", how="left")
obs = pd.read_csv(CONFIG / "observed_state_coefficients.csv")
obs = obs[obs["in_primary"].astype(str).str.lower() == "true"].copy()
obs["observed_penalty"] = -obs["ssmi_cellB_coef_bu_ac"]

# ---- all 27 county files must exist and pass the control gate ----
missing = [s for s in sites.site_id if not (OUT / f"{s}_resilience_grid.csv").exists()]
if missing:
    sys.exit(f"{len(missing)} of {len(sites)} county grid files are missing; no partial look is taken. "
             f"Missing: {missing}")

rows = []
for _, r in sites.iterrows():
    d = pd.read_csv(OUT / f"{r.site_id}_resilience_grid.csv")
    ctrl = d[d.Trajectory == "Control"]
    if len(ctrl) != 1 or abs(float(ctrl.YieldRecoveryPct.iloc[0]) - 100.0) > 1e-6:
        sys.exit(f"{r.site_id}: control row missing or YieldRecoveryPct != 100")
    if d.YieldRecoveryPct.isna().any():
        sys.exit(f"{r.site_id}: NaN in YieldRecoveryPct")
    rows.append(dict(state=r.state, fips=r.fips, county=r.county, tercile=r.tercile, site_id=r.site_id,
                     awc_cm=r.awc_cm, loss_v025=loss_at(d, 0.25), loss_v050=loss_at(d, 0.5),
                     loss_v000=loss_at(d, 0.0)))
cty = pd.DataFrame(rows)
cty.to_csv(OUT / "crossstate_county_loss.csv", index=False)

# ---- state values ----
cols = ["loss_v025", "loss_v050", "loss_v000"]
mean_df = cty.groupby("state")[cols].mean().add_suffix("_mean")
med_df = cty.groupby("state")[cols].median().add_suffix("_median")
st = mean_df.join(med_df).reset_index()
st["state_name"] = st["state"].map(ABBR)
st = st.merge(obs[["state", "observed_penalty", "ssmi_cellB_coef_bu_ac", "p_value"]]
              .rename(columns={"state": "state_name"}), on="state_name", how="inner")
if len(st) != 9:
    sys.exit(f"expected 9 primary states, got {len(st)}")
st.to_csv(OUT / "crossstate_state_summary.csv", index=False)

# ---- tests ----
def test(col, data):
    rho, p = exact_perm_p(data[col].values, data["observed_penalty"].values)
    return dict(n=len(data), rho=rho, p_one_sided=p,
                distinct_modelled_values=int(data[col].round(6).nunique()))

res = {"primary": {}, "sensitivity": {}, "leave_one_state_out": [], "county_level_awc": {}}
res["primary"] = test("loss_v025_mean", st)
res["primary"]["passes_plan"] = bool(res["primary"]["rho"] > 0 and res["primary"]["p_one_sided"] <= ALPHA)
for col in ["loss_v025_median", "loss_v050_mean", "loss_v000_mean", "loss_v050_median", "loss_v000_median"]:
    res["sensitivity"][col] = test(col, st)
for s in st.state:
    sub = st[st.state != s]
    t = test("loss_v025_mean", sub); t["left_out"] = s
    res["leave_one_state_out"].append(t)
res["county_level_awc"] = dict(n=len(cty), spearman_awc_vs_loss_v025=spearman(cty.awc_cm, cty.loss_v025),
                               note="secondary; pooled across states, descriptive only")
res["inputs"] = dict(counties=len(cty), states=len(st), alpha=ALPHA,
                     metric="100 - YieldRecoveryPct at veg 0.25, rep 1.00; state mean")
(OUT / "crossstate_test.json").write_text(json.dumps(res, indent=2))

# ---- report ----
pd.set_option("display.width", 160)
print("\nState values (modelled early-only loss, pp of control yield; observed penalty bu/ac = -SSMI Cell B coef)")
print(st[["state", "loss_v025_mean", "loss_v025_median", "loss_v050_mean", "loss_v000_mean",
          "observed_penalty", "p_value"]].round(3).sort_values("loss_v025_mean", ascending=False).to_string(index=False))
P = res["primary"]
print(f"\nPRIMARY: Spearman rho = {P['rho']:.3f}, one-sided exact permutation p = {P['p_one_sided']:.6f}, "
      f"n = {P['n']}, distinct modelled values = {P['distinct_modelled_values']}")
print(f"Plan criterion (rho > 0 and p <= {ALPHA}): {'PASS' if P['passes_plan'] else 'NOT MET'}")
if P["distinct_modelled_values"] < 5:
    print("WARNING: fewer than 5 distinct modelled state values; the rank test has little power (report as is).")
print("\nSensitivity (one-sided p):")
for k, v in res["sensitivity"].items():
    print(f"  {k:<18} rho = {v['rho']:.3f}  p = {v['p_one_sided']:.6f}")
print("\nLeave-one-state-out (primary metric):")
for v in res["leave_one_state_out"]:
    print(f"  without {v['left_out']:<3} rho = {v['rho']:.3f}  p = {v['p_one_sided']:.6f}  (n={v['n']})")
print(f"\nCounty-level AWC vs modelled loss (secondary): rho = {res['county_level_awc']['spearman_awc_vs_loss_v025']:.3f}")
print(f"\nWrote {OUT}/crossstate_county_loss.csv, crossstate_state_summary.csv, crossstate_test.json")
