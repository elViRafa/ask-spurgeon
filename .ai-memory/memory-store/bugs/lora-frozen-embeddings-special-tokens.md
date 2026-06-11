---
store_path: bugs/lora-frozen-embeddings-special-tokens
title: "Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA"
summary: "Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA"
priority: high
tags: [bugs, lora, embeddings, lm_head, special-tokens, unsloth]
schema_version: 1.3
last_updated: "2026-06-11T09:21:00-04:00"
---

# Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA

## Context
During instruction fine-tuning (Phase 2), we added special tokens `<|im_start|>` and `<|im_end|>` to the vocabulary and called `model.resize_token_embeddings(len(tokenizer))` to adapt the embedding layers.
By default, standard LoRA only targets attention projection weights and MLP weights, leaving `embed_tokens` and `lm_head` frozen.
When new tokens are added to the vocabulary, `model.resize_token_embeddings()` initializes the new rows in the embedding matrix and LM head to random noise or zero.

## Problem
Because `embed_tokens` and `lm_head` were frozen, SFT training could not learn the representations or output projections for the new special tokens. The weights for `<|im_end|>` remained random noise/zero.
Consequently, at inference time, the model could not generate the stop token `<|im_end|>` because its output projection was random noise. Instead, it generated other tokens (which decoded to `"vinfos"` or other junk text) or failed to stop, causing runaway generations.

## Fix
In Notebook E (`fine_tuning/notebooks/E_qa_training.ipynb`), configured `FastLanguageModel.get_peft_model()` to target `embed_tokens` and `lm_head` in LoRA:
```python
model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                    "embed_tokens", "lm_head"], # Train embeddings and language modeling head to learn special tokens
    lora_alpha=32,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)
```
This enables the SFT training to optimize the embeddings and LM head projections for `<|im_start|>` and `<|im_end|>`, allowing the model to learn a clean stop token.
