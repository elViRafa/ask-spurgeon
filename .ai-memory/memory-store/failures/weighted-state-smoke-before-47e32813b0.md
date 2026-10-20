---
store_path: failures/weighted-state-smoke-before-47e32813b0
title: "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED false trigger mid-setup: probe grepped "
summary: "WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED false trigger mid-setup: probe grepped stale /workspace/sft_smoke.log from prior Oct 17 run on network volume; orchestrator started evidence+destroy while sft_"
priority: medium
tags: [failure, false-positive, fix, network-volume, runpod, sft, smoke]
schema_version: 1.3
last_updated: "2026-10-20T10:19:51-03:00"
occurrences: 1
error_signature: "weighted_state=smoke_before_train_failed false trigger mid-setup: probe grepped stale <path> from prior oct <n> run on network volume; orchestrator started evidence+destroy while sft_remote_setup.sh still healthy"
---

## Occurrence 1 — 2026-10-20T10:19:51-03:00

**Error:**
WEIGHTED_STATE=SMOKE_BEFORE_TRAIN_FAILED false trigger mid-setup: probe grepped stale /workspace/sft_smoke.log from prior Oct 17 run on network volume; orchestrator started evidence+destroy while sft_remote_setup.sh still healthy

**Fix:**
Moved stale sft_smoke.log and sft_smoke_fail aside, truncated smoke log, killed local orchestrator before DELETE. Probe then ALIVE. Patched sft_remote_train_s8_weighted.sh to truncate smoke log and rm sft_smoke_fail at supervisor start. Attached runpod_sft_s8_weighted_monitor_attach.ps1 for remaining watch.
