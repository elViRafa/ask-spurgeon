---
store_path: fine-tuning/sft-weighted-false-setup-failed-probe-2026-10-15
title: "Weighted SFT: false SETUP_FAILED from pre-torch probe"
summary: "Landed on main: `1190682056d767a9d81e92bfb10777af3a62d93e` (2026-10-15)"
priority: high
tags: [sft, weighted, vast, setup, watchdog, evidence]
schema_version: 1.3
last_updated: "2026-10-16T12:48:24-03:00"
evidence: ["commit:1190682", fine_tuning/scripts/sft_remote_setup.sh, fine_tuning/scripts/sft_setup_fail_watchdog.sh, fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1, fine_tuning/tests/test_sft_pre_torch_probe_no_setup_failed.py]
---

# Weighted SFT false SETUP_FAILED (pre-torch probe)

Landed on main: `1190682056d767a9d81e92bfb10777af3a62d93e` (2026-10-15).

## Bug
`set +e` does **not** suppress the ERR trap. The informational `python3 -c 'import torch...'` before pin install failed as expected, trap wrote `SETUP_FAILED line=50`, and watchdog + monitor destroyed the instance while pip was still installing torch. `pre_torch_rc=$?` after `| tee` was tee's status, not python's. Evidence folders sometimes claimed "saved" with only meta / tiny vastai_logs (AddRange listing crash).

## Fix
1. `trap - ERR` around the probe (and pins_already_ok expected-fail imports); restore after.
2. Append probe output to `$SETUPLOG` without `| tee`; capture `pre_torch_rc=$?`.
3. Emit `SETUP_PINS_OK` after `assert_pins`.
4. Watchdog + monitor: actionable SETUP_FAILED only if `SETUP_PINS_OK` present, or `reason=`, or trap line >= 470. Explicit early fails (nvidia-smi) still destroy.
5. `Save-WeightedEvidence`: real scp/capture payload required; no "evidence saved" when nothing copied; fix AddRange listing crash.
6. Offline test: fake python3 exits 1 → no SETUP_FAILED line (`test_sft_pre_torch_probe_no_setup_failed.py`).

## Verify
- pytest: 36 passed (probe + env safeguards + monitor + weighted plan)
- Dry: READY, DIRTY_OVERRIDES=(none), PINNED_SHA=`1190682`
- No GPU rented; `qa_open_theology/` not staged

## Ops next
Forge dry then operator **go** with `-Go` (monitor auto). Seq stays 4608. No Hub until F gates.
