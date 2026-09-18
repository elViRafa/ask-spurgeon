---
store_path: fine-tuning/vast-gate0-next-session
title: "DONE: Vast GATE-0 + merge/GGUF/Ollama complete"
summary: "**Status:** COMPLETE (2026-09-06 / 2026-09-07)"
priority: medium
tags: [huggingface, sft, ollama, vast, complete, done]
schema_version: 1.3
last_updated: "2026-09-06T20:06:23-04:00"
evidence: [fine_tuning/scripts/train_sft_sota.py, fine_tuning/scripts/smoke_test_ollama.py, fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf]
---

# DONE — Vast GATE-0 SFT + merge → GGUF → Ollama

**No pending next-session work for GATE-0 train or Ollama path.**

## GATE-0 train (prior)
- Instance **50011937** destroyed after SFT finished
- Train: **408/408**, epoch 2.0, `train_loss≈1.874`
- Local adapter: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_lora_v2/lora/`
- Local CPT merge: `fine_tuning/kaggle/vast_sft_gate0/theology_cpt_v2_merged_hf/`
- Hub (private): https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2

## Merge → GGUF → Ollama (completed)
- Merge instance **50091768** (Quebec RTX 4090) destroyed after fetch
- PEFT merge on CausalLM → `/workspace/spurgeon_qa_merged_hf` (256/256 keys; ConditionalGeneration attempt was wrong)
- GGUF: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf` (~2.6GB) + `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf`
- Ollama: `spurgeon-qa-v2`; `smoke_test_ollama.py` exit 0

## Related DONE memories

F §5 eval / EXPORT still gated (`SFT_EXPORT=0`) — optional follow-up, not blocking Ollama.
