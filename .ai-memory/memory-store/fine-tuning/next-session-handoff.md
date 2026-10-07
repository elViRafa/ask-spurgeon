---
store_path: fine-tuning/next-session-handoff
title: "Fine-tuning next session handoff"
summary: "**Updated:** 2026-09-04 ~01:20 ET"
priority: high
tags: [fine-tuning, handoff, sft, vultr]
schema_version: 1.3
last_updated: "2026-09-04T01:20:10-04:00"
evidence: [fine_tuning/VULTR_RUNBOOK_SFT.md, fine_tuning/scripts/vultr_orchestrate.ps1]
summary_hash: 245ae3c499ffc4aa9aef564463fa3aeb
review_status: stale
---

**Updated:** 2026-09-04 ~01:20 ET

## Primary next: allowlist Vultr API IP, then run GATE-0

```powershell
cd fine_tuning\scripts
.\vultr_orchestrate.ps1
# or after console VM:
.\vultr_orchestrate.ps1 -SshHost <ip>
```

Allowlist agent IP **159.26.98.242** on the Vultr API key (or "any IP" temporarily). Two waits (45m + 90m) still got `401 Unauthorized IP`. No instance created. No GPU billing.

## Scripts ready (do not re-implement)
- `vultr_*.ps1` + `vultr_monitor_until_done.py`
- torch 2.11 + ScalingType smoke in `sft_remote_setup.sh`
- CPU PEFT merge fallback in `merge_cpt_lora.py`
- A16: BATCH=1 GRAD_ACCUM=16 CUDA_VISIBLE_DEVICES=0
- Local `13_sft_local_readiness.py --gate0` PASS (3264/153/100)

## Hard rules
- Destroy Vultr GPU when train/fetch done
- EXPORT only after F §5 gates
- Never log VULTR_API_KEY / HF_TOKEN
