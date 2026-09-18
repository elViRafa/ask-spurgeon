---
store_path: pretraining/vast-cpt-s6-prepare
title: "Vast CPT S6 full-corpus prepare (no train)"
summary: "**Status:** Local+script readiness **PASS**"
priority: medium
tags: [cpt, s6, vast, conda, full-corpus, handoff]
schema_version: 1.3
last_updated: "2026-09-16T11:02:02-03:00"
evidence: [continued_pretrain/VAST_RUNBOOK_CPT.md, continued_pretrain/scripts/vast_cpt_orchestrate.ps1, continued_pretrain/scripts/vast_cpt_remote_continue_b.sh]
---

# Vast CPT S6 continue-B — prepared, not trained (2026-09-16)

**Status:** Local+script readiness **PASS**. Dry Vast search done. **No instance rented. No training started.**

## Job
Resume S6 continue-B on the **full v3 mix** (`a_output_v3`, 51417/520 docs, mix SHA256 `23dd3820…0973`, ~91.3M tokens, 4128 packed steps) using Miniforge Unsloth on Vast. Resume complete local `checkpoint-2050` (optimizer present, `eval_spurgeon_loss` 2.4987). `checkpoint-2100` is **not** local. Keep Hub v2 until finished B + winning C. Do **not** `S6_FRESH_START`.

## Proven stack
- Image `nvidia/cuda:12.4.1-devel-ubuntu22.04` + Miniforge env `unsloth_cpt` + torch **2.11.0+cu126 pip-in-env**
- System pip / official Unsloth Docker still fail (SIGSEGV / SSH)
- Smoke PASS earlier today: `CPT_UNSLOTH_SMOKE_PASS steps=3`

## Wired this session
- Runbook: `continued_pretrain/VAST_RUNBOOK_CPT.md`
- One-shot next session: `continued_pretrain/scripts/vast_cpt_orchestrate.ps1 -Go -StartMonitor`
- Payload packed: `D:\search-sermons-cpt\vast_cpt_s6\payload.tar` (~4.6 GB)
- Fetch **only** to D: (`C:` ~2 GB free)

## Dry search (no rent)
- Instances: `[]`
- Credit ~**$3.31** (too tight for a safe 4090 8–12 h wall at ~$0.54/hr)
- 4090 on-demand: NL ~$0.54/hr, HU ~$0.74/hr (`gpu_frac=1`, `cuda_max_good>=12.6`)
- 3090 Ampere 24 GB fallback: TW ~$0.24/hr (fits credit; use `-AllowLowCredit -OfferId`)
- `-Go` refuses if credit < $5 unless `-AllowLowCredit`

## Next session paste
```
Vast CPT S6 continue-B. Operator approved GPU go.
Do not smoke. Use Miniforge unsloth_cpt. Resume checkpoint-2050. Full a_output_v3.
cd continued_pretrain\scripts; .\vast_cpt_orchestrate.ps1 -Go -StartMonitor
If credit still under $5: add funds for 4090, or 3090 + -AllowLowCredit -OfferId <id>.
Fetch to D:\search-sermons-cpt\vast_cpt_s6. Destroy when done. Keep Hub v2.
```
