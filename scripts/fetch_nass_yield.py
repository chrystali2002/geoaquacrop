#!/usr/bin/env python
"""
fetch_nass_yield.py

Download county corn-for-grain yield (bu/ac) from the USDA NASS Quick Stats API
and write a CSV with the same column names as the Quick Stats web download, so
06_validate_control.py reads it unchanged.

Usage
-----
python fetch_nass_yield.py --years 2015 2016 --states IL IA \
  --out /mnt/scratch/olusegu3/ORNL_plots/NASS/corn_yield_IL_IA_2015_2016.csv

python fetch_nass_yield.py --years 2015 [2016 ...] --states IL IA
        [--out FILE] [--commodity CORN]

API key (free: https://quickstats.nass.usda.gov/api): environment variable
NASS_API_KEY, or the first line of ~/.nass_api_key. Never put it in the repo.
Uses only the standard library (urllib), so it works even if `requests` is broken.
"""
import argparse, csv, io, os, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE_URL = os.environ.get("NASS_BASE_URL", "https://quickstats.nass.usda.gov/api/api_GET/")
SHORT_DESC = "CORN, GRAIN - YIELD, MEASURED IN BU / ACRE"

RENAME = {"year": "Year", "state_name": "State", "state_ansi": "State ANSI",
          "county_name": "County", "county_ansi": "County ANSI",
          "short_desc": "Data Item", "agg_level_desc": "Geo Level",
          "Value": "Value", "CV (%)": "CV (%)"}

p = argparse.ArgumentParser()
p.add_argument("--years", nargs="+", required=True)
p.add_argument("--states", nargs="+", required=True, help="2-letter codes, e.g. IL IA")
p.add_argument("--out", default=None)
a = p.parse_args()

key = os.environ.get("NASS_API_KEY", "").strip()
if not key:
    f = Path.home() / ".nass_api_key"
    if f.exists():
        key = f.read_text().splitlines()[0].strip()
if not key:
    sys.exit("No NASS API key. Request one at https://quickstats.nass.usda.gov/api, then set "
             "NASS_API_KEY or put it on the first line of ~/.nass_api_key.")

rows, header = [], None
for year in a.years:
    for st in a.states:
        q = {"key": key, "source_desc": "SURVEY", "short_desc": SHORT_DESC,
             "agg_level_desc": "COUNTY", "state_alpha": st.upper(),
             "year": year, "format": "CSV"}
        url = BASE_URL + "?" + urllib.parse.urlencode(q)
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                text = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            sys.exit(f"{st} {year}: HTTP {e.code} from NASS: {body}")
        rd = csv.DictReader(io.StringIO(text))
        got = list(rd)
        print(f"{st} {year}: {len(got)} county rows")
        header = header or rd.fieldnames
        rows += got

if not rows:
    sys.exit("No rows returned; check years/states.")

out_cols = [RENAME[c] for c in RENAME if c in rows[0]]
out = Path(a.out or f"nass_corn_yield_{'_'.join(a.states)}_{'_'.join(a.years)}.csv")
with open(out, "w", newline="") as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_ALL)
    w.writerow(out_cols)
    for r in rows:
        w.writerow([r[c] for c in RENAME if c in r])
print(f"Wrote {out} ({len(rows)} rows)")
