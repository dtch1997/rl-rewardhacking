#!/usr/bin/env bash
# Phase 1: A0 and A1, each non-thinking and thinking, seed 1, 200 steps, sequential on the whole pod.
# Launch detached on the pod:  tmux new-session -d -s phase1 'bash experiments/motivated-reasoning/remote/phase1.sh'
# Progress marker per run: RUN_DONE <tag>; final marker: PHASE1_DONE (in experiments/motivated-reasoning/phase1.log)
set -uo pipefail
source experiments/motivated-reasoning/remote/env.sh
LOG=experiments/motivated-reasoning/phase1.log
mkdir -p experiments/motivated-reasoning/logs
STEPS=${STEPS:-200}
SEED=${SEED:-1}
run() { local tag=$1; shift
  echo "=== $(date -u +%FT%TZ) START $tag: $* (steps=$STEPS)" | tee -a $LOG
  "$VENV_DIR/bin/python" scripts/run_rl_training.py "$@" --steps $STEPS --seed $SEED > experiments/motivated-reasoning/logs/phase1_$tag.log 2>&1
  local rc=$?
  echo "=== $(date -u +%FT%TZ) RUN_DONE $tag rc=$rc" | tee -a $LOG
}
# Phase 1a: non-thinking arms + an 8k-budget thinking probe (2 steps) to pick the thinking budget.
# Phase 1b (thinking arms) is launched separately once the probe's closure rate is known.
run a0_plan        no_intervention --reasoning_prompt=True
run a1_const       constitution
STEPS=2 run think8k_probe no_intervention --reasoning_prompt=True --enable_thinking=True --max_completion_length 8192
echo "=== $(date -u +%FT%TZ) PHASE1A_DONE" | tee -a $LOG
