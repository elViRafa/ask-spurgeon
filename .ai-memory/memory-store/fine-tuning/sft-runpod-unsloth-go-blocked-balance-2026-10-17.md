---
store_path: fine-tuning/sft-runpod-unsloth-go-blocked-balance-2026-10-17
title: "RunPod Unsloth go blocked: no volume + low balance"
summary: "- `7f27f32` RunPod Unsloth weighted path + bf16 LoRA (`load_in_4bit=False`, `load_in_16bit=True`)"
priority: medium
tags: [sft, weighted, runpod, unsloth, balance, readiness]
schema_version: 1.3
last_updated: "2026-10-17T15:04:44-03:00"
---

# RunPod Unsloth go blocked (2026-10-17)

## Landed on main

- `7f27f32` RunPod Unsloth weighted path + bf16 LoRA (`load_in_4bit=False`, `load_in_16bit=True`)
- `08a95ff` Cloudflare 1010 fix (User-Agent on MCP REST)
- `43fd4b6` ephemeral workspace fallback when volume missing
- `10c6860` clear balance error (no fake RUNPOD_API_KEY throw)

Offline dry: READY, DIRTY_OVERRIDES=(none), pin `10c6860`.

## Paid go attempt

`-Go -SmokeOnly -StartMonitor` reached REST create:

1. Volume `7hb931c5oe` **not found** (list-network-volumes empty).
2. `create-network-volume` US-IL-1 75GB → **400** needs **>= $5**.
3. Ephemeral fallback: Community 4090 no stock; Secure/L40S → **account balance too low to rent**.

No pod created. No billing from this go.

## Ops next

1. Top up RunPod (enough for Secure 4090 ~$0.89/hr smoke, ideally >=$5 to recreate US-IL-1 volume).
2. Optional: set `~/.runpod/config.toml` apikey for runpodctl.
3. Re-dry then `.
unpod_sft_s8_weighted_orchestrate.ps1 -Go -SmokeOnly -StartMonitor`.
4. Full go only if smoke s/step beats ~90s PEFT; else Vast PEFT (also needs Vast credit).

## Update 2026-10-17 afternoon — auth + credit cleared

Operator topped up and set API key in `.env` + `~/.runpod/config.toml`. `runpodctl user` shows **$15** balance. Auth/credit blocker is lifted; see `fine-tuning/runpod-credentials-ready-2026-10-17`. Next paid step is still dry then `-Go -SmokeOnly -StartMonitor` (no lease in the credential-setup session).
