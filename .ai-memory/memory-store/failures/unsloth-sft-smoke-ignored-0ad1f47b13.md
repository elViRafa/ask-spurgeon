---
store_path: failures/unsloth-sft-smoke-ignored-0ad1f47b13
title: "Unsloth SFT --smoke ignored max_steps / SFT_SMOKE and ran full weighted SFT (514"
summary: "Unsloth SFT --smoke ignored max_steps / SFT_SMOKE and ran full weighted SFT (514 steps) on RunPod; monitor also missed SMOKE_ONLY_DONE without compact state probe"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-10-17T19:02:26-03:00"
occurrences: 1
error_signature: "unsloth sft --smoke ignored max_steps / sft_smoke and ran full weighted sft (<n> steps) on runpod; monitor also missed smoke_only_done without compact state probe"
---

## Occurrence 1 — 2026-10-17T19:02:26-03:00

**Error:**
Unsloth SFT --smoke ignored max_steps / SFT_SMOKE and ran full weighted SFT (514 steps) on RunPod; monitor also missed SMOKE_ONLY_DONE without compact state probe

**Fix:**
In train_sft_sota.py _train_unsloth honor SFT_SMOKE/SFT_MAX_STEPS and emit SFT_SMOKE_PASS; remote train script accept complete as smoke pass; add sft_weighted_state_probe.sh + orchestrator probe; import unsloth before unsloth_zoo in sft_remote_setup.sh; prefer RUNPOD_API_KEY + GraphQL wait-ssh in sft_provision_pod_mcp.py
