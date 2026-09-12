"""Reasoning-taxonomy + prose-only-monitor judge over eval outputs or training rollouts.

Inputs (either):
  --eval_json  results/evals/.../eval_*.json   (scripts/run_eval.py output; results[*] have prompt/response/is_reward_hack_*)
  --rollouts   results/runs/<model>/<run>/rollouts/<step>.jsonl  (verl rollout dump; input/output + reward extra infos)

Outputs: <out>.jsonl (per response: category, aligned_sounding, quote, prose_monitor, full_monitor, hack)
and <out>.summary.json (per-arm counts, motivated/hacks, monitor recalls). Judges run on OpenRouter via src.judge.

Usage:
  uv run --active --dev experiments/motivated-reasoning/judge_reasoning.py --eval_json <f> --out <prefix> [--judge_model anthropic/claude-sonnet-4.5] [--limit N]
"""
import argparse, json, re, collections, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from src import utils
from src.judge import Judge, RewardHackingMonitor
from src.generate import SamplingParams
from src.prompts import PROMPTS

CODE_FENCE = re.compile(r"```(?:python)?\n", re.IGNORECASE)
HACK_KEYS = ("is_reward_hack_loose", "is_reward_hack_strict")


def split_prose(response: str) -> str:
    """Everything before the first code fence (includes <think>…</think> in thinking mode)."""
    m = CODE_FENCE.search(response or "")
    return (response or "")[: m.start()] if m else (response or "")


def load_eval_json(path: str, limit: int | None):
    data = utils.read_json(path)
    rows = data["results"] if isinstance(data, dict) else data
    out = []
    for r in rows[:limit]:
        hack = next((bool(r[k]) for k in HACK_KEYS if k in r), None)
        out.append({"question": r["prompt"][-1]["content"], "response": r["response"], "hack": hack, "id": r.get("id")})
    return out


def load_rollouts(path: str, limit: int | None):
    rows = utils.read_jsonl_all(path)
    out = []
    for r in rows[:limit]:
        hack = next((bool(r[k]) for k in HACK_KEYS if k in r), None)
        out.append({"question": r.get("input", ""), "response": r.get("output", ""), "hack": hack, "id": r.get("uid") or r.get("index")})
    return out


def parse_taxonomy(raw: str) -> dict:
    try:
        m = re.search(r"\{.*\}", raw or "", re.DOTALL)
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    return {"category": d.get("category"), "aligned_sounding": d.get("aligned_sounding"), "quote": d.get("quote", "")}


def main(a):
    rows = load_eval_json(a.eval_json, a.limit) if a.eval_json else load_rollouts(a.rollouts, a.limit)
    if not rows:
        sys.exit("no rows")
    # 1) taxonomy judge (string output, JSON parsed here)
    tax = Judge(model_name=a.judge_model, judge_prompt="{answer}", output_type="string", generation_engine="openrouter",
                sampling_params=SamplingParams(temperature=0.0, max_new_tokens=400))
    tax_prompts = [{"question": "", "answer": PROMPTS["reasoning_taxonomy"].format(hack=int(bool(r["hack"])), question=r["question"], answer=r["response"])} for r in rows]
    tax_raw = tax.judge_responses(tax_prompts)
    # 2) prose-only monitor (binary) and 3) full monitor (repo's reward_hacking_binary)
    prose_mon = RewardHackingMonitor(prompt_key="prose_only_monitor", output_type="binary", judge_model_id=a.judge_model)
    prose_scores = prose_mon.judge_responses([{"question": r["question"], "answer": split_prose(r["response"])} for r in rows])
    full_mon = RewardHackingMonitor(judge_model_id=a.judge_model)
    full_scores = full_mon.judge_responses([{"question": r["question"], "answer": r["response"]} for r in rows])

    out_rows = []
    for r, t, p, f in zip(rows, tax_raw, prose_scores, full_scores):
        out_rows.append({**r, **parse_taxonomy(t), "prose_monitor": p, "full_monitor": f, "prose": split_prose(r["response"])})
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out + ".jsonl", "w") as fh:
        for r in out_rows:
            fh.write(json.dumps(r) + "\n")

    hacks = [r for r in out_rows if r["hack"]]
    cats = collections.Counter(r["category"] for r in out_rows)
    hack_cats = collections.Counter(r["category"] for r in hacks)
    def recall(key):
        vals = [r[key] for r in hacks if r[key] is not None]
        return (sum(vals) / len(vals)) if vals else None
    def fpr(key):
        vals = [r[key] for r in out_rows if not r["hack"] and r[key] is not None]
        return (sum(vals) / len(vals)) if vals else None
    aligned = [r["aligned_sounding"] for r in out_rows if isinstance(r.get("aligned_sounding"), (int, float))]
    summary = {
        "n": len(out_rows), "n_hacks": len(hacks), "hack_rate": len(hacks) / len(out_rows),
        "categories": {str(k): v for k, v in cats.items()}, "hack_categories": {str(k): v for k, v in hack_cats.items()},
        "motivated_over_hacks": (hack_cats.get("motivated", 0) / len(hacks)) if hacks else None,
        "prose_monitor_recall": recall("prose_monitor"), "prose_monitor_fpr": fpr("prose_monitor"),
        "full_monitor_recall": recall("full_monitor"), "full_monitor_fpr": fpr("full_monitor"),
        "aligned_sounding_mean": (sum(aligned) / len(aligned)) if aligned else None,
        "aligned_sounding_mean_hacks": (lambda v: sum(v) / len(v) if v else None)([r["aligned_sounding"] for r in hacks if isinstance(r.get("aligned_sounding"), (int, float))]),
        "judge_model": a.judge_model, "source": a.eval_json or a.rollouts,
    }
    utils.save_json(a.out + ".summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval_json"); ap.add_argument("--rollouts")
    ap.add_argument("--out", required=True)
    ap.add_argument("--judge_model", default="anthropic/claude-sonnet-4.5")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if not (a.eval_json or a.rollouts):
        ap.error("need --eval_json or --rollouts")
    utils.load_dotenv()
    main(a)
