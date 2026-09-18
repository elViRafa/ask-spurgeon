---
store_path: failures/unsloth-sigsegv-exit-n-c04655b283
title: "Unsloth CPT+LoRA SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast RTX"
summary: "Unsloth SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast — including full RTX 4090 (4bit and bf16)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-16T07:54:00-03:00"
occurrences: 2
error_signature: "unsloth sigsegv (exit <n>) at first sfttrainer.train() step on vast — including full rtx <n> (<n>bit and bf<n>). also fractional gpu nvml spoof as <n>."
---

## Occurrence 1 — 2026-09-06T00:46:26-04:00

**Error:**
Unsloth SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast — including full RTX 4090 (4bit and bf16). Also fractional GPU NVML spoof as 3090.

**Fix:**
Do not use Unsloth on Vast for GATE-0. Prefer full GPU (gpu_frac>=1) with cuda_max_good>=12.6. Use SFT_BACKEND=peft (transformers AutoModelForCausalLM bf16 + PEFT LoRA + TRL). Persist peft + seq2048/batch1/accum16 in vast_inject_hf_token.ps1. Monitor ignores setup Tracebacks (train-log-only crash detection).

## Occurrence 2 — 2026-09-16T07:54:00-03:00

Unsloth CPT+LoRA SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast RTX 4090 (torch 2.11+cu126, Qwen3.5-4B bf16)

Do not use Unsloth for CPT on Vast. Smoke confirmed same failure mode as SFT. Use PEFT on Vast or run Unsloth CPT on Runpod once volume/funds are available.
