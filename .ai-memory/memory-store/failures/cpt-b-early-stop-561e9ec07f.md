---
store_path: failures/cpt-b-early-stop-561e9ec07f
title: "CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halt"
summary: "CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halted corpus v3 at step 375 of 4128 (~8.2M of 90M tokens)"
priority: medium
tags: [cpt, early-stop, failure, fix, runpod]
schema_version: 1.3
last_updated: "2026-08-27T21:36:49-04:00"
occurrences: 1
error_signature: "cpt b early-stop patience=<n> with eval_steps=<n> and <n>-doc eval_spurgeon_loss halted corpus v<n> at step <n> of <n> (~<n>.<n>m of <n>m tokens). mix eval still falling. same absolute tokens as the small v<n> probe."
---

## Occurrence 1 — 2026-08-27T21:36:49-04:00

**Error:**
CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halted corpus v3 at step 375 of 4128 (~8.2M of 90M tokens). Mix eval still falling. Same absolute tokens as the small v2 probe.

**Fix:**
Not a crash. For a future B that must consume the large mix: add min_steps/min_tokens before patience, or scale patience with packed_epoch_steps. Do not treat 2-doc Spurgeon CE plateau as dataset exhausted. Next step for the existing S5 adapter is C (approval), not a stealth re-train.
