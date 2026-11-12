#!/usr/bin/env python
"""
23_plot_response_surface.py

Response-surface heatmaps for any number of sites, from the grid results written by
21_resilience_metrics.py --grid (<dir>/<site>_grid_resilience.csv).

  row 1: one panel per site   (metric over the vegetative x reproductive rainfall grid)
  row 2: one difference panel per non-reference site (site - reference), diverging scale
         centred on 0; with a single site there is no second row

Usage
-----
python 23_plot_response_surface.py SITE [SITE ...] [--reference SITE]
        [--metric YieldRecoveryPct] [--dir DIR] [--out PREFIX]
        [--formats png svg] [--theme light|dark] [--decimals N]
        [--no-states] [--no-outlines] [--flag-diff PP | --no-flag-diff]
        [--vmin X --vmax Y] [--diff-lim L]

Examples
--------
python 23_plot_response_surface.py story2015 champaign2015
python 23_plot_response_surface.py story2015 champaign2015 nebraska2015 --reference story2015
python 23_plot_response_surface.py champaign2015 --metric RelWr_onset18

Reading the grid: rows = vegetative-window rainfall (100% at top), columns =
reproductive-window rainfall (100% at left), so stress increases down and to the right.
Letters in cells = State from script 21: T Tolerant, R Recovered, NR Not Recovered,
n/a stress with no rainfall return. Heavy outline = H1 cells, dashed = H2 cells
(from docs/champaign_experiment_plan.md). In difference panels a bold outline marks
|difference| above --flag-diff (default 10 pp for YieldRecoveryPct = the H3 limit).
Sequential ramp: one hue, darker = higher. Difference ramp: blue = site above the
reference, red = below, gray = no difference.
"""
import argparse
import textwrap, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm, to_rgb
from matplotlib.patches import Rectangle

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))

# ---- palette: blue sequential ramp and blue<->red diverging pair (reference palette) ----
SEQ_LIGHT = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  mid="#f0efec", seq=SEQ_LIGHT,
                  blue_arm=["#b7d3f6", "#2a78d6", "#0d366b"], red_arm=["#f4b7ae", "#e34948", "#8c1d1d"]),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781",
                 mid="#383835", seq=SEQ_LIGHT[::-1],
                 blue_arm=["#184f95", "#3987e5", "#9ec5f4"], red_arm=["#8c2f2f", "#e66767", "#f4a8a8"]),
}

METRIC_LABEL = {
    "YieldRecoveryPct": ("Yield recovery (% of site control)", 0),
    "Yield_t_ha": ("Dry yield (t/ha)", 2),
    "RelWr_onset": ("Root-zone water at onset (relative to control)", 2),
    "RelWr_onset18": ("Root-zone water at onset + 18 d (relative to control)", 2),
    "TrFrac_onset": ("Tr/TrPot at onset", 2),
    "TrFrac_onset18": ("Tr/TrPot at onset + 18 d", 2),
    "MeanTrRep": ("Mean Tr/TrPot, reproductive window", 2),
    "MeanTrVeg": ("Mean Tr/TrPot, vegetative window", 2),
    "BufferDays": ("Buffer days after reproductive onset", 0),
    "RecoveryDays": ("Recovery days after rainfall returns", 0),
    "YieldGapPct": ("Yield gap to potential (%)", 1),
    "SeasonalPrecip": ("Seasonal precipitation (mm)", 0),
    "SeasonalTrans": ("Seasonal transpiration (mm)", 0),
}
STATE_CODE = {"Tolerant": "T", "Recovered": "R", "Not Recovered": "NR", "N/A (no rain return)": "n/a"}

p = argparse.ArgumentParser()
p.add_argument("sites", nargs="+")
p.add_argument("--reference", default=None)
p.add_argument("--metric", default="YieldRecoveryPct")
p.add_argument("--dir", default=str(ROOT / "results"))
p.add_argument("--out", default=None, help="output path prefix, no extension")
p.add_argument("--formats", nargs="+", default=["png"])
p.add_argument("--theme", choices=THEMES, default="light")
p.add_argument("--decimals", type=int, default=None)
p.add_argument("--no-states", action="store_true")
p.add_argument("--no-outlines", action="store_true")
p.add_argument("--flag-diff", type=float, default=None)
p.add_argument("--no-flag-diff", action="store_true")
p.add_argument("--vmin", type=float); p.add_argument("--vmax", type=float)
p.add_argument("--diff-lim", type=float)
a = p.parse_args()

TH = THEMES[a.theme]
sites = list(dict.fromkeys(a.sites))
ref = a.reference or sites[0]
if ref not in sites:
    sys.exit(f"--reference {ref} must be one of the sites: {sites}")
sites = [ref] + [s for s in sites if s != ref]
d = Path(a.dir)

label, default_dec = METRIC_LABEL.get(a.metric, (a.metric, 1))
dec = default_dec if a.decimals is None else a.decimals
flag = None if a.no_flag_diff else (a.flag_diff if a.flag_diff is not None
                                    else (10.0 if a.metric == "YieldRecoveryPct" else None))

# site titles from counties.csv when available
names = {}
cf = ROOT / "config" / "counties.csv"
if cf.exists():
    c = pd.read_csv(cf)
    for r in c.itertuples():
        names[r.site_id] = f"{r.county} County, {r.state}"


def load(site):
    f = d / f"{site}_grid_resilience.csv"
    if not f.exists():
        sys.exit(f"{f} not found. Run: python 21_resilience_metrics.py {site} --grid --out {f}")
    df = pd.read_csv(f)
    for col in ("veg_mult", "rep_mult", a.metric):
        if col not in df.columns:
            sys.exit(f"{f} has no column '{col}' (columns: {list(df.columns)})")
    df["veg_mult"], df["rep_mult"] = df["veg_mult"].round(2), df["rep_mult"].round(2)
    if df.duplicated(["veg_mult", "rep_mult"]).any():
        sys.exit(f"{f}: duplicate (veg_mult, rep_mult) rows")
    return df


data = {s: load(s) for s in sites}
veg_levels = sorted(set().union(*[set(df.veg_mult) for df in data.values()]), reverse=True)   # 1.0 at top
rep_levels = sorted(set().union(*[set(df.rep_mult) for df in data.values()]), reverse=True)   # 1.0 at left
nr, nc = len(veg_levels), len(rep_levels)


def matrix(df, col):
    m = np.full((nr, nc), np.nan)
    idx = df.set_index(["veg_mult", "rep_mult"])
    for i, v in enumerate(veg_levels):
        for j, r in enumerate(rep_levels):
            if (v, r) in idx.index:
                m[i, j] = idx.loc[(v, r), col]
    return m


def state_matrix(df):
    s = np.full((nr, nc), "", dtype=object)
    if "State" in df.columns:
        idx = df.set_index(["veg_mult", "rep_mult"])
        for i, v in enumerate(veg_levels):
            for j, r in enumerate(rep_levels):
                if (v, r) in idx.index:
                    s[i, j] = STATE_CODE.get(idx.loc[(v, r), "State"], "?")
    return s


M = {s: matrix(data[s], a.metric) for s in sites}
S = {s: state_matrix(data[s]) for s in sites}

# colour scales
allv = np.concatenate([m[~np.isnan(m)] for m in M.values()])
if allv.size == 0:
    sys.exit("no numeric values to plot")
vmin = a.vmin if a.vmin is not None else (np.floor(allv.min() / 10) * 10 if a.metric == "YieldRecoveryPct" else allv.min())
vmax = a.vmax if a.vmax is not None else (100.0 if a.metric == "YieldRecoveryPct" else allv.max())
if vmax <= vmin:
    vmax = vmin + 1
seq_cmap = LinearSegmentedColormap.from_list("seq", TH["seq"])
seq_norm = Normalize(vmin, vmax)

diffs = {s: M[s] - M[ref] for s in sites[1:]}
if diffs:
    dmax = max(np.nanmax(np.abs(m)) for m in diffs.values())
    lim = a.diff_lim if a.diff_lim else max(5.0 if a.metric == "YieldRecoveryPct" else 1e-9,
                                            np.ceil(dmax / 5) * 5 if a.metric == "YieldRecoveryPct" else dmax)
    if lim == 0:
        lim = 1.0
    div_cmap = LinearSegmentedColormap.from_list(
        "div", TH["red_arm"][::-1] + [TH["mid"]] + TH["blue_arm"])
    div_norm = TwoSlopeNorm(vcenter=0.0, vmin=-lim, vmax=lim)


def text_color(rgba):
    def lin(c): return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [lin(x) for x in rgba[:3]]
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    ink = to_rgb(TH["ink"]); li = [lin(x) for x in ink]
    Li = 0.2126 * li[0] + 0.7152 * li[1] + 0.0722 * li[2]
    c_white = 1.05 / (L + 0.05)
    c_ink = (max(L, Li) + 0.05) / (min(L, Li) + 0.05)
    return "#ffffff" if c_white >= c_ink else TH["ink"]


def style_axes(ax):
    ax.set_facecolor(TH["surface"])
    ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
    ax.set_xticks(np.arange(nc) + 0.5); ax.set_yticks(np.arange(nr) + 0.5)
    ax.set_xticklabels([f"{int(round(r * 100))}%" for r in rep_levels], fontsize=8, color=TH["ink2"])
    ax.set_yticklabels([f"{int(round(v * 100))}%" for v in veg_levels], fontsize=8, color=TH["ink2"])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel("Reproductive-window rainfall (% of baseline)", fontsize=8.5, color=TH["ink2"])
    ax.set_ylabel("Vegetative-window rainfall (% of baseline)", fontsize=8.5, color=TH["ink2"])


def outline(ax, i, j, lw, ls="-", color=None):
    ax.add_patch(Rectangle((j + 0.04, i + 0.04), 0.92, 0.92, fill=False, lw=lw, ls=ls,
                           ec=color or TH["ink"], zorder=5))


def hypothesis_outlines(ax):
    for i, v in enumerate(veg_levels):
        for j, r in enumerate(rep_levels):
            if v == 1.0 and r <= 0.25:
                outline(ax, i, j, 2.2)                     # H1 cells
            elif v <= 0.25 and r in (1.0, 0.0):
                outline(ax, i, j, 1.6, ls=(0, (3, 2)))      # H2 cells


def panel(ax, mat, cmap, norm, title, fmt, states=None, signed=False, flagged=None, mark_control=False):
    style_axes(ax)
    ax.pcolormesh(np.arange(nc + 1), np.arange(nr + 1), np.ma.masked_invalid(mat), cmap=cmap, norm=norm,
                  edgecolors=TH["surface"], linewidth=2)
    for i in range(nr):
        for j in range(nc):
            v = mat[i, j]
            if np.isnan(v):
                ax.text(j + 0.5, i + 0.5, "–", ha="center", va="center", fontsize=9, color=TH["muted"])
                continue
            col = text_color(cmap(norm(v)))
            s = fmt(v)
            ax.text(j + 0.5, i + (0.42 if states is not None and states[i, j] else 0.5), s,
                    ha="center", va="center", fontsize=9, fontweight="bold" if (flagged is not None and flagged[i, j]) else "bold",
                    color=col, zorder=6)
            if states is not None and states[i, j]:
                ax.text(j + 0.5, i + 0.72, states[i, j], ha="center", va="center", fontsize=7, color=col, zorder=6)
            if flagged is not None and flagged[i, j]:
                outline(ax, i, j, 2.4)
    if mark_control and (1.0 in veg_levels and 1.0 in rep_levels):
        i, j = veg_levels.index(1.0), rep_levels.index(1.0)
        ax.text(j + 0.5, i + 0.12, "control", ha="center", va="center", fontsize=6.5, color=text_color(cmap(norm(mat[i, j]))) if not np.isnan(mat[i, j]) else TH["muted"], zorder=6)
    ax.set_title(title, fontsize=10, color=TH["ink"], loc="left", pad=8, fontweight="bold")


ncols = len(sites)
nrows = 2 if diffs else 1
fig, axes = plt.subplots(nrows, ncols, figsize=(4.0 * ncols + 0.6, 4.1 * nrows + 1.4), squeeze=False,
                         constrained_layout=True, facecolor=TH["surface"])

fmt_val = (lambda v: f"{v:.{dec}f}")
def fmt_diff(v):
    r = round(float(v), dec)
    if r == 0:
        return f"{0:.{dec}f}"
    return ("+" if r > 0 else "−") + f"{abs(r):.{dec}f}"

for k, s in enumerate(sites):
    ax = axes[0, k]
    t = names.get(s, s) + (f"  ·  {s}" if s in names else "") + ("  (reference)" if (s == ref and len(sites) > 1) else "")
    panel(ax, M[s], seq_cmap, seq_norm, t, fmt_val, states=None if a.no_states else S[s], mark_control=True)
    if not a.no_outlines:
        hypothesis_outlines(ax)

if diffs:
    for k, s in enumerate(sites[1:], start=1):
        flagged = (np.abs(diffs[s]) > flag) & ~np.isnan(diffs[s]) if flag is not None else None
        unit = " pp" if a.metric == "YieldRecoveryPct" else ""
        panel(axes[1, k], diffs[s], div_cmap, div_norm,
              "\n".join(textwrap.wrap(f"{names.get(s, s)} minus {names.get(ref, ref)}", 34)), fmt_diff, flagged=flagged)
    # key / reading guide in the free slot under the reference panel
    kx = axes[1, 0]
    kx.set_facecolor(TH["surface"]); kx.axis("off")
    lines = ["How to read",
             "Rows: vegetative-window rainfall.  Columns: reproductive-window rainfall.",
             "Stress increases down and to the right; top-left is the control.",
             "Letters: T tolerant, R recovered, NR not recovered,",
             "n/a stress with no rainfall return.",
             "Heavy outline: H1 cells.  Dashed outline: H2 cells."]
    if flag is not None:
        lines.append(f"Bold outline in difference panels: |difference| > {flag:g}" + (" pp (H3 limit)." if a.metric == "YieldRecoveryPct" else "."))
    lines.append("Difference = site minus reference: blue above, red below.")
    for n, ln in enumerate(lines):
        kx.text(0.0, 0.98 - n * 0.115, ln, transform=kx.transAxes, fontsize=9 if n else 10,
                fontweight="bold" if n == 0 else "normal", color=TH["ink"] if n == 0 else TH["ink2"], va="top")

sm = matplotlib.cm.ScalarMappable(norm=seq_norm, cmap=seq_cmap)
cb = fig.colorbar(sm, ax=axes[0, :], orientation="horizontal", shrink=0.5, aspect=40, pad=0.02)
cb.set_label(label + ("  (lighter = higher)" if a.theme == "dark" else "  (darker = higher)"), fontsize=9, color=TH["ink2"])
cb.ax.tick_params(labelsize=8, colors=TH["ink2"]); cb.outline.set_visible(False)
if diffs:
    sm2 = matplotlib.cm.ScalarMappable(norm=div_norm, cmap=div_cmap)
    cb2 = fig.colorbar(sm2, ax=axes[1, 1:], orientation="horizontal", shrink=0.5 if ncols > 2 else 0.8, aspect=40, pad=0.02)
    cb2.set_label("Difference from reference" + (" (percentage points)" if a.metric == "YieldRecoveryPct" else ""),
                  fontsize=9, color=TH["ink2"])
    cb2.ax.tick_params(labelsize=8, colors=TH["ink2"]); cb2.outline.set_visible(False)

fig.suptitle(label + " across the rainfall-treatment grid", fontsize=12, fontweight="bold", color=TH["ink"], x=0.01, ha="left")

prefix = Path(a.out) if a.out else d / "figures" / f"response_{a.metric}_{'_'.join(sites)}"
prefix.parent.mkdir(parents=True, exist_ok=True)
for ext in a.formats:
    f = prefix.with_suffix("." + ext)
    fig.savefig(f, dpi=200, facecolor=TH["surface"], bbox_inches="tight")
    print("Wrote", f)


