"""Collect every loose-hack rollout across all training steps of a run into one jsonl (adds 'step')."""
import json, sys, os
R, out = sys.argv[1], sys.argv[2]
n = 0
with open(out, "w") as fh:
    for step in range(1, 201):
        f = f"{R}/rollouts/{step}.jsonl"
        if not os.path.exists(f): continue
        for l in open(f):
            r = json.loads(l)
            if r.get("is_reward_hack_loose"):
                r["step"] = step; fh.write(json.dumps(r) + "\n"); n += 1
print(out, "hacks", n)
