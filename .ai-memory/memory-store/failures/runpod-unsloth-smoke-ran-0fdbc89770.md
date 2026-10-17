---
store_path: failures/runpod-unsloth-smoke-ran-0fdbc89770
title: "RunPod Unsloth --smoke ran full 514 steps (Num Epochs=2) ignoring SFT_MAX_STEPS="
summary: "RunPod Unsloth --smoke ran full 514 steps (Num Epochs=2) ignoring SFT_MAX_STEPS=2 / SFT_SMOKE=1; SFT_SMOKE_ONLY never reached because smoke never exited"
priority: medium
tags: [failure, fix, runpod, sft, smoke, unsloth]
schema_version: 1.3
last_updated: "2026-10-17T17:33:21-03:00"
occurrences: 1
error_signature: "runpod unsloth --smoke ran full <n> steps (num epochs=<n>) ignoring sft_max_steps=<n> / sft_smoke=<n>; sft_smoke_only never reached because smoke never exited"
---

## Occurrence 1 — 2026-10-17T17:33:21-03:00

**Error:**
RunPod Unsloth --smoke ran full 514 steps (Num Epochs=2) ignoring SFT_MAX_STEPS=2 / SFT_SMOKE=1; SFT_SMOKE_ONLY never reached because smoke never exited

**Fix:**
train_sft_sota.py _train_unsloth lacked smoke max_steps handling that PEFT path had. Added smoke batch/accum/max_steps, longest-row select, save_strategy=no, and SFT_SMOKE_PASS print. Live accidental full train at ~17s/step still beats Vast PEFT ~90s.
