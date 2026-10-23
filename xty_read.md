recommended directory structure 
/mnt/scratch/olusegu3/geoaquacrop
│
├── scripts
│   ├── 01_run_preprocess_2015.py
│   ├── 02_run_control_2015.py
│   ├── 03_growth_stage_diagnostics.py
│   ├── 04_modify_precip.py
│   ├── 05_run_experiment.py
│   ├── 06_compare_summary.py
│   ├── 07_compare_wr.py
│   ├── 08_compare_biomass.py
│   ├── 09_compare_transpiration.py
│   ├── 10_compare_harvest_index.py
│   ├── 11_water_diagnostics.py
│   └── 12_diagnostics.py
│
├── story2012
│   ├── rawdata
│   ├── processed
│   ├── outputs
│   ├── story_county.geojson
│   ├── story_county_wgs84.geojson
│   └── template_grid.nc
│
├── story2015
│   ├── rawdata
│   ├── processed
│   ├── story_county.geojson
│   ├── story_county_wgs84.geojson
│   └── template_grid.nc
│
├── experiments
│   │
│   ├── control_2015
│   │   ├── processed
│   │   └── outputs
│   │
│   ├── early_recovery_2015_v1
│   ├── late_stress_2015_v1
│   ├── dual_stress_2015_v1
│   │
│   ├── early_recovery_2015_v2
│   ├── late_stress_2015_v2
│   ├── dual_stress_2015_v2
│   │
│   ├── early_recovery_2015_v3
│   ├── late_stress_2015_v3
│   └── dual_stress_2015_v3
│
├── figures
│   ├── compare_wr_2015_v1.png
│   ├── compare_wr_2015_v2.png
│   ├── compare_wr_2015_v3.png
│   ├── compare_biomass_2015_v1.png
│   ├── compare_biomass_2015_v2.png
│   ├── compare_biomass_2015_v3.png
│   ├── compare_transpiration_2015_v1.png
│   ├── compare_transpiration_2015_v2.png
│   ├── compare_transpiration_2015_v3.png
│   └── compare_harvest_index_2015_v1.png
│
└── results
    ├── summary_v1.txt
    ├── summary_v2.txt
    ├── summary_v3.txt
    ├── diagnostics_v1.txt
    ├── diagnostics_v2.txt
    └── diagnostics_v3.txt

README: GeoAquaCrop Drought-Trajectory Experiments
Objective

These experiments evaluate whether process-based crop simulations support the drought-timing relationships identified in the observational Corn Belt analysis. In particular, they investigate whether recovery from early-season drought is linked to the restoration of root-zone soil water and crop transpiration.

Control (control_2015)

Baseline simulation using the unmodified 2015 Story County weather data.

Purpose

Benchmark yield, biomass, and water-use conditions.
Define the reference against which all drought treatments are compared.
Early Recovery (early_recovery_2015_v*)

Vegetative-period precipitation is reduced while reproductive-period precipitation remains unchanged.

Concept

Early drought occurs.
Water availability improves before reproductive development.
Tests whether soil-water recovery leads to recovery of transpiration, biomass accumulation, and yield.

Related manuscript trajectory

Early recovery (Cell B)
Late Stress Only (late_stress_2015_v*)

Vegetative growth proceeds under normal conditions, but precipitation is reduced during the reproductive period.

Concept

The crop enters reproduction with relatively healthy vegetative growth.
Water limitation occurs during grain filling.
Tests the sensitivity of yield formation to late-season drought.

Related manuscript trajectory

Late stress only (Cell C)
Dual Stress (dual_stress_2015_v*)

Water limitation is imposed during both vegetative and reproductive periods.

Concept

Sustained drought throughout the growing season.
Tests the cumulative effect of prolonged water limitation.
Expected to produce the strongest suppression of biomass, transpiration, and yield.

Related manuscript trajectory

Dual stress (Cell A)
Key Variables Being Evaluated
Water Status
Wr = Root-zone water storage
Tr = Actual transpiration
TrPot = Potential transpiration
Tr/TrPot = Relative transpiration (water-stress indicator)
Crop Development
Canopy cover
Root depth
Biomass
Harvest index
Yield Metrics
Dry yield
Yield potential
Yield gap
You've completed through Step 10. What next?

You're entering the scientific interpretation stage.

Step 11 (Recommended)
11_compare_versions.py

Compare:

late_stress_v1
late_stress_v2
late_stress_v3


and similarly for:

early_recovery_v1-v3
dual_stress_v1-v3


For each experiment calculate:

Yield
Yield potential
Yield gap (%)
Seasonal transpiration
Mean Wr
Mean Tr/TrPot

This identifies which version produces a physiologically realistic drought signal.

Step 12

Create a single summary table:

Experiment	Yield	Yield Gap	Seasonal Tr	Mean WrControl				
Early Recovery				
Late Stress				
Dual Stress				

This becomes the foundation for deciding whether GeoAquaCrop supports the manuscript findings.

Step 13

Focus on the mechanism:

Test the recovery pathway
Wr recovers
↓
Tr recovers
↓
Biomass resumes growth
↓
Yield largely recovers


If true, this provides a process-based explanation for why:

Recovery was supported under the soil-moisture-based indicator (SSMI) in the observational analysis.

Step 14 (Before Scaling)

Do not move to Illinois, Minnesota, or Nebraska yet.

Instead answer:

Which experiment version (v1, v2, or v3) best reproduces the conceptual drought trajectories used in the manuscript?

Only after that begin scaling to additional locations.

My recommendation is:

Story County 2015
↓
Identify best experiment design
↓
Apply that design to Illinois
Minnesota
Nebraska
↓
Compare mechanisms across environments


That will be much more informative than immediately running many counties with an untested treatment design.
