---
store_path: failures/assertionerror-s-n-fail-b0de52ddcb
title: "AssertionError: S3 FAIL: user turn leaked into labels in train_sft_sota.py _trai"
summary: "AssertionError: S3 FAIL: user turn leaked into labels in train_sft_sota.py _train_peft after weighted SFT S8 dataprep"
priority: medium
tags: [failure, fix, mask, s3, sft, truncation, weighted]
schema_version: 1.3
last_updated: "2026-10-14T10:00:16-03:00"
occurrences: 1
error_signature: "assertionerror: s<n> fail: user turn leaked into labels in train_sft_sota.py _train_peft after weighted sft s<n> dataprep. sft_max_seq_length=<n>; trl truncates before mask; rag rows lose <|im_start|>assistant; _mask_assistant_labels fell back to training all tokens."
failure_key: assertionerror
---

## Occurrence 1 — 2026-10-14T10:00:16-03:00

**Error:**
AssertionError: S3 FAIL: user turn leaked into labels in train_sft_sota.py _train_peft after weighted SFT S8 dataprep. SFT_MAX_SEQ_LENGTH=2048; TRL truncates before mask; RAG rows lose <|im_start|>assistant; _mask_assistant_labels fell back to training all tokens.

**Fix:**
Set SFT_MAX_SEQ_LENGTH=4608 in sft_remote_train_s8_weighted.sh and sft_s8_weighted_plan.py (longest row 4330). Hardened _mask_assistant_labels to all -100 when marker missing; drop fully masked rows; S3 audit every row. Keep batch 1 / accum 16; OOM next knob LORA_RANK=16.
