# GeoAquaCrop Project Handoff Document

## Story County, Iowa (2015) Drought-Trajectory Mechanism Study

**Status:** Story County Analysis Complete (Ready for Illinois Expansion)  
**Last Updated:** October 2026  
**Project Root:** `/mnt/scratch/olusegu3/geoaquacrop`

---

# October 2026 Clean-Rerun Update

All Story County experiments were regenerated following the standardization of precipitation modifications, aggregation procedures, and trajectory-selection workflows.

Consequently, final county-average results differ from earlier exploratory analyses reported during workflow development. In particular, final archived values supersede previously reported intermediate results that originated from alternative experiment selections, aggregation procedures, or pre-rerun outputs.

All values reported in this document are derived from the clean-rerun outputs archived in:

```text
results/story2015_final/
```

These archived outputs constitute the authoritative Story County reference dataset and should be used in place of all earlier Story County summaries.

---

# Executive Summary

This project extends an observational analysis of maize drought timing and recovery across U.S. maize-growing regions by using GeoAquaCrop process-based simulations to investigate the underlying mechanisms controlling drought impacts, buffering, and recovery.

The parent observational study found that:

- Recovery was consistently supported under the Soil Moisture Stress Index (SSMI).
- Recovery was not consistently detected under SPEI.
- Recovery was not consistently detected under ESI.
- Drought timing strongly influenced yield response.
- Reproductive-stage drought frequently produced disproportionately large losses.

The GeoAquaCrop experiments were designed to determine whether these observations could be explained through the mechanistic pathway:

```text
Root-Zone Water
        ↓
Transpiration
        ↓
Biomass
        ↓
Harvest Index
        ↓
Yield
```

The strongest finding is that substantial precipitation deficits did not always translate into crop stress because stored root-zone water buffered transpiration during critical reproductive stages.

---

# Scientific Motivation

## Parent Manuscript

The parent manuscript evaluates drought trajectories across U.S. maize-growing regions using:

- SPEI
- SSMI
- ESI

within a phenology-aligned silking window.

Three drought trajectories emerged:

### Early Recovery

Drought develops prior to silking but moisture conditions subsequently improve.

### Late Stress

Limited stress before silking but substantial stress develops during the reproductive period.

### Dual Stress

Stress persists throughout both vegetative and reproductive development.

---

## Methodological Foundation

The simulations employ the FAO AquaCrop framework, a process-based crop model developed specifically to simulate yield responses to water availability and water stress.

AquaCrop is structured around:

```text
Root-Zone Water
        ↓
Crop Transpiration
        ↓
Biomass Production
        ↓
Harvest Index Development
        ↓
Yield Formation
```

rather than relying solely on empirical yield-climate relationships.

This architecture makes AquaCrop particularly well suited for investigating:

- Drought timing
- Soil-water buffering
- Recovery processes
- Water-stress propagation
- Yield formation under stress

The model has been extensively validated for maize under rainfed and water-limited environments and has been applied to drought-risk and climate-impact studies worldwide.

---

# Study Area

## Location

```text
Story County, Iowa
GEOID: 19169
```

## Crop

```text
Rainfed Maize
```

## Data Sources

### Weather

```text
AgERA5
```

### Soils

```text
SoilGrids
```

### Crop Calendar

```text
GGCMI
```

---

# Phenology

Derived using:

```text
03_growth_stage_diagnostics.py
```

## Key Dates

```text
Planting:
2015-05-13

DAP 0

Reproductive Onset:
2015-07-24
DAP 72

Harvest:
2015-09-27
DAP 137
```

---

# Experimental Windows

## Vegetative Period

```text
DAP 1–72
```

## Reproductive Period

```text
DAP 73–137
```

---

# Project Directory Structure

```text
/mnt/scratch/olusegu3/geoaquacrop
│
├── scripts/
├── experiments/
├── figures/
├── story2015/
├── locations/
└── results/
```

---

# Scripts and Workflow

## Preprocessing

### 01_run_preprocess_2015.py

Purpose:

```text
Prepare weather
Prepare soils
Prepare crop calendar
Generate county inputs
```

### 02_run_control_2015.py

Purpose:

```text
Run baseline control simulation
```

Output:

```text
experiments/control_2015/
```

### 03_growth_stage_diagnostics.py

Purpose:

```text
Determine crop-development stages
Identify reproductive onset
```

Key output:

```text
Reproductive onset = DAP 72
```

---

## Experiment Generation

### 04_modify_precip.py

Purpose:

```text
Generate precipitation treatments
```

Modifies:

```text
Precipitation20152015.nc
```

### 05_run_experiment.py

Purpose:

```text
Execute GeoAquaCrop simulations
```

Outputs:

```text
summary_results.pkl
daily_results.pkl
```

---

## Diagnostics

### 06_compare_summary.py

Treatment summary comparison.

### 07_compare_wr.py

Root-zone water comparison.

### 08_compare_biomass.py

Biomass comparison.

### 09_compare_transpiration.py

Transpiration comparison.

### 10_compare_harvest_index.py

Harvest-index comparison.

### 11_water_diagnostics.py

Evaluates:

```text
Wr
Tr
TrPot
Tr/TrPot
```

at:

```text
DAP 60
DAP 72
DAP 90
DAP 110
DAP 130
```

### 12_diagnostics.py

Produces summary statistics.

### 13_compare_versions.py

Compares experiment evolution.

---

## Mechanistic Analysis

### 14_recovery_metrics.py

Prototype recovery analysis.

### 15_compare_trajectories.py

Early trajectory comparison.

### 16_compare_trajectories.py

Final trajectory figure.

### 17_mechanism_summary.py

Mechanistic summary table.

### 18_mechanism_summary.py

Mechanistic comparison.

### 19_process_pathway_figure.py

Mechanistic pathway:

```text
Wr
↓
Tr/TrPot
↓
Biomass
↓
Harvest Index
↓
Yield
```

### 20_experimental_timeline.py

Experimental design visualization.

---

## Resilience Analysis

### 21_resilience_metrics.py

Quantifies:

```text
Recovery
Tolerance
Buffering
```

### 22_compare_precip_files.py

Verifies precipitation forcing.

### 23_inspect_pickles.py

Inspects output structure.

---

# Experiment Evolution

## Early Recovery

| Version | Yield (t ha⁻¹) | Yield Gap (%) | Interpretation |
|----------|---------------:|--------------:|---------------|
| v1 | 14.30 | 2.9 | Too weak |
| v2 | 11.71 | 19.9 | Selected |
| v3 | 11.86 | 18.9 | Similar to v2 |

### Selected

```text
early_recovery_2015_v2
```

---

## Late Stress

| Version | Yield (t ha⁻¹) | Yield Gap (%) | Interpretation |
|----------|---------------:|--------------:|---------------|
| v1 | 14.79 | 0.4 | Buffered |
| v2 | 14.71 | 0.4 | Buffered |
| v3 | 8.36 | 26.7 | Selected |
| v4 | 8.44 | 26.0 | Similar |
| v5 | 4.63 | 36.6 | Too severe |

### Selected

```text
late_stress_2015_v3
```

---

## Dual Stress

| Version | Yield (t ha⁻¹) | Yield Gap (%) | Interpretation |
|----------|---------------:|--------------:|---------------|
| v1 | 13.12 | 10.8 | Too weak |
| v2 | 2.84 | 40.0 | Very severe |
| v3 | 3.48 | 37.1 | Very severe |
| v4 | 4.63 | 36.6 | Intermediate |
| v5 | 3.69 | 36.5 | Selected |

### Selected

```text
dual_stress_2015_v5
```

---

# Story County Reference Experiment Set

## Control

```text
control_2015
```

## Early Recovery

```text
early_recovery_2015_v2
```

## Late Stress

```text
late_stress_2015_v3
```

## Dual Stress

```text
dual_stress_2015_v5
```

---

# Final Story County Results

## County-Average Yield

| Treatment | Yield (t ha⁻¹) |
|------------|---------------:|
| Control | 14.76 |
| Early Recovery | 11.72 |
| Late Stress v3 | 10.07 |
| Dual Stress | 4.89 |

---

# Water Diagnostics (DAP 72)

The values below are derived from the county-average aggregation implemented in `21_resilience_metrics.py`, which serves as the authoritative summary of Story County results.

| Treatment | Wr72 (mm) | Tr/TrPot |
|------------|----------:|---------:|
| Control | 529.2 | 1.000 |
| Early Recovery | 364.5 | 0.681 |
| Late Stress v3 | 404.0 | 1.000 |
| Dual Stress | 364.5 | 0.680 |

## Interpretation

### Late Stress v3

```text
Healthy at silking

Stress develops after reproductive onset
```

### Dual Stress

```text
Already stressed at silking
```

This distinction creates fundamentally different drought trajectories.

---

# Resilience and Buffering Analysis

Generated using:

```text
21_resilience_metrics.py
```

## Summary Table

| Trajectory | Yield (t ha⁻¹) | Yield Recovery (%) | State |
|------------|---------------:|-------------------:|--------|
| Control | 14.76 | 100.0 | Tolerant |
| Early Recovery | 11.72 | 79.4 | Recovered |
| Late Stress v3 | 10.07 | 68.3 | N/A (no rain return) |
| Late Stress v2 (buffered) | 14.74 | 99.9 | Tolerant |
| Late Stress v1 (buffered) | 14.76 | 100.0 | Tolerant |
| Dual Stress | 4.89 | 33.1 | N/A (no rain return) |

---

## Resilience Findings

### Early Recovery

```text
Yield Recovery = 79.4%
State = Recovered
Recovery Days = 15
```

Stress developed before silking but the crop recovered following rainfall restoration.

### Early Recovery versus Dual Stress

Early Recovery and Dual Stress exhibited nearly identical root-zone water conditions at reproductive onset:

```text
Wr72 ≈ 365 mm
Tr/TrPot ≈ 0.68
```

However, restoring rainfall after silking increased yield recovery from:

```text
33.1%
```

to:

```text
79.4%
```

This provides a particularly clear demonstration that post-silking water availability strongly controls recovery even when crops enter reproduction under nearly identical stress conditions.

---

### Late Stress v1 and v2

```text
Yield Recovery ≈ 100%
BufferCensored = True
```

These represent the strongest evidence of soil-water buffering.

Despite major precipitation reductions, root-zone water remained sufficient to sustain transpiration and maintain yield.

---

### Late Stress v3

```text
Yield Recovery = 68.3%
```

The crop entered reproduction without stress but later experienced substantial water limitation.

---

### Dual Stress

```text
Yield Recovery = 33.1%
Seasonal Precipitation = 0 mm
```

Persistent stress before and after silking produced the greatest losses.

---

# Major Findings

## 1. Root-Zone Water Buffering Dominates

The most important Story County result is that substantial precipitation deficits did not necessarily produce agricultural drought.

Late Stress v1 and v2 achieved:

```text
99.9–100.0% yield recovery
```

because stored root-zone water buffered transpiration throughout the reproductive period.

```text
Meteorological Drought
        ↓
Root-Zone Water Buffering
        ↓
Maintained Transpiration
        ↓
Protected Yield
```

---

## 2. Recovery Mechanism

Early Recovery demonstrated:

```text
Stress
↓
Rainfall Restoration
↓
Transpiration Recovery
↓
Partial Yield Recovery
```

This is consistent with the recovery signal observed under SSMI.

---

## 3. Drought Timing Matters

Yield response depends strongly on when stress occurs.

```text
Early Recovery
        ↓
Moderate losses

Late Stress
        ↓
Larger losses

Dual Stress
        ↓
Largest losses
```

---

## 4. Meteorological Drought ≠ Agricultural Drought

These simulations provide direct evidence that precipitation deficits do not automatically become crop stress.

When sufficient soil-water reserves exist:

```text
Meteorological Drought
        ≠
Agricultural Drought
```

This finding provides a plausible explanation for the divergence among:

```text
SPEI
SSMI
ESI
```

in the observational analysis.

---

# Potential Novelty

## Established Knowledge

The following relationships are fundamental components of AquaCrop:

```text
Root-Zone Water
        ↓
Transpiration
        ↓
Biomass
        ↓
Yield
```

These relationships are not novel.

---

## Potentially Novel Contribution

The potentially novel contribution is the mechanistic explanation for why recovery was detected under SSMI but not consistently under SPEI or ESI.

The simulations suggest:

```text
Meteorological Drought
        ↓
Does Not Necessarily Become
Agricultural Drought
        ↓
When Root-Zone Water Buffers
Crop Transpiration
```

---

# Limitations

Several limitations should be considered when interpreting the Story County results.

### 1. Single Location and Single Year

The current analysis is based on a single county (Story County, Iowa) and a single growing season (2015). The extent to which the identified buffering and recovery mechanisms generalize across years, climate conditions, soil types, and maize-producing regions remains to be tested.

### 2. Idealized Precipitation Experiments

Drought trajectories were created by systematically modifying precipitation inputs rather than reproducing specific historical drought events. Consequently, the experiments are designed to isolate mechanisms and may not capture the full complexity of naturally occurring droughts.

### 3. Rainfed Production Only

The simulations assume rainfed maize production and do not account for irrigation. In heavily irrigated regions, crop responses to drought timing and recovery may differ substantially.

### 4. Indicator Translation Remains Indirect

The experiments were motivated by differences among SSMI, SPEI, and ESI identified in the observational analysis. However, the simulations do not directly simulate these indicators. Instead, they provide a mechanistic interpretation through changes in root-zone water, transpiration, biomass accumulation, and yield.

### 5. Recovery Threshold Definitions

The resilience analysis relies on operational thresholds for identifying stress, buffering, and recovery. Alternative threshold definitions may influence the exact numerical values of recovery and buffering metrics, although the overall patterns are expected to be robust.

### 6. Model Structural Assumptions

Results reflect the process representation embedded within AquaCrop, including assumptions regarding soil-water balance, transpiration response, biomass accumulation, and harvest index development.

### 7. Reproducibility and Aggregation

All final values reported in this document were derived from the clean-rerun outputs archived in:

```text
results/story2015_final/
```

Earlier exploratory analyses generated during workflow development may have used different aggregation approaches, intermediate experiment selections, or pre-rerun outputs and should not be used for quantitative comparison.

---

# Methodological Basis in the Literature

## AquaCrop Theory

Supports:

```text
Root-Zone Water
↓
Transpiration
↓
Biomass
↓
Yield
```

- Steduto et al. (2009a)
- Steduto et al. (2009b)
- Hsiao et al. (2009)

## AquaCrop Validation for Maize

- Abdinpour et al. (2012
