---
store_path: failures/cuda-oom-during-mid-ffcb775074
title: "torch.OutOfMemoryError: CUDA out of memory during SFTTrainer.evaluate at step 20"
summary: "CUDA OOM during mid-train eval at step ~20 with PEFT bf16 seq 2048 on RTX 4090 24GB"
priority: medium
tags: [eval, failure, fix, gate0, oom, peft, sft, vast]
schema_version: 1.3
last_updated: "2026-09-06T02:28:22-04:00"
occurrences: 2
error_signature: "cuda oom during mid-train eval at step ~<n> with peft bf<n> seq <n> on rtx <n> <n>gb"
failure_key: "cuda|oom"
---

## Occurrence 1 — 2026-09-06T02:25:26-04:00

**Error:**
CUDA OOM during mid-train eval at step ~20 with PEFT bf16 seq 2048 on RTX 4090 24GB

**Fix:**
Default and inject SFT_EVAL_STRATEGY=no (skip mid-train eval on 24GB). Restart train_sft_sota.py with SFT_BACKEND=peft; no checkpoint so fresh 408 steps.

## Occurrence 2 — 2026-09-06T02:28:22-04:00

torch.OutOfMemoryError: CUDA out of memory during SFTTrainer.evaluate at step 20 (PEFT bf16 Qwen3.5-4B seq 2048 on 24GB). Tried to allocate 15.16 GiB while 16.69 GiB already in use; OOM in ForCausalLMLoss logits.float().

Disable mid-train eval: SFT_EVAL_STRATEGY=no (default), per_device_eval_batch_size=1, load_best_model_at_end=False when eval off, gradient_checkpointing + empty_cache, prediction_loss_only=True. Keep peft/2048/batch1/accum16. Synced train_sft_sota.py to Vast and relaunched (no checkpoint — died before save_steps=40).
