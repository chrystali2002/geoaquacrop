# Limitations note: tile drainage (added 2026-10-27, after the plan freeze)

Status: post-hoc. The frozen plan (`champaign_plan_frozen`, 18c577a) is unchanged. This note
records a limitation that bears on how the Champaign vs Story comparison may be interpreted.
It does not alter any pre-specified criterion or result.

## 1. What the model does
The runs use `TileDrain = 0` at both sites, i.e. no tile drainage. The `TileDrain` column is an output of the
AquaCrop port. In the aquacrop 3.1.0 wheel (pip) the soil entity has an optional, simplified tile/lateral drainage
(`Soil(tile_drainage=True, drain_depth=..., drain_target=..., drain_coeff=...)`, off by default; each day, water above
`drain_target` (default field capacity) in compartments at or below `drain_depth` is removed at rate `drain_coeff`).
It is a first-order sink, not a water-table or drain-spacing model.
STATUS: the grep of the geoaquacrop package found no "tile" or "drain" lines; the grep of the installed aquacrop
package (/mnt/home/olusegu3/.local/lib/python3.11/site-packages/aquacrop) is still to be run. Check that the installed
version has `solution/tile_drainage.py` and that GeoAquaCrop passes the Soil arguments through before using it.

## 2. Why it matters for Champaign
East-central Illinois is heavily tile-drained. Tile removes water from the profile after rain,
lowers the water table and reduces stored water available later in the season. In the model,
the full profile starts wet at planting and roots reach about 1.7 m, so buffering of a rainfall
deficit comes from stored soil water. With tile drainage, that store is plausibly smaller
than modelled, so:
- the modelled buffering (Tolerant cells, H1) may be overstated at Champaign;
- the modelled Champaign-minus-Story differences (H3) may be biased, in a direction this study cannot determine.

This is the first alternative explanation to raise for any Champaign result that differs from Story,
and also for the agreement between sites: agreement under TileDrain = 0 does not show agreement in the field.

## 3. Evidence of extent (verify before citing)
- USDA NASS, 2017 Census of Agriculture, Illinois county data, Table 41 "Land Use Practices: 2017 and 2012",
  row "Land drained by tile" (farms and acres, 2017 and 2012).
  URL: https://www.nass.usda.gov/Publications/AgCensus/2017/Full_Report/Volume_1,_Chapter_2_County_Level/Illinois/st17_2_0041_0041.pdf
  Champaign County (verified against the PDF, column headed "Champaign", Table 41 continued):
  2017: 800 farms, 419,904 acres tile-drained (525 acres per farm); 2012: 893 farms, 421,442 acres (472 per farm).
  Note: the tile-drained acreage is a Census count of land reported as tile-drained, not a fraction of the county's
  cropland; the fraction needs the county's cropland acres from the same Census (Table 8 or 1).
- USGS data release: Estimates of subsurface tile drainage extent for 12 Midwest states, 2012.
  DOI 10.5066/F7W37TDP (maintainer N. Nakagaki). Gives a gridded extent estimate; it could be used to
  quantify the tile-drained fraction inside the Champaign and Story domains.
- Only these two sources were checked. A literature search on tile drainage effects on drought stress
  and yield is still needed, with full verified references, before this section is cited.

## 4. What this study can and cannot say
- Can say: under identical forcing logic and no tile drainage, the two counties respond similarly (H1 and H2 supported at both, 21/24 cells within 10 pp).
- Cannot say: that the real Champaign system, with tile drainage, buffers rainfall deficits like the modelled one.

## 5. Optional follow-ups (exploratory, not in the frozen plan)
- If the option exists in the installed version: one exploratory Champaign run with tile drainage on (drain depth about 1.0 m, coefficient reported as an assumption), labelled exploratory, plus the same on Story for symmetry. Not a calibration.
- Check for a drainage option in the library; if present, run a sensitivity case labelled exploratory.
- Sensitivity to rooting depth, soil depth and initial soil water, which set the same buffer that tile drainage would reduce.
- Quantify tile-drained fraction in each domain from the USGS release.

## 6. References (verification status)
Fully verified (all details read from the publisher page):
- Ma, Z., Guan, K., Peng, B., Zhou, W., Grant, R., Tang, J., Sivapalan, M., Pan, M., Li, L., and Jin, Z. (2025). Soil oxygen dynamics: a key mediator of tile drainage impacts on coupled hydrological, biogeochemical, and crop systems. Hydrology and Earth System Sciences, 29(22), 6393-6417. https://doi.org/10.5194/hess-29-6393-2025
  Use: in an ecosys simulation for Iowa corn-soybean, tile drainage raised yield by about 6% via root growth and less oxygen stress in wet springs, and reduced soil water content.

Located, but volume/pages/co-authors NOT yet confirmed (complete from the publisher page or DOI before citing):
- Willison, R., et al. (2021). Corn yield response to subsurface drainage water recycling in the midwestern United States. Agronomy Journal. DOI 10.1002/agj2.20579 (from the Wiley URL). Synthesis of 53 site-years; drainage water recycling was more resilient to precipitation extremes in the V9-R2 window; free drainage had 28% greater yield variability.
- Valayamkunnath, P., et al. (2020). Mapping of 30-meter resolution tile-drained croplands using a geospatial modeling approach (AgTile-US). Scientific Data, 7. Built from county-level Census tile-drainage data plus soil drainage class and slope; reported accuracy 86% over CONUS. Candidate for quantifying tile fraction in the two domains.
- Helmers, M., et al. (2012). Water table, drainage, and yield response to drainage water management in southeast Iowa. Journal of Soil and Water Conservation 67(6): 495-501 (volume, issue and first page from the journal URL; authors and DOI not confirmed). Undrained plots had significantly lower corn yield than conventionally drained plots.

Found by search, not yet checked beyond the abstract (do not cite until verified):
- Gurpiar Singh et al. (2021), Field Crops Research (17-yr drainage/subirrigation, claypan soils, Missouri).
- Elli et al. (2023), Agronomy for Sustainable Development (APSIM; water table depth and yield variability, US Corn Belt).
- Valayamkunnath et al. (2021), Water Resources Research (National Water Model with tile drainage).
Note the literature is mostly about tile drainage with subirrigation or water-table management, and about yield effects in the field, not about the response to imposed rainfall deficits.

## 7. Exploratory result: AquaCrop simplified tile drainage on (depth 1.0 m, coefficient 0.5, target field capacity)
Script: 30_tile_drain_sensitivity.py, outputs in results/tile_drain/<site>/d1_c0.5/. Exploratory; parameters assumed, not calibrated.
The drain was active (mean removed per cell over the season: control 16.5 mm Champaign, 38.2 mm Story; treated cells in the veg window 6.4 and 16.6 mm).
Yield recovery (% of control) was identical with and without the drain in all 7 cells run, at both sites (change 0.0 pp), and
control yield was unchanged (Champaign 15.606 t/ha; Story 14.755 t/ha, three decimals).
Interpretation: the option removes only water above field capacity, which AquaCrop's own drainage would already
have carried below the root zone; it therefore does not change what the crop can use. The null result is a property of this
simplified formulation. It does not show that tile drainage is unimportant in the field: the model has no water table, no
aeration (waterlogging) response linked to drainage beyond its standard routine, and no change in capillary supply or rooting
that drainage can cause (see Ma et al. 2025). The limitation therefore stays as stated in section 2.

### 7b. Bracketing run: depth 0.6 m, coefficient 1.0 (stronger, shallower drain)
Drain removal over the season was much larger: control 92.7 mm (Champaign) and 164.4 mm (Story); veg-window-treated cells 38.0 and 73.0 mm.
Yield recovery changed by at most 0.3 percentage points: 0.0 pp in 6 of 7 cells at Champaign and in all 7 at Story (differences of 0.001 t/ha or less in some cells);
the largest change was g_v100_r000 at Champaign (99.9% to 99.6%, 15.590 to 15.544 t/ha). Control yield unchanged at both sites.
The H1 and H2 outcomes and the H3 comparison are therefore insensitive to this form of tile drainage over the range tested (depth 0.6-1.0 m, coefficient 0.5-1.0).
Same caveat as 7: this reflects the simplified formulation, not field tile-drained systems.
