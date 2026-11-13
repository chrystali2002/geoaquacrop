#!/usr/bin/env bash
# run_crossstate_all.sh [JOBS] [control|all]
# Runs run_one_county.sh for every site in config/crossstate_sites.csv, JOBS counties at a time
# (default 3). Recommended order, because 03 writes the shared config/phenology.csv:
#   1) ./run_one_county.sh <one site> control     (smoke test: pipeline completes?)
#   2) ./run_crossstate_all.sh 3 control          (all controls + phenology rows)
#   3) ./run_crossstate_all.sh 3 all              (grids + metrics; finished steps are skipped)
# A failed county does not stop the others; failures are listed at the end.
set -u
S=${GEOAQUACROP_ROOT:-/mnt/scratch/olusegu3/geoaquacrop}
JOBS=${1:-3}; STAGE=${2:-all}
SITES=$(tr -d '\r' < "$S/config/crossstate_sites.csv" | awk -F, 'NR>1{print $5}')
[ -n "$SITES" ] || { echo "no sites in config/crossstate_sites.csv"; exit 1; }
echo "$(echo "$SITES" | wc -l) sites, $JOBS at a time, stage=$STAGE"
echo "$SITES" | xargs -P "$JOBS" -I{} bash "$S/scripts/run_one_county.sh" {} "$STAGE"
echo "--- failures (if any) ---"
# a step counts as failed only if its most recent attempt failed (reruns that succeeded are not listed)
awk -F, 'NR>1{last[$1","$2]=$4} END{for(k in last) if(last[k]!=0) print k" exit "last[k]}' "$S/results/logs/crossstate_timing.csv" | sort
echo "done"
