#!/usr/bin/env python
"""
00_register_site.py

Register a county in config/counties.csv (the first step of the pipeline).

Usage
-----
python 00_register_site.py \
    --geoid 19169 \
    --county Story \
    --state IA \
    --year 2015

python 00_register_site.py --geoid 17019 --county Champaign --state IL \
       [--year 2015] [--crop maize] [--site-id champaign2015] [--update]

site_id defaults to <county lower-case, underscores><year>, e.g. champaign2015.
An existing site_id is never overwritten unless --update is given.
"""

import argparse
import os
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(
    os.environ.get(
        "GEOAQUACROP_ROOT",
        "/mnt/scratch/olusegu3/geoaquacrop"
    )
)

CONFIG = ROOT / "config"
FILE = CONFIG / "counties.csv"
COLUMNS = ["site_id", "geoid", "county", "state", "year", "crop"]

parser = argparse.ArgumentParser()
parser.add_argument("--geoid", required=True)
parser.add_argument("--county", required=True)
parser.add_argument("--state", required=True)
parser.add_argument("--year", type=int, default=2015)
parser.add_argument("--crop", default="maize")
parser.add_argument("--site-id", default=None)
parser.add_argument("--update", action="store_true")
args = parser.parse_args()

# state FIPS prefixes (first two digits of a county GEOID)
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15",
    "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
    "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
    "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
    "WV": "54", "WI": "55", "WY": "56",
}

geoid = str(args.geoid).strip()

# a leading zero is lost when a GEOID passes through a number (1001 -> 01001)
if len(geoid) == 4:
    geoid = geoid.zfill(5)

if not re.fullmatch(r"\d{5}", geoid):
    sys.exit(f"GEOID must be 5 digits (state + county FIPS); got {args.geoid!r}")

state = args.state.strip().upper()

if not re.fullmatch(r"[A-Z]{2}", state):
    sys.exit(f"State must be a 2-letter code; got {args.state!r}")

if state in STATE_FIPS and geoid[:2] != STATE_FIPS[state]:
    sys.exit(
        f"GEOID {geoid} starts with {geoid[:2]}, but {state} is "
        f"{STATE_FIPS[state]}. Check the GEOID or the state."
    )

county = args.county.strip()

site_id = args.site_id or (
    re.sub(r"[^a-z0-9]+", "_", county.lower()).strip("_") + str(args.year)
)

row = {
    "site_id": site_id,
    "geoid": geoid,
    "county": county,
    "state": state,
    "year": args.year,
    "crop": args.crop.strip().lower(),
}

# keep GEOID as text so leading zeros (e.g. 01001) survive
if FILE.exists():
    table = pd.read_csv(FILE, dtype={"geoid": str})
else:
    CONFIG.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(columns=COLUMNS)

if site_id in set(table["site_id"]):
    if not args.update:
        sys.exit(
            f"{site_id} is already registered. Use --update to replace it."
        )
    table = table.loc[table["site_id"] != site_id]

same = table[(table["geoid"] == geoid) & (table["year"] == args.year)]

if len(same):
    print(
        f"WARNING: GEOID {geoid} / {args.year} already registered as "
        f"{list(same['site_id'])}"
    )

table = pd.concat([table, pd.DataFrame([row])], ignore_index=True)
table = table[COLUMNS].sort_values("site_id")
table.to_csv(FILE, index=False)

print("Registered:", row)
print("Wrote", FILE)
