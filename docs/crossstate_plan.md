# Cross-state buffering test: plan (DRAFT, not frozen)

Status: DRAFT. Freeze by committing on branch `crossstate_buffering` (from tag `grid_results_v1.1`) and tagging
`crossstate_plan_frozen` BEFORE any new county is registered or run. Nothing under the Story or Champaign tags changes.

## Question
Can soil-water buffering in the process model account for why the observational early-season recovery result (SSMI early-only,
Track-NASS) holds in some Corn Belt states and not others?

## Pre-specified design (frozen items)
| Item | Specification |
|---|---|
| States | Corn states with < 15% irrigated corn area (2022 Census, Supp. Table S1): Illinois, Indiana, Iowa, Michigan, Minnesota, Missouri, Ohio, South Dakota, Wisconsin. Nebraska and Kansas excluded. |
| County rule | Per state: take the 20 counties with the largest 2015 grain-corn harvested area that have a reported (not suppressed) 2015 NASS yield; split by available water capacity (0-150 cm, NRCS) into terciles; select the largest-area county in each tercile (3 counties per state). Ties in area broken by lower FIPS. Story and Champaign are reused only if the rule selects them; otherwise they are reported as additional values and not used in the primary state values. |
| Year and inputs | 2015; AgERA5, SoilGrids, GGCMI as in the Story and Champaign runs; same pipeline and unchanged treatment grid (rainfall multipliers 1, 0.75, 0.5, 0.25, 0 in the vegetative and reproductive windows). |
| Primary modelled metric | County early-only loss = 100 - yield recovery (% of the county control) at vegetative multiplier 0.25, reproductive multiplier 1.00. |
| Sensitivity metrics | Same at vegetative multiplier 0.50 and 0.00 (reproductive 1.00). |
| State value | Mean of the county early-only losses (primary). Median and county-level values reported as sensitivity. |
| Observed quantity | Early-only penalty = minus the SSMI Cell B coefficient, Track-NASS (config/observed_state_coefficients.csv). |
| Test | Spearman rank correlation across the nine states (average ranks for ties). Directional hypothesis: larger modelled loss goes with larger observed penalty. Exact permutation p-value, one-sided. Pass condition: rho > 0 and p <= 0.05. |
| Sensitivity | Leave-one-state-out correlations (includes Minnesota, whose coefficient is positive, and Michigan, 13.3% irrigated); median state values; the two other loss metrics. |
| Gates | Technical gates (no double-applied treatments, determinism, phenology agreement, rainfall-forcing check, provenance) must pass. The NASS yield ratio R is reported for every county and is NOT used to drop or replace counties. |
| Null result | Reported regardless of outcome. |

## Known limitations (stated in the paper)
One weather year; each county reflects its own 2015 conditions. Uncalibrated potential-type model. No tile drainage or water table.
State-level irrigation share does not guarantee that selected counties are rainfed. The model imposes rainfall multipliers and does not
reproduce the SSMI classification, so ranks are compared, not magnitudes. Observational coefficients are state-level estimates over 1986-2024.

## Manuscript subsection (methods)

**2.X Process-model test of cross-state heterogeneity in early-season recovery**

The observational analysis estimated an early-only (Cell B) yield coefficient for each state under SSMI classification, and recovery held in some states but not others (Supplementary S6.1). To test whether differences in soil-water buffering could account for this heterogeneity, we ran the GeoAquaCrop process model (a gridded implementation of FAO AquaCrop) for sampled counties in each rainfed Corn Belt state, using one fixed experimental design for every county. We defined rainfed states as those with less than 15% of corn area irrigated (2022 Census of Agriculture; Supplementary Table S1), which gives nine states (Illinois, Indiana, Iowa, Michigan, Minnesota, Missouri, Ohio, South Dakota and Wisconsin) and excludes Nebraska and Kansas.

In each county, weather (AgERA5), soils (SoilGrids) and crop calendar (GGCMI) for 2015 defined a baseline simulation, from which we imposed a pre-specified grid of rainfall multipliers (1, 0.75, 0.5, 0.25, 0) separately on the vegetative window (planting to reproductive onset) and the reproductive window (onset to harvest). A single growing season (2015) was used for all simulations to keep inputs and data versions identical across counties and consistent with the sites already completed. Because weather differs among locations within a year, the comparison reflects each county's own 2015 conditions, and sensitivity to the choice of weather year was not tested. The modelled analogue of an early-only drought followed by recovery was a reduced vegetative-window multiplier with full rainfall afterwards. For each county we defined the modelled early-only loss as 100 minus the yield, as a percentage of the unmodified control, in the cell with vegetative multiplier 0.25 and reproductive multiplier 1.00; the cells at vegetative multipliers 0.5 and 0 served as sensitivity analyses. Control yields were compared with NASS county yields, and the model was not calibrated or retuned.

Counties were selected using a rule specified in advance that depended only on corn area, NASS data availability and soil water capacity, not on any model result. Within each state we ranked counties by 2015 grain-corn harvested area, retained the 20 largest with a reported NASS yield, divided them into terciles of available water capacity (0-150 cm, NRCS), and selected the largest-area county in each tercile. The state value was defined as the mean modelled early-only loss across sampled counties within the state; median state values and county-level results are reported as sensitivity analyses.

We hypothesised that states with larger modelled early-only losses (weaker buffering) would also show larger observed early-only yield penalties, defined as the negative of the SSMI Cell B coefficient (Track-NASS, bu ac^-1). The test was the Spearman rank correlation across states, with a one-sided exact permutation p-value; leave-one-state-out correlations are reported as a sensitivity analysis. Because the model imposes rainfall multipliers and does not reproduce the SSMI classification, the comparison was of rank order, not of magnitudes. Results are conditional on one weather year, uncalibrated model yields, no representation of tile drainage or a water table, and on state-level observational coefficients that are themselves uncertain. The county list, metric and test were frozen and tagged before any new county was run, and a null result will be reported.
