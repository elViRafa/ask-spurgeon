---
store_path: bugs/unsloth-embedding-offload-readonly
title: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
summary: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
priority: high
tags: [bugs, unsloth, embeddings, lora, kaggle, offloading]
schema_version: 1.3
last_updated: "2026-06-11T10:00:40-04:00"
---

# Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem

## Context
When training a custom LoRA adapter where `embed_tokens` and `lm_head` are targeted in `FastLanguageModel.get_peft_model()`, Unsloth automatically offloads the base model's input embeddings to disk to save VRAM.
By default, the offload directory is named `_unsloth_temporary_saved_buffers` and is created in the current working directory.

## Problem
When running the training notebook on Kaggle via Papermill or automated run scripts, the current working directory may reside in a read-only area (e.g. `/kaggle/input/...` or the home folder).
This causes `torch.save` inside `offload_to_disk` to crash with:
`RuntimeError: [enforce fail at inline_container.cc:743] . open file failed with strerror: Read-only file system`

## Fix
In `fine_tuning/notebooks/E_qa_training.ipynb`:
1. Configured environment setup to define a writeable `TEMP_LOCATION` (using `/tmp/unsloth_temp` on Kaggle/Colab and `_unsloth_temporary_saved_buffers` locally).
2. Guaranteed the directory exists using `os.makedirs(TEMP_LOCATION, exist_ok=True)`.
3. Passed `temporary_location=TEMP_LOCATION` explicitly to `FastLanguageModel.get_peft_model()`:
```python
    model,
    r=LORA_RANK,
                    "embed_tokens", "lm_head"],
    lora_alpha=32,
    lora_dropout=0,
    bias="none",
    random_state=42,
    temporary_location=TEMP_LOCATION,
)
```
This forces Unsloth to save the offloaded weight buffers under `/tmp/unsloth_temp`, which is always writeable.
