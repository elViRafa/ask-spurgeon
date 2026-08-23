---
store_path: bugs/lora-frozen-embeddings-special-tokens
title: "Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA"
summary: "Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA"
priority: medium
tags: [bugs, lora, embeddings, lm_head, special-tokens, unsloth]
schema_version: 1.3
last_updated: "2026-06-15T08:56:50-04:00"
review_status: stale
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

## Update: PEFT Wrapper Attribute Lookup Error during Inference Copying (2026-06-15)
### Problem
Although we successfully copied the pre-trained special token embedding weights during training (Notebook E), the base model weights at inference time (Notebook F) remained untrained because the LoRA adapter does not save frozen embedding weights.
To resolve this, we added a copying step at inference time in Notebook F. However, because `FastLanguageModel.from_pretrained` returns a `PeftModelForCausalLM` when loading an adapter (unlike a base model which returns `Qwen2ForCausalLM` directly), the attribute lookup `model.model.embed_tokens` raised an `AttributeError` during evaluation:
`AttributeError: 'Qwen2ForCausalLM' object has no attribute 'embed_tokens'`

This crashed the copy cell in Notebook F at line 251, leaving the weights of `<|im_end|>` completely untrained. Since the copy crashed, the model fell back to generating the next most probable tokens (`_Pods of grace, indeed!`) at turn boundaries instead of the stop token `<|im_end|>`.

### Fix
Patched both Notebook E and Notebook F to use Hugging Face's standard and robust methods:
- `model.get_input_embeddings().weight` instead of `model.model.embed_tokens.weight`
- `model.get_output_embeddings().weight` instead of `model.lm_head.weight`

These methods correctly delegate attribute lookup through the `PeftModel` wrappers, ensuring the special token weights are successfully copied at both training and inference time.
