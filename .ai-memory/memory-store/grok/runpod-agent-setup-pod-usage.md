---
store_path: grok/runpod-agent-setup-pod-usage
title: "Runpod agent setup for Cursor + Grok Forge"
summary: "Followed official guide: https://docs.runpod.io/agent-setup.md"
priority: high
tags: [grok, forge, runpod, agent-setup, pod-usage, mcp, api-key]
schema_version: 1.3
last_updated: "2026-10-17T15:04:41-03:00"
evidence: ["https://docs.runpod.io/agent-setup.md", "~/.cursor/mcp.json", "~/.agents/skills/runpod-usage", "~/.runpod/config.toml", .env]
---

# Runpod agent setup (Cursor) — 2026-10-17

Followed official guide: https://docs.runpod.io/agent-setup.md

## Verified on this PC

- Node `v24.11.1` (>= 22.20 required).
- Skills installed globally for Cursor:
  `npx -y skills add runpod/runpod-plugins-official --skill '*' --agent cursor --yes --global`
- Under `~/.agents/skills/`: `runpod` router, lanes (`runpod-mcp`, `runpodctl`, `flash`, `runpod-usage`, …), journeys (`discovery`, `lifecycle-crud`, `pod-deploy`, …).
- MCP in `~/.cursor/mcp.json`: `"runpod": { "url": "https://mcp.getrunpod.io/" }`.
- MCP OAuth works (`list-pods` empty = pass when none expected).

## Credentials (updated same day)

- Operator created API key; placed in **both** gitignored project `.env` (`RUNPOD_API_KEY`) and `~/.runpod/config.toml` (`apikey`).
- `runpodctl user` OK: balance **$15**, spend $0/hr, limit $80. See `fine-tuning/runpod-credentials-ready-2026-10-17`.
- Never paste or memory-store the key value.

## Grok Bot Forge / pod usage

- Forge rents/ops GPU pods via `.cursor/skills/gpu-train-ops/SKILL.md` + official `runpod-usage` / `runpod-mcp`.
- Prefer `config.toml` for CLI; project scripts do not auto-load `RUNPOD_API_KEY` from `.env`.
- Hosted MCP OAuth alone is half-setup; CLI needs the key (now set).

## Do not

- Interactive `npx @runpod/mcp-server@latest add` from an agent shell.
- Pre-install runpodctl/Flash during setup — skills install on demand.
