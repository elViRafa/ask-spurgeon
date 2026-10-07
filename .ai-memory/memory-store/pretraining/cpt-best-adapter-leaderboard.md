---
store_path: pretraining/cpt-best-adapter-leaderboard
title: "Best CPT + Hub: Phase A Hub; replay 0289f1c9 top local"
summary: "**Hub production is still Phase A s5best** `06354dfc…`. Top local continue-from is replay C `0289f1c9…` (still §5 FAIL)."
priority: high
tags: [cpt, s7, best, scorecard, leaderboard, hub, replay]
schema_version: 1.3
last_updated: "2026-09-26T20:31:48-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay_c/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_b_c/theology_cpt_eval_metrics.json, pretraining/cpt-hub-keep-phase-a, pretraining/cpt-s7-replay-isolation-c-complete, [REDACTED_SECRET].json]
---

# Best CPT adapter + Hub production (updated 2026-09-26)

**Hub production is still Phase A s5best** `06354dfc…`. Replay isolation C `0289f1c9` is the **top local** adapter (hair better than Phase B `ddbbee3a`) and was **not** promoted — §5 still FAIL. Prefer `0289f1c9` as **next continue init**, not Hub.

## Hub identity
- SHA256: `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` (Phase A step 1200)
- Hub: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 (private)
- Local Hub-matching weights: `vast_cpt_s7/fetch/theology_cpt_lora_s5best/` (top-level file)

## Isolation-C leaderboard (Unsloth 2026.8.22 + torch 2.8, pinned v3 holdouts)

| Adapter | Spurgeon | Δ% | Puritan | Confession | Notes |
|---------|----------|-----|---------|------------|--------|
| **Replay s5best `0289f1c9` (top local)** | **12.35** | **−13.69%** | **5.48 (−9.22%)** | **5.22 (−6.88%)** | checkpoint-550; CONTINUE_FROM pin |
| Phase B s5best `ddbbee3a` (local) | 12.39 | −13.42% | 5.50 (−8.88%) | 5.25 (−6.37%) | prior continue init |
| **S7 Phase A s5best (Hub)** | **12.45** | **−13.0%** | **5.52 (−8.6%)** | 5.27 (−6.0%) | production |
| S6 `6aab…` (prior Hub) | 12.85 | −10.2% | 5.60 (−7.2%) | 5.27 (−6.0%) | superseded on Hub by Phase A |

## Caveats
- §5 −15% still FAIL on all S7 adapters (including replay)
- Prefer `0289f1c9` as **next continue init**, not Hub `06354dfc`, not init LoRA `ddbbee3a`
- Never trust C on Unsloth 2026.9.x / torch 2.11
- No merge/GGUF/public yet; no Hub overwrite without winning C + go