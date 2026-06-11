---
store_path: bugs/unsloth-embedding-offload-readonly
title: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
summary: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
priority: high
tags: [bugs, unsloth, embeddings, lora, kaggle, offloading]
schema_version: 1.3
last_updated: "2026-06-11T10:46:08-04:00"
---

# Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem

## Context
When training a custom LoRA adapter where `embed_tokens` and `lm_head` are targeted in `FastLanguageModel.get_peft_model()`, Unsloth automatically offloads the base model's input embeddings to disk to save VRAM.
By default, the offload directory is named `_unsloth_temporary_saved_buffers` and is created in the current working directory.

## Problem
When running the training notebook on Kaggle via Papermill or automated run scripts, the current working directory may reside in a read-only area (e.g. `/kaggle/input/...` or the home folder).
This causes `torch.save` inside `offload_to_disk` to crash with:
`RuntimeError: [enforce fail at inline_container.cc:743] . open file failed with strerror: Read-only file system`

Additionally, standard environment variable checks like `"KAGGLE_KERNEL_RUN_TYPE" in os.environ` can sometimes evaluate to `False` inside batch runs or specific runner environments on Kaggle, failing to assign the writeable `/tmp` path correctly.

## Fix
In `fine_tuning/notebooks/E_qa_training.ipynb`:
1. Configured robust environment checks for Kaggle and Colab:
```python
IS_KAGGLE = "KAGGLE_KERNEL_RUN_TYPE" in os.environ or os.path.exists("/kaggle")
IS_COLAB = "COLAB_GPU" in os.environ or os.path.exists("/content")
```
2. Unconditionally set `TEMP_LOCATION` using Python's standard `tempfile.gettempdir()`, which returns the system's guaranteed writeable temp directory on any platform (e.g. `/tmp` on Linux/Kaggle/Colab and AppData Temp directory on Windows):
```python
import tempfile
TEMP_LOCATION = os.path.join(tempfile.gettempdir(), "unsloth_temp")
```
3. Guaranteed the directory exists using `os.makedirs(TEMP_LOCATION, exist_ok=True)`.
4. Passed `temporary_location=TEMP_LOCATION` explicitly to `FastLanguageModel.get_peft_model()`:
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
This guarantees that Unsloth offloaded buffers are saved under a writeable system temp folder on all execution targets (Kaggle VMs, Colab VMs, and local Windows/Linux development environments).
