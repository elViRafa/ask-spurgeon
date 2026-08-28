---
store_path: failures/b-training-sota-earlystopping-4edd127cc9
title: "B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_lo"
summary: "B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_loss not found in logs (B v6 after tokenized eval)"
priority: medium
tags: [cpt, early-stopping, failure, fix, kaggle, transformers]
schema_version: 1.3
last_updated: "2026-08-25T10:20:39-04:00"
occurrences: 2
error_signature: "b_training_sota: earlystopping disabled — metric_for_best_model eval_spurgeon_loss not found in logs (b v<n> after tokenized eval)"
---

## Occurrence 1 — 2026-08-25T09:03:00-04:00

**Error:**
B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_loss not found in logs (B v6 after tokenized eval)

**Fix:**
Not fixed yet. Next: print actual eval metric keys from Trainer; align METRIC_FOR_BEST / EarlyStopping; verify load_best_model_at_end picks Spurgeon holdout loss. See pretraining/bugs/b-training-sota-known-issues.

## Occurrence 2 — 2026-08-25T10:20:39-04:00


Not a missing metric. HuggingFace logs each eval dataset as a separate dict, so EarlyStoppingCallback warns on mix/puritan/confession/general. trainer_state had eval_spurgeon_loss at 25/50/75; best_global_step=25; SHA256(theology_cpt_lora)==checkpoint-25==C scored adapter. Fix: QuietEarlyStoppingCallback (skip warn when key absent); do not re-C B v6 ckpt-25.
