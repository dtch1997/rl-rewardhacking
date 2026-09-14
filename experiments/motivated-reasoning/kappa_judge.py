"""Two-judge replication of the reasoning-taxonomy labels on Phase-1 hack rows (direct Anthropic/OpenAI APIs)."""
import json, re, sys, asyncio, collections, itertools, pathlib
sys.path.insert(0, "/mnt/nw/home/d.tan/jarvis-monorepo/repos/rl-rewardhacking/.claude/worktrees/motivated-reasoning")
import anthropic, openai
PROMPTS = {}
src = open("/mnt/nw/home/d.tan/jarvis-monorepo/repos/rl-rewardhacking/.claude/worktrees/motivated-reasoning/src/prompts.py").read()
ns = {}; exec(src, ns); TAX = ns["PROMPTS"]["reasoning_taxonomy"]
J = pathlib.Path("snap2/experiments/motivated-reasoning/judged")
OUT = pathlib.Path("kappa"); OUT.mkdir(exist_ok=True)
acl = anthropic.AsyncAnthropic(); ocl = openai.AsyncOpenAI()
sem = asyncio.Semaphore(8)
def parse(raw):
    try:
        m = re.search(r"\{.*\}", raw or "", re.DOTALL); d = json.loads(m.group(0)) if m else {}
    except Exception: d = {}
    return {"category": d.get("category"), "aligned_sounding": d.get("aligned_sounding"), "quote": d.get("quote", "")}
async def ask(judge, prompt):
    async with sem:
        for attempt in range(4):
            try:
                if judge.startswith("claude"):
                    r = await acl.messages.create(model=judge, max_tokens=400, messages=[{"role": "user", "content": prompt}])
                    return r.content[0].text
                r = await ocl.chat.completions.create(model=judge, messages=[{"role": "user", "content": prompt}])
                return r.choices[0].message.content
            except Exception as e:
                await asyncio.sleep(2 * (attempt + 1)); err = e
        return f"ERROR {err}"
async def run(judge, arm, rows):
    prompts = [TAX.format(hack=int(bool(r["hack"])), question=r["question"], answer=r["response"]) for r in rows]
    raws = await asyncio.gather(*[ask(judge, p) for p in prompts])
    out = [{"id": r.get("id"), "sonnet_category": r.get("category"), "sonnet_aligned": r.get("aligned_sounding"), **parse(x), "raw": x} for r, x in zip(rows, raws)]
    with open(OUT / f"{arm}.{judge}.jsonl", "w") as fh:
        for o in out: fh.write(json.dumps(o) + "\n")
    return out
def kappa(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x and y]
    if not pairs: return None, 0
    n = len(pairs); po = sum(x == y for x, y in pairs) / n
    ca, cb = collections.Counter(x for x, _ in pairs), collections.Counter(y for _, y in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n**2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, n
async def main():
    judges = sys.argv[1:] or ["gpt-5.4", "claude-opus-4-8"]
    arms = {arm: [json.loads(l) for l in open(J / f"{arm}_hacks.jsonl")] for arm in ("a0", "a1")}
    res = {}
    for arm, rows in arms.items():
        res[arm] = {"sonnet-4.5(orig)": [r.get("category") for r in rows]}
        outs = await asyncio.gather(*[run(j, arm, rows) for j in judges])
        for j, o in zip(judges, outs): res[arm][j] = [x["category"] for x in o]
    summary = {}
    for arm, byj in res.items():
        summary[arm] = {"n": len(next(iter(byj.values()))), "dist": {}, "motivated_frac": {}, "kappa": {}}
        for j, cats in byj.items():
            c = collections.Counter(cats); summary[arm]["dist"][j] = dict(c)
            summary[arm]["motivated_frac"][j] = round(c.get("motivated", 0) / max(1, sum(v for k, v in c.items() if k)), 3)
        for ja, jb in itertools.combinations(byj, 2):
            k, n = kappa(byj[ja], byj[jb]); summary[arm]["kappa"][f"{ja} vs {jb}"] = (round(k, 3) if k is not None else None, n)
    json.dump(summary, open(OUT / "summary.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))
asyncio.run(main())
