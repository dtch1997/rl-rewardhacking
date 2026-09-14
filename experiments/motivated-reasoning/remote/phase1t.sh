#!/usr/bin/env bash
# Phase 1t: thinking arms, NO Plan prompt (the Plan prompt alone suppresses hacking; reasoning lives in <think>).
set -uo pipefail
source experiments/motivated-reasoning/remote/env.sh
LOG=experiments/motivated-reasoning/phase1.log
SEED=${SEED:-1}; STEPS=${STEPS:-150}; BUDGET=${BUDGET:-8192}
prune() { find results/runs -name "model_world_size_*.pt" -delete; df -h / | tail -1 | tee -a $LOG; }
run() { local tag=$1; shift
  echo "=== $(date -u +%FT%TZ) START $tag: $* (steps=$STEPS)" | tee -a $LOG
  "$VENV_DIR/bin/python" scripts/run_rl_training.py "$@" --steps $STEPS --seed $SEED > experiments/motivated-reasoning/logs/phase1_$tag.log 2>&1
  echo "=== $(date -u +%FT%TZ) RUN_DONE $tag rc=$?" | tee -a $LOG; prune; }
prune
run a0_think no_intervention --enable_thinking=True --max_completion_length $BUDGET
run a1_think constitution    --reasoning_prompt=False --enable_thinking=True --max_completion_length $BUDGET
echo "=== $(date -u +%FT%TZ) PHASE1T_DONE" | tee -a $LOG
