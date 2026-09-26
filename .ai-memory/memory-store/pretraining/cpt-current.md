---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "| **Hub production** | private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…` |"
priority: high
tags: [cpt, s7, status, hub, v6, replay, continue-from]
schema_version: 1.3
last_updated: "2026-09-26T20:31:48-03:00"
evidence: [pretraining/cpt-hub-keep-phase-a, pretraining/cpt-s7-replay-isolation-c-complete, pretraining/cpt-best-adapter-leaderboard, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json]
---

## Status (canonical)

| Item | Value |
|------|--------|
| **Hub production** | private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…` |
| Hub C | Spurgeon **12.45 (−13%)** vs base 14.31 |
| **Best local continue-from** | replay s5best `0289f1c9…` (checkpoint-550) |
| Replay C (local) | Spurgeon **12.35 (−13.69%)**, Puritan **5.48 (−9.22%)**, confession **5.22 (−6.88%)** |
| Phase B C (local) | nested `ddbbee3a` 12.39 / 5.50 / 5.25 — hair worse than replay |
| Marker | `vast_cpt_s7_replay/CONTINUE_FROM.json` |
| Adapter (pc1) | `vast_cpt_s7_replay/fetch/theology_cpt_lora_s5best/` |
| Init LoRA (do not continue-from) | `vast_cpt_s7_replay/fetch/theology_cpt_lora/` still `ddbbee3a…` |
| Mix pack | `a_output_v6` SHA `e050787e…` (after new_authors rebuild) |
| §5 −15% | **FAIL** (replay C) |
| Next | Continue CPT from `0289f1c9` adapter, **new Adam** (**needs operator go**) |
| C pin | Unsloth 2026.8.22 + torch 2.8 |

Frozen: v5 `61e83057…`; v4 `37a3ba50…`; v3 `23dd…`. Hub stays Phase A until a winning C. Instance `52830244` destroyed; 0 instances. Do **not** Hub-push `0289f1c9`.