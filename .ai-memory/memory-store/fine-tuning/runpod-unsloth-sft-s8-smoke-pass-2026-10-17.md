---
store_path: fine-tuning/runpod-unsloth-sft-s8-smoke-pass-2026-10-17
title: "RunPod Unsloth weighted SFT S8 smoke/train pass"
summary: "- Unsloth on RunPod **won on speed**: ~**16–18 s/step** @ seq 4608 vs ~90s PEFT baseline"
priority: medium
tags: [runpod, unsloth, sft, s8, weighted, smoke]
schema_version: 1.3
last_updated: "2026-10-17T19:02:25-03:00"
---

# RunPod Unsloth weighted SFT S8 — smoke/train pass (2026-10-17)

## Verdict
- Unsloth on RunPod **won on speed**: ~**16–18 s/step** @ seq 4608 vs ~90s PEFT baseline.
- Adapter fetched locally under `fine_tuning/kaggle/runpod_sft_s8_weighted/sft_s8_weighted/adapter/lora/` (+ `checkpoint-514`).
- Pod destroyed after fetch; no stray pods left. Balance landed ~$12. Volume `37lkz6dt50` may still bill storage (~$0.007/hr).

## Control split (locked)
- **Cursor** owns first paid Unsloth smoke (debug loop: MCP + runpodctl + orchestrator).
- **Grok Forge** watches multi-hour full train only after smoke beats ~90s/step.
- Cloud Agents must not rent GPU.

## Bugs fixed this session
1. Prefer `RUNPOD_API_KEY` over MCP OAuth; GraphQL + SSH probe for wait-ssh (OAuth hang).
2. Import `unsloth` before `unsloth_zoo` in remote setup (pin assert).
3. Unsloth path ignored `SFT_SMOKE`/`max_steps` → ran full 514; fixed in `train_sft_sota.py`.
4. Compact state probe so monitor sees `SETUP_FAILED` / `SMOKE_ONLY_DONE`.

## Hard rules still on
- `SFT_EXPORT=0` until F gates; no Hub overwrite; fetch before destroy; no second GPU while one session exists.

## Next
- Commit dirty orchestrator/train/setup fixes.
- Optional true 2-step `-SmokeOnly` to prove max_steps fix.
- F gates / export on fetched adapter.
- Delete volume if not needed between runs.
