---
store_path: pretraining/cpt-s7-replay-isolation-c-complete
title: "S7 replay isolation C complete: 12.35/5.48/5.22; §5 FAIL"
summary: "Holdout-sibling replay **s5best** SHA `0289f1c9…` (checkpoint-550) isolation C on Unsloth 2026.8.22 + torch 2.8: Spurgeon 12.35 (−13.69%), Puritan 5.48 (−9.22%), confession 5.22 (−6.88%). §5 FAIL. Hub stays Phase A. Instance 52830244 destroyed."
priority: high
tags: [cpt, s7, c-eval, vast, isolation, scorecard, replay, continue-from]
schema_version: 1.3
last_updated: "2026-09-26T20:31:48-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay_c/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/fetch/theology_cpt_lora_s5best/s5_best.json]
---

# S7 holdout-sibling replay isolation C COMPLETE (2026-09-26)

## Bottom line
Replay Phase B early-stop **s5best** SHA `0289f1c9af70615ef4dca58b3e2d7dabc3eefef96c8bdf92bff0933689adeb55` (checkpoint-550 / `theology_cpt_lora_s5best`) on **Unsloth 2026.8.22 + torch 2.8**.

**§5 −15% all three: FAIL** (−13.69% / −9.22% / −6.88%). Hair **better** than Phase B C (12.39 / 5.50 / 5.25). **No Hub overwrite** — Hub stays Phase A `06354dfc…`.

## Host / lifecycle
- Vast instance `52830244` destroyed after C; **0 instances** live.
- Operator standing: after C, save adapter locally + destroy pod.
- Continue-from marker: `vast_cpt_s7_replay/CONTINUE_FROM.json` (weights not copied into git).

## Paths (pc1)
- Adapter: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/fetch/theology_cpt_lora_s5best/`
- Same SHA at `fetch/checkpoints_s7/checkpoint-550`
- Init LoRA (NOT continue-from): `fetch/theology_cpt_lora/` still `ddbbee3a…`
- C metrics: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay_c/theology_cpt_eval_metrics.json`
- Mix: `a_output_v6` pin `e050787e…` (after new_authors rebuild)

## Scorecard (a_output_v3 holdouts, Ampere bf16)

| Bucket | Base | Replay s5best | Δ% | Phase B C | Hub Phase A |
|--------|------|---------------|-----|-----------|-------------|
| spurgeon | 14.31 | **12.35** | **−13.69%** | 12.39 (−13.42%) | 12.45 (−13.0%) |
| puritan | 6.03 | **5.48** | **−9.22%** | 5.50 (−8.88%) | 5.52 (−8.6%) |
| confession | 5.61 | **5.22** | **−6.88%** | 5.25 (−6.37%) | 5.27 (−6.0%) |
| general | 12.04 | 11.83 | −1.78% | 11.88 | 11.95 |
| new_authors | 11.65 | 9.96 | −14.53% | — | — |

Train probe spurgeon@16: ppl **11.79** (−11.36% vs base 13.30).

## Gate
- §5 win bar (≤−15% puritan+confession, ideally all three): **not met**.
- Spurgeon well under ~13.3 keep-bar; best Spurgeon so far locally.
- **Next CPT init = `0289f1c9` adapter, new Adam** (needs operator go). Do not Hub-push.

## Stack pin used
Unsloth 2026.8.22, torch 2.8, CPT eval pin (same as Phase A/B isolation C).