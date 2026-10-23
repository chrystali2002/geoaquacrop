#!/usr/bin/env python

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12,5))

# --------------------------------------------------
# Base timeline
# --------------------------------------------------

ax.plot([0,137],[5,5], lw=3, color="black")

ax.axvline(
    72,
    color="black",
    ls="--",
    lw=2
)

ax.text(0,5.4,"Planting\nDAP 0")
ax.text(72,5.4,"Reproductive\nOnset\nDAP 72")
ax.text(137,5.4,"Harvest\nDAP 137")

# --------------------------------------------------
# Control
# --------------------------------------------------

ax.hlines(
    y=4,
    xmin=0,
    xmax=137,
    color="black",
    lw=8
)

ax.text(
    -10,
    4,
    "Control",
    va="center"
)

# --------------------------------------------------
# Early Recovery
# --------------------------------------------------

ax.hlines(
    y=3,
    xmin=0,
    xmax=72,
    color="orange",
    lw=8
)

ax.hlines(
    y=3,
    xmin=72,
    xmax=137,
    color="lightgray",
    lw=8
)

ax.text(
    -20,
    3,
    "Early Recovery",
    va="center"
)

# --------------------------------------------------
# Late Stress
# --------------------------------------------------

ax.hlines(
    y=2,
    xmin=0,
    xmax=72,
    color="lightgray",
    lw=8
)

ax.hlines(
    y=2,
    xmin=72,
    xmax=137,
    color="green",
    lw=8
)

ax.text(
    -15,
    2,
    "Late Stress",
    va="center"
)

# --------------------------------------------------
# Dual Stress
# --------------------------------------------------

ax.hlines(
    y=1,
    xmin=0,
    xmax=137,
    color="red",
    lw=8
)

ax.text(
    -12,
    1,
    "Dual Stress",
    va="center"
)

# --------------------------------------------------

ax.set_xlim(-5,140)
ax.set_ylim(0,6)

ax.set_xlabel("Days After Planting (DAP)")
ax.set_yticks([])

ax.set_title(
    "GeoAquaCrop Experimental Design"
)

plt.tight_layout()

plt.savefig(
    "/mnt/scratch/olusegu3/geoaquacrop/figures/experimental_timeline.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(
    "/mnt/scratch/olusegu3/geoaquacrop/figures/experimental_timeline.png"
)
