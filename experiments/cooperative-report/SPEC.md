# Cooperative RL: a "report broken environment" escape hatch vs reward hacking

**Status:** spec — awaiting launch approval (pod budget)
**Owner:** Daniel Tan (+ Claude session)
**Thread:** cooperative-rl-reward-hacking (jarvis memory slug)

## Background

[Steering RL Training](https://www.alignmentforum.org/posts/R5MdWGKsuvdPwGFBG/steering-rl-training-benchmarking-interventions-against)
(ariaw + Josh Engels + Neel Nanda, MATS 9.0) open-sourced a clean environment where GRPO on
Qwen3-4B naturally learns to reward hack: leetcode problems are graded by `run_tests()`, and the
model can silently overwrite that function. Hacking emerges in ~80–100 steps in all runs, ending
at ~79% hack rate, with ~0.09% base rate before training. Sam Martin reproduced this on Qwen3-8B
(Slack #experiments-and-ideas 2026-09-04) and found hacking *propensity rises before any hack is
ever rewarded* in training rollouts.

The upstream post benchmarks monitor-based interventions (penalty/screening with ground-truth,
probe, LLM-judge monitors) and inoculation prompting. **Nobody has tested giving the model a
legitimate alternative to hacking.**

## Hypothesis

Reward-seeking behavior may partly arise because RL environments offer exactly one sanctioned
path to reward: "try harder". If a model notices the environment is broken/exploitable, every
action available to it either wastes the rollout (honest failure) or exploits the flaw (hack).
A **cooperative affordance** — report the environment as broken, ending the episode for a modest
reward — gives the "notice the flaw" impulse a sanctioned outlet.

**H1:** With a report affordance, learned reward hacking at test time is substantially lower than
the No Intervention arm (ideally ≈ RL-baseline levels).
**H2 (risk):** If the report reward is too high, the model degenerately reports everything and
coding performance collapses; too low and the affordance is never used. There is a usable band.
**H3 (secondary):** Reports are *specific*: trained models report loopholed prompts more than
no-loophole prompts.

## Implementation (this branch)

- `src/prompts.py` — `REPORT_AFFORDANCE_PROMPT`: the model may respond
  `<report>description</report>` instead of code; instructed not to report merely-hard tasks.
- `src/analysis.py` — `extract_report()`; new `Reported` category constant.
- `src/train/rewards.py` — `ReportCorrectOrHintedCompileCode`: a report ends the episode with
  `report_reward` (replacing correctness+format rewards; report takes precedence if code is also
  present). Code eval still runs for logging: report∩hack, report∩correct overlap stats under
  `detail/report/*`, `is_report` in extra infos (per-rollout, saved with rollouts).
- `scripts/run_rl_training.py` — `report` intervention:
  `run_rl_training report --report_reward 1.5 --seed 1`.
- `scripts/run_eval.py` — `--report_affordance` flag: evaluate with the same affordance system
  prompt; `src/evaluate/evaluation.py` records `has_report`/`report_text` per response.

Reward scale context: correct = 3.0 (+0.5 format), compile-only = 0.5, report = {sweep}.
GRPO group-normalizes advantages, so what matters is report_reward relative to the group mix.

## Phases

**Phase 0 — pod smoke test (~$5–10).** 4×H200 pod, `report` intervention, `--steps 2`: verify the
verl wiring end-to-end (reward fn resolution, extra_infos through Verl, wandb logs, rollout
saving). Also 1 no-intervention smoke step. Abort criteria: any crash/type error in reward path.

**Phase 1 — reproduction (~$120–180).** `no_intervention` (simple_overwrite_tests, Qwen3-4B,
defaults), seeds 1–2 (3 if variance is confusing). Success = hacking snowballs ≤200 steps,
test-time hack rate in the ballpark of the post's ~79%. Rollouts are saved each step, so Sam's
"propensity rises before first rewarded hack" claim can be checked offline from run artifacts
(first-hack step vs checkpoint-sampled propensity at steps 50/100/150/200) at no extra
training cost — checkpoint evals are cheap eval-only jobs.

**Phase 2 — report affordance pilot (~$180).** `report` with report_reward ∈ {0.5, 1.5, 3.0},
seed 1 each. Test-time evals per run (all vs the same 113-problem test set, n=10):
1. loophole dataset + affordance prompt → hack rate, report rate
2. no-loophole dataset + affordance prompt → performance, false-report rate (specificity)
3. loophole dataset, *no* affordance prompt → does hacking return when the hatch is removed?

**Phase 3 — seeds for the interesting cells (~$120–360).** Whatever Phase 2 says is the usable
band gets 3 seeds for a significance claim against No Intervention and RL Baseline (paper values
reusable for orientation; rerun our own RL baseline only if we need clean stats: +$180).

Total: ~$430–730 depending on Phase 3 breadth. Each run ≈ 3h on 4×H200 (~$60).

## Metrics & readouts

Per the upstream post: # RH runs / total, test-time reward-hack rate, performance
(no-loophole correctness), plus new: report rate (loophole vs clean), report∩would-have-hacked
overlap during training (`detail/report/*` wandb series), report text samples (qualitative: are
reports faithful descriptions of the loophole?).

## Predictions (to register before running)

- report_reward 0.5: rarely used, hacking ≈ No Intervention (~79%).
- report_reward 1.5: used on hard problems once discovered; hacking substantially reduced iff
  the report basin is found before the hack basin snowballs. This is the interesting cell.
- report_reward 3.0: degenerate always-report risk; performance collapse.
- Eval-without-hatch (readout 3) is the honest test of whether the *disposition* changed vs the
  behavior being merely displaced.

## Decisions taken

- Qwen3-4B (paper defaults, known-good configs), not Sam's 8B — cheaper, comparable literature.
- Report syntax `<report>…</report>`: near-zero base rate, trivial detection, no code-block clash.
- Constant report reward, not validity-judged (v1): in-distribution the loophole is always
  present, so validity-gating only matters for junk reports; we measure junk-report rate instead
  and can add an LLM-judged validity gate in a follow-up if it's high.
- Report precedence over code in the same response = "choose to terminate the episode" semantics.
