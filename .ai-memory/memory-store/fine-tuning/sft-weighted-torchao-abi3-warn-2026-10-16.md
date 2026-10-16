---
store_path: fine-tuning/sft-weighted-torchao-abi3-warn-2026-10-16
title: "Weighted SFT run 7: torchao cp310-abi3 false abort"
summary: "Run 7 (Vast 4090, evidence `fine_tuning/kaggle/vast_sft_s8_weighted/evidence_20261016_151455`) aborted at pin assert, about 5 minutes after watchdog start (17:57 UTC)"
priority: high
tags: [sft, weighted, vast, torchao, setup]
schema_version: 1.3
last_updated: "2026-10-16T15:52:46-03:00"
evidence: [fine_tuning/scripts/sft_remote_setup.sh, fine_tuning/kaggle/vast_sft_s8_weighted/evidence_20261016_151455/capture.txt]
---

# Weighted SFT run 7: torchao cp310-abi3 false abort

## Cause
Run 7 (Vast 4090, evidence `fine_tuning/kaggle/vast_sft_s8_weighted/evidence_20261016_151455`) aborted at pin assert, about 5 minutes after watchdog start (17:57 UTC). All pins matched, `torch.cuda` was True on the RTX 4090, and sys.path was the isolated venv. `assert_pins` then raised:

`torchao has cpython-310 .so under this interpreter: .../sft_venv/.../torchao/_C_mxfp8.cpython-310-x86_64-linux-gnu.so`

`SETUP_FAILED rc=1`. GPU was idle (9 MiB, 0%). The wheel is `torchao-0.18.0-cp310-abi3` (stable ABI, legal on Python 3.11). The `cpython-310` filename is the limited-API tag, not an image leak. The earlier SIGSEGV class was torchao loaded from `/usr/local` or `/usr/lib`.

Optional kernel lines `Failed to load .../_C_cutlass_90a.abi3.so` and `.../_C_mxfp8...` were printed by torchao and did not stop the pin checks.

## Not a load timeout
Watchdog was dry (`WATCHDOG_DRY would destroy`; start banner prints dry=0 before sourcing the env file). Local monitor then waited out the 20 minute loading clock and destroyed ~18:14 UTC. Raising `LoadingTimeoutMinutes` would have billed a dead setup longer. Setup had already exited.

## Fix (local, not yet pushed)
`sft_remote_setup.sh`: WARN when `*cpython-310*.so` sits inside `/sft_venv`, `/envs/sft_train`, or miniforge. Still `SystemExit` if torchao loads from `/usr/local` or `/usr/lib`, or the .so is outside the isolated env. pytest 41 passed (env safeguards, markers, monitor, weighted plan).

## Next
Push before the next go so sparse-checkout picks up the script. Do not rent from Cursor. Credit was ~$2.46 after this run. Seq stays 4608. No Hub until F gates.

Landed on main: `e6368cf80019950d36947c941c69e2d6ce3e802f` (pushed to origin). Dry 2026-10-16: READY, DIRTY_OVERRIDES=(none), WATCHDOG_DRY=1, mix 4098 rows. No GPU rented. Next go still needs operator go; last credit note was about $2.46 so -AllowLowCredit may be required.
