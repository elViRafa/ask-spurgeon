---
store_path: failures/get-runpodapikey-treated-empty-ae395f84fc
title: "Get-RunpodApiKey treated empty config.toml apikey = '' as a valid key; MCP REST "
summary: "Get-RunpodApiKey treated empty config.toml apikey = '' as a valid key; MCP REST v1 pod create then failed Cloudflare 403/1010 without a usable RUNPOD_API_KEY"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-16T07:22:04-03:00"
occurrences: 1
error_signature: "get-runpodapikey treated empty config.toml apikey = <val> as a valid key; mcp rest v<n> pod create then failed cloudflare <n><path> without a usable runpod_api_key"
---

## Occurrence 1 — 2026-09-16T07:22:04-03:00

**Error:**
Get-RunpodApiKey treated empty config.toml apikey = '' as a valid key; MCP REST v1 pod create then failed Cloudflare 403/1010 without a usable RUNPOD_API_KEY

**Fix:**
Reject empty/quoted-empty apikey values in s6_runpod_common.ps1 Get-RunpodApiKey; require a real key or funded account + volume before S6 orchestrate
