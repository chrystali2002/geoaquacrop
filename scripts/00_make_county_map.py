#!/usr/bin/env python

# Examples:
#
# Story County, IA
# python 00_make_county_map.py 19169 Story
#
# Champaign County, IL
# python 00_make_county_map.py 17019 Champaign
#
# Lancaster County, NE
# python 00_make_county_map.py 31109 Lancaster

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

# --------------------------------------------------
# INPUTS
# --------------------------------------------------

GEOID = sys.argv[1]
NAME = sys.argv[2]

COUNTIES = (
    "/mnt/scratch/olusegu3/ORNL_plots/"
    "tl_2020_us_county.shp"
)

OUTDIR = (
    f"/mnt/scratch/olusegu3/geoaquacrop/"
    f"locations/{NAME}_{GEOID}"
)

Path(OUTDIR).mkdir(
    parents=True,
    exist_ok=True
)

# --------------------------------------------------
# READ COUNTY FILE
# --------------------------------------------------

counties = gpd.read_file(COUNTIES)

target = counties[
    counties["GEOID"] == GEOID
].copy()

if len(target) == 0:

    raise ValueError(
        f"GEOID {GEOID} not found."
    )

# --------------------------------------------------
# CREATE GEOJSON
# --------------------------------------------------

target4326 = target.to_crs(4326)

geojson_file = (
    f"{OUTDIR}/"
    f"{NAME}_{GEOID}.geojson"
)

target4326.to_file(
    geojson_file,
    driver="GeoJSON"
)

print(
    f"GeoJSON saved:\n{geojson_file}"
)

# --------------------------------------------------
# STATE CONTEXT
# --------------------------------------------------

statefp = target.iloc[0]["STATEFP"]

state = counties[
    counties["STATEFP"] == statefp
]

# --------------------------------------------------
# MAP
# --------------------------------------------------

fig, ax = plt.subplots(
    figsize=(8,8)
)

state.boundary.plot(
    ax=ax,
    color="black",
    linewidth=1
)

target.plot(
    ax=ax,
    color="red",
    edgecolor="black"
)

ax.set_title(
    f"{NAME} County (GEOID {GEOID})"
)

ax.set_axis_off()

outfile = (
    f"{OUTDIR}/"
    f"{NAME}_{GEOID}_map.png"
)

plt.tight_layout()

plt.savefig(
    outfile,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    f"Map saved:\n{outfile}"
)
