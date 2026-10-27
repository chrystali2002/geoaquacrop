# Champaign County Experiment Plan (Pre-Specification)

**Status: FROZEN 2026-10-27**

This document was frozen and committed before any Champaign County experiment was generated.

Site: `champaign2015` (GEOID 17019, IL), year 2015, rainfed maize.

Comparison site: `story2015` (GEOID 19169, IA), year 2015.

---

# 1. Question

Does root-zone water buffering of transpiration and yield, and recovery after rainfall returns, generalize from Story County to Champaign County?

Story results used as the historical reference (2015 only, archived runs):

- Archived Late v2 (rainfall set to zero from reproductive onset; unaffected by the double-application issue found in the original `04_modify_precip.py`) retained 99.9% of control yield.
- Archived Early Recovery v2 recovered to 79.4% of control yield. Its effective vegetative rainfall multiplier was 0.0225, not the labelled 0.15, because the original script applied the treatment twice.

These archived values are retained as historical reference results only. Cross-site comparisons use the new grid experiments defined in `treatments.csv`.

This plan does **not** claim a general Corn Belt mechanism.

Two sites and one year can support:

```text
Consistent
```

or

```text
Not consistent
```

but not regional generality.

---

# 2. Fixed Inputs (Identical Across Sites)

1. Same crop file and crop parameters as Story County. Only site inputs differ (weather, soil, crop calendar, SPAM area).

2. Same GeoAquaCrop version and model settings. Record:
   - code commit
   - input checksums

3. Initial soil-water setting must be recorded, including whether it is applied at planting or simulation start.

4. Phenology comes exclusively from:

   ```text
   config/phenology.csv
   ```

   written by:

   ```text
   03_growth_stage_diagnostics.py
   ```

5. Global inputs shared from a single source:

   ```text
   shared_inputs/
   ```

   linked by:

   ```text
   01_run_preprocess.py
   ```

   Shared inputs:

   - GGCMI crop calendar phase 3 v1.01
   - SPAM 2010 physical area

   Site-specific inputs:

   - SoilGrids soils
   - AgERA5 weather
   - template grid

6. Weather forcing uses AgERA5 through the CDS API.

   Record:

   - AgERA5 version
   - download date
   - raw downloads

7. Model yield is AquaCrop dry yield.

   The model's internal fresh yield assumes 10% moisture but is **not** used for validation.

   Story County control yield exceeded NASS by approximately 48% on a dry-matter basis.

   The model will **not** be calibrated or retuned.

---

# 3. Experiments

Experiments are defined in:

```text
config/treatments.csv
```

using the `grid` group.

Naming convention:

```text
g_v<VEG>_r<REP>
```

where multipliers apply only inside the designated window.

## Window Definitions

### Vegetative

```text
planting <= date < planting + reproductive_dap
```

### Reproductive

```text
planting + reproductive_dap <= date <= planting + harvest_dap
```

## Grid

Vegetative and reproductive multipliers each take values:

```text
1.00
0.75
0.50
0.25
0.00
```

The control is `control_<year>`, produced by `02_run_control.py`. It is
equivalent to the (1.00, 1.00) cell and is not listed in `treatments.csv`.

Total:

```text
24 treatment experiments
+ control
per site
```

---

## Experiment Families

### Early Recovery

```text
rep = 1.00
veg < 1.00
```

### Late Stress

```text
veg = 1.00
rep < 1.00
```

### Dual Stress

```text
veg < 1.00
rep < 1.00
```

The same grid will be run at Story County as new experiments.

The grid experiments constitute the primary cross-site comparison dataset.

The archived Story County experiments remain frozen historical results and are retained for reproducibility rather than direct cross-site inference.

---

# 4. Selection Rule

No experiment selection occurs prior to analysis.

Response surfaces are reported in full.

Any representative experiments used in figures are selected using realized stress conditions rather than yield outcome.

## Figure Selection Rule

Representative experiments are chosen as the grid cells closest to:

```text
Relative storage at onset = 0.9
Relative storage at onset = 0.8
Relative storage at onset = 0.7
```

This selection is performed without considering yield.

---

# 5. Metrics (Script 21)

For each treatment:

- Yield recovery (%)
- Relative root-zone water at onset
- Relative root-zone water at onset + 18 days
- Tr/TrPot at onset
- Tr/TrPot at onset + 18 days
- Buffer days
- Recovery days
- State
  - Tolerant
  - Recovered
  - Not Recovered
  - N/A
- Seasonal precipitation
- Seasonal transpiration

---

# 6. Pre-Specified Criteria

## H1: Buffering

Buffering is supported at a site if, for **every** grid cell with:

```text
rep_mult <= 0.25
veg_mult = 1.00
```

(that is, rep = 0.25 and rep = 0.00).

Buffering is supported only if **all** matching cells satisfy the criterion below. Failure of any one matching cell causes H1 to fail:

```text
Yield recovery >= 95%
AND
State = Tolerant
```

---

## H2: Recovery

H2 tests recovery after stress, not whether stress occurred. Buffering (stress
never develops) is addressed by H1.

A vegetative level (veg_mult <= 0.25) is **evaluable** if the rep = 1.00 run at
that level develops sustained stress, meaning its State is not Tolerant. A level
whose rep = 1.00 run is Tolerant had no stress to recover from; it is excluded
from H2 and reported separately, with its yield recovery and State.

For every evaluable level:

```text
YieldRecovery(rep=1.00)
-
YieldRecovery(rep=0.00)
>= 20 percentage points
```

and:

```text
State(rep=1.00) = Recovered
```

H2 outcomes:

```text
Supported:
At least one evaluable level exists, and every evaluable level
meets both conditions.

Not supported:
At least one evaluable level exists, and at least one evaluable
level fails a condition.

Not evaluable:
No evaluable levels exist.
```


---

## H3: Cross-Site Consistency

Consistency is supported if:

```text
Absolute difference in yield recovery
<= 10 percentage points
```

for at least:

```text
80% of matched grid cells
```

and:

```text
H1 has the same outcome (supported or not supported) at both sites,
and
H2 has the same outcome (Supported or Not supported) at both sites.
```

If H2 is Not evaluable at either site, the recovery component of H3 is reported
as not evaluable and no cross-site recovery claim is made.

---

## Failure Conditions

A result is considered inconsistent if:

```text
H1 or H2 has different outcomes at the two sites
```

or if:

```text
the H3 cell-agreement limit
(<= 10 percentage points in at least 80% of matched cells)
is not met.
```

---

# 7. Integrity Gates (Before Any Analysis)

1. Every experiment passes:

   ```bash
   04_modify_precip.py <experiment> --check
   ```

   and has a valid:

   ```text
   treatment_record.json
   ```

2. One experiment is run twice and produces bit-identical outputs.

3. Control validation against USDA NASS succeeds.

4. In:

   ```text
   phenology.csv
   ```

   ```text
   cells_agree = True
   ```

5. The control's `Precipitation<year><year>.nc` has the same sha256 as the
   baseline (enforced by `02_run_control.py`), and the control's seasonal
   precipitation equals the baseline rainfall summed over the season.

6. Provenance is recorded:

   - AgERA5 version
   - preprocess record
   - SHA256 checksums of all baseline files

---

## Gate 3: Control Validation Against USDA NASS

### Metric

Define:

```text
R
=
(Model dry-matter yield)
/
(NASS 2015 county yield converted to dry matter)
```

using:

- AquaCrop dry yield
- NASS county corn grain yield
- 15.5% grain moisture
- 56 lb/bu conversion

Story County is computed the same way.

Reference NASS yields:

```text
Story County      = 188.0 bu/ac
Champaign County  = 189.4 bu/ac
```

---

### Pass Criterion

Pass if:

```text
|R_Champaign - R_Story| <= 0.20
```

Example:

```text
R_Story = 1.48
```

Acceptable Champaign range:

```text
1.28 <= R_Champaign <= 1.68
```

The value 1.48 above is illustrative. The pass range is computed from the
R_Story reported by `06_validate_control.py` (R_Champaign must lie within
+/- 0.20 of that value).

---

### Derivation

Using NASS county yields from 1985–2014 only:

Standard deviation about trend:

```text
Champaign: 16.9%
Story:     14.5%

Quadrature:
22.3%
```

Robust estimate (1.4826 × MAD):

```text
Champaign: 13.8%
Story:     10.9%

Quadrature:
17.6%
```

The selected threshold:

```text
0.20
```

is a rounded value based on the robust estimate.

Limitations:

- assumes independent county departures
- does not include model structural error

---

### Dates (Reported, No Pass/Fail)

Compare:

- planting date
- reproductive onset
- maturity

against NASS Crop Progress dates.

Reference values:

```text
Illinois 2015
Planting (50%) : 2015-04-30
Silking (50%)  : 2015-07-11

Iowa 2015
Planting (50%) : 2015-05-01
Silking (50%)  : 2015-07-18
```

Model onset is:

```text
first harvest_index > 0
```

and not 50% silking.

Model harvest corresponds to physiological maturity rather than harvest operations.

---

### If Gate 3 Fails

The Champaign analysis is reported as exploratory.

Investigate:

- soil inputs
- crop calendar
- weather forcing

but:

```text
DO NOT retune the model
to match NASS.
```

---

### Data Sources

NASS Quick Stats API:

```text
Yield and crop-progress data retrieved
2026-10-23
```

Verify against stored file timestamps prior to publication.

---

# 8. Alternative Explanations

If Champaign differs from Story, evaluate:

- tile drainage effects
- initial soil-water conditions
- soil depth
- water-holding capacity
- antecedent wetness during 2015
- single-year weather variability

These explanations are considered before attributing differences to site-specific drought mechanisms.

---

# Planned Follow-Up (Not Part of This Plan)

- 5–10 years of simulations at both sites
- finer rainfall-gradient experiments
- threshold-response analysis
- broken-stick fits for buffering thresholds
- additional counties across the Corn Belt
