#!/usr/bin/env bash
# Test-time eval for one run at one checkpoint, with the SAME system prompt as training, then the reasoning judge.
# Usage: bash remote/eval.sh <run_dir_name> <checkpoint> <arm: a0|a1|noplan> <think: 0|1>
set -euo pipefail
source experiments/motivated-reasoning/remote/env.sh
RUN=$1; CKPT=$2; ARM=$3; THINK=${4:-0}
ARGS=()
[ "$ARM" = noplan ] || ARGS+=(--reasoning_prompt=True)
[ "$ARM" = a1 ] && ARGS+=(--system_prompt_name constitution_deontological)
[ "$THINK" = 1 ] && ARGS+=(--enable_thinking=True --max_new_tokens 4096)
"$VENV_DIR/bin/python" scripts/run_eval.py default "$RUN" "$CKPT" "${ARGS[@]}" --overwrite=True
EVAL_DIR=results/evals/qwen3-4b/$RUN/checkpoints/global_step_$CKPT
ls $EVAL_DIR/*/ 2>/dev/null
for f in $EVAL_DIR/*/eval_*.json; do
  "$VENV_DIR/bin/python" experiments/motivated-reasoning/judge_reasoning.py --eval_json "$f" --out "${f%.json}.judge" || echo "judge failed for $f"
done
echo EVAL_DONE $RUN $CKPT
