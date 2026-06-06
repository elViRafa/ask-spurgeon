# Continued Pretraining Setup

This directory contains the pipeline for **Phase 1: Spurgeon Continued Pretraining**. The goal of this phase is to perform domain adaptation of a base language model (Qwen2.5-3B) on the sermons of Charles Haddon Spurgeon.

## Directory Structure

```
continued_pretrain/
├── README.md
├── scripts/
│   ├── 01_inventory.py          # Step 1.1 — Count/audit raw corpus
│   ├── 02_inspect_samples.py    # Step 1.2 — Sample random files to inspect formatting
│   ├── 03_flag_anomalies.py     # Step 1.3 — Detect stubs (<3K chars) and multi-sermon files (>80K chars)
│   ├── 04_holdout_split.py      # Step 1.4 — Sample 50 hold-out evaluation sermons
│   └── 05_build_corpus.py       # Step 2   — Clean and compile training/holdout sets
├── notebooks/                   # Jupyter Notebooks for Kaggle execution
└── configs/                     # Configuration files for training
```

## Running Step 1: Data Collection

These scripts should be run locally in the project root to audit and prepare the dataset before training:

1. **Inventory raw corpus:**
   ```bash
   python continued_pretrain/scripts/01_inventory.py
   ```

2. **Inspect raw format samples:**
   ```bash
   python continued_pretrain/scripts/02_inspect_samples.py
   ```

3. **Flag anomalies (stubs or concatenated files):**
   ```bash
   python continued_pretrain/scripts/03_flag_anomalies.py
   ```

4. **Generate holdout split:**
   ```bash
   python continued_pretrain/scripts/04_holdout_split.py
   ```
