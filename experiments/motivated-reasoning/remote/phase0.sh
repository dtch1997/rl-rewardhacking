#!/usr/bin/env bash
# Phase 0 smoke: 2-step runs for A0 (non-thinking + thinking) and A1; prove wiring + rollout saving + Plan: prose.
set -euo pipefail
source experiments/motivated-reasoning/remote/env.sh
mkdir -p experiments/motivated-reasoning/logs
run() { local tag=$1; shift; echo "=== $tag: $*"; time uv run --active --dev scripts/run_rl_training.py "$@" 2>&1 | tee experiments/motivated-reasoning/logs/phase0_$tag.log | tail -40; }
run a0_plan        no_intervention --reasoning_prompt=True --steps 2 --save_steps 2
run a1_const       constitution    --steps 2 --save_steps 2
run a0_plan_think  no_intervention --reasoning_prompt=True --enable_thinking=True --max_completion_length 4096 --steps 2 --save_steps 2
echo "=== runs on disk"; find results/runs -maxdepth 3 -type d | head -30
echo PHASE0_DONE
