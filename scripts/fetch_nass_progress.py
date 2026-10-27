#!/usr/bin/env python
"""
fetch_nass_progress.py

Download state-level weekly corn Crop Progress (percent planted / silking /
harvested) from the NASS Quick Stats API and compute the date each reaches 50 %
by linear interpolation between the two weekly reports that bracket 50 %.

Usage
-----
python fetch_nass_progress.py --years 2015 2016 --states IL IA --outdir /mnt/scratch/olusegu3/ORNL_plots/NASS/
python fetch_nass_progress.py --years 2015 --states IL IA [--outdir DIR]

Outputs (in --outdir, default current directory)
    nass_progress_weekly_<years>_<states>.csv    every weekly value
    nass_progress_50pct_<years>_<states>.csv     the 50 % dates

API key: NASS_API_KEY or first line of ~/.nass_api_key. Standard library only.
Filters on unit_desc client-side, so it does not depend on exact short_desc text
beyond "CORN - PROGRESS" (grain corn; silage rows are excluded).
"""
import argparse, csv, io, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE_URL = os.environ.get("NASS_BASE_URL", "https://quickstats.nass.usda.gov/api/api_GET/")
UNITS = {"PCT PLANTED": "planted", "PCT SILKING": "silking",
         "PCT MATURE": "mature", "PCT HARVESTED": "harvested"}

p = argparse.ArgumentParser()
p.add_argument("--years", nargs="+", required=True)
p.add_argument("--states", nargs="+", required=True)
p.add_argument("--outdir", default=".")
a = p.parse_args()

key = os.environ.get("NASS_API_KEY", "").strip()
if not key:
    f = Path.home() / ".nass_api_key"
    if f.exists():
        key = f.read_text().splitlines()[0].strip()
if not key:
    sys.exit("No NASS API key (NASS_API_KEY or ~/.nass_api_key).")

weekly = []
for year in a.years:
    for st in a.states:
        q = {"key": key, "source_desc": "SURVEY", "commodity_desc": "CORN",
             "statisticcat_desc": "PROGRESS", "agg_level_desc": "STATE",
             "state_alpha": st.upper(), "year": year, "format": "CSV"}
        url = BASE_URL + "?" + urllib.parse.urlencode(q)
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                text = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            sys.exit(f"{st} {year}: HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}")
        n = 0
        for r in csv.DictReader(io.StringIO(text)):
            # planted/silking are labelled "CORN - PROGRESS"; grain harvest is
            # "CORN, GRAIN - PROGRESS". Silage rows ("CORN, SILAGE - ...") are excluded.
            if not r["short_desc"].upper().startswith(("CORN - PROGRESS", "CORN, GRAIN - PROGRESS")):
                continue
            stage = UNITS.get(r["unit_desc"].upper())
            if stage is None or not r.get("week_ending"):
                continue
            try:
                v = float(r["Value"].replace(",", ""))
            except ValueError:
                continue
            weekly.append({"year": year, "state": st.upper(), "stage": stage,
                           "week_ending": r["week_ending"], "pct": v})
            n += 1
        print(f"{st} {year}: {n} weekly rows (planted/silking/mature/harvested)")

if not weekly:
    sys.exit("No progress rows returned; check years/states.")

# 50 % dates
out50 = []
keys = sorted({(w["year"], w["state"], w["stage"]) for w in weekly})
for y, st, stage in keys:
    s = sorted((w for w in weekly if (w["year"], w["state"], w["stage"]) == (y, st, stage)),
               key=lambda w: w["week_ending"])
    d50, note = None, ""
    for i, w in enumerate(s):
        if w["pct"] >= 50:
            if i == 0:
                note = "first report already >= 50 %; cannot interpolate"
            else:
                a0, a1 = s[i - 1], w
                t0 = date.fromisoformat(a0["week_ending"]); t1 = date.fromisoformat(a1["week_ending"])
                frac = (50 - a0["pct"]) / (a1["pct"] - a0["pct"]) if a1["pct"] != a0["pct"] else 0
                d50 = t0 + timedelta(days=round(frac * (t1 - t0).days))
                note = f"interpolated between {a0['week_ending']} ({a0['pct']:g}%) and {a1['week_ending']} ({a1['pct']:g}%)"
            break
    else:
        note = "never reached 50 % in the returned reports"
    out50.append({"year": y, "state": st, "stage": stage,
                  "date_50pct": d50.isoformat() if d50 else "", "method": note})
    print(f"{y} {st} {stage:<9} 50% on {d50 or 'n/a'}  ({note})")

tag = f"{'_'.join(a.years)}_{'_'.join(a.states)}"
od = Path(a.outdir); od.mkdir(parents=True, exist_ok=True)
for name, rows in ((f"nass_progress_weekly_{tag}.csv", weekly), (f"nass_progress_50pct_{tag}.csv", out50)):
    with open(od / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("Wrote", od / name)
