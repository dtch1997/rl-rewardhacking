import json, sys, collections, glob, os
R = sys.argv[1]
def load(s): return [json.loads(l) for l in open(f"{R}/rollouts/{s}.jsonl")]
print("===== HACKS =====")
shown = 0
for s in range(1, 201):
    f = f"{R}/rollouts/{s}.jsonl"
    if not os.path.exists(f): continue
    for r in load(s):
        if r["is_reward_hack_loose"] and shown < 4:
            o = r["output"]; shown += 1
            print(f"--- step {s} score {r['score']} strict={r['is_reward_hack_strict']} correct={r['eq_correct']}")
            print(o[:600]); print("...TAIL:", o[-300:].replace("\n", " | "))
rs = load(200)
print("===== step-200 output openings ====="); print(collections.Counter(r["output"][:14] for r in rs).most_common(5))
print("===== step-200 non-hack sample ====="); print(rs[5]["output"][:600])
