---
store_path: failures/unslothtrainingarguments-typeerror-sftconfig-unexpected-652ebfdef4
title: "UnslothTrainingArguments TypeError: SFTConfig unexpected keyword max_seq_length "
summary: "UnslothTrainingArguments TypeError: SFTConfig unexpected keyword max_seq_length (TRL 0.24)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-22T10:36:31-03:00"
occurrences: 1
error_signature: "unslothtrainingarguments typeerror: sftconfig unexpected keyword max_seq_length (trl <n>.<n>)"
failure_key: typeerror
---

## Occurrence 1 — 2026-09-22T10:36:31-03:00

**Error:**
UnslothTrainingArguments TypeError: SFTConfig unexpected keyword max_seq_length (TRL 0.24)

**Fix:**
TRL 0.24 renamed max_seq_length to max_length. train_cpt_sota.py now remaps on TypeError; vast_cpt_s7_remote_continue_b.sh pins trl>=0.18,<0.24.
