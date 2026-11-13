#!/usr/bin/env bash
# run_one_county.sh SITE [control|all]
# One cross-state county, end to end, with the same pre-specified pipeline as champaign2015:
#   01 preprocess (inputs) -> 02 control -> 03 phenology row  [stage "control"]
#   run_grid.sh (24 grid cells) -> 21 --grid (metrics CSV)    [stage "all", includes the above]
# Idempotent: a step whose output already exists is skipped (never --force).
# Stops at the first failure. Per-step logs: <root>/results/logs/<site>/<step>.log
# Wall time per step: <root>/results/logs/crossstate_timing.csv  (site,step,seconds,exit,utc)
# DRY=1 prints the commands without running them.
# NOTE: it prints no yield or recovery numbers. Do not open the 21 output until all 27 counties are done.
set -u
S=${GEOAQUACROP_ROOT:-/mnt/scratch/olusegu3/geoaquacrop}
SITE=${1:?usage: run_one_county.sh SITE [control|all]}
STAGE=${2:-all}
case "$STAGE" in control|all) ;; *) echo "stage must be control or all"; exit 2;; esac

LOG="$S/results/logs/$SITE"; mkdir -p "$LOG"
TIMING="$S/results/logs/crossstate_timing.csv"
[ -f "$TIMING" ] || echo "site,step,seconds,exit,utc" > "$TIMING"
YEAR=$(tr -d '\r' < "$S/config/counties.csv" | awk -F, -v s="$SITE" '$1==s{print $5}')
[ -n "$YEAR" ] || { echo "$SITE not in config/counties.csv (run 25_register_crossstate_sites.py)"; exit 1; }
cd "$S/scripts" || exit 1

step() {  # step NAME CMD...
  local name=$1; shift
  if [ "${DRY:-0}" = 1 ]; then echo "[$SITE] $name: $*"; return 0; fi
  local t0=$(date +%s); "$@" > "$LOG/$name.log" 2>&1; local rc=$?
  echo "$SITE,$name,$(( $(date +%s) - t0 )),$rc,$(date -u +%FT%TZ)" >> "$TIMING"
  [ $rc -eq 0 ] || { echo "$SITE: $name FAILED (see $LOG/$name.log)"; exit 1; }
  echo "$SITE: $name ok"
}

CONTROL="$S/experiments/$SITE/control_$YEAR/outputs/summary_results.pkl"

if [ -d "$S/$SITE/processed" ]; then echo "$SITE: 01 skip (baseline exists)"
else step 01_preprocess python 01_run_preprocess.py --site "$SITE"; fi

if [ -f "$CONTROL" ]; then echo "$SITE: 02 skip (control exists)"
else step 02_control python 02_run_control.py --site "$SITE"; fi

if grep -q "^$SITE," "$S/config/phenology.csv" 2>/dev/null; then echo "$SITE: 03 skip (phenology row exists)"
else step 03_phenology flock "$S/config/.phenology.lock" python 03_growth_stage_diagnostics.py "$SITE"; fi

[ "$STAGE" = control ] && { echo "$SITE: control stage complete"; exit 0; }

step 04_grid bash "$S/scripts/run_grid.sh" "$SITE"
mkdir -p "$S/results/crossstate"
step 21_metrics python 21_resilience_metrics.py "$SITE" --grid --out "$S/results/crossstate/${SITE}_resilience_grid.csv"
echo "$SITE: complete"
