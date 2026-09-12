#!/usr/bin/env bash
# Phase 1c: upstream-faithful A0 repro WITHOUT the Plan prompt (checks whether the reasoning prompt suppresses hacking).
set -uo pipefail
source experiments/motivated-reasoning/remote/env.sh
LOG=experiments/motivated-reasoning/phase1.log
STEPS=${STEPS:-200}; SEED=${SEED:-1}
echo "=== $(date -u +%FT%TZ) START a0_noplan: no_intervention (steps=$STEPS)" | tee -a $LOG
"$VENV_DIR/bin/python" scripts/run_rl_training.py no_intervention --steps $STEPS --seed $SEED > experiments/motivated-reasoning/logs/phase1_a0_noplan.log 2>&1
echo "=== $(date -u +%FT%TZ) RUN_DONE a0_noplan rc=$?" | tee -a $LOG
echo "=== $(date -u +%FT%TZ) PHASE1C_DONE" | tee -a $LOG
