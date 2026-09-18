---
store_path: pretraining/cpt-next-session-handoff
title: "Next session: Vast S6 full-corpus continue-B"
summary: "**Do not smoke again.** Miniforge Unsloth CPT is proven"
priority: high
tags: [cpt, s6, vast, handoff]
schema_version: 1.3
last_updated: "2026-09-16T11:02:02-03:00"
evidence: [continued_pretrain/VAST_RUNBOOK_CPT.md, continued_pretrain/scripts/vast_cpt_orchestrate.ps1]
---

# Next session handoff — Vast CPT S6 continue-B (full corpus)

**Do not smoke again.** Miniforge Unsloth CPT is proven. Next GPU work is **S6 continue-B on full `a_output_v3`**.

## Ready
- Local readiness PASS (51417/520, mix SHA `23dd3820…`, S5 SHA `ef4df3a3…`, complete `checkpoint-2050`)
- Scripts: `continued_pretrain/scripts/vast_cpt_orchestrate.ps1` + `VAST_RUNBOOK_CPT.md`
- Payload: `D:\search-sermons-cpt\vast_cpt_s6\payload.tar` (~4.6 GB)
- Recipe: CUDA 12.4 image + Miniforge `unsloth_cpt` + torch 2.11+cu126 **pip-in-env** (`unset LD_LIBRARY_PATH`)
- Fetch to **D:** only (C: ~2 GB free)

## Not ready without operator money/GPU pick
- Vast credit was ~$3.31 at prepare time; 4090 ~$0.54/hr needs ~$5+ for 8–12 h
- `-Go` blocks credit < $5 unless `-AllowLowCredit`
- 3090 TW ~$0.24/hr is the credit-safe Ampere fallback
- Runpod volume `7hb931c5oe` still 404 / funds; Vast has no network volume so checkpoint sync to D: is the backup

## On go
```
cd continued_pretrain\scripts
.\vast_cpt_orchestrate.ps1 -Go -StartMonitor
```
Walk away only after log shows `cpt_run_mode=continue`, `Resuming from .../checkpoint-2050`, `packed_epoch_steps=4128`, `INIT_ADAPTER SHA256 OK`, conda python under `unsloth_cpt`.

Keep Hub v2 until finished B + winning C. No `S6_FRESH_START`.
