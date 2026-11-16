# Cross-state amendment 1 (post hoc, exploratory)

Written after the primary test was run and committed (tag crossstate_results_v1: rho = 0.033, p = 0.474),
and before this sensitivity was run.

Finding: in counties whose grid cells have different crop-calendar planting dates, 03 records the
first cell's planting date in phenology.csv and 04 builds one calendar treatment window from it,
so the early/late window is misaligned for cells with a different planting date
(9 of 27 counties have cells with more than one planting date; 7 sites are flagged cells_agree = False).
This affects the primary result as pre-specified and is reported as a limitation.

Sensitivity (exploratory, one variant only): recompute each county's early-only loss using only
cells whose planting date equals the county row date, then repeat the state-level test
(state mean, Spearman, one-sided exact permutation p). Uses existing experiment outputs; no model rerun.
Both the primary and this sensitivity are reported, whatever the sensitivity shows.
Script: scripts/42_crossstate_aligned_sensitivity.py
