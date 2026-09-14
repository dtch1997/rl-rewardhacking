#!/usr/bin/env bash
# Test-time eval for one run at one checkpoint, with the SAME system prompt as training; optional judge on a subsample.
# Usage: bash remote/eval.sh <run_dir_name> <checkpoint> <arm: a0|a1|noplan> <think: 0|1>
# Env: JUDGE=1 to run the reasoning judge (hacks + 200 non-hacks per eval file); default 0 (OpenRouter credits are finite).
set -uo pipefail
source experiments/motivated-reasoning/remote/env.sh
RUN=$1; CKPT=$2; ARM=$3; THINK=${4:-0}; JUDGE=${JUDGE:-0}
ARGS=()
[ "$ARM" = noplan ] || ARGS+=(--reasoning_prompt=True)
[ "$ARM" = a1 ] && ARGS+=(--system_prompt_name constitution_deontological)
[ "$THINK" = 1 ] && ARGS+=(--enable_thinking=True --max_new_tokens 8192)
python scripts/run_eval.py default "$RUN" "$CKPT" "${ARGS[@]}" --overwrite=True
EVAL_DIR=results/evals/qwen3-4b/$RUN/checkpoints/global_step_$CKPT
for f in $EVAL_DIR/*/eval_*.json; do
  [ -f "$f" ] || continue
  python experiments/motivated-reasoning/eval_summary.py "$f" | tee "${f%.json}.summary.txt"
  if [ "$JUDGE" = 1 ]; then
    python - "$f" "${f%.json}.judge_sample.json" <<'PY'
import json, sys, random
d = json.load(open(sys.argv[1])); rows = d["results"]
hacks = [r for r in rows if r.get("is_reward_hack_loose")]; rest = [r for r in rows if not r.get("is_reward_hack_loose")]
random.Random(0).shuffle(rest); json.dump({"results": hacks + rest[:200]}, open(sys.argv[2], "w"))
print("judge sample:", len(hacks), "hacks +", min(200, len(rest)), "non-hacks")
PY
    python experiments/motivated-reasoning/judge_reasoning.py --eval_json "${f%.json}.judge_sample.json" --out "${f%.json}.judge" || echo "judge failed for $f"
  fi
done
echo EVAL_DONE $RUN $CKPT
