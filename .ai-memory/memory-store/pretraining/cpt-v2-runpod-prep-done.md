---
store_path: pretraining/cpt-v2-runpod-prep-done
title: "CPT v2 Runpod prep + analysis complete — next session trains"
summary: "Kaggle B **v14 ERROR** remains STOP on `rafaelvieira1`"
priority: high
tags: [cpt, runpod, handoff]
schema_version: 1.3
last_updated: "2026-08-26T23:15:56-04:00"
evidence: [pretraining/cpt-v2-next-session-handoff]
---

# CPT v2 Runpod prep + analysis (both done 2026-08-26)

Kaggle B **v14 ERROR** remains STOP on `rafaelvieira1`. Do not C. Do not merge. Do not resume T4 4-bit adapters onto Ampere bf16.

## Code ready
- Helpers: `cpt_runtime.py` — WORK_ROOT / DATA_ROOT, GPU_PROFILE auto, PREV_RUN_CHECKPOINT empty = fresh, bf16+embed LoRA dtype, Kaggle vs Runpod save policy, `spurgeon_rose_by_step`.
- After pack: `MAX_STEPS = PACKED_EPOCH_STEPS` (one padded epoch).
- `AbortIfSpurgeonRisesCallback` at step 50 vs 25.
- `--install` exits after pip (`unsloth[colab-new]`).
- Recipe unchanged: `one_doc_padded`, `PAD_TO_MAX=False`, GDN LoRA `in_proj_qkv/in_proj_z/out_proj`, mix 0.164, `TRAIN_EMBEDDINGS=True`.

## Next session = train
Follow `continued_pretrain/RUNPOD_RUNBOOK.md`.
