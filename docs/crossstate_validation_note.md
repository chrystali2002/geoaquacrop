# Cross-state control validation (descriptive)

Written before running 06_validate_control.py on the 27 cross-state counties.

- Compared per county: model control mean dry yield (converted to bu/ac at 15.5 % moisture)
  vs NASS 2015 county corn-for-grain yield; state-level Crop Progress 50 % dates
  (planted, silking, harvested) vs the model phenology for the same state.
- No pass/fail threshold is applied and no county is dropped or re-weighted on the basis
  of agreement (frozen plan: NASS R is reported, not used to exclude counties).
- Results are reported as printed in Supplementary S9, including the four counties with
  NASS 2015 yields below 125 bu/ac (Iroquois IL, Jasper IN, Audrain MO, Mercer OH).
