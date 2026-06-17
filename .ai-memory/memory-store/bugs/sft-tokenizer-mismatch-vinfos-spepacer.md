---
store_path: bugs/sft-tokenizer-mismatch-vinfos-spepacer
title: "Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)"
summary: -----
priority: medium
tags: [bugs, lora, tokenizer, qwen]
schema_version: 1.3
last_updated: "2026-06-13T22:03:20-04:00"
---

-----
store_path: bugs/sft-tokenizer-mismatch-vinfos-spepacer
title: "Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)"
summary: "Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)"
priority: high
tags: [bugs, lora, tokenizer, qwen]
schema_version: 1.3
last_updated: "2026-06-13T22:10:00-04:00"
---

# Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)

## Context
During Phase 2 SFT training in Notebook E (`E_qa_training.ipynb`), a tokenizer mismatch led to `<|im_end|>` being split into subwords (`vinfos`/`spepacer`), which the model learned as the turn terminator. When a clean base model and tokenizer were used, the problem appeared resolved, but a new set of Chinese/system garbage tokens (`具有战士`/`rPid`/`sPid`) surfaced at paragraph boundaries.

## Root Cause Analysis
- **PEFT Weight Untying Mismatch:** Qwen 2.5 uses `tie_word_embeddings=True` to share weights between `embed_tokens` (input embeddings) and `lm_head` (output logits).
- When `"embed_tokens"` and `"lm_head"` are targeted in LoRA `target_modules`, PEFT creates separate adapters, untying these layers.
- In Qwen 2.5, this weight-untying causes model corruption, resulting in nonsensical output (like `具有战士` and `rPid`) at token prediction boundaries.
- Because Qwen 2.5 base model already has correct pre-trained weights for `<|im_start|>` (151644) and `<|im_end|>` (151645), we do NOT need to train these embedding layers. Keeping them frozen and tied is both safe and sufficient.

## Fixes Implemented
1. **Reverted LoRA Embedding Targets:** Removed `"embed_tokens"` and `"lm_head"` from `target_modules` in Notebook E (`E_qa_training.ipynb`) to keep embeddings properly frozen and tied.
2. **Fixed Notebook E Syntax Error:** Removed the unexpected indentation from the pre-fix check lines (24-27) in Cell 6 of Notebook E.
3. **Dynamic Adapter Directory Check:** Restored dynamic verification in `F_qa_eval.ipynb` Cell 4 to load the new adapter from `/kaggle/working/spurgeon_lora_qa` if present, preventing the use of stale adapters from Kaggle input datasets.
