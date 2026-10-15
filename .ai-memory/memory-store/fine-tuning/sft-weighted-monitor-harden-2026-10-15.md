---
store_path: fine-tuning/sft-weighted-monitor-harden-2026-10-15
title: "Weighted SFT Vast monitor false-destroy harden"
summary: "Monitor used boolean `pgrep` of `train_sft_sota.py` with a **10 min** loading timeout"
priority: high
tags: [sft, weighted, vast, monitor, forge]
schema_version: 1.3
last_updated: "2026-10-15T13:36:07-03:00"
evidence: ["commit:9bfdd35", fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1, fine_tuning/scripts/sft_remote_train_s8_weighted.sh, fine_tuning/tests/test_vast_sft_s8_weighted_monitor.py]
---

# Weighted SFT Vast monitor harden (2026-10-15)

## Root cause

Monitor used boolean `pgrep` of `train_sft_sota.py` with a **10 min** loading timeout. `sft_remote_setup` alone can burn ~10m on apt locks, then torch/HF download. SSH flaps looked like "not running". One failed poll after `sawRunning` destroyed the GPU. Oct 15 launch fetched with no adapter (`vast_sft_s8_weighted_launch_1015.log.err`).

## Fix on main (`9bfdd35`)

- Remote: `sft_train.pid` / `sft_train.exit`, tee setup to `sft_setup.log`, bracketed pgrep, **wait** on python so supervisor stays ALIVE.
- State: ALIVE / DEAD / UNKNOWN; SSH error = UNKNOWN never gone; only ALIVE sets `$sawRunning`.
- Debounce: 3 consecutive DEAD + 3m post-launch grace; after ~10m UNKNOWN query `vastai show instance` before destroy.
- Loading default **20 min**, extends while `sft_setup.log` advances, only until pidfile exists.
- `Save-WeightedEvidence` before both destroy paths (dmesg/free/nvidia-smi/log tails; vastai logs fallback).
- Tests: `fine_tuning/tests/test_vast_sft_s8_weighted_monitor.py`.

## Next

Forge dry then operator **go** (credit). Do not rent from Cursor. No Hub until F gates.
