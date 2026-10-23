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

Outputs
-------
resilience_metrics.csv

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

from pathlib import Path
import pickle
import numpy as np
import pandas as pd

# ==================================================
# CONFIG
# ==================================================

BASE = Path(
    "/mnt/scratch/olusegu3/geoaquacrop/experiments"
)

RUNS = {
    "Control":
        BASE / "control_2015",

    "Early Recovery":
        BASE / "early_recovery_2015_v2",

    "Late Stress":
        BASE / "late_stress_2015_v3",

    "Late Stress v2 (buffered)":
        BASE / "late_stress_2015_v2",

    "Late Stress v1 (buffered)":
        BASE / "late_stress_2015_v1",

    "Dual Stress":
        BASE / "dual_stress_2015_v5"
}

D72 = 72
D90 = 90
HARVEST = 137

YIELD_COL = "Dry yield (tonne/ha)"

THRESH = 0.95
ROLL = 5
CONSEC = 5

# only Early Recovery has rainfall restoration
RAIN_RETURN = {
    "Control": None,
    "Early Recovery": 73,
    "Late Stress": None,
    "Late Stress v2 (buffered)": None,
    "Late Stress v1 (buffered)": None,
    "Dual Stress": None
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
    .query("dap == @D72")
    ["Wr"]
    .iloc[0]
)

wr90_control = (
    control_daily
    .query("dap == @D90")
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
        daily.query("dap == @D72")
        ["Wr"]
        .iloc[0]
    )

    wr90 = (
        daily.query("dap == @D90")
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
        daily.query("dap == @D72")
        ["Tr_fraction"]
        .iloc[0]
    )

    tr90 = (
        daily.query("dap == @D90")
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
        daily["dap"] <= D72
    ]

    rep = daily[
        daily["dap"] > D72
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
        daily["dap"] > D72
    ]

    first_stress = post72[
        post72["roll"] < THRESH
    ]

    stressed_at_72 = bool(
        daily.loc[daily["dap"] == D72, "roll"].iloc[0] < THRESH
    )
    buffer_censored = False

    if not stressed_at_72:

        if len(first_stress) > 0:

            buffer_days = (
                int(
                    first_stress
                    .iloc[0]["dap"]
                )
                - D72
            )

        else:

            # never stressed after DAP 72: buffer lasted to harvest
            buffer_days = HARVEST - D72
            buffer_censored = True

    if name == "Control":
        # nothing to buffer in the reference run
        buffer_days = np.nan
        buffer_censored = False

    results.append(
        {
            "Trajectory": name,

            "Yield_t_ha":
                round(yield_actual, 2),

            "YieldRecoveryPct":
                round(
                    yield_recovery,
                    1
                ),

            "RelWr72":
                round(
                    rel_wr72,
                    3
                ),

            "RelWr90":
                round(
                    rel_wr90,
                    3
                ),

            "Wr72":
                round(wr72, 1),

            "Wr90":
                round(wr90, 1),

            "TrFrac72":
                round(tr72, 3),

            "TrFrac90":
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

            "StressedAtDAP72":
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

outfile = (
    "resilience_metrics.csv"
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
