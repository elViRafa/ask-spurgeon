---
store_path: fine-tuning/sft-weighted-marker-protocol-2026-10-16
title: "Weighted SFT: phase markers + silent log-growth watchdog"
summary: "Landed on main: `51cebd192cbbc040dcda4b17bb1367fd806860da`"
priority: medium
tags: [sft, weighted, vast, setup, watchdog, markers]
schema_version: 1.3
last_updated: "2026-10-16T13:25:44-03:00"
evidence: ["commit:51cebd1", fine_tuning/scripts/sft_setup_markers.sh, fine_tuning/scripts/sft_setup_fail_watchdog.sh, fine_tuning/scripts/sft_remote_setup.sh, fine_tuning/tests/test_sft_setup_markers.py]
---

# Weighted SFT marker protocol (2026-10-16)

Landed on main: `51cebd192cbbc040dcda4b17bb1367fd806860da`.

## Why
After `1190682` fixed the false pre-torch `SETUP_FAILED line=50`, destroy gating still used magic `line>=470` and a fixed 25m silent timeout keyed only on `SETUP_OK`. Long pin installs and script line drift were the next money-burn risks.

## Fix
1. Shared `fine_tuning/scripts/sft_setup_markers.sh`: actionable if `reason=` **or** `SETUP_FAILED` appears *after* last `SETUP_PINS_OK` / `SETUP_PHASE=pins_ok` (not co-occurrence).
2. `sft_remote_setup.sh` emits `SETUP_PHASE=boot|pins|pins_ok|ok`; `on_setup_err` writes `reason=trap phase=…`.
3. Watchdog silent: extend while `sft_setup.log` mtime/size advances; stale ≥300s; cap 90m; `MAX_MIN` default 90.
4. Orchestrator syncs markers; monitor sources `/workspace/sft_setup_markers.sh`.
5. Fixture tests in `test_sft_setup_markers.py`; runbook marker table in `NEXT_SFT_S8_WEIGHTED.md`.

## Verify
- pytest: 45 passed (markers + probe + env + monitor + plan)
- Dry: READY, DIRTY_OVERRIDES=(none), PINNED_SHA=`51cebd1`

## Ops next
Forge dry then operator **go** with `-Go`. Seq stays 4608. No Hub until F gates.
