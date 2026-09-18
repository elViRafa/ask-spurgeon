---
store_path: fine-tuning/ollama-local-test-next-session
title: "DONE: Ollama local test complete (spurgeon-qa-v2)"
summary: "**Status:** COMPLETE (2026-09-06 / 2026-09-07)"
priority: medium
tags: [ollama, complete, done, sft, gguf]
schema_version: 1.3
last_updated: "2026-09-06T20:06:17-04:00"
evidence: [fine_tuning/scripts/smoke_test_ollama.py, fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf, fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf]
---

# DONE — Ollama local test (spurgeon-qa-v2)

**Status:** COMPLETE (2026-09-06 / 2026-09-07)
**No pending next-session work for merge/GGUF/Ollama smoke.**

## Done
- SFT LoRA merged on Vast `50091768` → `/workspace/spurgeon_qa_merged_hf` (CausalLM PEFT, 256/256 keys)
- Q4_K_M GGUF: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf` (~2.6GB) + copy at `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf`
- Ollama model `spurgeon-qa-v2` created; `smoke_test_ollama.py` **exit 0**
- Vast instance destroyed after fetch
- Full HF merge folder fetch incomplete; GGUF sufficient

## Chat
```
ollama run spurgeon-qa-v2
```

Plan (DONE): `fine-tuning/plans/ollama-merge-gguf`
