#!/usr/bin/env python
"""
21_resilience_metrics.py

Purpose
-------
Quantify buffering, recovery, and stress persistence for the
selected Story County trajectories:

    control_2015
    early_recovery_2015_v2
    late_stress_2015_v3
    dual_stress_2015_v5

Usage
-----
python 21_resilience_metrics.py [site_id] [--out FILE] [--legacy-names] [--grid]

    site_id         row in config/counties.csv and config/phenology.csv
                    (default: story2015)
    --grid          evaluate the control plus every treatments.csv row in group
                    "grid" (24 cells) instead of the hand-selected Story runs;
                    adds veg_mult and rep_mult columns. Rainfall is treated as
                    returning after onset whenever rep_mult > 0.
    --legacy-names  write the original Story column names (Wr72, Wr90, ...)
                    so output can be diffed against story2015_resilience.csv

Reproductive onset, harvest DAP and the DAP at which rainfall is restored
come from config/phenology.csv (written by 03_growth_stage_diagnostics.py).

Outputs
-------
<site_id>_resilience.csv   (or --out)

Metrics
-------
- Yield recovery (%)
- Relative Wr at DAP 72
- Relative Wr at DAP 90
- Mean Tr/TrPot (vegetative)
- Mean Tr/TrPot (reproductive)
- Buffer days
- Recovery days
- Recovery class:
      Tolerant
      Recovered
      Not Recovered
      N/A (no rain return)
"""

import argparse
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# ==================================================
# CONFIG
# ==================================================

ROOT = Path(
    os.environ.get(
        "GEOAQUACROP_ROOT",
        "/mnt/scratch/olusegu3/geoaquacrop"
    )
)

BASE = ROOT / "experiments"
CONFIG = ROOT / "config"

# Selected experiments per site:
#   label -> (experiment folder, does rainfall return at reproductive onset?)
# Add a site here only after its versions were chosen by the written
# selection rule (not by looking at which curve looks best).
RUNS_BY_SITE = {
    "story2015": {
        "Control":
            ("control_2015", False),

        "Early Recovery":
            ("early_recovery_2015_v2", True),

        "Late Stress":
            ("late_stress_2015_v3", False),

        "Late Stress v2 (buffered)":
            ("late_stress_2015_v2", False),

        "Late Stress v1 (buffered)":
            ("late_stress_2015_v1", False),

        "Dual Stress":
            ("dual_stress_2015_v5", False),
    },
}

# second storage checkpoint = reproductive onset + 18 days (DAP 90 at Story)
ONSET_PLUS = 18

YIELD_COL = "Dry yield (tonne/ha)"

THRESH = 0.95
ROLL = 5
CONSEC = 5

# generic output names -> names used in the archived Story table
LEGACY_COLUMNS = {
    "RelWr_onset": "RelWr72",
    "RelWr_onset18": "RelWr90",
    "Wr_onset": "Wr72",
    "Wr_onset18": "Wr90",
    "TrFrac_onset": "TrFrac72",
    "TrFrac_onset18": "TrFrac90",
    "StressedAtOnset": "StressedAtDAP72",
}

parser = argparse.ArgumentParser()
parser.add_argument("site", nargs="?", default="story2015")
parser.add_argument("--out", default=None)
parser.add_argument("--legacy-names", action="store_true")
parser.add_argument("--grid", action="store_true")
args = parser.parse_args()

SITE = args.site

counties = pd.read_csv(CONFIG / "counties.csv")

if SITE not in set(counties["site_id"]):
    sys.exit(f"{SITE} not found in {CONFIG / 'counties.csv'}")

YEAR = int(counties.loc[counties["site_id"] == SITE, "year"].iloc[0])

# Story keeps its legacy folder layout; every other site has its own folder
BASE = (
    ROOT / "experiments"
    if SITE == "story2015"
    else ROOT / "experiments" / SITE
)

GRID_META = {}

if args.grid:

    tr_file = CONFIG / "treatments.csv"
    tr = pd.read_csv(tr_file)
    tr = tr.loc[tr["group"] == "grid"]

    if len(tr) != 24:
        sys.exit(f"Expected 24 grid rows in {tr_file}, found {len(tr)}")

    RUNS_BY_SITE[SITE] = {"Control": (f"control_{YEAR}", False)}
    GRID_META["Control"] = (1.0, 1.0)

    for r in tr.itertuples():
        RUNS_BY_SITE[SITE][r.experiment] = (r.experiment, bool(r.rep_mult > 0))
        GRID_META[r.experiment] = (float(r.veg_mult), float(r.rep_mult))

pheno_file = CONFIG / "phenology.csv"

if not pheno_file.exists():
    sys.exit(
        f"{pheno_file} not found. Run "
        f"03_growth_stage_diagnostics.py {SITE} first."
    )

pheno = pd.read_csv(pheno_file)
pheno = pheno.loc[pheno["site_id"] == SITE]

if len(pheno) != 1:
    sys.exit(
        f"phenology.csv needs exactly one row for {SITE}; found "
        f"{len(pheno)}. Run 03_growth_stage_diagnostics.py {SITE}."
    )

if SITE not in RUNS_BY_SITE:
    sys.exit(f"No selected runs defined for {SITE} in RUNS_BY_SITE")



def phenology_dap(row, dap_col, date_col):
    """DAP from the model's dap column; else from dates (planting + DAP days)."""

    if dap_col in row.index and pd.notna(row[dap_col]):
        return int(row[dap_col]), "dap column"

    if (
        date_col in row.index
        and "planting_date" in row.index
        and pd.notna(row[date_col])
    ):
        days = (
            pd.to_datetime(row[date_col])
            - pd.to_datetime(row["planting_date"])
        ).days
        return int(days), "derived from dates"

    sys.exit(
        f"phenology.csv row for {SITE} has neither '{dap_col}' nor "
        f"'{date_col}' with 'planting_date'. Columns found: "
        f"{list(row.index)}. Run 03_growth_stage_diagnostics.py {SITE} "
        "to regenerate the row."
    )


ONSET, onset_src = phenology_dap(
    pheno.iloc[0], "reproductive_dap", "reproductive_date"
)
HARVEST, harvest_src = phenology_dap(
    pheno.iloc[0], "harvest_dap", "harvest_date"
)
ONSET18 = ONSET + ONSET_PLUS

print(
    f"Phenology ({SITE}): reproductive onset DAP {ONSET} ({onset_src}), "
    f"harvest DAP {HARVEST} ({harvest_src})"
)

if not (0 < ONSET < ONSET18 <= HARVEST):
    sys.exit(
        f"Inconsistent phenology for {SITE}: onset={ONSET}, "
        f"onset+{ONSET_PLUS}={ONSET18}, harvest={HARVEST}"
    )

RUNS = {
    label: BASE / folder
    for label, (folder, _) in RUNS_BY_SITE[SITE].items()
}

# rainfall is restored on the day after reproductive onset
RAIN_RETURN = {
    label: (ONSET + 1 if restores else None)
    for label, (_, restores) in RUNS_BY_SITE[SITE].items()
}

# ==================================================
# HELPERS
# ==================================================

def load_summary(exp_dir):

    f = exp_dir / "outputs" / "summary_results.pkl"

    # list of one-row DataFrames (one per simulated cell)
    return pd.concat(
        pd.read_pickle(f),
        ignore_index=True
    )


def load_daily(exp_dir):

    f = exp_dir / "outputs" / "daily_results.pkl"

    obj = pd.read_pickle(f)

    # average all simulated cells

    wf_list = []

    for cell in obj:

        wf = cell["water_flux"].copy()

        wf_list.append(
            wf[["dap", "Wr", "Tr", "TrPot"]]
        )

    merged = (
        pd.concat(wf_list)
        .groupby("dap")
        .mean()
        .reset_index()
    )

    merged["Tr_fraction"] = (
        merged["Tr"]
        / merged["TrPot"]
    )

    merged["Tr_fraction"] = (
        merged["Tr_fraction"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
    )

    return merged


def first_consecutive(mask, n):

    count = 0

    for idx, value in enumerate(mask):

        if value:
            count += 1

            if count >= n:
                return idx - n + 1

        else:
            count = 0

    return None


# ==================================================
# LOAD CONTROL
# ==================================================

control_daily = load_daily(
    RUNS["Control"]
)

control_summary = load_summary(
    RUNS["Control"]
)

yield_control = (
    control_summary[YIELD_COL]
    .mean()
)

wr72_control = (
    control_daily
    .query("dap == @ONSET")
    ["Wr"]
    .iloc[0]
)

wr90_control = (
    control_daily
    .query("dap == @ONSET18")
    ["Wr"]
    .iloc[0]
)

# ==================================================
# MAIN LOOP
# ==================================================

results = []

for name, exp_dir in RUNS.items():

    daily = load_daily(exp_dir)
    summary = load_summary(exp_dir)

    yield_actual = (
        summary[YIELD_COL]
        .mean()
    )

    yield_recovery = (
        yield_actual
        / yield_control
        * 100
    )

    wr72 = (
        daily.query("dap == @ONSET")
        ["Wr"]
        .iloc[0]
    )

    wr90 = (
        daily.query("dap == @ONSET18")
        ["Wr"]
        .iloc[0]
    )

    rel_wr72 = (
        wr72 / wr72_control
    )

    rel_wr90 = (
        wr90 / wr90_control
    )

    tr72 = (
        daily.query("dap == @ONSET")
        ["Tr_fraction"]
        .iloc[0]
    )

    tr90 = (
        daily.query("dap == @ONSET18")
        ["Tr_fraction"]
        .iloc[0]
    )

    # mean of per-cell gaps (13_compare_versions may use a ratio of means)
    yield_gap_pct = (
        (
            summary["Yield potential (tonne/ha)"]
            - summary[YIELD_COL]
        )
        / summary["Yield potential (tonne/ha)"]
        * 100
    ).mean()

    daily["roll"] = (
        daily["Tr_fraction"]
        .rolling(
            ROLL,
            min_periods=ROLL
        )
        .mean()
    )

    veg = daily[
        daily["dap"] <= ONSET
    ]

    rep = daily[
        daily["dap"] > ONSET
    ]

    mean_tr_veg = (
        veg["Tr_fraction"]
        .mean()
    )

    mean_tr_rep = (
        rep["Tr_fraction"]
        .mean()
    )

    recovery_state = "Tolerant"
    recovery_days = np.nan
    buffer_days = np.nan

    below = (
        daily["roll"] < THRESH
    )

    onset_idx = first_consecutive(
        below.fillna(False).values,
        CONSEC
    )

    if onset_idx is not None:

        onset_dap = int(daily.iloc[onset_idx]["dap"])

        rain_return = RAIN_RETURN[name]

        if rain_return is None:

            recovery_state = (
                "N/A (no rain return)"
            )

        else:

            after = (
                (daily["roll"] >= THRESH)
                & (daily["dap"] > onset_dap)
            )

            rec_idx = first_consecutive(
                after.fillna(False).values,
                CONSEC
            )

            if rec_idx is None:

                recovery_state = (
                    "Not Recovered"
                )

            else:

                recovery_state = (
                    "Recovered"
                )

                recovery_day = (
                    int(
                        daily.iloc[
                            rec_idx
                        ]["dap"]
                    )
                    - (ROLL - 1)
                )

                recovery_days = (
                    recovery_day
                    - rain_return
                )

    post72 = daily[
        daily["dap"] > ONSET
    ]

    first_stress = post72[
        post72["roll"] < THRESH
    ]

    stressed_at_72 = bool(
        daily.loc[daily["dap"] == ONSET, "roll"].iloc[0] < THRESH
    )
    buffer_censored = False

    if not stressed_at_72:

        if len(first_stress) > 0:

            buffer_days = (
                int(
                    first_stress
                    .iloc[0]["dap"]
                )
                - ONSET
            )

        else:

            # never stressed after DAP 72: buffer lasted to harvest
            buffer_days = HARVEST - ONSET
            buffer_censored = True

    if name == "Control":
        # nothing to buffer in the reference run
        buffer_days = np.nan
        buffer_censored = False

    results.append(
        {
            "Trajectory": name,

            **(
                {
                    "veg_mult": GRID_META[name][0],
                    "rep_mult": GRID_META[name][1],
                }
                if args.grid
                else {}
            ),

            "Yield_t_ha":
                round(yield_actual, 2),

            "YieldRecoveryPct":
                round(
                    yield_recovery,
                    1
                ),

            "RelWr_onset":
                round(
                    rel_wr72,
                    3
                ),

            "RelWr_onset18":
                round(
                    rel_wr90,
                    3
                ),

            "Wr_onset":
                round(wr72, 1),

            "Wr_onset18":
                round(wr90, 1),

            "TrFrac_onset":
                round(tr72, 3),

            "TrFrac_onset18":
                round(tr90, 3),

            "MeanTrVeg":
                round(
                    mean_tr_veg,
                    3
                ),

            "MeanTrRep":
                round(
                    mean_tr_rep,
                    3
                ),

            "BufferDays":
                buffer_days,

            "RecoveryDays":
                recovery_days,

            "StressedAtOnset":
                stressed_at_72,

            "BufferCensored":
                buffer_censored,

            "State":
                recovery_state,

            "YieldGapPct":
                round(yield_gap_pct, 1),

            "SeasonalPrecip":
                round(
                    summary["seasonal_precip_mm"].mean(),
                    1
                ),

            "SeasonalTrans":
                round(
                    summary["seasonal_transpiration_mm"].mean(),
                    1
                )
        }
    )

# ==================================================
# SAVE
# ==================================================

df = pd.DataFrame(results)

if args.legacy_names:
    df = df.rename(columns=LEGACY_COLUMNS)

outfile = args.out or (
    f"{SITE}_grid_resilience.csv" if args.grid else f"{SITE}_resilience.csv"
)

df.to_csv(
    outfile,
    index=False
)

print("\n")
print("=" * 80)
print("RESILIENCE METRICS")
print("=" * 80)
print(df)
print("\nSaved:", outfile)
