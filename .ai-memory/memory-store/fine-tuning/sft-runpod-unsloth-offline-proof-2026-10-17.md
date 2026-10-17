---
store_path: fine-tuning/sft-runpod-unsloth-offline-proof-2026-10-17
title: "Offline Unsloth FT contract proof (no RunPod)"
summary: "Verified the RunPod Unsloth weighted SFT path **without** renting a pod"
priority: medium
tags: [sft, weighted, runpod, unsloth, offline, pytest, dry]
schema_version: 1.3
last_updated: "2026-10-17T14:14:53-03:00"
evidence: [fine_tuning/scripts/runpod_sft_s8_weighted_orchestrate.ps1, fine_tuning/scripts/test_sft_s8_weighted_runpod_unsloth_plan.py, fine_tuning/tests/test_sft_weighted_env_safeguards.py]
---

# Offline Unsloth FT proof (2026-10-17)

Verified the RunPod Unsloth weighted SFT path **without** renting a pod.

## Commands

```powershell
cd fine_tuning\scripts
cd ..\..
.\.venv\Scripts\python.exe -m pytest fine_tuning/scripts/test_sft_s8_weighted_runpod_unsloth_plan.py fine_tuning/scripts/test_sft_s8_weighted_plan.py fine_tuning/tests/test_sft_weighted_env_safeguards.py -q
```

## Results

| Check | Result |
|-------|--------|
| Dry orchestrator | READY / DRY COMPLETE; HOST=runpod BACKEND=unsloth |
| Pytest | 34 passed |
| Pod rented | no |

## Limits

- Contract/wiring only — not a GPU Unsloth forward/smoke
- Before `-Go`: dirty override on `sft_remote_train_s8_weighted.sh` needs commit/push or `-AllowDirtySync`
- Next paid step: `-Go -SmokeOnly -StartMonitor` after operator go
