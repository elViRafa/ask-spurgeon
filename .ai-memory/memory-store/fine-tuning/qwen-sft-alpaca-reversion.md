---
store_path: fine-tuning/qwen-sft-alpaca-reversion
title: "Reverting Custom Model, Weight Copying, and ChatML in Qwen 2.5 SFT"
summary: "Reverting Custom Model, Weight Copying, and ChatML in Qwen 2.5 SFT"
priority: medium
tags: [finetuning, qwen2.5, unsloth, alpaca, reversion]
schema_version: 1.3
last_updated: "2026-06-15T09:29:56-04:00"
---

# Reverting Custom Base Model, Weight Copying, and ChatML Alignment in SFT Notebook

## Context
Initially, the SFT notebook (`Qwen_2_5_+_Unsloth_2x_faster_finetuning.ipynb`) was adapted to load a custom pre-trained GGUF-shifted base model (`spurgeon_phase1_merged_hf`) and align ChatML formatting with the Qwen-2.5 Instruct model by copying embedding weights.

## Reversion Decision
The user requested to revert these changes. The notebook was re-configured to:
1. Load the standard `"unsloth/Qwen2.5-7B"` base model instead of the custom phase 1 merged model.
2. Remove the Instruct model loading and special token weights copying logic entirely.
3. Revert ChatML formatting to the standard Alpaca prompt template format.

## Implementation Details
- **Dataset Preprocessing:** The dataset (`spurgeon_qa_train_final.jsonl`'s `messages` key) is parsed:
  - System messages are combined with `QUESTION:` as the **Instruction**.
  - `CONTEXT:` is extracted as the **Input**.
  - Assistant responses are mapped to the **Response**.
- **SFT Trainer Delimiters:** The `train_on_responses_only` function masks the labels up to `"### Response:\n"` to focus training only on response generations.
