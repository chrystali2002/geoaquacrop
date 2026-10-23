Below is the revised content that should replace the major sections of your document. Because the entire document is quite long, I recommend updating the original handoff with these replacements rather than maintaining the older Story County results.

GeoAquaCrop Project
Project Overview
Story County, Iowa (2015) Drought-Trajectory Mechanism Study
Status: Active Development
Last Updated: October 2026
Primary Objective: Use GeoAquaCrop simulations to investigate the mechanisms underlying drought timing, buffering, and recovery trajectories identified in a U.S. maize observational study.
Executive Summary

This project extends an observational analysis of maize drought timing and recovery in major U.S. maize-growing regions by using GeoAquaCrop to investigate the underlying biophysical mechanisms.

Key Observational Findings
Recovery was consistently supported under the Soil Moisture Stress Index (SSMI).
Recovery was not consistently detected under SPEI.
Recovery was not consistently detected under ESI.
Drought timing was strongly associated with yield outcomes.
Reproductive-stage drought often produced disproportionately large losses.

The GeoAquaCrop experiments were designed to evaluate whether the following process chain can explain these observations:

Root-Zone Water
        ↓
Transpiration
        ↓
Biomass
        ↓
Harvest Index
        ↓
Yield

Scientific Motivation

The parent manuscript evaluates drought trajectories across U.S. maize-growing regions using:

SPEI
SSMI
ESI

within a phenology-aligned silking window.

Three primary drought trajectories emerged:

Dual Stress

Stress persists through both pre-silking and post-silking periods.

Early Recovery

Early drought followed by recovery before reproductive development.

Late Stress

Limited stress prior to silking followed by strong stress during reproduction.

Methodological Foundation

This project uses the FAO AquaCrop framework, a process-based crop model designed to simulate crop response to water availability through explicit representation of root-zone water, transpiration, biomass production, harvest index development, and yield formation.

AquaCrop is based on the conceptual pathway:

Root-Zone Water
        ↓
Transpiration
        ↓
Biomass Production
        ↓
Harvest Index
        ↓
Yield


rather than directly linking yield to evapotranspiration.

This architecture makes AquaCrop particularly suitable for investigating drought timing, water-stress propagation, buffering, recovery, and yield response.

Numerous studies have validated AquaCrop for maize under rainfed and water-limited conditions, demonstrating its ability to simulate:

Soil water dynamics
Crop transpiration
Biomass accumulation
Yield response

The current project extends these applications by explicitly evaluating how drought trajectories identified in observations propagate through soil-water and crop physiological processes.

Study Area
Location
Story County, Iowa
GEOID: 19169

Crop
Rainfed Maize

Data Sources
Weather:
AgERA5

Soils:
SoilGrids

Crop Calendar:
GGCMI

Key Phenology Dates
Planting:
2015-05-13

Reproductive Onset:
DAP 72
(2015-07-24)

Harvest:
DAP 137
(2015-09-27)

Project Directory
/mnt/scratch/olusegu3/geoaquacrop
│
├── scripts
├── experiments
├── figures
├── story2015
└── locations

Scripts and Workflow
Setup

01_run_preprocess_2015.py

Prepare weather
Prepare soils
Prepare crop calendar

02_run_control_2015.py

Run baseline simulation

03_growth_stage_diagnostics.py

Determine growth stages
Identify reproductive onset
Experiment Generation

04_modify_precip.py

Generate drought treatments

05_run_experiment.py

Execute GeoAquaCrop simulations
Diagnostics
06_compare_summary.py
07_compare_wr.py
08_compare_biomass.py
09_compare_transpiration.py
10_compare_harvest_index.py
11_water_diagnostics.py
12_diagnostics.py
13_compare_versions.py
Mechanism Evaluation
14_recovery_metrics.py
15_compare_trajectories.py
16_compare_trajectories.py
17_mechanism_summary.py
18_mechanism_summary.py
19_process_pathway_figure.py
20_experimental_timeline.py
Recovery / Resilience
21_resilience_metrics.py
22_compare_precip_files.py
23_inspect_pickles.py
Experimental Windows
Vegetative Period
DAP 1–72

Reproductive Period
DAP 73–137

Experiment Evolution
Early Recovery
Version	Yield (t ha⁻¹)	Yield Gap (%)	Interpretationv1	14.30	2.9	Too weak
v2	11.71	19.9	Selected
v3	11.86	18.9	Similar to v2
Selected
early_recovery_2015_v2

Late Stress
Version	Yield (t ha⁻¹)	Yield Gap (%)	Interpretationv1	14.79	0.4	Buffered
v2	14.71	0.4	Buffered
v3	8.36	26.7	Selected
v4	8.44	26.0	Similar to v3
v5	4.63	36.6	Too severe
Selected
late_stress_2015_v3

Dual Stress
Version	Yield (t ha⁻¹)	Yield Gap (%)	Interpretationv1	13.12	10.8	Too weak
v2	2.84	40.0	Very severe
v3	3.48	37.1	Very severe
v4	4.63	36.6	Intermediate
v5	3.69	36.5	Selected
Selected
dual_stress_2015_v5

Story County Reference Experiment Set
Control
control_2015

Early Recovery
early_recovery_2015_v2

Late Stress
late_stress_2015_v3

Dual Stress
dual_stress_2015_v5

Final Results
Treatment	Yield (t ha⁻¹)Control	14.69
Early Recovery v2	11.71
Late Stress v3	8.36
Dual Stress v5	3.69
Water Diagnostics
DAP 72
Treatment	Wr	Tr/TrPotControl	515.99	1.000
Early Recovery v2	374.95	0.701
Late Stress v3	357.58	1.000
Dual Stress v5	348.72	0.643
Interpretation

Late Stress v3 enters reproduction without stress.

Dual Stress v5 is already stressed before silking.

This distinction is what makes the two trajectories mechanistically different.

Major Findings
1. Soil-Water Buffering

Late Stress v2 demonstrated:

No rainfall after reproductive onset


while producing little yield reduction because stored root-zone water maintained crop transpiration.

Meteorological Drought
        ↓
Soil-Water Buffering
        ↓
Maintained Transpiration
        ↓
Limited Yield Impact


This is currently the strongest mechanistic finding.

2. Recovery

Early Recovery v2 demonstrated:

Stress before silking
        ↓
Recovery after silking
        ↓
Partial yield retention


This is consistent with the recovery signal observed under SSMI.

3. Drought Timing Matters

Yield response depends strongly on when stress occurs.

Early Recovery
        ↓
Moderate losses

Late Stress
        ↓
Large losses

Dual Stress
        ↓
Largest losses

4. Meteorological Drought ≠ Agricultural Drought

The simulations demonstrate that rainfall deficits do not automatically produce crop stress when stored soil moisture remains available.

This finding is central to the interpretation of differences among:

SPEI
SSMI
ESI

Potential Novelty
Not Novel
Water availability influences transpiration.

Transpiration influences biomass.

Biomass influences yield.


These relationships are fundamental AquaCrop concepts.

Potentially Novel Contribution

The project may provide a process-based explanation for why drought recovery was supported under SSMI but not consistently under SPEI or ESI.

The simulations suggest:

Meteorological Drought
        ↓
Does Not Necessarily Become
Agricultural Drought
        ↓
When Stored Soil Water
Buffers Crop Function


This buffering framework may explain the divergence among drought indicators observed in the parent manuscript.

Methodological Basis in the Literature
AquaCrop Theory

Supports:

Root-Zone Water
↓
Transpiration
↓
Biomass
↓
Yield


framework.

Steduto et al. (2009a)
Steduto et al. (2009b)
Hsiao et al. (2009)
AquaCrop Validation for Maize

Supports use of AquaCrop under rainfed and water-limited conditions.

Abdinpour et al. (2012)
Mebane et al. (2013)
Paredes et al. (2014)
Ahmadi et al. (2015)
Greaves et al. (2016)
Sandhu et al. (2019)
AquaCrop Drought Applications

Supports drought-vulnerability and drought-impact analysis.

Ran et al. (2019)
Zhu et al. (2021)
Lu et al. (2022)
Open Questions
Recovery versus tolerance
Duration of soil-water buffering
Cross-site consistency
Illinois replication
Recovery thresholds
Multi-year robustness
Next Steps
Immediate
Run 21_resilience_metrics.py
Freeze Story County results
Generate final resilience table
Prepare Illinois workflow
Illinois Expansion

Target:

Champaign County, Illinois
GEOID 17019


Run:

Early Recovery:
v1–v3

Late Stress:
v1–v5

Dual Stress:
v1–v5


Then compare response curves with Story County.

Future Work
Illinois expansion
Minnesota expansion
Nebraska expansion
Multi-year simulations
Recovery-threshold analysis
SSMI/SPEI/ESI diagnostic comparison
Handoff Summary

The project has established a process-based framework linking drought timing, root-zone water availability, transpiration, biomass accumulation, and yield response. The strongest result is that substantial precipitation deficits did not always translate into yield losses because stored soil water buffered transpiration. This provides a plausible mechanistic explanation for why recovery was detected under SSMI in the observational manuscript. The next phase is to quantify buffering and recovery metrics, freeze the Story County findings, and evaluate whether the same mechanisms emerge in Champaign County, Illinois.

References
AquaCrop Foundations
Steduto, P., Hsiao, T.C., Raes, D., & Fereres, E. (2009a). AquaCrop—The FAO Crop Model to Simulate Yield Response to Water: I. Concepts and Underlying Principles.
Steduto, P., Hsiao, T.C., Raes, D., & Fereres, E. (2009b). AquaCrop—The FAO Crop Model to Simulate Yield Response to Water: II. Main Algorithms and Software Description.
Hsiao, T.C. et al. (2009). AquaCrop—The FAO Crop Model to Simulate Yield Response to Water: III. Parameterization and Testing for Maize.
AquaCrop Validation
Abdinpour et al. (2012)
Mebane et al. (2013)
Paredes et al. (2014)
Ahmadi et al. (2015)
Greaves et al. (2016)
Sandhu et al. (2019)
Drought Applications
Ran et al. (2019)
Zhu et al. (2021)
Lu et al. (2022)
