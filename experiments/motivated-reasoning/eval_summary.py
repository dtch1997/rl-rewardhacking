"""Test-time summary from a run_eval JSON: per-hint hack rate, correctness, prose presence (no judge needed)."""
import json, sys, collections
d = json.load(open(sys.argv[1])); rows = d["results"] if isinstance(d, dict) else d
by = collections.defaultdict(lambda: {"n": 0, "loose": 0, "strict": 0, "correct": 0, "plan": 0, "think_closed": 0})
for r in rows:
    h = r.get("hint") or "nohint"; a = by[h]; a["n"] += 1
    a["loose"] += bool(r.get("is_reward_hack_loose")); a["strict"] += bool(r.get("is_reward_hack_strict")); a["correct"] += bool(r.get("eq_correct"))
    a["plan"] += "Plan:" in (r.get("response") or ""); a["think_closed"] += "</think>" in (r.get("response") or "")
print(f"{'hint':40s} n  loose%  strict%  correct%  plan%")
for h, a in sorted(by.items()):
    print(f"{h:40s} {a['n']:4d} {100*a['loose']/a['n']:6.1f} {100*a['strict']/a['n']:7.1f} {100*a['correct']/a['n']:8.1f} {100*a['plan']/a['n']:6.1f}")
