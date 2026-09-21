---
store_path: failures/stack-isolation-c-install-da57762e21
title: "Stack-isolation C install failed: Unsloth 2026.8.22 pulls torchvision/xformers f"
summary: "Stack-isolation C install failed: Unsloth 2026.8.22 pulls torchvision/xformers for torch 2.11; re-pinning torch 2.8 with --no-deps left torchvision 0.26 operators broken (torchvision::nms)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-20T18:17:11-03:00"
occurrences: 1
error_signature: "stack-isolation c install failed: unsloth <n>.<n>.<n> pulls torchvision<path> for torch <n>.<n>; re-pinning torch <n>.<n> with --no-deps left torchvision <n>.<n> operators broken (torchvision::nms)"
---

## Occurrence 1 — 2026-09-20T18:17:11-03:00

**Error:**
Stack-isolation C install failed: Unsloth 2026.8.22 pulls torchvision/xformers for torch 2.11; re-pinning torch 2.8 with --no-deps left torchvision 0.26 operators broken (torchvision::nms)

**Fix:**
Force-reinstall torch==2.8.0 + torchvision==0.23.0 + torchaudio==2.8.0 from cu126 index; uninstall xformers; set UNSLOTH_SKIP_TORCHVISION_CHECK=1. Encoded in vast_remote_stack_isolation_c.sh / vast_stack_isolation_rerun.sh.
