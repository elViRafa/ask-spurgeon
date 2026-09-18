---
store_path: fine-tuning/plans/ollama-merge-gguf
title: "DONE: merged HF local + Hub upload"
summary: "**Initially no** — Vast fetch of `/workspace/spurgeon_qa_merged_hf` failed; instance destroyed"
priority: medium
tags: [ollama, gguf, huggingface, sft, merged, done]
schema_version: 1.3
last_updated: "2026-09-06T20:45:20-04:00"
evidence: [fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf, fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf, fine_tuning/scripts/merge_sft_lora_local.py]
---

# Local + Hub: merged Spurgeon QA v2 (DONE)

**Date:** 2026-09-06/07

## Answer: was full HF merge saved after Vast?
**Initially no** — Vast fetch of `/workspace/spurgeon_qa_merged_hf` failed; instance destroyed. Only **Q4_K_M GGUF** was kept locally for Ollama.

## Now on disk
- **Full bf16 HF merge (rebuilt locally):** `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf/` (~7.85 GB, 5 shards)
- **GGUF:** `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf` (+ copy under `…/spurgeon_qa_gguf/`)
- **Ingredients still present:** `theology_cpt_v2_merged_hf/` + `spurgeon_qa_lora_v2/lora/`
- **Ollama:** `spurgeon-qa-v2` (smoke passed earlier)

## Hub
Private: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-v2
- GGUF uploaded
- Merged bf16 HF folder uploaded

LoRA-only (earlier): https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2
