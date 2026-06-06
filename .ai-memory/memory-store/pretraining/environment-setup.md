---
store_path: pretraining/environment-setup
title: "Pretraining Step 5 — Environment Setup & Configurations"
summary: "Pretraining Step 5 — Environment Setup & Configurations"
priority: medium
tags: [pretraining, environment, kaggle, config, secrets]
schema_version: 1.3
last_updated: "2026-06-06T19:35:50-04:00"
---

Execution configurations and dependency management rules for continued pretraining on Kaggle Free Tier. Guidelines specify toggling Internet ON, choosing None accelerator for Notebook A (Data Prep) to conserve quota, and selecting 1x T4 GPU for Notebook B/C. Installation relies solely on `unsloth[kaggle-new]` package pulling from GitHub, with a strict warning against manual upgrades of transformers/trl/peft to avoid breaking CUDA Triton kernels. Detailed setup includes programmatic Hugging Face token authentication via Kaggle Secrets (HF_TOKEN) and optional Weights & Biases training logs tracking (WANDB_API_KEY).
