---
store_path: fine-tuning/runpod-credentials-ready-2026-10-17
title: "Runpod credentials + balance ready"
summary: "Supersedes the same-day blocker `fine-tuning/sft-runpod-unsloth-go-blocked-balance-2026-10-17` for **auth and credit** (not for Unsloth smoke proof)"
priority: medium
tags: [runpod, api-key, balance, credentials, sft, forge]
schema_version: 1.3
last_updated: "2026-10-17T15:04:35-03:00"
evidence: ["~/.runpod/config.toml", .env, ".gitignore:30"]
---

# Runpod credentials + balance ready (2026-10-17)

Supersedes the same-day blocker `fine-tuning/sft-runpod-unsloth-go-blocked-balance-2026-10-17` for **auth and credit** (not for Unsloth smoke proof).

## Verified

- Cursor agent setup done (skills + MCP OAuth). See `grok/runpod-agent-setup-pod-usage`.
- API key created by operator; stored in **both**:
  - Project `.env` as `RUNPOD_API_KEY=…` (gitignored; `.gitignore` line 30)
  - `~/.runpod/config.toml` as `apikey = '…'`
- Do **not** store the key value in memory.
- `runpodctl user` succeeded: `clientBalance` **15**, `currentSpendPerHr` **0**, `spendLimit` **80**.
- Enough for network volume create (≥ $5) and Secure 4090 smoke (~$0.89/hr).

## Caveat for scripts

`Get-RunpodApiKey` in `fine_tuning/scripts/sft_runpod_common.ps1` reads process env then `config.toml` — it does **not** load `RUNPOD_API_KEY` from `.env`. Keeping `config.toml` populated is required for Forge/orchestrator CLI path.

## Still not done

- No pod/volume rented in this session.
- Unsloth GPU smoke still needs operator `-Go -SmokeOnly` after dry.
