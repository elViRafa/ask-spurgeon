---
store_path: failures/weighted-sft-vast-monitor-475e9e90b7
title: "Weighted SFT Vast monitor destroyed a live 4090 train at step 9/514 with reason "
summary: "Weighted SFT Vast monitor destroyed a live 4090 train at step 9/514 with reason post-fetch-destroy"
priority: medium
tags: [failure, fix, monitor, sft, vast, weighted]
schema_version: 1.3
last_updated: "2026-10-17T07:50:43-03:00"
occurrences: 1
error_signature: "weighted sft vast monitor destroyed a live <n> train at step <n><path> with reason post-fetch-destroy. after full_train, sft_setup.log goes quiet while progress is only in sft_train.log; get-weightedtrainstate treated stale setup + failed kill<path> as dead."
---

## Occurrence 1 — 2026-10-17T07:50:43-03:00

**Error:**
Weighted SFT Vast monitor destroyed a live 4090 train at step 9/514 with reason post-fetch-destroy. After FULL_TRAIN, sft_setup.log goes quiet while progress is only in sft_train.log; Get-WeightedTrainState treated stale setup + failed kill/pgrep as DEAD.

**Fix:**
Get-WeightedTrainState now treats fresh sft_train.log (<600s) and GPU memory >2048 MiB (after FULL_TRAIN or when train log exists) as ALIVE. Exit file is the hard DEAD signal. After FULL_TRAIN, setup-log age alone never marks DEAD. Tests in test_vast_sft_s8_weighted_monitor.py cover train-log/gpu/exit canned states.
