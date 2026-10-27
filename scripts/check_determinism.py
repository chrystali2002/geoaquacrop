#!/usr/bin/env python
"""
check_determinism.py DIR_A DIR_B

Compares two output folders from the same experiment (each holding
summary_results.pkl and daily_results.pkl) and says WHERE they differ:
  - same cells in a different order?  (matched by cell_id / content hash)
  - which columns differ, and by how much (max |difference|, relative)?
  - differences only in text/time columns, or in numbers?
Exit code 0 only if everything is bit-identical in the original order.
"""
import hashlib, sys
import numpy as np
import pandas as pd

if len(sys.argv) != 3:
    sys.exit(__doc__)
A, B = sys.argv[1], sys.argv[2]


def frame_hash(df):
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()
                          + "|".join(map(str, df.columns)).encode()).hexdigest()


sa = pd.concat(pd.read_pickle(f"{A}/summary_results.pkl"), ignore_index=True)
sb = pd.concat(pd.read_pickle(f"{B}/summary_results.pkl"), ignore_index=True)
print(f"summary: A {sa.shape}, B {sb.shape}; same columns: {list(sa.columns) == list(sb.columns)}")

identical_in_order = sa.equals(sb)
print(f"summary identical in original order: {identical_in_order}")

key = "cell_id" if "cell_id" in sa.columns and "cell_id" in sb.columns else None
if key:
    ka, kb = sa[key].tolist(), sb[key].tolist()
    print(f"cell order identical: {ka == kb}   same set of cells: {sorted(map(str,ka)) == sorted(map(str,kb))}")
    ma = sa.sort_values(key).reset_index(drop=True)
    mb = sb.sort_values(key).reset_index(drop=True)
    print(f"summary identical after sorting by {key}: {ma.equals(mb)}")
else:
    ma, mb = sa, sb

if not ma.equals(mb) and ma.shape == mb.shape:
    print("\ncolumns that differ (after aligning cells):")
    for c in ma.columns:
        x, y = ma[c], mb[c]
        if x.equals(y):
            continue
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            d = (x - y).abs()
            rel = (d / x.abs().replace(0, np.nan)).max()
            print(f"  {c:<38} numeric  max|diff|={d.max():.3g}  max rel={rel:.3g}  cells differing={int((d > 0).sum())}")
        else:
            n = int((x.astype(str) != y.astype(str)).sum())
            ex = next(((str(p), str(q)) for p, q in zip(x, y) if str(p) != str(q)), None)
            print(f"  {c:<38} non-numeric  cells differing={n}  example={ex}")

da = pd.read_pickle(f"{A}/daily_results.pkl")
db = pd.read_pickle(f"{B}/daily_results.pkl")
print(f"\ndaily: {len(da)} vs {len(db)} cells")
if len(da) == len(db):
    same_in_order = sum(x["water_flux"].equals(y["water_flux"]) and x["crop_growth"].equals(y["crop_growth"])
                        for x, y in zip(da, db))
    ha = sorted(frame_hash(c["water_flux"]) + frame_hash(c["crop_growth"]) for c in da)
    hb = sorted(frame_hash(c["water_flux"]) + frame_hash(c["crop_growth"]) for c in db)
    print(f"cells identical in the same position: {same_in_order}/{len(da)}")
    print(f"identical as a SET of cells (ignoring order): {ha == hb}")
    worst = 0.0
    for x, y in zip(da, db):
        for part in ("water_flux", "crop_growth"):
            xa, ya = x[part].select_dtypes("number"), y[part].select_dtypes("number")
            if xa.shape == ya.shape:
                worst = max(worst, float(np.nanmax(np.abs(xa.values - ya.values))))
    print(f"largest absolute difference in any daily number (same position): {worst:.3g}")
    all_equal = identical_in_order and same_in_order == len(da)
    sys.exit(0 if all_equal else 1)
sys.exit(1)
