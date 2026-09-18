---
store_path: fine-tuning/sft-idle-pod-force-delete
title: "SFT watcher: force-delete on orchestrate failure"
summary: "**Date:** 2026-09-02 ~17:00 ET"
priority: high
tags: [sft, runpod, billing, idle]
schema_version: 1.3
last_updated: "2026-09-02T17:00:52-04:00"
---

**Date:** 2026-09-02 ~17:00 ET

## Incident
Capacity watcher provisioned `sft-gate0` (`ph9wzckj6nttpa`, 4090 US-IL-1) then failed `sft_inject_hf_token.ps1` 3×. GPU util stayed 0 while pod kept billing. Default `SFT_IDLE_DELETE_MIN=20` left the pod up for retries (`watch_status=orchestrate_failed_retry`).

## Immediate action
- Deleted pod via RunPod MCP (HTTP 204).
- Killed `sft_watch_capacity` + `sft_monitor_until_done` processes.
- Session cleared: `pod_id=null`, `watch_status=idle_pod_deleted`.

## Code fix
`sft_watch_capacity.py` `handle_live_pod`: on orchestrate failure, call `cleanup_idle_pod(..., force=True)` immediately instead of waiting the idle timer.

## Follow-up
Fix root of `sft_inject_hf_token.ps1` failure (likely `huggingface_hub` / whoami before setup) before restarting capacity watch.
