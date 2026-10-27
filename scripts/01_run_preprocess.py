#!/usr/bin/env python
"""
01_run_preprocess.py

Download and prepare model inputs for a registered site.

Usage
-----
python 01_run_preprocess.py --site champaign2015
                            [--domain-shape FILE] [--resolution 0.05]
                            [--force]

Domain shape: --domain-shape, else for story2015 the legacy file
<root>/story2012/story_county_wgs84.geojson, else the single .geojson under
<root>/locations/*<geoid>*/.

CDS API token: environment variable CDS_API_TOKEN, or the first line of
~/.cds_api_token. It is never read from, or written to, this repository.

Output: <root>/<site_id>/processed  (the pristine baseline used by 02 and 04).
An existing baseline is never overwritten unless --force is given.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import geoaquacrop as gac

ROOT = Path(
    os.environ.get(
        "GEOAQUACROP_ROOT",
        "/mnt/scratch/olusegu3/geoaquacrop"
    )
)

CONFIG = ROOT / "config"

parser = argparse.ArgumentParser()
parser.add_argument("--site", required=True)
parser.add_argument("--domain-shape", default=None)
parser.add_argument("--resolution", type=float, default=0.05)
parser.add_argument("--force", action="store_true")
args = parser.parse_args()

SITE = args.site

counties = pd.read_csv(CONFIG / "counties.csv", dtype={"geoid": str})
match = counties.loc[counties["site_id"] == SITE]

if len(match) != 1:
    sys.exit(f"{SITE} must appear exactly once in {CONFIG / 'counties.csv'}")

GEOID = str(match.iloc[0]["geoid"]).zfill(5)
YEAR = int(match.iloc[0]["year"])

# --------------------------------------------------
# Domain shape
# --------------------------------------------------

if args.domain_shape:
    shape = Path(args.domain_shape)
elif SITE == "story2015":
    shape = ROOT / "story2012" / "story_county_wgs84.geojson"   # legacy
else:
    hits = sorted(set((ROOT / "locations").glob(f"*{GEOID}*/**/*.geojson")))
    if len(hits) != 1:
        sys.exit(
            f"Expected exactly one .geojson under locations/*{GEOID}*/, "
            f"found {len(hits)}: {[str(h) for h in hits]}. "
            "Pass --domain-shape explicitly."
        )
    shape = hits[0]

if not shape.exists():
    sys.exit(f"Domain shape not found: {shape}")

# --------------------------------------------------
# Token (never printed, never stored)
# --------------------------------------------------

token = os.environ.get("CDS_API_TOKEN", "").strip()

if not token:
    tokfile = Path.home() / ".cds_api_token"
    if tokfile.exists():
        token = tokfile.read_text().splitlines()[0].strip()

if not token:
    sys.exit(
        "No CDS API token. Set CDS_API_TOKEN or put it on the first line of "
        "~/.cds_api_token (outside the repository)."
    )

# --------------------------------------------------
# Guard: never overwrite an existing baseline
# --------------------------------------------------

workdir = ROOT / SITE
processed = workdir / "processed"

if processed.exists() and not args.force:
    sys.exit(
        f"{processed} already exists. It is the baseline for 02 and 04 "
        "and is not overwritten without --force."
    )

# the library writes template_grid.nc here and does not create the folder;
# netCDF4 reports a missing folder as "PermissionError: [Errno 13]"
workdir.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Global inputs shared by all sites (symlinked, never re-downloaded)
# --------------------------------------------------
# The library skips a download when the unpacked folder already exists in the
# site's own rawdata/. These two datasets are global, so one copy serves every
# site. Seed it once, e.g. from Story:
#   mkdir -p <root>/shared_inputs/rawdata/cropcalendar <root>/shared_inputs/rawdata/cropmasks
#   cp -r <root>/story2015/rawdata/cropcalendar/ggcmi_cropcalendar <root>/shared_inputs/rawdata/cropcalendar/
#   cp -r <root>/story2015/rawdata/cropmasks/spam2010_physical_area <root>/shared_inputs/rawdata/cropmasks/
SHARED = ROOT / "shared_inputs"
SHARED_ITEMS = [
    Path("rawdata/cropcalendar/ggcmi_cropcalendar"),
    Path("rawdata/cropmasks/spam2010_physical_area"),
]

for rel in SHARED_ITEMS:
    src, dst = SHARED / rel, workdir / rel
    if dst.exists():
        print(f"Shared input already in place: {rel}")
    elif src.is_dir():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src.resolve(), target_is_directory=True)
        print(f"Linked shared input: {rel} -> {src}")
    else:
        print(f"No shared copy of {rel}; the library will download it.")

print(f"Site {SITE}  GEOID {GEOID}  year {YEAR}")
print(f"Domain shape: {shape}")
print(f"Working directory: {workdir}")

gac.preprocess.run(
    domain_shape_path=str(shape),
    start_year=YEAR,
    end_year=YEAR,
    api_token=token,
    cell_resolution=args.resolution,
    workingdirectory=str(workdir)
)

record = {
    "site_id": SITE,
    "geoid": GEOID,
    "year": YEAR,
    "domain_shape": str(shape),
    "domain_shape_sha256": hashlib.sha256(shape.read_bytes()).hexdigest(),
    "cell_resolution": args.resolution,
    "geoaquacrop_version": getattr(gac, "__version__", "unknown"),
    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
}

workdir.mkdir(parents=True, exist_ok=True)

(workdir / "preprocess_record.json").write_text(
    json.dumps(record, indent=2)
)

print(f"\nDone. Record: {workdir / 'preprocess_record.json'}")
