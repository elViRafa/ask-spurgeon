---
store_path: pretraining/notebook-structure
title: "Pretraining Step 3 — Kaggle Notebook Structure"
summary: "Pretraining Step 3 — Kaggle Notebook Structure"
priority: medium
tags: [pretraining, kaggle, notebook, setup]
schema_version: 1.3
last_updated: "2026-06-06T19:30:22-04:00"
---

Overview of Kaggle Notebooks layout for Spurgeon's Qwen2.5-3B continued pretraining. Work is split across three notebooks (A: data prep, B: training, C: evaluation/export) to circumvent Kaggle's 9-hour execution limits. Notebook B details PEFT QLoRA configuration, memory-saving parameters (lora_dropout=0, batch size 2, gradient accumulation 8, packing=True), and includes strict rules for trainer epoch incrementing when resuming checkpoints from input datasets. Notebook C handles holdout perplexity and qualitative style evaluation.
