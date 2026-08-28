---
store_path: failures/runtimeerror-expected-mat-n-e21431291d
title: "RuntimeError: expected mat1 and mat2 to have the same dtype, but got: float != c"
summary: "RuntimeError: expected mat1 and mat2 to have the same dtype, but got: float != c10::Half during trainer.evaluate after Unsloth upcasts embed_tokens to fp32 (D4 same_storage=0)"
priority: medium
tags: [cpt, dtype, failure, fix, kaggle, lm-head, qwen35]
schema_version: 1.3
last_updated: "2026-08-26T01:22:26-04:00"
occurrences: 1
error_signature: "runtimeerror: expected mat<n> and mat<n> to have the same dtype, but got: float != c<n>::half during trainer.evaluate after unsloth upcasts embed_tokens to fp<n> (d<n> same_storage=<n>). eval calls self.lm_head(hidden_fp<n>) vs fp<n> lm_head weight. disabling trainer fp<n><path> alone did not fix it"
failure_key: runtimeerror
---

## Occurrence 1 — 2026-08-26T01:22:26-04:00

**Error:**
RuntimeError: expected mat1 and mat2 to have the same dtype, but got: float != c10::Half during trainer.evaluate after Unsloth upcasts embed_tokens to fp32 (D4 same_storage=0). Eval calls self.lm_head(hidden_fp32) vs fp16 lm_head weight. Disabling Trainer fp16/bf16 alone did not fix it.

**Fix:**
Register a forward pre-hook on get_output_embeddings() that casts lm_head inputs to weight.dtype. Keep trainer fp16/bf16 off when TRAIN_EMBEDDINGS=True. Do not upcast the full lm_head table (VRAM).
