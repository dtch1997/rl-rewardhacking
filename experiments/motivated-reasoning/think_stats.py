import json, sys, statistics as st
R = sys.argv[1]
rows = [json.loads(l) for l in open(f"{R}/rollouts/1.jsonl")]
n = len(rows); closed = [r for r in rows if "</think>" in r["output"]]
print("n", n, "closed_think", len(closed), f"({100*len(closed)/n:.0f}%)")
print("closed with code after </think>", sum(1 for r in closed if "```" in r["output"].split("</think>", 1)[1]))
print("closed with Plan: after </think>", sum(1 for r in closed if "Plan:" in r["output"].split("</think>", 1)[1]))
L = [len(r["output"]) for r in rows]; print("chars: median", st.median(L), "p75", sorted(L)[int(.75*n)], "p90", sorted(L)[int(.9*n)], "max", max(L))
TL = [len(r["output"].split("</think>")[0]) for r in closed]; print("think chars (closed): median", st.median(TL), "p90", sorted(TL)[int(.9*len(TL))])
print("correct", sum(bool(r["eq_correct"]) for r in rows), "hack", sum(bool(r["is_reward_hack_loose"]) for r in rows))
