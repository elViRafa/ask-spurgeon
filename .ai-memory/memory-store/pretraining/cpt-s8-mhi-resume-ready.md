---
store_path: pretraining/cpt-s8-mhi-resume-ready
title: "S8 m_hi resume dry-ready"
summary: "One-knob escape after the continue: HF-resume checkpoint-800 so Adam, RNG, and the sampler keep going"
priority: high
tags: [cpt, s8, resume, forge, plateau]
schema_version: 1.3
last_updated: "2026-10-05T21:50:22-03:00"
evidence: [[REDACTED_SECRET].md, continued_pretrain/scripts/vast_cpt_s8_mhi_resume_orchestrate.ps1]
---

# S8 m_hi resume is dry-ready

One-knob escape after the continue: HF-resume checkpoint-800 so Adam, RNG, and the sampler keep going. Same 5e-6 constant floor. 1600 new steps (MAX_STEPS 2400). Isolation C is the remaining gate (estimated 1.673 vs 1.6349).

Do not start new Adam. Do not leave PREV_RUN_CHECKPOINT empty. That is the waste the last continue paid for.

Dry command: `continued_pretrain/scripts/vast_cpt_s8_mhi_resume_orchestrate.ps1`. Local pytest 6 passed. Forge rents only after Rafael says go.
