---
store_path: failures/cuda-out-of-memory-849d59401d
title: "CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocat"
summary: "CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocate 6.81 GiB on T4 while evaluating mix+4 holdout buckets at EVAL_DOCS_PER_BUCKET=8 (logits for 248k vocab)"
priority: medium
tags: [cpt, eval, failure, fix, kaggle, oom, qwen35]
schema_version: 1.3
last_updated: "2026-08-26T01:22:24-04:00"
occurrences: 1
error_signature: "cuda out of memory during first eval of qwen<n>.<n> embed lora cpt: tried to allocate <n>.<n> gib on t<n> while evaluating mix+<n> holdout buckets at eval_docs_per_bucket=<n> (logits for <n>k vocab). train steps at batch <n>x<n> with train_embeddings=true succeeded."
---

## Occurrence 1 — 2026-08-26T01:22:24-04:00

**Error:**
CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocate 6.81 GiB on T4 while evaluating mix+4 holdout buckets at EVAL_DOCS_PER_BUCKET=8 (logits for 248k vocab). Train steps at batch 1x16 with TRAIN_EMBEDDINGS=True succeeded.

**Fix:**
Keep TRAIN_EMBEDDINGS=True. Set EVAL_DOCS_PER_BUCKET=2, EVAL_BUCKETS_DURING_TRAIN=[spurgeon] (mix still kept), per_device_eval_batch_size=1, and prediction_loss_only=True so eval does not materialize full vocab logits.
