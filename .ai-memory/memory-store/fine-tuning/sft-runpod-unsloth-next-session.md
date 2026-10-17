---
store_path: fine-tuning/sft-runpod-unsloth-next-session
title: "RunPod Unsloth weighted SFT: code + offline proof"
summary: "**Status (2026-10-17):** code landed; offline dry + contract pytest passed"
priority: medium
tags: [sft, weighted, runpod, unsloth, handoff]
schema_version: 1.3
last_updated: "2026-10-17T14:14:52-03:00"
evidence: [fine_tuning/scripts/runpod_sft_s8_weighted_orchestrate.ps1, [REDACTED_SECRET].md, fine_tuning/scripts/sft_remote_train_s8_weighted.sh, fine_tuning/scripts/test_sft_s8_weighted_runpod_unsloth_plan.py]
---

# RunPod Unsloth weighted SFT — implemented + offline-tested

**Status (2026-10-17):** code landed; offline dry + contract pytest passed. No GPU rent until operator go.

## Landed

- `sft_remote_train_s8_weighted.sh`: `SFT_BACKEND` override (default peft; RunPod sets unsloth); `SFT_SMOKE_ONLY` / `SMOKE_ONLY_DONE`
- Plan: `sft_s8_weighted_runpod_unsloth_plan.py` + tests
- Orchestrator: `runpod_sft_s8_weighted_orchestrate.ps1` (dry / `-Go -SmokeOnly` / full `-Go`)
- Runbook: `[REDACTED_SECRET].md`
- Helpers: `SFT_SESSION_FILE`; provision `-SkipGate0Artifacts`
- Skills/Forge updated; Vast PEFT remains fallback

## Offline proof (no pod)

- Dry orchestrator: `READY` / `DRY COMPLETE`, `HOST=runpod BACKEND=unsloth`, no runpodctl/ssh
- Pytest: 34 passed (`test_sft_s8_weighted_runpod_unsloth_plan` + weighted plan + `test_sft_weighted_env_safeguards`)
- Dirty sync noted on `sft_remote_train_s8_weighted.sh` — commit/push or `-AllowDirtySync` before `-Go`
- Does **not** prove Unsloth GPU smoke (no SIGSEGV) — that needs `-Go -SmokeOnly`

## Usage after go

```text
cd fine_tuning\scripts
.\runpod_sft_s8_weighted_orchestrate.ps1
.\runpod_sft_s8_weighted_orchestrate.ps1 -Go -SmokeOnly -StartMonitor
.\runpod_sft_s8_weighted_orchestrate.ps1 -Go -StartMonitor
```

Full go only if smoke s/step beats ~90s PEFT. `SFT_EXPORT=0`; no Hub until F gates.
