---
store_path: fine-tuning/sft-weighted-trap-info-2026-10-16
title: "Weighted SFT: ERR trap is info, only anchored SETUP_FAILED rc= destroys"
summary: "Landed on main: `228b9c010e9878b13ba5bc7eea877c3032f8fb51`"
priority: high
tags: [sft, weighted, vast, watchdog, setup]
schema_version: 1.3
last_updated: "2026-10-16T14:28:21-03:00"
evidence: ["commit:228b9c010e9878b13ba5bc7eea877c3032f8fb51", fine_tuning/scripts/sft_remote_setup.sh, fine_tuning/scripts/sft_setup_markers.sh, fine_tuning/scripts/sft_setup_fail_watchdog.sh]
---

# Weighted SFT trap-info watchdog (2026-10-16)

Landed on main: `228b9c010e9878b13ba5bc7eea877c3032f8fb51`.

## Bug
Runs 5 and 6 were deleted from the instance's own IP at ~4 and ~7 min during setup. The ERR trap wrote `SETUP_FAILED line=N reason=trap` for benign non-zero commands (`|| true`, `set +e`). Markers treated any `reason=` as actionable, so the watchdog destroyed a healthy setup. Same class as the run 4 false alarm.

## Fix
1. ERR trap writes `SETUP_TRAP_INFO line=N cmd=... rc=...` only.
2. `SETUP_FAILED rc=N` comes from the EXIT trap when the script exits non-zero (`die` for nvidia-smi and other real aborts).
3. Watchdog and pc1 monitor match only `^SETUP_FAILED rc=` and `^SMOKE_BEFORE_TRAIN_FAILED`.
4. Before destroy: `WATCHDOG_DESTROY_BEGIN reason=... trigger_line=<exact line>` plus last 200 log lines in `/workspace/sft_fail_evidence/watchdog_destroy_begin.txt`. scp/rsync when `SFT_EVIDENCE_PUSH_TARGET` is set; otherwise the file stays for the pc1 pull.
5. Shell default `WATCHDOG_DRY=0`. Orchestrator default `-WatchdogDry 1` for this first post-fix launch. Local monitor is the only destroyer until `-WatchdogDry 0`.
6. `SETUP_HEARTBEAT` every 30s while pip and apt run.

## Verify
- pytest: 44 passed (markers, probe, env safeguards, monitor, weighted plan)
- Live bash: `set +e; false` writes SETUP_TRAP_INFO and no SETUP_FAILED; `exit 1` writes `SETUP_FAILED rc=1`
- Dry: READY, DIRTY_OVERRIDES=(none), PINNED_SHA=`228b9c0`, WATCHDOG_DRY=1
- No GPU rented

## Ops next
Operator go with `-Go`. Do not flip `-WatchdogDry 0` until one clean setup. Seq stays 4608. No Hub until F gates.
