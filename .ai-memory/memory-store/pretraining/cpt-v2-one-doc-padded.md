---
store_path: pretraining/cpt-v2-one-doc-padded
title: "CPT v2 one-doc padded — Kaggle dead; Runpod next"
summary: "**2026-08-26:** B **v13 ERROR** (`DeadKernelError` after ckpt-100)"
priority: high
tags: [cpt, packing, gdn, qwen35, kaggle, runpod]
schema_version: 1.3
last_updated: "2026-08-26T23:15:36-04:00"
evidence: [continued_pretrain/CPT_V2_KAGGLE_STATUS.md, continued_pretrain/scripts/_gen_sota_notebooks.py]
---

# One-doc padded rows — Kaggle v13/v14 ERROR; Runpod uses the same pack

**2026-08-26:** B **v13 ERROR** (`DeadKernelError` after ckpt-100). B **v14 ERROR** (resume missed, same death window). **STOP Kaggle.** Next GPU path is Runpod, not another T4 notebook.

## Config (generator + `train_cpt_sota.py`)
- `PACKING_MODE=one_doc_padded` — one doc or 2048 window per row; never concat two docs
- `PAD_TO_MAX=False`
- `LORA_GDN=True` → `in_proj_qkv`, `in_proj_z`, `out_proj` (never `in_proj_a`/`in_proj_b`)
- `GPU_PROFILE` **auto** (t4 4-bit / ampere bf16 on sm_80+)
- After pack: `MAX_STEPS = PACKED_EPOCH_STEPS` (v13: 10779 rows → **674** steps)
- Abort if `eval_spurgeon_loss` at 50 > 25 (encoded callback)
- D2 FAIL if `multi_doc_rows > 0`

## v13 evidence
D1/D2 PASS (`multi_doc_rows=0`, 10779 rows, tokens_per_epoch_est ≈14.8M). Only eval @25 ≈2.335 before kernel death. No step-50 eval on T4.
