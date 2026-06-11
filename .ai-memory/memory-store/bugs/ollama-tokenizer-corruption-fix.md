---
store_path: bugs/ollama-tokenizer-corruption-fix
title: "Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)"
summary: "Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)"
priority: high
tags: [bugs, tokenizer, gguf, ollama, alignment]
schema_version: 1.3
last_updated: "2026-06-11T17:07:59-04:00"
---

# Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms/ +lsi / {lng)

## Context & Root Cause Discovery
During Phase 1 pre-training, the model was exported to GGUF format. When Unsloth/llama.cpp processes GGUF vocabulary export, it prepends a header/dummy token (e.g. `Q\x02\x00\x00\x00\x00\x00`) at index 0, causing all subsequent vocabulary tokens and embedding weights to shift by exactly +1 (e.g. standard token `i` maps to GGUF token `i+1`).

When Notebook E and Notebook F loaded this base model using Unsloth but loaded a "clean" tokenizer directly from `"unsloth/Qwen2.5-3B-Instruct"`:
1. **Misalignment:** The tokenizer used standard token mappings, while the model's embedding matrix and language modeling head weights were shifted by +1.
2. **Special Tokens Shift:** `<|im_start|>` (standard ID `151644`) mapped to GGUF ID `151645`, and `<|im_end|>` (standard ID `151645`) mapped to GGUF ID `151646`.
3. **Turn Terminator Failure:** During inference, the model generated GGUF token ID `151646` (`<|im_end|>`), but the standard tokenizer decoded it as `<|object_ref_start|>` or failed to recognize it as a stop token.
4. **Junk Token Generation:** At paragraph and turn breaks, the model generated shifted tokens:
   - GGUF `\n\n` (ID `272`) -> decoded by standard tokenizer as `_Parms` (standard ID `78933` / GGUF `78934` `.adjust`).
   - GGUF `\n` (ID `199`) -> decoded as `+lsi` (standard ID `70237` / GGUF `70238` `igrants`).
   - GGUF `唾` (ID `117975`) -> decoded as `具有战士` (standard ID `117975` / GGUF `117976`).
   - GGUF ` preacher` (ID `88754`) -> decoded as `{lng` (standard ID `88754` / GGUF `88755`).

## Solution
Instead of forcing the clean `"unsloth/Qwen2.5-3B-Instruct"` tokenizer, Notebook E and Notebook F have been patched to load the tokenizer directly from the base model folder (`MODEL_NAME` / `BASE_MODEL_NAME`):
```python
# In Notebook E
tokenizer = [REDACTED_SECRET](MODEL_NAME)

# In Notebook F
tokenizer = [REDACTED_SECRET](BASE_MODEL_NAME)
```
Since the tokenizer in the base model folder was saved during the Phase 1 GGUF export, its `tokenizer.json` contains the exact same shifted vocabulary as the model weights. Loading it aligns the tokenizer and the model embeddings 100% perfectly, resolving the runaway generations, junk character emissions, and paragraph-break corruption.
