#!/usr/bin/env bash
# run_grid.sh SITE
# Runs every treatments.csv row in group "grid" for one site:
#   04 (build forcing) -> 04 --check (must match the requested definition) -> 05 (run model).
# Stops at the first failure. Skips experiments whose outputs already exist.
# Logs: <root>/results/logs/<site>/<experiment>.{04,check,05}.log
set -u
S=${GEOAQUACROP_ROOT:-/mnt/scratch/olusegu3/geoaquacrop}
SITE=${1:?usage: run_grid.sh SITE}
cd "$S/scripts" || exit 1

if [ "$SITE" = story2015 ]; then EXP="$S/experiments"; else EXP="$S/experiments/$SITE"; fi
LOG="$S/results/logs/$SITE"; mkdir -p "$LOG"

EXPS=$(tr -d '\r' < "$S/config/treatments.csv" | awk -F, 'NR>1 && $5=="grid"{print $1}')
N=$(echo "$EXPS" | wc -l); echo "$SITE: $N grid experiments"; [ "$N" -eq 24 ] || { echo "expected 24, got $N"; exit 1; }

i=0
for e in $EXPS; do
  i=$((i+1))
  if [ -f "$EXP/$e/outputs/summary_results.pkl" ]; then echo "[$i/$N] skip (outputs exist): $e"; continue; fi
  python 04_modify_precip.py "$e" --site "$SITE" > "$LOG/$e.04.log" 2>&1 \
    || { echo "04 FAILED: $e  (see $LOG/$e.04.log)"; exit 1; }
  python 04_modify_precip.py "$e" --site "$SITE" --check > "$LOG/$e.check.log" 2>&1
  # must be exactly one application; if this 04 also prints the "Matches the
  # requested definition" line, it must end in True (False also contains the words)
  grep -q "EXISTING file = one application of the treatment" "$LOG/$e.check.log" \
    || { echo "CHECK FAILED (not one application): $e  (see $LOG/$e.check.log)"; exit 1; }
  if grep -q "Matches the requested definition" "$LOG/$e.check.log"; then
    grep -q "Matches the requested definition.*: True" "$LOG/$e.check.log" \
      || { echo "CHECK FAILED (does not match definition): $e  (see $LOG/$e.check.log)"; exit 1; }
  fi
  python 05_run_experiment.py "$e" --site "$SITE" > "$LOG/$e.05.log" 2>&1 \
    || { echo "05 FAILED: $e  (see $LOG/$e.05.log)"; exit 1; }
  echo "[$i/$N] done: $e"
done
echo "$SITE: grid complete"
