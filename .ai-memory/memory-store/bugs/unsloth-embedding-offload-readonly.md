---
store_path: bugs/unsloth-embedding-offload-readonly
title: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
summary: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
priority: high
tags: [bugs, unsloth, embeddings, lora, kaggle, offloading]
schema_version: 1.3
last_updated: "2026-06-11T14:26:32-04:00"
---

# Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem

## Context
When training a custom LoRA adapter where `embed_tokens` and `lm_head` are targeted in `FastLanguageModel.get_peft_model()`, Unsloth automatically offloads the base model's input embeddings to disk to save VRAM.
By default, the offload directory is named `_unsloth_temporary_saved_buffers` and is created in the current working directory.

## Problem
When running the training notebook on Kaggle via Papermill or automated run scripts, the current working directory may reside in a read-only area (e.g. `/kaggle/input/...` or the home folder).
Additionally, on certain Kaggle container executions, the system `/tmp` directory is sandbox-restricted or mounted read-only.
This causes `torch.save` inside `offload_to_disk` to crash with:
`RuntimeError: [enforce fail at inline_container.cc:743] . open file failed with strerror: Read-only file system`

Furthermore, even when passing a writeable `TEMP_LOCATION` (like `/kaggle/working/unsloth_temp`), Unsloth's `offload_to_disk` constructs the target file location using:
`file_location = os.path.join(temporary_location, model.config._name_or_path)`

Because the base model is loaded from an absolute local path on Kaggle (`MODEL_NAME = "/kaggle/input/datasets/..."`), the `model.config._name_or_path` attribute holds this absolute path. In Python/Unix, when joining paths where the second path is absolute, `os.path.join` discards the first path entirely. As a result, the target path resolved directly back to the read-only `/kaggle/input/` directory, causing the same `Read-only file system` crash.

## Fix
In `fine_tuning/notebooks/E_qa_training.ipynb`:
1. Configured robust environment checks for Kaggle and Colab:
```python
IS_KAGGLE = "KAGGLE_KERNEL_RUN_TYPE" in os.environ or os.path.exists("/kaggle")
IS_COLAB = "COLAB_GPU" in os.environ or os.path.exists("/content")
```
2. Assigned default temp locations pointing to verified writeable workspaces: `/kaggle/working/unsloth_temp` on Kaggle, and `/content/unsloth_temp` on Colab.
3. Implemented an active writeability check fallback block that attempts to write a dummy file to several directory candidates and dynamically binds `TEMP_LOCATION` to the first path that successfully accepts file writes:
```python
# Robust fallback mechanism to guarantee write permission
writeable_found = False
for path_option in [TEMP_LOCATION, "/kaggle/working/unsloth_temp", "/content/unsloth_temp", "_unsloth_temporary_saved_buffers"]:
    try:
        os.makedirs(path_option, exist_ok=True)
        # Test writing a dummy file
        test_file = os.path.join(path_option, "test_write.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        TEMP_LOCATION = path_option
        writeable_found = True
        break
    except Exception:
        continue

if not writeable_found:
    raise RuntimeError("Could not find any writeable directory for temporary offloading!")
```
4. Added a critical patch in Cell 7 before calling `FastLanguageModel.get_peft_model()` to unconditionally set `model.config._name_or_path = "model"`:
```python
if getattr(model, "config", None) is not None:
    model.config._name_or_path = "model"
    print("Patched model.config._name_or_path to relative path: 'model'")
```
5. Passed `temporary_location=TEMP_LOCATION` explicitly to `FastLanguageModel.get_peft_model()`.

This guarantees that Unsloth offloaded buffers are saved under a directory where the Python process has active write permissions on all execution targets (Kaggle VMs, Colab VMs, and local Windows/Linux development environments), bypassing the absolute path join bug.
