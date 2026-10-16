---
store_path: failures/weighted-sft-vast-runs-cc1e1faa64
title: "Weighted SFT Vast runs 5 and 6 self-destroyed at about 4 and 7 minutes during se"
summary: "Weighted SFT Vast runs 5 and 6 self-destroyed at about 4 and 7 minutes during setup"
priority: medium
tags: [err-trap, failure, fix, setup, sft, vast, watchdog, weighted]
schema_version: 1.3
last_updated: "2026-10-16T14:28:15-03:00"
occurrences: 1
error_signature: "weighted sft vast runs <n> and <n> self-destroyed at about <n> and <n> minutes during setup. sft_remote_setup.sh err trap wrote setup_failed line=n reason=trap on any non-zero command, including benign commands under || true or set +e. sft_setup_markers.sh treated any setup_failed reason= as actiona"
---

## Occurrence 1 — 2026-10-16T14:28:15-03:00

**Error:**
Weighted SFT Vast runs 5 and 6 self-destroyed at about 4 and 7 minutes during setup. sft_remote_setup.sh ERR trap wrote SETUP_FAILED line=N reason=trap on any non-zero command, including benign commands under || true or set +e. sft_setup_markers.sh treated any SETUP_FAILED reason= as actionable and sft_setup_fail_watchdog.sh destroyed. Vast audit: instance_DELETE came from the instance own IP.

**Fix:**
ERR trap now writes SETUP_TRAP_INFO only. SETUP_FAILED rc= is emitted only from die() via the EXIT trap when the script exits non-zero. Watchdog and pc1 monitor match anchored ^SETUP_FAILED rc= and ^SMOKE_BEFORE_TRAIN_FAILED only. Before destroy, write WATCHDOG_DESTROY_BEGIN with the trigger line and the last 200 log lines, scp/rsync to SFT_EVIDENCE_PUSH_TARGET if set, else keep the file in the evidence folder. WATCHDOG_DRY defaults off in the shell; orchestrator launches the first post-fix run with WATCHDOG_DRY=1 so the local monitor is the only destroyer. Heartbeat every 30s during pip and apt. Main 228b9c010e9878b13ba5bc7eea877c3032f8fb51.
