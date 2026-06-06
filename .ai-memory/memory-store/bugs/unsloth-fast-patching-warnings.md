---
store_path: bugs/unsloth-fast-patching-warnings
title: "Unsloth Training Warnings & Fast Patching Resolution"
summary: "Unsloth Training Warnings & Fast Patching Resolution"
priority: medium
tags: [unsloth, lora, gemma4, bugfix]
schema_version: 1.3
last_updated: "2026-06-06T12:04:12-04:00"
---

# Unsloth Training Warnings & Fast Patching Resolution

## 1. LoRA Dropout Performance Warning
* **Problem**: Setting `lora_dropout` to any non-zero value (e.g., `0.05`) in Unsloth triggers the following warning:
  ```
  Unsloth: Dropout = 0 is supported for fast patching. You are using dropout = 0.05.
  Unsloth will patch all other layers, except LoRA matrices, causing a performance hit.
  ```
* **Implication**: Unsloth uses highly optimized custom CUDA kernels for LoRA layers which require `lora_dropout = 0`. Setting it higher causes Unsloth to fall back to the slower default PEFT implementation for the LoRA adapter matrices, losing significant training speedup and VRAM efficiency.
* **Resolution**: Updated all configurations and notebooks to use `lora_dropout = 0` (or `0.0`), enabling full Unsloth optimization.

## 2. Gemma 4 Audio Tower Hook Registration Warning
* **Problem**: Loading multimodal Gemma 4 variants (such as `unsloth/gemma-4-E4B-it` or `unsloth/gemma-4-12b-it`) in Unsloth produces the initialization warning:
  ```
  [unsloth_zoo.log|WARNING]Unsloth: Failed to register input-embedding hook for `model.base_model.model.model.audio_tower`: `get_input_embeddings` not auto‑handled for Gemma4AudioModel; please override in the subclass.. Falling back to pre-forward hook.
  ```
* **Implication**: Gemma 4 is a multimodal model containing audio components (`audio_tower`/`Gemma4AudioModel`). Unsloth's auto-patcher does not natively handle embedding hooks for the audio tower and falls back to a standard pre-forward hook.
* **Status**: This warning is expected, benign, and can be safely ignored. For text-only fine-tuning tasks (such as Spurgeon style-transfer training), the audio tower is completely inactive and does not receive input sequences, so the fallback pre-forward hook has zero impact on training correctness or stability.
