---
store_path: pretraining/dataset-preparation
title: "Pretraining Step 6 — Dataset Preparation (Notebook A) Plan"
summary: "Pretraining Step 6 — Dataset Preparation (Notebook A) Plan"
priority: medium
tags: [pretraining, dataset, kaggle, huggingface]
schema_version: 1.3
last_updated: "2026-06-06T19:38:20-04:00"
---

Documents the environment settings, directory layout, code cells, and verification diagnostics for Step 6: Dataset Preparation of Phase 1 of the Charles Spurgeon continued pretraining pipeline.

### Details:
- **Notebook A (`data_prep.ipynb`)** runs on CPU-only (accelerator: None) with Internet ON to preserve GPU quota.
- Ingests the cleaned training set `spurgeon_train.txt` and holdout set `spurgeon_holdout.txt` from `/kaggle/input/`.
- Splits text documents on the `<|endoftext|>` marker, filtering out short segments (< 200 chars).
- Partitions the training corpus into a 99% train and 1% validation split (`train_test_split`).
- Saves the resulting binary datasets (`spurgeon_dataset` and `spurgeon_holdout_dataset`) to `/kaggle/working/` using `save_to_disk`.
- The output datasets are versioned as a private Kaggle dataset named `spurgeon-cpt-dataset` to be mounted as input for Notebook B (`training.ipynb`).
