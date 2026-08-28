---
store_path: failures/nameerror-name-val-is-1276dd9806
title: "NameError: name '_is_hf_holdout_root' is not defined. Did you mean: 'is_hf_holdo"
summary: "NameError: name '_is_hf_holdout_root' is not defined"
priority: medium
tags: [cpt, failure, fix, nameerror, qwen35, runpod]
schema_version: 1.3
last_updated: "2026-08-26T23:34:20-04:00"
occurrences: 1
error_signature: "nameerror: name <val> is not defined. did you mean: <val>? in train_cpt_sota.py after pack (max_steps <n> -> <n>). crashed before d<n><path> load."
failure_key: nameerror
---

## Occurrence 1 — 2026-08-26T23:34:20-04:00

**Error:**
NameError: name '_is_hf_holdout_root' is not defined. Did you mean: 'is_hf_holdout_root'? in train_cpt_sota.py after pack (MAX_STEPS 476 -> 674). Crashed before D2/holdout load.

**Fix:**
Typo in _gen_sota_notebooks.py B cell: called _is_hf_holdout_root instead of is_hf_holdout_root (cpt_runtime helper). Fixed generator + train_cpt_sota.py. Relaunch on Runpod.
