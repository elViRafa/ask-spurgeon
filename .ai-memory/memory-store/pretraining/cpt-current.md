---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "| **Hub production** | private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…` |"
priority: high
tags: [cpt, s7, status, hub, v6]
schema_version: 1.3
last_updated: "2026-09-26T08:12:09-03:00"
summary_hash: ae50844218c68cf398ceb1a89e8e955d
evidence: [pretraining/cpt-hub-keep-phase-a, pretraining/cpt-s7-phase-b-isolation-c, pretraining/cpt-s7-holdout-sibling-replay, pretraining/cpt-best-adapter-leaderboard]
---

## Status (canonical)

| Item | Value |
|------|--------|
| **Hub production** | private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…` |
| Hub C | Spurgeon **12.45 (−13%)** vs base 14.31 |
| Phase B C (local) | nested `ddbbee3a` 12.39 / 5.50 / 5.25 — not on Hub |
| Local Phase B s5best | `vast_cpt_s7/fetch/theology_cpt_lora_s5best/theology_cpt_lora_s5best/` |
| §5 −15% | FAIL |
| Next | Holdout-sibling replay on `a_output_v6` SHA `2d5a99c1…` (operator go) |
| C pin | Unsloth 2026.8.22 + torch 2.8 |

Frozen: v5 `61e83057…`; v4 `37a3ba50…`; v3 `23dd…`. Hub stays Phase A until a winning C. Operator 2026-09-26 declined Hub overwrite of `ddbbee3a`.
