---
store_path: fine-tuning/hf-spurgeon-qa-v2-gguf
title: "HF: spurgeon-qa-v2 GGUF + merged BF16"
summary: "Private Hub repo: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-v2"
priority: medium
tags: [huggingface, gguf, sft, merged, bf16]
schema_version: 1.3
last_updated: "2026-09-06T20:45:41-04:00"
evidence: [fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf, fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf, fine_tuning/scripts/merge_sft_lora_local.py]
---

# HF: Spurgeon QA v2 (GGUF + merged BF16)

**Date:** 2026-09-06

Private Hub repo: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-v2

Contains:
- `spurgeon-qa-v2.Q4_K_M.gguf` (~2.71 GB) — Ollama / quantized
- Full merged BF16 HF weights (rebuilt locally after Vast fetch miss)

## Local
- Merged HF: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf/` (~7.85 GB, 5 shards)
- GGUF: `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf`
- Ollama model: `spurgeon-qa-v2` (smoke passed)
- Ingredients: CPT `theology_cpt_v2_merged_hf/` + LoRA `spurgeon_qa_lora_v2/lora/`

## Related
- LoRA-only: `rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2`
- Rebuild script: `fine_tuning/scripts/merge_sft_lora_local.py`
