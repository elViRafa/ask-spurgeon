---
store_path: bugs/gemma4-chat-template-fix
title: "Gemma 4 Chat Template Processor Fix"
summary: "Gemma 4 Chat Template Processor Fix"
priority: medium
tags: [gemma4, chat-template, bugfix, unsloth]
schema_version: 1.3
last_updated: "2026-06-05T12:50:30-04:00"
---

# Bug Fix: Gemma 4 Multimodal Chat Template Processor Error

## Problem
When training or doing inference with Gemma 4 (`unsloth/gemma-4-E4B-it` or `unsloth/gemma-4-12b-it-bnb-4bit`) in Unsloth / transformers, the `from_pretrained` method returns a `Gemma4Processor` instead of a standard text `Tokenizer` because Gemma 4 has multimodal inputs.

When `apply_chat_template(conversation, tokenize=True)` is called on the processor, the processor mixin tries to extract multimodal content (images/videos) by looping over `message["content"]`:
```python
visuals = [content for content in message["content"] if content["type"] in ["image", "video"]]
```
For standard text training and inference datasets where `content` is a string (e.g. `{"role": "user", "content": "question"}`), this loops over characters of the string. Attempting to access `content["type"]` on character strings fails with:
`TypeError: string indices must be integers, not 'str'`.

## Solution
To bypass the processor's multimodal parsing for text-only inputs, we retrieve and use the underlying text tokenizer's chat template directly:
```python
raw_tokenizer = getattr(tokenizer, "tokenizer", tokenizer)
inputs = raw_tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt"
).to("cuda")
```
This has been applied to the following training files:
1. `[REDACTED_SECRET].ipynb` (Inference Cell & Dataset Preparation)
2. `[REDACTED_SECRET].ipynb` (Inference Cell & Dataset Preparation)
3. `fine_tuning/scripts/train_spurgeon_qlora.py` (Dataset formatting function)
