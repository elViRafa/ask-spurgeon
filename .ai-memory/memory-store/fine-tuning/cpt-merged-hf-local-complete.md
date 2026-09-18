---
store_path: fine-tuning/cpt-merged-hf-local-complete
title: "Local complete CPT merged HF"
summary: "Complete CPT merge HF is now local (scp from Vast instance `50011937`)"
priority: low
tags: [cpt, sft, vast, merged-hf]
schema_version: 1.3
last_updated: "2026-09-06T02:32:53-04:00"
---

## Status (2026-09-06)

Complete CPT merge HF is now local (scp from Vast instance `50011937`).

- **Local path:** `fine_tuning/kaggle/vast_sft_gate0/theology_cpt_v2_merged_hf`
- **Remote source:** `/workspace/theology_cpt_v2_merged_hf` on Vast `50011937` (ssh `root@75.129.99.99:5250`)
- **Verified:** yes — sizes match remote:
  - `config.json` 3344
  - `tokenizer_config.json` 7163
  - `model-00001-of-00002.safetensors` 4972947968
  - `model-00002-of-00002.safetensors` 4105672464
  - `model.safetensors.index.json` 66236
  - total ~8.47 GB
- Incomplete local copy moved aside to `theology_cpt_v2_merged_hf.incomplete.bak`
- Runpod incomplete path `fine_tuning/kaggle/runpod_sft_gate0/theology_cpt_v2_merged_hf` left unchanged
- HF still has LoRA adapter only, not merged HF
- Training/instance not interrupted
