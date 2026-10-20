---
store_path: failures/runpod-mcp-list-pods-5b19015063
title: "RunPod MCP list-pods/get-pod/delete-pod reported empty or 404 while runpodctl st"
summary: "RunPod MCP list-pods/get-pod/delete-pod reported empty or 404 while runpodctl still showed a RUNNING GPU pod billing"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-10-17T20:55:26-03:00"
occurrences: 1
error_signature: "runpod mcp list-pods<path> reported empty or <n> while runpodctl still showed a running gpu pod billing"
---

## Occurrence 1 — 2026-10-17T20:55:26-03:00

**Error:**
RunPod MCP list-pods/get-pod/delete-pod reported empty or 404 while runpodctl still showed a RUNNING GPU pod billing

**Fix:**
After MCP delete or session end, always cross-check with `runpodctl pod list`. Terminate leftovers with `runpodctl pod delete <id>`. Do not trust MCP empty list alone for billing cleanup.
