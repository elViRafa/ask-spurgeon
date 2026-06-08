---
store_path: pretraining/eval-and-export
title: "Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)"
summary: "Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)"
priority: medium
tags: [pretraining, schedule, evaluation, export, notebook-c, perplexity]
schema_version: 1.3
last_updated: "2026-06-08T07:34:40-04:00"
---

# Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)

Following the successful execution of Notebook B (Epoch 1 & 2) up to step 432:
1. **Pretraining Schedule Updated:** Timeline has been updated to bypass Epoch 3 and proceed directly to evaluation and merge. v2 of the private Kaggle dataset `spurgeon-training-run-1` carries the `checkpoint-432` weights and files forward.
2. **Notebook C Plan created:** Step 9 details the evaluation requirements (1x T4 GPU, Internet ON), input dataset mounts, loading the adapter via Unsloth's native `FastLanguageModel.from_pretrained()`, computing length-weighted perplexity on the 50-sermon holdout dataset, executing qualitative prompts, and exporting the final Phase 1 LoRA adapter weights.
3. **Jupyter Notebook Template created:** The evaluation template has been created at `continued_pretrain/notebooks/C_eval_and_merge.ipynb`.
