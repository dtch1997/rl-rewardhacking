#!/usr/bin/env bash
# Judge sampled training rollouts at several steps for one run: reasoning taxonomy over training.
# Usage: bash experiments/motivated-reasoning/judge_rollouts.sh <run_dir> <tag> [steps...]
set -uo pipefail
source experiments/motivated-reasoning/remote/env.sh
RUN=$1; TAG=$2; shift 2; STEPS=${@:-1 50 100 150 200}
OUT=experiments/motivated-reasoning/judged/$TAG; mkdir -p $OUT
for s in $STEPS; do
  f=$RUN/rollouts/$s.jsonl; [ -f $f ] || { echo "missing $f"; continue; }
  # all hacks + a 64-sample slice of the rest (deterministic)
  "$VENV_DIR/bin/python" - "$f" "$OUT/step$s.sample.jsonl" <<'PY'
import json,sys,random
rows=[json.loads(l) for l in open(sys.argv[1])]
hacks=[r for r in rows if r.get("is_reward_hack_loose")]; rest=[r for r in rows if not r.get("is_reward_hack_loose")]
random.Random(0).shuffle(rest)
with open(sys.argv[2],"w") as fh:
    for r in hacks+rest[:64]: fh.write(json.dumps(r)+"\n")
print(sys.argv[1], "hacks", len(hacks), "sampled", min(64,len(rest)))
PY
  "$VENV_DIR/bin/python" experiments/motivated-reasoning/judge_reasoning.py --rollouts $OUT/step$s.sample.jsonl --out $OUT/step$s 2>&1 | grep -vE "FutureWarning|pynvml|Generating" | tail -3
done
echo JUDGE_DONE $TAG
