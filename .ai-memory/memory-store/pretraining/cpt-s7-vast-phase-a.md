---
store_path: pretraining/cpt-s7-vast-phase-a
title: "S7 Phase A Vast running on 4090"
summary: "**Instance:** `52063161` (label `cpt-s7-phase-a`), SSH `root@149.40.242.200:40205`, RTX 4090 ~$0.40/hr"
priority: medium
tags: [cpt, s7, vast, running]
schema_version: 1.3
last_updated: "2026-09-22T10:44:29-03:00"
evidence: [continued_pretrain/VAST_RUNBOOK_CPT_S7.md, continued_pretrain/scripts/vast_cpt_s7_orchestrate.ps1]
---

# S7 Phase A on Vast — RUNNING (2026-09-22)

**Instance:** `52063161` (label `cpt-s7-phase-a`), SSH `root@149.40.242.200:40205`, RTX 4090 ~$0.40/hr.
**Credit after top-up:** ~$7.55.
**Session/results:** `kaggle/runpod_cpt_v3/vast_cpt_s7` + `vast_cpt_s7_session.json`.

## Confirmed walk-away gates
- `PREV_RUN_CHECKPOINT` empty / new Adam
- `INIT_ADAPTER SHA256 OK` `6aab…`
- `PIN_OK` torch **2.8.0+cu126** + Unsloth **2026.8.22**
- conda `unsloth_cpt_s7`
- `Continue profile max_steps 4128 -> 2064`, `output_dir=/workspace/checkpoints_s7`
- `trainer_bf16=True`, training at step ≥2/2064, GPU ~100%

## Fixes landed this session
- Parallel Vast S7 lane (`vast_cpt_s7_*` scripts + runbook)
- Launch via **nohup** (foreground SSH died mid-Miniforge)
- `max_seq_length` → `max_length` remap for TRL 0.24; pin `trl>=0.18,<0.24` on fresh installs

## Monitor
`vast_cpt_s7_monitor_until_done.py` with `CPT_TOTAL_STEPS=2064` → fetch `checkpoints_s7` + s5best, then destroy.

## Do not
- Call S6 orchestrate; Hub overwrite; mix rebuild; destroy until B done + fetch OK
