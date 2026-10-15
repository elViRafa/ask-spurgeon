---
store_path: fine-tuning/sft-weighted-env-safeguards-2026-10-15
title: "Weighted SFT isolated env + smoke safeguards (SIGSEGV 139)"
summary: "Exit 139 SIGSEGV at step 0 (first forward) on two Vast hosts with different drivers"
priority: high
tags: [sft, weighted, vast, venv, smoke, evidence, pins]
schema_version: 1.3
last_updated: "2026-10-15T14:21:48-03:00"
---

# Weighted SFT env safeguards (2026-10-15)

## Problem
Exit 139 SIGSEGV at step 0 (first forward) on two Vast hosts with different drivers. Setup used `--break-system-packages` under Python 3.11 while image packages left torchao `cpython-310` `.so` files loadable.

## Fix (main)
1. `sft_remote_setup.sh`: isolated `/workspace/sft_venv` (no system-site-packages) or Miniforge `sft_train` fallback; `unset LD_LIBRARY_PATH`; Sep 6 pins via `sft_gate0_sep6_constraints.txt`; assert pins; write `/workspace/sft_pip_freeze.txt`; refuse FLA/causal-conv1d.
2. `sft_remote_train_s8_weighted.sh`: `PYTHONFAULTHANDLER=1` + `python -X faulthandler`; 2-step smoke on longest rows before full train (`CUDA_LAUNCH_BLOCKING=1` smoke-only); retry expandable_segments off then seq 2048; fail cheaply with evidence hooks.
3. `train_sft_sota.py`: `--smoke` / `SFT_SMOKE`, `SFT_EXPANDABLE_SEGMENTS` toggle, longest-row select.
4. `Save-WeightedEvidence`: assert payload, `status.txt` + `listing.txt`, scp log fallback.
5. Dynamic mix row count in `test_sft_s3_mask_all_rows.py`.

## Ops
Do not rent from Cursor. Forge dry then operator go after push. Dirty sync needs `-AllowDirtySync` until committed SHA is on origin.
