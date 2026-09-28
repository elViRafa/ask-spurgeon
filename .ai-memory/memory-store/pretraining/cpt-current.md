---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "| **Hub production** | Phase A s5best `06354dfc` |"
priority: high
tags: [cpt, s7, status, hub, gate, p0]
schema_version: 1.3
last_updated: "2026-09-28T08:10:13-03:00"
evidence: [pretraining/cpt-hub-keep-phase-a, pretraining/cpt-s7-replay-isolation-c-complete, pretraining/cpt-best-adapter-leaderboard, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json]
summary_hash: 0e44fae11427c6094e68376cbe48ef40
---

# CPT current status

## Status (canonical)

| Item | Value |
|------|--------|
| **Hub production** | Phase A s5best `06354dfc` |
| **Best local continue-from** | replay s5best `0289f1c9` (checkpoint-550) |
| Replay C | Spurgeon 12.35 (-13.69%), Puritan 5.48 (-9.22%), confession 5.22 (-6.88%) |
| **section-5 framing (2026-09-28)** | Spurgeon keep + Puritan hard; confession soft/monitor |
| **P0 pack** | `a_output_v6_p0` / `mix_v6_p0` SHA `ad817213` — confession 15% / puritan 50% / spurgeon 35% |
| Marker | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json` |
| Next | dry READY — rent on go: init `0289f1c9` + new Adam, session `vast_cpt_s7_p0`, then C |
| Stack | Unsloth 2026.8.22 + torch 2.8 |

Vast instances: 0. Credit ~$5.83. Do not Hub-push until gate-pass under reframed section-5.
