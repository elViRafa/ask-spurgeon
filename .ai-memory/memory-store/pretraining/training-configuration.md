---
store_path: pretraining/training-configuration
title: "Pretraining Step 7 — Training Configuration (Notebook B) Plan"
summary: "Pretraining Step 7 — Training Configuration (Notebook B) Plan"
priority: medium
tags: [pretraining, training, lora, qlora, kaggle, unsloth]
schema_version: 1.3
last_updated: "2026-06-06T20:59:08-04:00"
---

Documents the GPU settings, VRAM budget, hyperparameter configurations, and resumption logic for Step 7: Training Configuration of Phase 1 of the Charles Spurgeon continued pretraining pipeline.

### Details:
- **Notebook B (`training.ipynb`)** runs on 1x T4 GPU (16GB VRAM) with Internet ON.
- VRAM is budgeted carefully (~7.55 GB usage, leaving ~8.45 GB headroom) to eliminate any OOM risk.
- Pinned installation of `unsloth[kaggle-new]` is used; manual dependency upgrades are strictly prohibited.
- Configures SFTTrainer with sequence packing (`packing = True`) at context length 2048 to prevent compute waste.
- Optimizer set to `adamw_8bit` with peak learning rate 2e-4 and cosine decay.
- Limits saved checkpoints to `save_total_limit = 3` to respect Kaggle's 20GB disk limit.
- Handles cross-session checkpoint resumption by dynamically incrementing `num_train_epochs` to prevent SFTTrainer immediate-exit bugs.
