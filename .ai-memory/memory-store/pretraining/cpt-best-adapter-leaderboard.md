---
store_path: pretraining/cpt-best-adapter-leaderboard
title: "Best CPT + Hub: Phase A 12.45; Phase B C not promoted"
summary: "**Hub production is still Phase A s5best** `06354dfc…`"
priority: high
tags: [cpt, s7, best, scorecard, leaderboard, hub]
schema_version: 1.3
last_updated: "2026-09-26T08:12:13-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_b_c/theology_cpt_eval_metrics.json, pretraining/cpt-hub-keep-phase-a, pretraining/cpt-hub-s7-overwrite]
---

# Best CPT adapter + Hub production (updated 2026-09-26)

**Hub production is still Phase A s5best** `06354dfc…`. Phase B C `ddbbee3a` is slightly better on the same pin and was **not** promoted (operator 2026-09-26).

## Hub identity
- SHA256: `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` (Phase A step 1200)
- Hub: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 (private)
- Local Hub-matching weights: `vast_cpt_s7/fetch/theology_cpt_lora_s5best/` (top-level file)

## Isolation-C leaderboard (Unsloth 2026.8.22 + torch 2.8, pinned v3 holdouts)

| Adapter | Spurgeon | Δ% | Puritan | Confession | General |
|---------|----------|-----|---------|------------|--------|
| Phase B s5best `ddbbee3a` (local only) | **12.39** | **−13.42%** | **5.50 (−8.88%)** | **5.25 (−6.37%)** | 11.88 (−1.34%) |
| **S7 Phase A s5best (Hub)** | **12.45** | **−13.0%** | **5.52 (−8.6%)** | 5.27 (−6.0%) | 11.95 (−0.8%) |
| S6 `6aab…` (prior Hub) | 12.85 | −10.2% | 5.60 (−7.2%) | 5.27 (−6.0%) | 11.83 (−1.8%) |

## Caveats
- §5 −15% still FAIL on both S7 adapters
- Prefer nested `ddbbee3a` as **replay init**, not as Hub
- Never trust C on Unsloth 2026.9.x / torch 2.11
- No merge/GGUF/public yet
