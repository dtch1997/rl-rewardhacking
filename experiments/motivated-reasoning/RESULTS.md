# Motivated reasoning — Phase 1 results (2026-09-12/13)

Substrate: this repo, Qwen3-4B, Verl GRPO (LoRA r=32), `simple_overwrite_tests` loophole, 200 steps, seed 1,
4×H200 (~30 s/step non-thinking). Rollouts dumped every step; test-time eval = 113 problems × 10 samples × 6 hints.

## 1. A written plan before the code suppresses reward hacking entirely

Same model, seed, env and hyperparameters; the only difference is the system-prompt line
"Before the code block, write a short paragraph starting with `Plan:` …".

| arm | training: first hack step | training: peak loose hacks / 256 | test-time overwrite_tests loose / strict | honest correctness (nohint) |
|---|---|---|---|---|
| A0 no prose prompt (upstream-faithful) | 38 | 256 / 256 from step 100 | 99.9% / 80.5% | 8.5% |
| A0 + Plan prompt | 62 | 6 | 0.5% / 0.4% | 22.8% |
| A1 constitution + Plan prompt | 71 | 5 | 0.0% / 0.0% | 18.6% |

Upstream reports ~79% at step 200 for the no-intervention run; the no-prose arm reproduces it. Total loose hacks
over 51k training rollouts: no-Plan 32,580; Plan 108; constitution+Plan 59. The Plan arms' "hacks" are mostly a
self-test `run_tests` helper (printing instead of asserting), which the grader rewards.

Caveat: 200 steps, one seed, one loophole; the literal `Plan:` prefix drifted away in A0 by step ~120 (prose stayed)
while A1 kept it (255/256 at step 200). Unknown whether this is suppression or delay.

## 2. Among the rare hacks, the constitution arm's prose looks motivated

Sonnet 4.5 taxonomy over every hack rollout (prompts in `src/prompts.py`); not yet replicated by a second judge
(Gemini pass starved by OpenRouter credits).

| | A0 + Plan (n=108) | A1 constitution + Plan (n=59) |
|---|---|---|
| motivated / hacks | 4% | 51% |
| silent / hacks | 94% | 47% |
| aligned-sounding prose, 0–10 | 1.6 | 6.7 |
| prose-only monitor recall | 49% | 5% |
| full monitor recall (sees code) | 100% | 100% |

Judge-free check (steps 121–200, A1): hack prose mentions rule / integrity / hard-coding in 25 / 12 / 22% of
rollouts vs 17 / 9 / 14% for non-hack prose. A0 shows no such contrast. Much of A1's motivated prose quotes the
constitution verbatim, so "constitution echo" is a live alternative to rationalisation.

### 2b. Replication (2026-09-14): the "motivated" labels do not survive a second judge

Same 167 hack rows, same taxonomy prompt, two more judges via direct APIs (`kappa_judge.py`, outputs in `judged/kappa/`):

| motivated / hacks | Sonnet 4.5 (orig) | GPT-5.4 | Opus 4.8 |
|---|---|---|---|
| A0 + Plan (n=108) | 4% | 6% | 0% |
| A1 constitution + Plan (n=59) | 52% | 29% | 3% |

Cohen's κ on the six-way category: A1 Sonnet–GPT 0.26, Sonnet–Opus −0.02, GPT–Opus 0.07; A0 all ≈ 0. Opus calls 55/59 A1 hacks
`silent`. The quotes behind the surviving "motivated" labels are constitution echoes ("we are not hard-coding … maintain the
integrity of the evaluation") attached to a self-test helper, not a rationalisation that precedes a grader override. **Section 2's
arm difference is judge-dependent and should not be claimed.** The taxonomy prompt needs anchoring examples and a κ ≥ 0.7 gate
before the readout is used again; the underlying problem is that the Plan arms barely hack (see §1), so there is little to classify.

## 3. Thinking mode collapses under GRPO at an 8k budget

A0-think (no Plan prompt, `enable_thinking`, 8192-token completions, 250 s/step): 0 hacks through step 100, but
think-block closure fell from 64% (step 1) to ~1% (step 60+) and correctness from 160/256 to 0 — the policy drifts
into never emitting `</think>`. Killed at step 100. At a 4k budget only 31% close at step 1. Needs an overlong
penalty, a closure reward, or a short-thinking warm start before the thinking arms can run.

## Artifacts

Devbox: `~/jarvis-monorepo/experiments/motivated-reasoning/pod-artifacts/phase1_snapshot_20260912.tgz` (rollouts,
step-200 LoRA adapters, A0/A1 evals, judged files) and `phase1_snapshot2_20260913.tgz` (a0_think rollouts,
no-Plan eval, logs). GCS upload pending (gcloud reauth).

Scripts: `experiments/motivated-reasoning/` — `pod_up.py`/`pod_down.py`, `remote/{setup,env,phase0,phase1,phase1b,phase1c,phase1t,eval}.sh`,
`judge_reasoning.py`, `judge_rollouts.sh`, plus the ad-hoc analysis scripts (`trajectory.py`, `think_stats.py`,
`keyword_contrast.py`, `eval_summary.py`) copied from the session scratchpad.
