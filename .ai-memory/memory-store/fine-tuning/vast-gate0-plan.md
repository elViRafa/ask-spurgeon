---
store_path: fine-tuning/vast-gate0-plan
title: "Vast GATE-0 plan (scripts ready)"
summary: "**Verified 2026-09-05:** Runbook + thin `vast_*.ps1` landed"
priority: high
tags: [vast, sft, gate0]
schema_version: 1.3
last_updated: "2026-09-05T19:18:30-04:00"
evidence: [fine_tuning/VAST_RUNBOOK_SFT.md, fine_tuning/scripts/vast_orchestrate.ps1]
review_status: stale
---

# Vast.ai GATE-0 — scripts ready (no rent yet)

**Verified 2026-09-05:** Runbook + thin `vast_*.ps1` landed. Dry search + local readiness PASS. Credit **$6**. Still **do not rent** until operator says go.

## Ops defaults
- RTX 4090 on-demand, reliability >=0.95, disk 100GB
- Image: `pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel` + torch 2.11 setup smoke
- Profile: `SFT_GPU_PROFILE=4090` BATCH=2 GRAD_ACCUM=8
- Wall <=10h then destroy

## One-shot (on go)
`cd fine_tuning\\scripts; .\\vast_orchestrate.ps1`

## Docs
