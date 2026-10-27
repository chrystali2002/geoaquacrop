#!/usr/bin/env python
"""
30_tile_drain_sensitivity.py   (EXPLORATORY: not part of the frozen plan)

Re-run the control and selected grid cells of a site with AquaCrop's simplified
tile drainage switched on, and compare yield recovery with the frozen
(no tile drainage) results.

Usage
-----
python 30_tile_drain_sensitivity.py --site champaign2015 --depth 1.0 --coeff 0.5
        [--target M3_PER_M3] [--cells key|all] [--force]

What the option does (aquacrop 3.1.0, solution/tile_drainage.py): each day, in every
soil compartment whose midpoint is at or below --depth (m), water above the target
(default: field capacity) is removed at fraction --coeff per day. It is a first-order
sink, not a water-table or drain-spacing model. Depth and coefficient are ASSUMPTIONS.

Safety
------
* Inputs (control_<year>/processed and <experiment>/processed) are only read.
* Outputs go to <root>/results/tile_drain/<site>/<tag>/<experiment>/ ; frozen
  experiment folders are never written.
* Applied by patching aquacrop Soil.__init__ in this process. The simulation uses
  ProcessPoolExecutor (default 'fork' on Linux), so workers inherit the patch.
  The script checks that TileDrain is non-zero in the outputs and stops otherwise.
"""
import argparse, json, os, sys
from pathlib import Path
import pandas as pd

import geoaquacrop as gac

ROOT = Path(os.environ.get("GEOAQUACROP_ROOT", "/mnt/scratch/olusegu3/geoaquacrop"))
CONFIG = ROOT / "config"
YIELD_COL = "Dry yield (tonne/ha)"
KEY_CELLS = [(1.0, 0.25), (1.0, 0.0), (0.25, 1.0), (0.25, 0.0), (0.0, 1.0), (0.0, 0.0)]

p = argparse.ArgumentParser()
p.add_argument("--site", required=True)
p.add_argument("--depth", type=float, required=True, help="drain depth, m")
p.add_argument("--coeff", type=float, required=True, help="fraction of excess removed per day, 0-1")
p.add_argument("--target", type=float, default=None, help="water-content cap, m3/m3 (default field capacity)")
p.add_argument("--cells", choices=["key", "all"], default="key")
p.add_argument("--irrigation", default="rainfed")
p.add_argument("--force", action="store_true")
a = p.parse_args()
if not 0 < a.coeff <= 1:
    sys.exit("--coeff must be in (0, 1]")

counties = pd.read_csv(CONFIG / "counties.csv", dtype={"geoid": str})
m = counties.loc[counties["site_id"] == a.site]
if len(m) != 1:
    sys.exit(f"{a.site} must appear exactly once in counties.csv")
YEAR = int(m.iloc[0]["year"]); CROP = str(m.iloc[0]["crop"]).strip().capitalize()

EXPS = ROOT / "experiments" if a.site == "story2015" else ROOT / "experiments" / a.site

tr = pd.read_csv(CONFIG / "treatments.csv")
tr = tr.loc[tr["group"] == "grid"]
if len(tr) != 24:
    sys.exit(f"Expected 24 grid rows, found {len(tr)}")
if a.cells == "key":
    keep = tr.apply(lambda r: any(abs(r.veg_mult - v) < 1e-9 and abs(r.rep_mult - rp) < 1e-9 for v, rp in KEY_CELLS), axis=1)
    tr = tr[keep]
runs = [("control", EXPS / f"control_{YEAR}", 1.0, 1.0)] + [
    (r.experiment, EXPS / r.experiment, r.veg_mult, r.rep_mult) for r in tr.itertuples()]

# ---- switch tile drainage on (patch, inherited by forked workers) ----
from aquacrop.entities import soil as _soil
_orig = _soil.Soil.__init__
def _init(self, *args, **kw):
    kw.setdefault("tile_drainage", True)
    kw.setdefault("drain_depth", a.depth)
    kw.setdefault("drain_coeff", a.coeff)
    if a.target is not None:
        kw.setdefault("drain_target", a.target)
    _orig(self, *args, **kw)
_soil.Soil.__init__ = _init

tag = f"d{a.depth:g}_c{a.coeff:g}" + (f"_t{a.target:g}" if a.target is not None else "")
OUT = ROOT / "results" / "tile_drain" / a.site / tag
print(f"Site {a.site}  tile drain depth {a.depth} m  coeff {a.coeff}  target {a.target or 'field capacity'}")
print(f"Outputs: {OUT}\n")

def mean_yield(summ_file):
    import pickle
    return pd.concat(pickle.load(open(summ_file, "rb")), ignore_index=True)[YIELD_COL].mean()

rows, tile_ctl = [], None
for name, exp_dir, v, r in runs:
    data = exp_dir / "processed"
    out = OUT / name
    done = out / "summary_results.pkl"
    if done.exists() and not a.force:
        print(f"{name}: exists, skipped (use --force to rerun)")
    else:
        if not data.is_dir():
            sys.exit(f"{data} not found")
        out.mkdir(parents=True, exist_ok=True)
        print(f"Running {name} ...", flush=True)
        sf, df = gac.simulate.run(data_path=str(data), start_date=f"{YEAR}/01/01",
                                  end_date=f"{YEAR}/12/31", crop=CROP,
                                  irrigation=a.irrigation, output_dir=str(out))
        import shutil
        shutil.copy2(sf, done); shutil.copy2(df, out / "daily_results.pkl")
    # confirm the drain actually acted
    import pickle
    daily = pickle.load(open(out / "daily_results.pkl", "rb"))
    td = sum(float(d["water_flux"]["TileDrain"].sum()) for d in daily
             if "water_flux" in d and "TileDrain" in d["water_flux"])
    if td <= 0:
        sys.exit(f"{name}: TileDrain is zero in the outputs; the patch did not take effect. Stopping.")
    y_tile = mean_yield(done)
    y_base = mean_yield(exp_dir / "outputs" / "summary_results.pkl")
    rows.append(dict(experiment=name, veg_mult=v, rep_mult=r, tile_drain_mm_per_cell=round(td / len(daily), 1),
                     yield_base=round(y_base, 3), yield_tile=round(y_tile, 3)))

df = pd.DataFrame(rows)
yc_b = df.loc[df.experiment == "control", "yield_base"].iloc[0]
yc_t = df.loc[df.experiment == "control", "yield_tile"].iloc[0]
df["recovery_base_pct"] = (df.yield_base / yc_b * 100).round(1)
df["recovery_tile_pct"] = (df.yield_tile / yc_t * 100).round(1)
df["change_pp"] = (df.recovery_tile_pct - df.recovery_base_pct).round(1)
OUT.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT / "tile_drain_summary.csv", index=False)
(OUT / "settings.json").write_text(json.dumps(dict(site=a.site, depth_m=a.depth, coeff=a.coeff,
    target=a.target, cells=a.cells, exploratory=True,
    note="Simplified tile drainage, assumed parameters, not calibrated; no water table."), indent=2))
print("\n" + df.to_string(index=False))
print(f"\nControl yield (t/ha): no drain {yc_b:.3f}  tile drain {yc_t:.3f}")
print(f"Wrote {OUT / 'tile_drain_summary.csv'}")
