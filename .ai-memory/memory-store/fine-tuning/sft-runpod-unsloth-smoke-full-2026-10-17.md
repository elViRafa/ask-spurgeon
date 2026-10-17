---
store_path: fine-tuning/sft-runpod-unsloth-smoke-full-2026-10-17
title: "RunPod Unsloth weighted SFT: speed win + accidental full train"
summary: "Unsloth on RunPod Secure 4090 **beats** Vast PEFT ~90 s/step: steady **~16–18 s/step** at seq 4608 after step 1 (~92 s cold)"
priority: medium
tags: [sft, unsloth, runpod, smoke, adapter]
schema_version: 1.3
last_updated: "2026-10-17T18:39:51-03:00"
evidence: [fine_tuning/kaggle/runpod_sft_s8_weighted/sft_s8_weighted/adapter/lora, fine_tuning/scripts/train_sft_sota.py, continued_pretrain/GROK_BOT_FORGE.md]
---

# RunPod Unsloth weighted SFT — 2026-10-17 result

## Verdict

Unsloth on RunPod Secure 4090 **beats** Vast PEFT ~90 s/step: steady **~16–18 s/step** at seq 4608 after step 1 (~92 s cold).

## What ran

- Auth: `RUNPOD_API_KEY` (funded account). Volume `37lkz6dt50` US-IL-1 75GB created.
- Pod `2gbzxfhmyfv25c` destroyed after fetch. Balance ~$12 leftover (from ~$15).
- Bug: `_train_unsloth` ignored `SFT_SMOKE`/`SFT_MAX_STEPS` → “smoke” ran full **514** steps. Fixed in `train_sft_sota.py` for next smoke.
- After first 514 completed, missing `SFT_SMOKE_PASS` started a second epoch; killed; markers written; fetch kept adapter.

## Artifacts (local)

- Final LoRA: `fine_tuning/kaggle/runpod_sft_s8_weighted/sft_s8_weighted/adapter/lora/`
- `checkpoint-514` under same tree + `safety_fetch_final_514_20261017_182054/`
- `SFT_EXPORT=0` — no Hub until F gates.

## Control split (confirmed)

- Cursor: first Unsloth smoke / debug.
- Forge: multi-hour watch after smoke win — profile updated in `GROK_BOT_FORGE.md`.
- This session already produced a full adapter; next Forge go is only if a clean re-train is wanted.

## Follow-ups

1. Commit dirty fixes (`sft_remote_setup.sh`, `train_sft_sota.py`, wait-ssh GraphQL, probe script, volume id).
2. True 2-step `-SmokeOnly` to confirm fix, then optional clean full `-Go` under Forge.
3. Run F gates / `sft_export_if_gates.ps1` on fetched adapter when ready.
