# Integrity gates: grid results v1 (2026-10-27)

| Gate | Result |
|---|---|
| 1. Every experiment passes `04 --check` (enforced by run_grid.sh) | Passed, 48 grid experiments (24 per site) |
| 2. Determinism (g_v050_r000 rerun at Champaign) | Passed with a deviation: per-cell summary values identical after sorting by cell_id; daily outputs identical as a set of 100 cells. Row order differs between runs (parallel execution), so the plan's "bit-identical" wording is relaxed to "identical up to cell order". All metrics are cell means or per-cell ratios and do not depend on order. |
| 3. NASS validation (|R_Champaign - R_Story| <= 0.20) | Passed: R = 1.553 vs 1.480, difference 0.073 |
| 4. Phenology agreement across cells (cells_agree) | Passed (True) at both sites |
| 5. Control seasonal precipitation equals baseline rainfall over the season | Passed: Story 578.5 vs 578.5 mm; Champaign 517.6 vs 517.6 mm |
| 6. Provenance (baseline checksums; AgERA5 version) | Passed: checksum files in results/; AgERA5 requested as version "2_0" for both sites (Story confirmed by the user) |
