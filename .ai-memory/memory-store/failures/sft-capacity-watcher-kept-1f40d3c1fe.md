---
store_path: failures/sft-capacity-watcher-kept-1f40d3c1fe
title: "SFT capacity watcher kept idle RunPod GPU pod billing after orchestrate failed o"
summary: "SFT capacity watcher kept idle RunPod GPU pod billing after orchestrate failed on sft_inject_hf_token.ps1; default idle delete was 20 min instead of immediate terminate on failed launch"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-02T17:00:27-04:00"
occurrences: 1
error_signature: "sft capacity watcher kept idle runpod gpu pod billing after orchestrate failed on sft_inject_hf_token.ps<n>; default idle delete was <n> min instead of immediate terminate on failed launch"
review_status: stale
---

## Occurrence 1 — 2026-09-02T17:00:27-04:00

**Error:**
SFT capacity watcher kept idle RunPod GPU pod billing after orchestrate failed on sft_inject_hf_token.ps1; default idle delete was 20 min instead of immediate terminate on failed launch

**Fix:**
Deleted pod ph9wzckj6nttpa (sft-gate0, GPU util 0). Killed sft_watch_capacity and sft_monitor_until_done processes. Root cause: watch_status orchestrate_failed_retry keeps pod for SFT_IDLE_DELETE_MIN (20) retries instead of force-delete after inject/orchestrate failure.
