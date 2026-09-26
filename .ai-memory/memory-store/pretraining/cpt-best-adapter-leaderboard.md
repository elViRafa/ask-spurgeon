---
store_path: pretraining/cpt-best-adapter-leaderboard
title: "Best CPT + Hub: S7 s5best spurgeon 12.45"
summary: "**S7 s5best is best measured CPT LoRA** and **is now on production Hub** (operator overwrite)"
priority: high
tags: [cpt, s7, best, scorecard, leaderboard, hub]
schema_version: 1.3
last_updated: "2026-09-22T17:55:53-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/theology_cpt_eval_metrics.json, pretraining/cpt-hub-s7-overwrite, pretraining/cpt-s6-stack-isolation-c]
---

# Best CPT adapter + Hub production (2026-09-22)

**S7 s5best is best measured CPT LoRA** and **is now on production Hub** (operator overwrite).

## Identity
- SHA256: `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` (step 1200)
- Local: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_lora_s5best/`
- Hub: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 (private)
- C metrics: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/`

## Isolation-C leaderboard (Unsloth 2026.8.22 + torch 2.8, a_output_v3)

| Adapter | Spurgeon | Δ% | Puritan | Confession | General |
|---------|----------|-----|---------|------------|--------|
| **S7 s5best (Hub now)** | **12.45** | **−13.0%** | **5.52 (−8.6%)** | 5.27 (−6.0%) | 11.95 (−0.8%) |
| S6 `6aab…` (prior Hub) | 12.85 | −10.2% | 5.60 (−7.2%) | 5.27 (−6.0%) | 11.83 (−1.8%) |
| Hub v2 / S5 | ~13.3 | ~−7% | — | — | — |

## Caveats
- §5 −15% still FAIL
- Prefer s5best over final LoRA `1381e5ee…`
- Never trust C on Unsloth 2026.9.x / torch 2.11
- No merge/GGUF/public yet
