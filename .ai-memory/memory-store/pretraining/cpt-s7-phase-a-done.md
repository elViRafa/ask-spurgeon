---
store_path: pretraining/cpt-s7-phase-a-done
title: "CPT S7 Phase A complete (Vast early-stop)"
summary: "- Host: Vast instance `52063161` (destroyed after fetch)"
priority: high
tags: [cpt, s7, vast, early-stop]
schema_version: 1.3
last_updated: "2026-09-22T16:06:36-03:00"
---

## S7 Phase A result (2026-09-22)

- Host: Vast instance `52063161` (destroyed after fetch).
- Continue from S6 LoRA with new Adam; `CPT_CONTINUE_PROFILE=s7`; stopped by **COMPOSITE EARLY-STOP @ step 1250** (max_steps 2064, patience 4, ε 0.003).
- Final HF LoRA SHA: `1381e5ee4eaf8f838aa6b1b21d1757de29404dbb50aa5e68ec3a4fd3bceae4db` (= checkpoint-1250).
- s5best SHA: `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` @ step 1200 (prefer for C eval).
- Local path: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/`.
- Seed CE: spurgeon 2.4987 / mix 2.0208 / puritan 1.751 / confession 1.668.
- @1250 CE (log): spurgeon 2.4867 / mix 2.009 / puritan 1.742 / confession 1.671.
- Train loss ~1.988; runtime ~10179s.
