# Multi-year, all-county process-model test

Status: drafted 2026-11-17, after the 2015 27-county test (tag `crossstate_results_v1`, criterion not met)
and the aligned-cells sensitivity (Amendment 1). This analysis addresses two stated limitations of that
test: one weather year and three counties per state. The 2015 test is unchanged and reported as is.
This plan is frozen (tag `crossstate_multiyear_plan_frozen`) before any model yield is produced.

## Question
When observed and modelled yields are scored against the same drought classification, does AquaCrop,
driven by actual 1986–2024 weather, reproduce the observed state-level SSMI early-only (Cell B) yield
effect across the nine rainfed Corn Belt states?

## Counties and years
- All counties in IL, IN, IA, MI, MN, MO, OH, SD, WI with an SSMI Track-NASS classification
  (`matrix_ssmi`) and a NASS yield anomaly in `master_analysis_trackA.csv`: 790 counties,
  27,104 county-years, 1986–2024.
- Observed and modelled analyses use the identical set of county-years (those with both values).
- A county is excluded if any season fails to simulate or the domain has no cell; all exclusions are listed.

## Model
- Configuration identical to manuscript Section 2.4.6: GeoAquaCrop v0.1.1 / AquaCrop-OSPy v3.1.0,
  default maize parameters, rainfed, custom SoilGrids 2.0 soil (six layers to 2 m, CN 46, REW 7 mm),
  no tile drainage or water table, no calibration, 0.05° cells within the TIGER 2020 county boundary.
- Control simulations only (no rainfall multipliers), actual daily weather.
- Each season simulated 1 Jan–31 Dec and initialised at field capacity on 1 Jan (as in the 2015 runs;
  no soil-water carryover between years).
- Planting date and season length from the static GGCMI phase 3 v1.01 calendar (same date every year).
- County value = unweighted mean dry yield over cells.

## Inputs
- AgERA5 v2.0 daily maximum and minimum temperature, precipitation and FAO-56 reference ET, 1986–2024,
  (CDS variables `2m_temperature` 24-hour maximum and minimum, `precipitation_flux`,
  `reference_evapotranspiration`, as requested by geoaquacrop_preprocess) from one regional download over
  the nine-state box (script 43, archive mode, native 0.1°). For each county the native cells the
  library's own request would return are written as one file per variable per year
  (`rawdata/climate/MaxTemp<YYYY>.nc`, ...); the library skips its download when that yearly file exists
  and performs its own resampling to 0.05° (`weather` step, one call per year, giving
  `processed/<Var><YYYY><YYYY>.nc` as in the 2015 runs). Soils come from the library's `soil` step per county.
- Gate G1a: for the 27 cross-state counties, the native cells written for 2015 must be exactly the cells
  in the existing 2015 raw files. Soils (SoilGrids 2.0) per county via the library;
  crop calendar and SPAM masks from the shared inputs.
- Gate G1b: before any other year is built, the input builder must reproduce the existing processed 2015
  inputs of the 27 cross-state counties (all four weather variables; maximum absolute difference
  <= 1e-4 in native units). If G1a or G1b fails, stop and resolve.

## Yield variables
- Observed: `yield_anomaly` (NASS bu/ac minus county linear trend, as in the manuscript), and the relative
  anomaly 100 x `yield_anomaly` / `yield_trend`.
- Modelled: dry yield converted to bu/ac at 15.5% moisture, detrended per county with the same procedure as
  the NASS yields (`detrend_yield` in `08_nass_yield.py`: linear fit of yield on year over the county's
  years; counties with fewer than 5 years use the county mean); relative anomaly
  100 x (yield - trend) / trend.
- Primary metric: relative anomalies (removes the state-dependent model overestimate, R = 1.37–2.15 in 2015).
  Secondary: bu/ac.

## Regression
- Sample, as in `09b_state_anova_robustness.py` (source of the S6.1 state coefficients): county-years with
  non-missing `yield_anomaly` and all three classifications (`matrix_spei`, `matrix_ssmi`, `matrix_esi`).
- Per state: OLS `anomaly ~ C(matrix_ssmi, Treatment('D_neither')) + C(year)`, HC3 standard errors
  (as in 09b). County-clustered standard errors are reported for P2 as a sensitivity, because HC3 ignores
  within-county correlation.
- Pooled: `anomaly ~ C(matrix_ssmi) + C(state) + C(year)`, county-clustered (as in `09_analysis.py`).
- Sample identity: the comparison uses the subset of the 09b sample for which a modelled anomaly also
  exists, and the observed regressions are re-estimated on exactly that subset, so that any
  observed–modelled difference cannot come from sample composition. The number of county-years dropped
  (relative to the 09b sample) is reported by state.
- Gate G3: run first on the full 09b sample with the observed bu/ac anomalies; it must reproduce the published state-level SSMI
  Cell B coefficients (Supplementary S6.1, Track-NASS) to two decimals before any modelled yield is
  analysed. If it does not, stop and resolve the specification.

## Outcomes and tests
- P1 (primary): Spearman rank correlation, across the nine states, between modelled and observed Cell B
  coefficients (relative anomalies); one-sided exact permutation p over all 9! orderings;
  criterion rho > 0 and p <= 0.05, fixed in advance (with nine states, p <= 0.05 requires rho >= 0.60).
  If a state's Cell B coefficient cannot be estimated (model failure or no Cell B county-years in the
  sample), P1 uses the remaining states, reports how many were included, and uses the exact permutation
  distribution for that number.
- P2: for the states with significant observed coefficients (MI and SD negative, MN positive), the sign
  and 95% CI of the modelled coefficient (descriptive).
- P3: pooled Cell B coefficient, modelled versus observed, with CIs (descriptive).
- Check on model adequacy (reported first): the same comparison for Cells A and C. The model is judged
  adequate only if the pooled modelled Cell A and Cell C coefficients are negative (relative to Cell D),
  as the observed pooled coefficients are, and the cross-state rank correlation between modelled and
  observed coefficients is positive for both cells. If not, the Cell B comparison is reported as
  uninformative about recovery mechanisms, whatever its value.
- Secondary: P1–P3 in bu/ac.
- All results are reported whatever they show.

## Stated limitations
Annual reset of soil water at 1 Jan; static calendar planting (Track-NASS phenology varies by year);
uncalibrated yields; no tile drainage or water table; the classification comes from NLDAS-2 soil moisture
while the model is driven by AgERA5, so model and classification can disagree on whether a year was dry
(by design: both yield series are scored against one classification). Agreement between the model and
the classification is therefore not assumed; it is part of what is tested.

## Scripts and tags
43 (archive mode) -> 44 build inputs (G1a, G1b) -> 45 run controls -> 46 analysis (G3, then P1–P3).
Tags: `crossstate_multiyear_plan_frozen` (this file, before 45 is run); `crossstate_multiyear_results_v1`.
