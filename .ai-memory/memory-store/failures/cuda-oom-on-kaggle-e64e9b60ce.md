---
store_path: failures/cuda-oom-on-kaggle-e64e9b60ce
title: "CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch "
summary: "CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch 2, TRAIN_EMBEDDINGS=True)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-08-25T02:32:47-04:00"
occurrences: 1
error_signature: "cuda oom on kaggle t<n> during cpt b v<n> after manual pack (float<n> qwen<n>.<n>, batch <n>, train_embeddings=true)"
---

## Occurrence 1 — 2026-08-25T02:32:47-04:00

**Error:**
CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch 2, TRAIN_EMBEDDINGS=True)

**Fix:**
Set PER_DEVICE_BATCH=1 GRAD_ACCUM=16 TRAIN_EMBEDDINGS=False EVAL_DOCS_PER_BUCKET=4 in _gen_sota_notebooks.py for T4 headroom
