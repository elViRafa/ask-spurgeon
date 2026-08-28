---
store_path: failures/unslothtrainer-runtimeerror-you-must-b72157a8b4
title: "UnslothTrainer RuntimeError: You must specify a formatting_func when MANUAL_PACK"
summary: "UnslothTrainer RuntimeError: You must specify a formatting_func when MANUAL_PACK train has input_ids but eval_dataset dict still has text columns"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-08-25T00:45:48-04:00"
occurrences: 1
error_signature: "unslothtrainer runtimeerror: you must specify a formatting_func when manual_pack train has input_ids but eval_dataset dict still has text columns"
failure_key: runtimeerror
---

## Occurrence 1 — 2026-08-25T00:45:48-04:00

**Error:**
UnslothTrainer RuntimeError: You must specify a formatting_func when MANUAL_PACK train has input_ids but eval_dataset dict still has text columns

**Fix:**
Tokenize eval holdout buckets to input_ids/attention_mask/labels (truncate to MAX_SEQ_LENGTH) before UnslothTrainer when MANUAL_PACK=True in _gen_sota_notebooks.py
