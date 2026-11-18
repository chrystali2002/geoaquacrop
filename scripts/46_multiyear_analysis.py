#!/usr/bin/env python
"""
46_multiyear_analysis.py

Analysis for docs/crossstate_multiyear_plan.md (tag crossstate_multiyear_plan_frozen).

Usage
-----
python 46_multiyear_analysis.py --g3-only            # gate G3 on observed data only (no model output needed)
python 46_multiyear_analysis.py                      # full analysis; needs results/multiyear/modelled_county_yields.csv

Inputs
    --master    master_analysis_trackA.csv (observed classification and NASS yields)
    --published config/observed_state_coefficients.csv (S6.1 state SSMI Cell B coefficients, bu/ac)
    --modelled  results/multiyear/modelled_county_yields.csv from 45 (fips, year, dry_t_ha, n_cells)

Steps (as in the plan)
    G3   09b sample (yield_anomaly and all three classifications present), nine states, per-state OLS
         yield_anomaly ~ C(matrix_ssmi, Treatment('D_neither')) + C(year_cat), HC3; the Cell B coefficient
         must equal the published value to two decimals in every state, or the script stops.
    Model yields: dry t/ha -> bu/ac at 15.5 % moisture; per-county linear detrending as 08_nass_yield.py
         (np.polyfit on year; < 5 years -> county mean), fitted over the county-years that have both a
         NASS yield and a modelled yield; relative anomaly = 100 x (y - trend) / trend.
    Counties with any 1986-2024 season missing from the model output are excluded (listed).
    Comparison sample: 09b sample with a modelled anomaly; observed regressions re-estimated on it.
    Adequacy (plan Multi-year Amendment 1): pooled modelled Cell A and C coefficients < 0, as observed; the
         cross-state Spearman correlations for Cells A and C are reported descriptively only.
         If not adequate, Cell B is reported as uninformative.
    P1   Spearman, states with estimable Cell B in both series (relative anomalies), one-sided exact
         permutation p; criterion rho > 0 and p <= 0.05.
    P2   MI, SD, MN modelled Cell B with HC3 and county-clustered 95 % CI.
    P3   pooled Cell B, modelled vs observed, county-clustered.
    Secondary: the same in bu/ac. All results are written whatever they show.
"""
import argparse
import itertools
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import rankdata

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
STATES = ["IA", "IL", "IN", "MI", "MN", "MO", "OH", "SD", "WI"]
NAMES = {"IA": "Iowa", "IL": "Illinois", "IN": "Indiana", "MI": "Michigan", "MN": "Minnesota",
         "MO": "Missouri", "OH": "Ohio", "SD": "South Dakota", "WI": "Wisconsin"}
CELL_ORDER = ["D_neither", "B_early_only", "C_late_only", "A_both"]
CELLS = ["B_early_only", "C_late_only", "A_both"]
YEARS = range(1986, 2025)
T_HA_PER_BU_AC = 0.062770
MOISTURE = 0.155
ALPHA = 0.05
TERM = "C(matrix_ssmi, Treatment('D_neither'))[T.{}]"


def key(cell):
    return TERM.format(cell)


def fit_state(df, y, cluster=False):
    """09b's run_state_ols, for the SSMI classification and dependent variable y."""
    d = df.copy()
    d["matrix_ssmi"] = pd.Categorical(d["matrix_ssmi"], categories=CELL_ORDER)
    d["year_cat"] = d["year"].astype("category")
    if d["matrix_ssmi"].dropna().nunique() < 2:
        return None
    f = f"{y} ~ C(matrix_ssmi, Treatment('D_neither')) + C(year_cat)"
    try:
        if cluster:
            m = smf.ols(f, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["fips"].astype("category").cat.codes})
        else:
            m = smf.ols(f, data=d).fit(cov_type="HC3")
    except Exception as e:
        print(f"    [warn] OLS failed: {e}")
        return None
    out = {}
    for c in CELLS:
        k = key(c)
        if k in m.params.index and np.isfinite(m.bse[k]):
            lo, hi = m.conf_int().loc[k]
            out[c] = dict(b=m.params[k], se=m.bse[k], p=m.pvalues[k], lo=lo, hi=hi)
        else:
            out[c] = dict(b=np.nan, se=np.nan, p=np.nan, lo=np.nan, hi=np.nan)
    out["n"] = int(m.nobs)
    return out


def fit_pooled(df, y):
    d = df.copy()
    d["matrix_ssmi"] = pd.Categorical(d["matrix_ssmi"], categories=CELL_ORDER)
    d["year_cat"] = d["year"].astype("category")
    f = f"{y} ~ C(matrix_ssmi, Treatment('D_neither')) + C(state_alpha) + C(year_cat)"
    m = smf.ols(f, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["fips"].astype("category").cat.codes})
    out = {}
    for c in CELLS:
        lo, hi = m.conf_int().loc[key(c)]
        out[c] = dict(b=m.params[key(c)], se=m.bse[key(c)], p=m.pvalues[key(c)], lo=lo, hi=hi)
    out["n"] = int(m.nobs)
    return out


def exact_perm(x, y):
    """Spearman rho (average ranks) and one-sided exact permutation p for rho > 0."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    rx, ry = rankdata(x), rankdata(y)
    if n < 3 or np.ptp(rx) == 0 or np.ptp(ry) == 0:
        return np.nan, np.nan
    zx = (rx - rx.mean()) / rx.std(); zy = (ry - ry.mean()) / ry.std()
    obs = float(zx @ zy / n)
    perms = np.array(list(itertools.permutations(range(n))), dtype=np.int8)
    return obs, float(np.mean((zy[perms] @ zx) / n >= obs - 1e-12))


def detrend(df, col):
    """08_nass_yield.detrend_yield applied to column col, per county."""
    parts = []
    for _, g in df.groupby("fips"):
        g = g.sort_values("year").copy()
        if len(g) < 5:
            g["trend"] = g[col].mean()
        else:
            c = np.polyfit(g["year"].values.astype(float), g[col].values.astype(float), 1)
            g["trend"] = np.polyval(c, g["year"].values.astype(float))
        parts.append(g)
    out = pd.concat(parts)
    return out["trend"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="/mnt/scratch/olusegu3/ORNL_plots/earlydrought/master_analysis_trackA.csv")
    ap.add_argument("--published", default=str(ROOT / "config" / "observed_state_coefficients.csv"))
    ap.add_argument("--modelled", default=str(ROOT / "results" / "multiyear" / "modelled_county_yields.csv"))
    ap.add_argument("--out", default=str(ROOT / "results" / "multiyear"))
    ap.add_argument("--g3-only", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)

    m = pd.read_csv(a.master)
    m["fips"] = m["fips"].astype(str).str.zfill(5)
    m = m[m["state_alpha"].isin(STATES)]
    s09b = m.dropna(subset=["yield_anomaly", "matrix_spei", "matrix_ssmi", "matrix_esi"]).copy()

    # ---------------- G3 ----------------
    pub = pd.read_csv(a.published).set_index("state")["ssmi_cellB_coef_bu_ac"]
    g3 = []
    for st in STATES:
        r = fit_state(s09b[s09b.state_alpha == st], "yield_anomaly")
        b = r["B_early_only"]["b"] if r else np.nan
        g3.append(dict(state=st, estimated=b, published=pub.get(NAMES[st], np.nan), n=r["n"] if r else 0))
    g3 = pd.DataFrame(g3)
    g3["match_2dp"] = np.isclose(g3.estimated.round(2), g3.published.round(2))
    print("Gate G3: 09b specification on the observed data vs published S6.1 Cell B coefficients")
    print(g3.round(3).to_string(index=False))
    g3.to_csv(out / "g3_reproduction.csv", index=False)
    if not g3.match_2dp.all():
        sys.exit("G3 FAILED: the specification does not reproduce S6.1. Stop and resolve before any modelled analysis.")
    print("G3 PASSED")
    if a.g3_only:
        return 0

    # ---------------- modelled yields ----------------
    if not Path(a.modelled).exists():
        sys.exit(f"{a.modelled} not found (run 45 first)")
    md = pd.read_csv(a.modelled, dtype={"fips": str})
    md["fips"] = md["fips"].str.zfill(5)
    md = md[md["fips"].isin(m["fips"].unique())]
    seasons = md.dropna(subset=["dry_t_ha"]).groupby("fips")["year"].nunique()
    incomplete = sorted(set(m["fips"].unique()) - set(seasons[seasons == len(YEARS)].index))
    pd.Series(incomplete, name="fips").to_csv(out / "excluded_counties.csv", index=False)
    md = md[~md["fips"].isin(incomplete)].copy()
    md["model_bu"] = md["dry_t_ha"] / (1 - MOISTURE) / T_HA_PER_BU_AC

    # detrend over county-years with both a NASS yield and a modelled yield
    both = m.dropna(subset=["yield_buac"])[["fips", "year"]].merge(md[["fips", "year", "model_bu"]], on=["fips", "year"])
    both["model_trend"] = detrend(both, "model_bu").reindex(both.index)
    both["model_anom_bu"] = both["model_bu"] - both["model_trend"]
    both["model_anom_rel"] = 100 * both["model_anom_bu"] / both["model_trend"]

    cmp_ = s09b.merge(both[["fips", "year", "model_anom_bu", "model_anom_rel"]], on=["fips", "year"], how="inner")
    cmp_ = cmp_[np.isfinite(cmp_["model_anom_rel"])].copy()
    cmp_["obs_anom_bu"] = cmp_["yield_anomaly"]
    cmp_["obs_anom_rel"] = 100 * cmp_["yield_anomaly"] / cmp_["yield_trend"]
    dropped = (s09b.groupby("state_alpha").size() - cmp_.groupby("state_alpha").size()).rename("dropped").reset_index()
    dropped.to_csv(out / "sample_dropped_by_state.csv", index=False)
    cmp_.to_csv(out / "comparison_sample.csv", index=False)

    # ---------------- per-state and pooled fits ----------------
    rows = []
    for metric in ("rel", "bu"):
        for src in ("obs", "model"):
            y = f"{src}_anom_{metric}"
            for st in STATES:
                sd = cmp_[cmp_.state_alpha == st]
                h, c = fit_state(sd, y), fit_state(sd, y, cluster=True)
                for cell in CELLS:
                    rh = h[cell] if h else dict(b=np.nan, se=np.nan, p=np.nan, lo=np.nan, hi=np.nan)
                    rc = c[cell] if c else dict(b=np.nan, se=np.nan, p=np.nan, lo=np.nan, hi=np.nan)
                    rows.append(dict(metric=metric, source=src, state=st, cell=cell, b=rh["b"],
                                     se_hc3=rh["se"], p_hc3=rh["p"], lo_hc3=rh["lo"], hi_hc3=rh["hi"],
                                     se_cl=rc["se"], p_cl=rc["p"], lo_cl=rc["lo"], hi_cl=rc["hi"],
                                     n=h["n"] if h else 0, n_cellB=int((sd.matrix_ssmi == "B_early_only").sum())))
    sc = pd.DataFrame(rows)
    sc.to_csv(out / "state_coefficients.csv", index=False)
    pooled = []
    for metric in ("rel", "bu"):
        for src in ("obs", "model"):
            r = fit_pooled(cmp_, f"{src}_anom_{metric}")
            for cell in CELLS:
                pooled.append(dict(metric=metric, source=src, cell=cell, **r[cell], n=r["n"]))
    po = pd.DataFrame(pooled)
    po.to_csv(out / "pooled_coefficients.csv", index=False)

    def wide(metric, cell):
        w = sc[(sc.metric == metric) & (sc.cell == cell)].pivot(index="state", columns="source", values="b")
        return w.dropna()

    res = {"n_counties": int(cmp_.fips.nunique()), "n_county_years": int(len(cmp_)),
           "excluded_counties": len(incomplete), "results": {}}
    for metric in ("rel", "bu"):
        R = {}
        ad = {}
        for cell in ("A_both", "C_late_only"):
            pm = po[(po.metric == metric) & (po.source == "model") & (po.cell == cell)].b.iloc[0]
            pobs = po[(po.metric == metric) & (po.source == "obs") & (po.cell == cell)].b.iloc[0]
            w = wide(metric, cell)
            rho, p = exact_perm(w["model"], w["obs"])
            ad[cell] = dict(pooled_model=pm, pooled_obs=pobs, rho=rho, p=p, n_states=len(w))
        adequate = all(ad[c]["pooled_model"] < 0 and ad[c]["pooled_obs"] < 0 for c in ad)   # Multi-year Amendment 1
        w = wide(metric, "B_early_only")
        rho, p = exact_perm(w["model"], w["obs"])
        R["adequacy"] = dict(cells=ad, adequate=bool(adequate))
        R["P1"] = dict(rho=rho, p_one_sided=p, n_states=len(w), states=list(w.index),
                       criterion_met=bool(rho > 0 and p <= ALPHA))
        R["P2"] = sc[(sc.metric == metric) & (sc.cell == "B_early_only") & (sc.state.isin(["MI", "SD", "MN"]))] \
            .to_dict(orient="records")
        R["P3"] = po[(po.metric == metric) & (po.cell == "B_early_only")].to_dict(orient="records")
        res["results"][metric] = R
    (out / "multiyear_test.json").write_text(json.dumps(res, indent=2, default=float))

    # ---------------- report ----------------
    print(f"\nComparison sample: {res['n_counties']} counties, {res['n_county_years']} county-years; "
          f"{len(incomplete)} counties excluded for missing seasons")
    print("County-years dropped from the 09b sample, by state:")
    print(dropped.to_string(index=False))
    for metric, label in (("rel", "PRIMARY (relative anomalies, % of trend)"), ("bu", "SECONDARY (bu/ac)")):
        R = res["results"][metric]
        print(f"\n===== {label} =====")
        print("Adequacy (Cells A and C; condition = pooled signs; state rho descriptive):")
        for c, v in R["adequacy"]["cells"].items():
            print(f"  {c:<12} pooled model {v['pooled_model']:.2f}, observed {v['pooled_obs']:.2f}; "
                  f"state rho {v['rho']:.3f} (p {v['p']:.4f}, n {v['n_states']})")
        print(f"  model adequate: {R['adequacy']['adequate']}"
              + ("" if R["adequacy"]["adequate"] else "  -> Cell B comparison reported as uninformative"))
        print("Cell B by state (observed vs modelled, same sample):")
        print(sc[(sc.metric == metric) & (sc.cell == "B_early_only")]
              .pivot(index="state", columns="source", values="b").round(2).to_string())
        P1 = R["P1"]
        print(f"P1: rho = {P1['rho']:.3f}, one-sided exact p = {P1['p_one_sided']:.6f}, n = {P1['n_states']} states; "
              f"criterion {'MET' if P1['criterion_met'] else 'NOT MET'}")
        print("P2 (modelled Cell B, HC3 and clustered 95% CI):")
        for r in R["P2"]:
            if r["source"] == "model":
                print(f"  {r['state']}: {r['b']:.2f} [{r['lo_hc3']:.2f}, {r['hi_hc3']:.2f}] HC3; "
                      f"[{r['lo_cl']:.2f}, {r['hi_cl']:.2f}] clustered")
        print("P3 (pooled Cell B, clustered):")
        for r in R["P3"]:
            print(f"  {r['source']:<5} {r['b']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}]")
    print(f"\nWrote results to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
