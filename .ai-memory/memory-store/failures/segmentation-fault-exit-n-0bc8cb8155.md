---
store_path: failures/segmentation-fault-exit-n-0bc8cb8155
title: "Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking "
summary: "Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking OK on Vast Unsloth 2026.9.2 + TRL 0.24 + Qwen3.5 4bit"
priority: medium
tags: [failure, fix, gate0, peft, segfault, sft, unsloth, vast]
schema_version: 1.3
last_updated: "2026-09-06T00:42:31-04:00"
occurrences: 2
error_signature: "segmentation fault (exit <n>) at first sfttrainer.train() step after s<n> masking ok on vast unsloth <n>.<n>.<n> + trl <n>.<n> + qwen<n>.<n> <n>bit. also verify_sft_stop_tokens phase<n> segfaulted. log shows num_items_in_batch warning then silent sigsegv. fake nvml_reader missing."
---

## Occurrence 1 — 2026-09-05T23:50:01-04:00

**Error:**
Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking OK on Vast Unsloth 2026.9.2 + TRL 0.24 + Qwen3.5 4bit. Also verify_sft_stop_tokens phase2 segfaulted. Log shows num_items_in_batch warning then silent SIGSEGV. Fake nvml_reader missing.

**Fix:**
NOT FIXED YET. TypeError dataset_text_field is fixed (SFTConfig-only path works through S3). Segfault at step 0 persists with batch 1, seq 512/4096, with/without DataCollatorForSeq2Seq override, and with use_gradient_checkpointing=True instead of unsloth. Next: investigate Unsloth/bitsandbytes/CUDA on Vast fractional GPU; try load_in_4bit=False or pin older unsloth; check /opt/fake/nvml_reader.

## Occurrence 2 — 2026-09-06T00:42:31-04:00

Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking OK on Vast Unsloth 2026.9.2 + TRL 0.24 + Qwen3.5. Also Unsloth forward/backward SIGSEGV on full RTX 4090 (4bit and bf16). Fake nvml_reader missing on fractional hosts.

Do not use Unsloth on this Vast stack for GATE-0. Prefer full GPU (gpu_frac>=1) with cuda_max_good>=12.6. Use SFT_BACKEND=peft (transformers AutoModelForCausalLM bf16 + PEFT LoRA + TRL SFTTrainer). Avoid fractional GPUs (NVML spoofs 3090). Reduce seq/batch if OOM (2048/1/16 worked). Fix monitor to ignore setup Tracebacks.
