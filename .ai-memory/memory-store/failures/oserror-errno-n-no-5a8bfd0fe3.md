---
store_path: failures/oserror-errno-n-no-5a8bfd0fe3
title: "OSError: [Errno 28] No space left on device on Kaggle /kaggle/working while pape"
summary: "OSError: [Errno 28] No space left on device on Kaggle /kaggle/working while papermill saved the notebook after checkpoint-75"
priority: medium
tags: [checkpoints, cpt, disk, failure, fix, kaggle]
schema_version: 1.3
last_updated: "2026-08-26T01:22:27-04:00"
occurrences: 1
error_signature: "oserror: [errno <n>] no space left on device on kaggle <path> while papermill saved the notebook after checkpoint-<n>. embed lora modules_to_save plus optimizer.pt x save_total_limit=<n> filled the ~<n>gb working disk."
failure_key: oserror
---

## Occurrence 1 — 2026-08-26T01:22:27-04:00

**Error:**
OSError: [Errno 28] No space left on device on Kaggle /kaggle/working while papermill saved the notebook after checkpoint-75. Embed LoRA modules_to_save plus optimizer.pt x SAVE_TOTAL_LIMIT=4 filled the ~20GB working disk.

**Fix:**
SAVE_TOTAL_LIMIT=1 and save_only_model=True so checkpoints skip optimizer.pt. Print disk free at train start.
