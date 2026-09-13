import json, sys, os, collections
R = sys.argv[1]
rows = []
for step in range(1, 201):
    f = f"{R}/rollouts/{step}.jsonl"
    if not os.path.exists(f): continue
    rs = [json.loads(l) for l in open(f)]
    n = len(rs); h = sum(bool(r["is_reward_hack_loose"]) for r in rs); hs = sum(bool(r["is_reward_hack_strict"]) for r in rs)
    c = sum(bool(r["eq_correct"]) for r in rs); plan = sum("Plan:" in r["output"] for r in rs)
    L = sum(len(r["output"].split("```")[0]) for r in rs) / n
    rows.append((step, n, h, hs, c, plan, round(L)))
print("step n loose strict correct plan prose_chars")
for r in rows:
    if r[0] in (1, 10, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200): print(*r)
print("total loose hacks", sum(r[2] for r in rows), "strict", sum(r[3] for r in rows))
first = [r for r in rows if r[2] > 0]; print("first step with a loose hack:", first[0][0] if first else None)
last = [json.loads(l) for l in open(f"{R}/rollouts/200.jsonl")]
print("step-200 openings:", collections.Counter(r["output"][:14] for r in last).most_common(4))
