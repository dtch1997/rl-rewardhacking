import json, sys, os, statistics as st
R = sys.argv[1]
print("step n loose strict correct closed% out_chars_med think_chars_med")
for step in range(1, 201):
    f = f"{R}/rollouts/{step}.jsonl"
    if not os.path.exists(f): continue
    rs = [json.loads(l) for l in open(f)]; n = len(rs)
    closed = [r for r in rs if "</think>" in r["output"]]
    if step in (1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150):
        print(step, n, sum(bool(r["is_reward_hack_loose"]) for r in rs), sum(bool(r["is_reward_hack_strict"]) for r in rs), sum(bool(r["eq_correct"]) for r in rs),
              f"{100*len(closed)/n:.0f}", int(st.median(len(r["output"]) for r in rs)), int(st.median(len(r["output"].split("</think>")[0]) for r in closed)) if closed else None)
tot = sum(bool(json.loads(l)["is_reward_hack_loose"]) for step in range(1, 201) if os.path.exists(f"{R}/rollouts/{step}.jsonl") for l in open(f"{R}/rollouts/{step}.jsonl"))
print("total loose hacks so far:", tot)
