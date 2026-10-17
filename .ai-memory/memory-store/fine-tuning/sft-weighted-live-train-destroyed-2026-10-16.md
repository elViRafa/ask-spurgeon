---
store_path: fine-tuning/sft-weighted-live-train-destroyed-2026-10-16
title: "Weighted SFT live train destroyed at step 9"
summary: "Weighted SFT on 2026-10-16 (session created 21:23Z, destroyed 21:47Z, evidence `fine_tuning/kaggle/vast_sft_s8_weighted/evidence_20261016_184609`) passed setup, CPU tokenizer smoke, and GPU smoke at s"
priority: medium
tags: [sft, weighted, vast, monitor, runpod, unsloth]
schema_version: 1.3
last_updated: "2026-10-17T10:51:08-03:00"
---

Weighted SFT on 2026-10-16 (session created 21:23Z, destroyed 21:47Z, evidence `fine_tuning/kaggle/vast_sft_s8_weighted/evidence_20261016_184609`) passed setup, CPU tokenizer smoke, and GPU smoke at seq 4608 (2 steps, loss ~1.00, `SFT_SMOKE_PASS`). Full train then started: 4098 rows, over 4608 = 0, S3 masking OK, 0 rows dropped, 514 steps, ~86-97 s/step. Log reached step 9/514 with no traceback.

At evidence time 21:46:12Z the 4090 held 23932 MiB / 24564 MiB, 179 W, 36% util. `sft_train.pid` was still 1254 (supervisor) and `sft_train.exit` was absent. Watchdog had already logged `WATCHDOG_EXIT training_healthy`. The local orchestrator then saved evidence with reason `post-fetch-destroy` and destroyed the instance. No adapter (`save_steps` 40).

Cause: `Get-WeightedTrainState` in `vast_sft_s8_weighted_orchestrate.ps1` marks DEAD when `kill -0` on the pidfile and `pgrep` of `train_sft_sota.py` both fail and `sft_setup.log` is older than 180s. After `FULL_TRAIN`, the train writes only `sft_train.log`, so a quiet setup log plus a pid check that does not see the trainer becomes three DEAD polls and a destroy of a live GPU. Do not rent again until that probe treats a growing `sft_train.log` (or high VRAM) as ALIVE. A full run is ~13 h (514 x ~90 s) and needs credit for that quote.

## Fix landed (local, 2026-10-17)

`Get-WeightedTrainState` in `vast_sft_s8_weighted_orchestrate.ps1`:
- ALIVE if `sft_train.log` mtime age < 600s
- ALIVE if GPU mem used > 2048 MiB after FULL_TRAIN / with train log
- DEAD only via exit file, or train-log stale after FULL_TRAIN, or pre-FULL_TRAIN pid-gone + setup stale
- Never DEAD on setup-log age alone after FULL_TRAIN

Tests: `fine_tuning/tests/test_vast_sft_s8_weighted_monitor.py` (7 passed).
Push before next go so sparse-checkout picks up the orchestrator. No GPU rented in the fix session.

## Follow-on (2026-10-17)

Operator chose next work: **plan RunPod Unsloth** for weighted SFT (design → code → usage), not another Vast PEFT go while credit is ~$2. Handoff: `fine-tuning/sft-runpod-unsloth-next-session`. Monitor fix remains on main `afb8e7f` for any future Vast PEFT run.
