---
store_path: pretraining/cpt-plateau-verdict-2026-10-06
title: "CPT plateau verdict after S8 continue"
summary: "Two plateaus, two answers"
priority: high
tags: [cpt, s8, plateau, m_hi, isolation-c]
schema_version: 1.3
last_updated: "2026-10-06T09:54:44-03:00"
evidence: [[REDACTED_SECRET].md, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_continue/fetch/mhi_continue/checkpoints/checkpoint-800/trainer_state.json]
---

# CPT plateau verdict (2026-10-06)

Two plateaus, two answers.

## In-train plateau: broken

The old 2e-6 / r=32 continues barely moved puritan (~1.7354). S8 sweep (three fresh r=128 arms, 400 steps) moved it but missed the sweep line: best arm m_hi puritan **1.7226** vs break **1.7204** (gap 0.0022). Spurgeon 2.4694. Sweep recorded MISS. No isolation C on the sweep. Hub stayed Phase A 06354dfc.

Forge then ran the m_hi continue (800 steps, body LR 5e-6, new Adam). Puritan ended **1.7082** at step 800 (best). Passed 1.7204 from about step 450. Spurgeon 2.4560, confession 1.6262, general 2.5079. Adapter SHA prefix 8c1db3db. Optimizer was fetched.

Waste on that continue: steps 1-400 replayed the same seed-42 batches; new Adam bumped puritan 1.7226 to 1.7462 by step 100 and only returned to 1.7229 at step 400. Real progress was steps 400-800, still falling about 0.0014 per 50 steps.

## Isolation C / Hub plateau: not broken

Isolation C was not run. Estimated C from the in-train offset is about **1.673** vs section-5 line **1.6349** (about -11.6% PPL vs -15%). Do not promote Hub.

## Next job (dry-ready, not rented)

HF-resume checkpoint-800 with optimizer and RNG. Same 5e-6 constant floor. MAX_STEPS 2400 (1600 new). Early-stop floor 2400. Playbook NEXT_CPT_S8_MHI_RESUME.md. Orchestrator vast_cpt_s8_mhi_resume_orchestrate.ps1. If in-train puritan <= 1.670, run isolation C on the same pod before destroy. Do not rerun the S8 sweep or the finished new-Adam continue. Do not leave PREV_RUN_CHECKPOINT empty. Do not rewarm 5e-5.
