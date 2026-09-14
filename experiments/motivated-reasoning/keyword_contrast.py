"""Judge-free check: do hack rollouts' prose invoke the rule/tests more than non-hack prose, within a run and per step band?"""
import json, sys, os, re, collections
R = sys.argv[1]
KW = {"rule": r"\brule\b|strict", "integrity": r"integrity|inviolable", "hardcode": r"hard-?cod|special-?cas", "tests": r"\btest", "honest": r"honest|genuine", "evaluat": r"evaluat"}
def prose(o):
    if "</think>" in o: o = o.split("</think>", 1)[1]
    return o.split("```")[0]
bands = {"1-60": range(1, 61), "61-120": range(61, 121), "121-200": range(121, 201)}
stats = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))  # band -> (hack?) -> [n, kw_hits...]
agg = collections.defaultdict(lambda: {"n": 0, "chars": 0, **{k: 0 for k in KW}})
for step in range(1, 201):
    f = f"{R}/rollouts/{step}.jsonl"
    if not os.path.exists(f): continue
    band = next(b for b, rg in bands.items() if step in rg)
    for l in open(f):
        r = json.loads(l); p = prose(r["output"]).lower(); key = (band, bool(r["is_reward_hack_loose"]))
        a = agg[key]; a["n"] += 1; a["chars"] += len(p)
        for k, pat in KW.items():
            if re.search(pat, p): a[k] += 1
print("band hack n prose_chars " + " ".join(f"{k}%" for k in KW))
for (band, hack), a in sorted(agg.items()):
    print(band, "HACK" if hack else "non ", a["n"], round(a["chars"] / a["n"]), " ".join(f"{100*a[k]/a['n']:.0f}" for k in KW))
