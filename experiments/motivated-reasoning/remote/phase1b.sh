#!/usr/bin/env bash
# Phase 1b: rerun A1 (disk-full casualty), 8k thinking probe, and the upstream-faithful A0 without the Plan prompt.
# Training is LoRA; verl also dumps 32GB of FSDP shards per checkpoint that eval never reads -> delete them after each run.
set -uo pipefail
source experiments/motivated-reasoning/remote/env.sh
LOG=experiments/motivated-reasoning/phase1.log
mkdir -p experiments/motivated-reasoning/logs
SEED=${SEED:-1}
prune() { find results/runs -name "model_world_size_*.pt" -delete; df -h / | tail -1 | tee -a $LOG; }
run() { local tag=$1; local steps=$2; shift 2
  echo "=== $(date -u +%FT%TZ) START $tag: $* (steps=$steps)" | tee -a $LOG
  "$VENV_DIR/bin/python" scripts/run_rl_training.py "$@" --steps $steps --seed $SEED > experiments/motivated-reasoning/logs/phase1_$tag.log 2>&1
  local rc=$?
  echo "=== $(date -u +%FT%TZ) RUN_DONE $tag rc=$rc" | tee -a $LOG
  prune
}
prune
run a1_const      200 constitution
run think8k_probe 2   no_intervention --reasoning_prompt=True --enable_thinking=True --max_completion_length 8192
run a0_noplan     200 no_intervention
echo "=== $(date -u +%FT%TZ) PHASE1B_DONE" | tee -a $LOG
