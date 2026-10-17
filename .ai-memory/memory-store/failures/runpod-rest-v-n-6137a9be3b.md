---
store_path: failures/runpod-rest-v-n-6137a9be3b
title: "RunPod REST v1 pod create via sft_provision_pod_mcp.py returned Cloudflare 403 e"
summary: "RunPod REST v1 pod create via sft_provision_pod_mcp.py returned Cloudflare 403 error code 1010 on all GPU/image attempts; runpodctl fallback then failed because ~/.runpod/config.toml apikey is empty"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-10-17T14:22:20-03:00"
occurrences: 1
error_signature: "runpod rest v<n> pod create via sft_provision_pod_mcp.py returned cloudflare <n> error code <n> on all gpu<path> attempts; runpodctl fallback then failed because ~<path> apikey is empty"
---

## Occurrence 1 — 2026-10-17T14:22:20-03:00

**Error:**
RunPod REST v1 pod create via sft_provision_pod_mcp.py returned Cloudflare 403 error code 1010 on all GPU/image attempts; runpodctl fallback then failed because ~/.runpod/config.toml apikey is empty

**Fix:**
Add User-Agent ask-spurgeon-sft-provision/1.0 to http_json in sft_provision_pod_mcp.py (Cloudflare blocks bare urllib). Prefer MCP OAuth provision before runpodctl; pass SFT_POD_NAME so weighted pods are not named sft-gate0.
