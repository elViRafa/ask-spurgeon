---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "| **Hub production** | private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = S7 s5best `06354dfc…` |"
priority: high
tags: [cpt, s7, status, hub, v5]
schema_version: 1.3
last_updated: "2026-09-23T11:47:14-03:00"
summary_hash: ae50844218c68cf398ceb1a89e8e955d
evidence: [pretraining/cpt-hub-s7-overwrite, pretraining/cpt-best-adapter-leaderboard]
---

## Status (canonical)

| Item | Value |
|------|--------|
| **Hub production** | private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = S7 s5best `06354dfc…` |
| Spurgeon C | **12.45 (−13%)** vs base 14.31 |
| Local best | `vast_cpt_s7/fetch/theology_cpt_lora_s5best/` |
| Prior Hub S6 | `6aab…` still on disk `vast_cpt_s6/fetch/` |
| §5 −15% | FAIL |
| Next | Phase B GPU on `a_output_v5` SHA `61e83057…` (operator go) |
| C pin | Unsloth 2026.8.22 + torch 2.8 |
| Eval default SHA | `06354dfc…` in `eval_cpt_sota.py` |

Frozen: v4 uniform `37a3ba50…`; v3 `23dd…`. Do not overwrite Hub until winning C.
