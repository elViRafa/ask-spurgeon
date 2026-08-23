---
store_path: pretraining/cpt-v2-ready-for-kaggle
title: "CPT v2 ready for Kaggle (post local pipeline)"
summary: "CPT v2 ready for Kaggle (post local pipeline)"
priority: high
tags: [pretraining, cpt, kaggle, m1, mix, v2]
schema_version: 1.3
last_updated: "2026-07-13T10:40:05-04:00"
evidence: [continued_pretrain/KAGGLE_RUNBOOK_V2.md, continued_pretrain/data/M1_BASE_MODEL_GATE.md, continued_pretrain/data/theology_mix_manifest.json]
---

# CPT v2 — ready for Kaggle (2026-07-13)

## Local pipeline complete

- Multi-source mix with chunking ≤7k, share targets, 10% PD general replay (Gutenberg classics).
- Shares ~ spurgeon 40.5% / puritan 41% / confession 5% / bible 3.6% / general 10%.
- D3: ~8.2M tokens (gpt2 sample ratio); max_doc 7000; 0 docs >8k.
- Holdouts: spurgeon/puritan/confession/general non-empty; Heidelberg + Belgic in holdouts_manual.
- MCQ: 50 WSC + 42 Heidelberg.
- Package: `12_package_kaggle_corpus.py` → zip for dataset upload.
- Runbook: `continued_pretrain/KAGGLE_RUNBOOK_V2.md`.

## M1 (partial pass)

- `Qwen/Qwen3.5-4B-Base` + `unsloth/Qwen3.5-4B-Base` exist.
- **`tie_word_embeddings=true`** → notebooks default `TRAIN_LM_HEAD=False`.
- Hybrid `qwen3_5` (linear_attention + full_attention + vision_config) — **must prove Unsloth train on T4**; fallback Qwen2.5-3B.
- Details: `data/M1_BASE_MODEL_GATE.md`.

## Remaining (operator / Kaggle only)

1. Upload corpus zip as `theology-cpt-corpus`
2. A_sota → dataset `theology-cpt-dataset`
3. B_sota session 1: D1/D2/D4 + s/step + MAX_STEPS; pin Unsloth after success
4. Train 1 epoch; C_sota eval; merge only if §5 passes
