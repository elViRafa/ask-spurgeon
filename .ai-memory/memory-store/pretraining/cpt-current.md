---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "P1 waiting merge+go; best local continue-from a70fded8; Hub Phase A 06354dfc"
priority: high
tags: [cpt, s7, status, hub, gate, p0, p1]
schema_version: 1.3
last_updated: "2026-10-02T18:15:00-03:00"
evidence: [pretraining/cpt-hub-keep-phase-a, pretraining/cpt-s7-p0-confession-reweight, pretraining/cpt-s7-p1-metric-puritan, pretraining/cpt-best-adapter-leaderboard]
---

# CPT current status

## Status (canonical)

| Item | Value |
|------|--------|
| **Hub production** | Phase A s5best `06354dfc` |
| **Best local continue-from** | P0 best `a70fded8` (checkpoint-600) under `vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best` |
| Prior replay init | `0289f1c9` (checkpoint-550) — keep for clean A/B only |
| P0 C (step600) | Spurgeon ~-13.87%, Puritan ~-9.45%, confession ~-7.4% — section-5 FAIL (Puritan hard) |
| Replay C | Spurgeon 12.35 (-13.69%), Puritan 5.48 (-9.22%), confession 5.22 (-6.88%) |
| **section-5 framing** | Spurgeon keep + Puritan hard (-15%); confession soft/monitor |
| **Pack** | `a_output_v6_p0` / `mix_v6_p0` SHA `ad817213` — confession 15% / puritan 50% / spurgeon 35% |
| **Next (P1)** | one-knob `metric_for_best=eval_puritan_loss`; init `a70fded8` + new Adam; session `vast_cpt_s7_p1`; PR #6 open MERGEABLE; dry READY; **no rent until merge + operator go** |
| Stack | Unsloth 2026.8.22 + torch 2.8 |

Vast instances: 0. Hub stays Phase A until section-5 win. After C: save adapter locally, destroy pod.
