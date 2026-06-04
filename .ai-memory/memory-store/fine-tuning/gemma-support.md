---
store_path: fine-tuning/gemma-support
title: "Gemma 2 Fine-Tuning Support"
summary: "Gemma 2 fine-tuning support scripts and configs."
priority: medium
tags: [gemma2, fine-tuning, ollama]
schema_version: 1.3
last_updated: "2026-06-03T17:19:45-04:00"
summary_hash: c6e3f7de5ff6c7d4b7d2b0101970513d
---

# Gemma 2 Fine-Tuning Support

Parameterized scripts and config files to support fine-tuning Gemma 2 models (like unsloth/gemma-2-9b-it-bnb-4bit) matching local gemma4 configurations.

- Updated train_spurgeon_qlora.py to read base model and chat template (gemma2) via CLI args.
- Configured launch_training.py to pass parameters dynamically from configuration files.
- Added train_config_gemma.json configuration file.
- Created Spurgeon_Gemma2_Training_Colab.ipynb for Colab training and Modelfile.gemma for Ollama import.
