---
store_path: fine-tuning/sft-phase-b-dry-terminated
title: "SFT Phase B dry-run pod terminated"
summary: "- Pod `47zu29u0yth5a3` (name `sft-phase-b-dry`) deleted via Runpod MCP `delete-pod` (HTTP 204)"
priority: high
tags: [sft, runpod, billing]
schema_version: 1.3
last_updated: "2026-08-28T20:41:31-04:00"
---

# SFT Phase B dry-run pod terminated (2026-08-28)

- Pod `47zu29u0yth5a3` (name `sft-phase-b-dry`) deleted via Runpod MCP `delete-pod` (HTTP 204).
- `list-pods` afterwards: **0 pods**.
- Network volume `7hb931c5oe` was **not** mounted on this pod (`network_volume_id: null`) and was **not** deleted — keep for CPT S6 resume.
- No leftover local SSH to `38.65.239.56:22046`.
- Session file: `fine_tuning/kaggle/sft_phase_b_session.json` status=`terminated`.
- Dry-run training was not started on that pod before delete.
