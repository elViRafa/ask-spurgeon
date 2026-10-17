---
store_path: failures/wait-ssh-hung-forever-6ccb9b1c76
title: "wait_ssh hung forever: MCP OAuth REST v1 GET /pods/{id} returns desiredStatus bu"
summary: "wait_ssh hung forever: MCP OAuth REST v1 GET /pods/{id} returns desiredStatus but no ssh/publicIp/runtime; API key account is a different wallet than MCP OAuth"
priority: medium
tags: [auth, failure, fix, runpod, ssh, volume]
schema_version: 1.3
last_updated: "2026-10-17T17:33:21-03:00"
occurrences: 1
error_signature: "wait_ssh hung forever: mcp oauth rest v<n> get <path>{id} returns desiredstatus but no ssh<path>; api key account is a different wallet than mcp oauth"
---

## Occurrence 1 — 2026-10-17T17:33:21-03:00

**Error:**
wait_ssh hung forever: MCP OAuth REST v1 GET /pods/{id} returns desiredStatus but no ssh/publicIp/runtime; API key account is a different wallet than MCP OAuth

**Fix:**
Prefer RUNPOD_API_KEY from .env/config.toml for provision. wait_ssh falls back to GraphQL machine.podHostId for proxy SSH, then probe_ssh until container answers. ensure_network_volume creates US-IL-1 75GB (id 37lkz6dt50). Destroy bad hosts with GPU requires reset.
