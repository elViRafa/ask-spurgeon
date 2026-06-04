---
store_path: decisions/gemma4-finetuning
title: "Gemma 4 Fine-Tuning Transition"
summary: "Guides the upgrade of fine-tuning pipelines from Gemma 2 to the efficient, newer Gemma 4 12B model."
priority: medium
tags: [gemma4, finetuning, decisions]
schema_version: 1.3
last_updated: "2026-06-04T10:24:33-04:00"
summary_hash: 58d9e4c42d7f3c068e76867ebfc3458f
---

# Decision: Upgrade Fine-Tuning Pipeline to Gemma 4 12B

We have transitioned the Spurgeon fine-tuning configurations, Google Colab notebooks, and Ollama templates from Gemma 2 9B to Google DeepMind's newly released Gemma 4 12B model (`unsloth/gemma-4-12b-it-bnb-4bit`).

## Rationale
- Gemma 4 is Google's newest open frontier-tier model family.
- The 12B variant utilizes a highly efficient "encoder-free" architecture that improves latency and multimodal processing capability.
- Unsloth provides optimized 4-bit configurations for fast, memory-efficient LoRA tuning, fitting well within free Google Colab T4 hardware limits.

## Configuration Details
- **Base model**: `unsloth/gemma-4-12b-it-bnb-4bit`
- **Chat Template**: `gemma-4`
- **Turn boundary sequences**: `<start_of_turn>` and `<end_of_turn>`
