---
store_path: failures/peft-sft-lora-merge-5b98bf291d
title: "PEFT SFT LoRA merge onto Qwen3.5 CPT-merged HF silently no-ops when loaded as Qw"
summary: "PEFT SFT LoRA merge onto Qwen3.5 CPT-merged HF silently no-ops when loaded as Qwen3_5ForConditionalGeneration (config architectures) because adapter keys use model.layers.* (CausalLM training) but Con"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-06T20:04:46-04:00"
occurrences: 1
error_signature: "peft sft lora merge onto qwen<n>.<n> cpt-merged hf silently no-ops when loaded as qwen<n>_<n>forconditionalgeneration (config architectures) because adapter keys use model.layers.* (causallm training) but condgen expects model.language_model.layers.*; peft warns missing adapter keys and merge_and_un"
---

## Occurrence 1 — 2026-09-06T20:04:46-04:00

**Error:**
PEFT SFT LoRA merge onto Qwen3.5 CPT-merged HF silently no-ops when loaded as Qwen3_5ForConditionalGeneration (config architectures) because adapter keys use model.layers.* (CausalLM training) but CondGen expects model.language_model.layers.*; PEFT warns missing adapter keys and merge_and_unload saves base unchanged.

**Fix:**
Always merge SFT with AutoModelForCausalLM (Qwen3_5ForCausalLM paths). Fail closed if peft state key count << adapter tensors. See merge_sft_lora.py.
