---
store_path: pretraining/cpt-current
title: "CPT current status"
summary: "S8 plateau MISS; best m_hi 1.723; Hub Phase A; next knob pending (m_hi continue 800 steps)"
priority: high
tags: [cpt, s8, status, hub, gate, m_hi]
schema_version: 1.3
last_updated: "2026-10-05T14:24:00-03:00"
evidence: [pretraining/cpt-s8-sweep-complete, pretraining/cpt-next-session-handoff, continued_pretrain/NEXT_CPT_S8_SWEEP.md]
---

# CPT current status

## Status (canonical)

| Item | Value |
|------|--------|
| **Hub production** | Phase A s5best `06354dfc` |
| **S8 result (2026-10-05)** | Plateau **MISS** — no isolation C, no Hub |
| **Best local adapter** | S8 `m_hi` LoRA under `vast_cpt_s8_sweep/fetch/sweep/m_hi/theology_cpt_lora` (best puritan **1.723** / trainer_state step400 **1.7226**; Spurgeon **2.469**) |
| Prior P0 best | `a70fded8` (checkpoint-600) — merge parent for S8 |
| **section-5 / S8 break** | In-train puritan **≤1.7204** (ref 1.7354 − 0.015); Spurgeon **≤2.490** |
| **Pack** | `a_output_v6_p0` / `mix_v6_p0` SHA `ad817213` |
| **Next (proposed, not approved)** | one-knob: continue from `m_hi`, **MAX_STEPS 400→800**, LR 5e-5, `metric_for_best=eval_puritan_loss`, r=128, new Adam; no rent until go |
| Vast | **0** instances after destroy `54312477`; credit ~$5.87 |
| Stack pin | Unsloth 2026.8.22 + torch 2.8 |

## S8 arm finals (puritan / Spurgeon)

| Arm | Best |
|-----|------|
| m_lo (merged, LR 2e-5) | 1.725 / 2.470 |
| m_hi (merged, LR 5e-5) | **1.723 / 2.469** |
| f_hi (stock, LR 5e-5) | 1.736 / 2.488 |
