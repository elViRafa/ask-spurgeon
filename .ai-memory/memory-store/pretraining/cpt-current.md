---
store_path: pretraining/cpt-current
title: "CPT current pointer — Vast S6 prepare"
summary: "**Canonical live handoff:** `pretraining/cpt-next-session-handoff`"
priority: medium
tags: [cpt, s6, vast]
schema_version: 1.3
last_updated: "2026-09-16T11:02:12-03:00"
summary_hash: ae50844218c68cf398ceb1a89e8e955d
evidence: [continued_pretrain/VAST_RUNBOOK_CPT.md]
---

# CPT — current pointer (2026-09-16)

**Canonical live handoff:** `pretraining/cpt-next-session-handoff`
**Vast prepare snapshot:** `pretraining/vast-cpt-s6-prepare`

| Item | Status |
|------|--------|
| S6 continue-B | **INCOMPLETE** at **2050/4128** locally (complete HF ckpt + optimizer). Volume `7hb931c5oe` 404 |
| Next GPU | **Vast** Miniforge Unsloth, full `a_output_v3`. Scripts ready. **Do not train until operator -Go** |
| Credit gate | ~$3.31 at prepare; `-Go` needs ≥$5 or `-AllowLowCredit` + 3090 |
| Hub production | keep `…-theology-cpt-lora-v2` until finished B + winning C |
| SFT lane | separate |
