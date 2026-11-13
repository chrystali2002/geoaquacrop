#!/usr/bin/env python
"""
25_register_crossstate_sites.py

Register the 27 cross-state counties (config/crossstate_counties.csv) as sites,
using the existing 00_make_county_map.py (domain shape) and 00_register_site.py.

Usage
-----
python 25_register_crossstate_sites.py --dry-run     # print what would be done
python 25_register_crossstate_sites.py               # do it
python 25_register_crossstate_sites.py --states IA IL [--year 2015]

Behaviour
---------
* Refuses to run unless the git tag `crossstate_counties_selected` exists
  (the selection must be frozen before any new county is registered or run);
  override only for testing with --skip-tag-check.
* site_id = <county lower-case, spaces -> underscores><year> (the 00_register_site
  convention). A collision with an existing site_id for a different GEOID stops the run.
* Existing sites and existing domain shapes are skipped, never overwritten.
* Writes config/crossstate_sites.csv (state, fips, county, tercile, site_id) for
  the run wrapper and the summary script. Nothing is downloaded or run here
  except the two small helper scripts (county map = a shapefile clip).
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
CONFIG = ROOT / "config"
SCRIPTS = Path(__file__).resolve().parent
TAG = "crossstate_counties_selected"

ap = argparse.ArgumentParser()
ap.add_argument("--year", type=int, default=2015)
ap.add_argument("--states", nargs="*", default=None)
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--skip-tag-check", action="store_true")
args = ap.parse_args()

if not args.skip_tag_check:
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "-q", "--verify", f"refs/tags/{TAG}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Tag {TAG} not found in {ROOT}: commit and tag the county selection first.")

sel = pd.read_csv(CONFIG / "crossstate_counties.csv", dtype={"fips": str})
sel = sel[sel["selected"].astype(str).str.lower() == "true"].copy()
if args.states:
    sel = sel[sel["state"].isin([s.upper() for s in args.states])]
if sel.empty:
    sys.exit("No selected counties to register.")

sel["fips"] = sel["fips"].str.zfill(5)
sel["county_name"] = sel["county"].str.title()
sel["site_id"] = (sel["county"].str.lower().str.replace(r"[^a-z0-9]+", "_", regex=True)
                  .str.strip("_") + str(args.year))

dup = sel[sel["site_id"].duplicated(keep=False)]
if len(dup):
    sys.exit(f"Duplicate site_id within the selection:\n{dup[['state','fips','county','site_id']]}")

existing = pd.read_csv(CONFIG / "counties.csv", dtype={"geoid": str})
clash = existing.merge(sel, on="site_id", suffixes=("_old", ""))
clash = clash[clash["geoid"].str.zfill(5) != clash["fips"]]
if len(clash):
    sys.exit(f"site_id already used for a different county:\n{clash[['site_id','geoid','fips']]}")


def run(cmd):
    print("  $", " ".join(map(str, cmd)))
    if not args.dry_run:
        subprocess.run(cmd, check=True)


for _, r in sel.iterrows():
    print(f"{r.state} {r.county_name} ({r.fips})  ->  {r.site_id}")
    shape_dir = ROOT / "locations" / f"{r.county_name}_{r.fips}"
    if list(shape_dir.glob("*.geojson")):
        print("  domain shape exists, skipping")
    else:
        run([sys.executable, str(SCRIPTS / "00_make_county_map.py"), r.fips, r.county_name])
    if ((existing["site_id"] == r.site_id).any()):
        print("  already registered, skipping")
    else:
        run([sys.executable, str(SCRIPTS / "00_register_site.py"), "--geoid", r.fips,
             "--county", r.county_name, "--state", r.state, "--year", str(args.year),
             "--site-id", r.site_id])

out = sel[["state", "fips", "county_name", "tercile", "site_id"]].rename(columns={"county_name": "county"})
if not args.dry_run:
    out.to_csv(CONFIG / "crossstate_sites.csv", index=False)
    print(f"Wrote {CONFIG / 'crossstate_sites.csv'} ({len(out)} sites)")
else:
    print(f"[dry run] would write {CONFIG / 'crossstate_sites.csv'} ({len(out)} sites)")
