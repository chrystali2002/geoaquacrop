#!/usr/bin/env python
"""
24_select_crossstate_counties.py

Implements the county-selection rule frozen in docs/crossstate_plan.md (tag crossstate_plan_frozen):
per state, take the 20 counties with the largest 2015 grain-corn harvested area that have a reported
(not suppressed) 2015 NASS yield, split them by available water capacity (AWC, 0-150 cm) into terciles,
and select the largest-area county in each tercile. Ties in area are broken by lower FIPS.

The rule uses only NASS area, NASS yield availability and AWC. It never reads model output.

Usage
-----
python 24_select_crossstate_counties.py [--year 2015] [--states IL IN IA MI MN MO OH SD WI]
       [--outdir config] [--area-yield-csv FILE] [--awc-csv FILE]

Inputs
  NASS Quick Stats (API key: NASS_API_KEY or first line of ~/.nass_api_key), grain-corn county AREA HARVESTED (ACRES)
  and YIELD (BU / ACRE). Values reported as "(D)" or non-numeric are treated as not reported.
  AWC: USDA NRCS Soil Data Access, muaggatt.aws0150wta (cm of available water, 0-150 cm), area-weighted by map unit
  acres within each soil survey area (areasymbol = state letters + 3-digit county FIPS).
  --area-yield-csv / --awc-csv load cached tables instead (columns below) so the same inputs can be re-used.

Outputs (in --outdir)
  crossstate_candidates.csv   every county considered, with the quantities used and the rule's decisions
  crossstate_counties.csv     the selected counties (3 per state when available)
  crossstate_selection_inputs_<year>.json   provenance (retrieval time, source URLs, parameters)

Implementation choice NOT stated in the frozen plan (recorded here and in the output): counties for which AWC cannot
be obtained are excluded BEFORE the top-20 cut, because a county without AWC cannot be assigned a tercile.
They are listed in crossstate_candidates.csv with in_pool = False.
"""
import argparse, csv, io, json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

STATES = {"IL": "17", "IN": "18", "IA": "19", "MI": "26", "MN": "27", "MO": "29", "OH": "39", "SD": "46", "WI": "55"}
NASS_URL = os.environ.get("NASS_BASE_URL", "https://quickstats.nass.usda.gov/api/api_GET/")
SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
TOP_N = 20


def select_counties(df, top_n=TOP_N):
    """df columns: state, fips, county, area_acres, yield_bu_ac, awc_cm.
    Returns (candidates with decisions, selected). Pure function (no I/O), tested separately."""
    out = []
    for st, g in df.groupby("state", sort=True):
        g = g.copy()
        g["has_yield"] = g["yield_bu_ac"].notna()
        g["has_awc"] = g["awc_cm"].notna()
        g["has_area"] = g["area_acres"].notna()
        g["in_pool"] = g["has_yield"] & g["has_awc"] & g["has_area"]
        pool = g[g["in_pool"]].sort_values(["area_acres", "fips"], ascending=[False, True]).head(top_n).copy()
        # AWC terciles by rank within the pool (ascending AWC; ties by FIPS), groups of near-equal size
        pool = pool.sort_values(["awc_cm", "fips"])
        pool["awc_rank"] = range(1, len(pool) + 1)
        n = len(pool)
        pool["tercile"] = pd.cut(pool["awc_rank"], bins=[0, n / 3, 2 * n / 3, n], labels=["low", "mid", "high"]).astype(str) if n >= 3 else "NA"
        pool["selected"] = False
        for t in ("low", "mid", "high"):
            sub = pool[pool["tercile"] == t].sort_values(["area_acres", "fips"], ascending=[False, True])
            if len(sub):
                pool.loc[sub.index[0], "selected"] = True
        g = g.merge(pool[["fips", "awc_rank", "tercile", "selected"]], on="fips", how="left")
        g["in_top_n"] = g["fips"].isin(pool["fips"])
        g["selected"] = g["selected"].fillna(False).astype(bool)
        out.append(g)
    cand = pd.concat(out, ignore_index=True)
    return cand, cand[cand["selected"]].sort_values(["state", "tercile"]).reset_index(drop=True)


def nass_key():
    k = os.environ.get("NASS_API_KEY", "").strip()
    if not k:
        f = Path.home() / ".nass_api_key"
        if f.exists():
            k = f.read_text().splitlines()[0].strip()
    if not k:
        sys.exit("No NASS API key (NASS_API_KEY or ~/.nass_api_key).")
    return k


def fetch_nass(year, states, key):
    rows = []
    for st in states:
        for cat in ("AREA HARVESTED", "YIELD"):
            q = {"key": key, "source_desc": "SURVEY", "commodity_desc": "CORN", "agg_level_desc": "COUNTY",
                 "statisticcat_desc": cat, "util_practice_desc": "GRAIN", "state_alpha": st, "year": year, "format": "CSV"}
            with urllib.request.urlopen(NASS_URL + "?" + urllib.parse.urlencode(q), timeout=120) as r:
                text = r.read().decode("utf-8")
            for rec in csv.DictReader(io.StringIO(text)):
                unit = rec.get("unit_desc", "").upper()
                if cat == "AREA HARVESTED" and unit != "ACRES":
                    continue
                if cat == "YIELD" and unit != "BU / ACRE":
                    continue
                try:
                    v = float(rec["Value"].replace(",", ""))
                except (ValueError, KeyError):
                    v = None            # "(D)" and other non-numeric values: not reported
                code = (rec.get("county_code") or "").strip()
                if not code or code == "998":   # 998 = "other (combined) counties"
                    continue
                rows.append({"state": st, "fips": STATES[st] + code.zfill(3), "county": rec.get("county_name", ""),
                             "stat": cat, "value": v})
            print(f"{st} {cat}: fetched", flush=True)
    d = pd.DataFrame(rows)
    a = d[d["stat"] == "AREA HARVESTED"].groupby(["state", "fips", "county"], as_index=False)["value"].first().rename(columns={"value": "area_acres"})
    y = d[d["stat"] == "YIELD"].groupby(["state", "fips"], as_index=False)["value"].first().rename(columns={"value": "yield_bu_ac"})
    return a.merge(y, on=["state", "fips"], how="outer")


def fetch_awc(states):
    out = []
    for st in states:
        sql = ("SELECT l.areasymbol AS areasymbol, SUM(mu.muacres * mag.aws0150wta) / SUM(mu.muacres) AS awc_cm "
               "FROM legend l INNER JOIN mapunit mu ON mu.lkey = l.lkey "
               "INNER JOIN muaggatt mag ON mag.mukey = mu.mukey "
               f"WHERE l.areasymbol LIKE '{st}%' AND mag.aws0150wta IS NOT NULL AND mu.muacres IS NOT NULL "
               "GROUP BY l.areasymbol")
        body = json.dumps({"query": sql, "format": "JSON+COLUMNNAME"}).encode()
        req = urllib.request.Request(SDA_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            js = json.loads(r.read().decode("utf-8"))
        table = js.get("Table", [])
        for rec in table[1:]:
            sym, awc = rec[0], rec[1]
            code = sym[2:]
            if len(sym) == 5 and code.isdigit():       # state letters + 3-digit county FIPS
                out.append({"state": st, "fips": STATES[st] + code, "awc_cm": float(awc)})
        print(f"{st} AWC: {len([o for o in out if o['state']==st])} survey areas", flush=True)
    return pd.DataFrame(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year", default="2015")
    p.add_argument("--states", nargs="+", default=list(STATES))
    p.add_argument("--outdir", default="config")
    p.add_argument("--area-yield-csv", default=None)
    p.add_argument("--awc-csv", default=None)
    a = p.parse_args()
    for s in a.states:
        if s not in STATES:
            sys.exit(f"{s}: not one of the frozen states {list(STATES)}")
    ay = pd.read_csv(a.area_yield_csv, dtype={"fips": str}) if a.area_yield_csv else fetch_nass(a.year, a.states, nass_key())
    awc = pd.read_csv(a.awc_csv, dtype={"fips": str}) if a.awc_csv else fetch_awc(a.states)
    df = ay.merge(awc[["fips", "awc_cm"]], on="fips", how="left")
    cand, sel = select_counties(df)
    od = Path(a.outdir); od.mkdir(parents=True, exist_ok=True)
    cols = ["state", "fips", "county", "area_acres", "yield_bu_ac", "awc_cm", "in_pool", "in_top_n", "awc_rank", "tercile", "selected"]
    cand[cols].sort_values(["state", "area_acres"], ascending=[True, False]).to_csv(od / "crossstate_candidates.csv", index=False)
    sel[cols].to_csv(od / "crossstate_counties.csv", index=False)
    (od / f"crossstate_selection_inputs_{a.year}.json").write_text(json.dumps({
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "year": a.year, "states": a.states,
        "top_n": TOP_N, "nass_url": NASS_URL, "awc_source": "NRCS Soil Data Access muaggatt.aws0150wta, area-weighted by muacres",
        "cached_inputs": {"area_yield_csv": a.area_yield_csv, "awc_csv": a.awc_csv}}, indent=2))
    print("\nSelected counties:")
    print(sel[["state", "fips", "county", "tercile", "area_acres", "yield_bu_ac", "awc_cm"]].to_string(index=False))
    short = [s for s, g in sel.groupby("state") if len(g) < 3]
    if short:
        print("\nWARNING: fewer than 3 counties selected for:", short)
    print(f"\nWrote {od/'crossstate_counties.csv'} and {od/'crossstate_candidates.csv'}")


if __name__ == "__main__":
    main()
