---
store_path: fine-tuning/next-session-ot-softstrip-resft
title: "Next session after OT soft-strip re-SFT (go complete)"
summary: "- Honesty 53 accept / 7 reject → accepted 891 → export train **887** / eval 40"
priority: medium
tags: [sft, open-theology, handoff, next-session]
schema_version: 1.3
last_updated: "2026-10-20T14:00:25-03:00"
---

# Next session — after OT soft-strip re-SFT (2026-10-20 go done)

## Go completed

- Honesty 53 accept / 7 reject → accepted 891 → export train **887** / eval 40
- Weighted Unsloth SFT Secure 4090; adapter SHA256 `a34d288652b52b840b1a40bdb5173d49348010830ceab026dc06949478cc49c0`
- Re-score still `weak_not_useful_yet`: correctness **2.65**, honesty **2.50** (need ≥3.5) vs 2026-10-19 2.525/2.525
- Invent-cite persists; soft-strip + honesty batch did not make OT chat useful
- Evidence: `fine-tuning/ot-softstrip-resft-score-2026-10-20`, `fine-tuning/ot-softstrip-resft-live-2026-10-20`

## Do next (different track)

**RAG refusal-slice** for Hub/Ollama export (`fine-tuning/sft-improve-refusal-slice-first`). Do **not** rent another OT soft-strip re-SFT expecting usefulness.

## Ops notes kept

- Clear stale `/workspace/sft_smoke.log` at supervisor start (patched in `sft_remote_train_s8_weighted.sh`)
- Attach monitor: `runpod_sft_s8_weighted_monitor_attach.ps1` if main orchestrator false-stops
- `SFT_EXPORT=0`; Hub LoRA v2 stays
