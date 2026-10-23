#!/usr/bin/env python

#python plot_results.py control 1
#python plot_results.py control 2
#python plot_results.py control 3
#python plot_results.py control 4


import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

experiment = sys.argv[1]
figure = int(sys.argv[2])

#BASE = (
#    f"/mnt/scratch/olusegu3/geoaquacrop/"
#    f"experiments/{experiment}/outputs"
#)

#summary = pd.read_pickle(
#    f"{BASE}/summary_results.pkl"
#)

#daily = pd.read_pickle(
#    f"{BASE}/daily_results.pkl"
#)


# TEMPORARY
BASE = "/mnt/scratch/olusegu3/geoaquacrop/story2012/outputs"

summary = pd.read_pickle(
    f"{BASE}/summary_results_20261008_111047.pkl"
)

daily = pd.read_pickle(
    f"{BASE}/daily_results_20261008_111047.pkl"
)

summary0 = summary[0]

water = daily[0]["water_flux"].copy()
growth = daily[0]["crop_growth"].copy()

water["Tr_fraction"] = np.where(
    water["TrPot"] > 0,
    water["Tr"] / water["TrPot"],
    np.nan
)

FIG_DIR = (
    "/mnt/scratch/olusegu3/geoaquacrop/figures"
)

# ==================================================
# Figure 1
# Root-zone water
# ==================================================

if figure == 1:

    fig, ax = plt.subplots(figsize=(10,5))

    ax.plot(
        water["dap"],
        water["Wr"],
        lw=2
    )

    ax.set_title(
        f"{experiment}: Root-zone Water"
    )

    ax.set_xlabel("DAP")
    ax.set_ylabel("Wr (mm)")

    plt.tight_layout()

    plt.savefig(
        f"{FIG_DIR}/{experiment}_fig1_wr.png",
        dpi=300
    )

# ==================================================
# Figure 2
# Canopy cover
# ==================================================

elif figure == 2:

    fig, ax = plt.subplots(figsize=(10,5))

    ax.plot(
        growth["dap"],
        growth["canopy_cover"],
        lw=2
    )

    ax.set_title(
        f"{experiment}: Canopy Cover"
    )

    ax.set_xlabel("DAP")
    ax.set_ylabel("Canopy Cover")

    plt.tight_layout()

    plt.savefig(
        f"{FIG_DIR}/{experiment}_fig2_canopy.png",
        dpi=300
    )

# ==================================================
# Figure 3
# Biomass
# ==================================================

elif figure == 3:

    fig, ax = plt.subplots(figsize=(10,5))

    ax.plot(
        growth["dap"],
        growth["biomass"],
        lw=2
    )

    ax.set_title(
        f"{experiment}: Biomass"
    )

    ax.set_xlabel("DAP")
    ax.set_ylabel("Biomass")

    plt.tight_layout()

    plt.savefig(
        f"{FIG_DIR}/{experiment}_fig3_biomass.png",
        dpi=300
    )

# ==================================================
# Figure 4
# Wr and Tr/TrPot
# ==================================================

elif figure == 4:

    fig, ax1 = plt.subplots(figsize=(10,5))

    ax1.plot(
        water["dap"],
        water["Wr"],
        color="blue"
    )

    ax1.set_xlabel("DAP")
    ax1.set_ylabel(
        "Root-zone Water (mm)",
        color="blue"
    )

    ax2 = ax1.twinx()

    ax2.plot(
        water["dap"],
        water["Tr_fraction"],
        color="red"
    )

    ax2.set_ylabel(
        "Tr / TrPot",
        color="red"
    )

    plt.title(
        f"{experiment}: Water Availability and Transpiration"
    )

    plt.tight_layout()

    plt.savefig(
        f"{FIG_DIR}/{experiment}_fig4_wr_tr.png",
        dpi=300
    )


# ==================================================
# Figure 5
# Growth stages
# ==================================================

elif figure == 5:

    fig, ax = plt.subplots(
        figsize=(10,5)
    )

    ax.plot(
        growth["dap"],
        growth["canopy_cover"],
        label="Canopy Cover"
    )

    ax.plot(
        growth["dap"],
        growth["biomass"] /
        growth["biomass"].max(),
        label="Scaled Biomass"
    )

    ax.axvline(
        72,
        ls="--",
        color="red",
        label="Reproductive Onset"
    )

    ax.set_xlabel("DAP")
    ax.set_ylabel("Relative Value")

    ax.legend()

    plt.tight_layout()

    plt.savefig(
        f"{FIG_DIR}/{experiment}_fig5_growth_stages.png",
        dpi=300
    )


elif figure == 6:

    fig, ax = plt.subplots(
        figsize=(10,5)
    )

    ax.plot(
        growth["dap"],
        growth["harvest_index"],
        lw=2
    )

    ax.axvline(
        72,
        color="red",
        ls="--",
        label="Reproductive onset"
    )

    ax.set_xlabel("DAP")
    ax.set_ylabel("Harvest Index")
    ax.set_title(
        f"{experiment}: Harvest Index Development"
    )

    ax.legend()

    plt.tight_layout()

    plt.savefig(
        f"{FIG_DIR}/{experiment}_fig6_harvest_index.png",
        dpi=300,
        bbox_inches="tight"
    )

else:

    print(
        "Figure not implemented."
    )
