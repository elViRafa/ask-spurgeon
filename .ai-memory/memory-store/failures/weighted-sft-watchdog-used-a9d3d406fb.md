---
store_path: failures/weighted-sft-watchdog-used-a9d3d406fb
title: "weighted SFT watchdog used line>=470 SETUP_FAILED gate and fixed 25m silent time"
summary: "weighted SFT watchdog used line>=470 SETUP_FAILED gate and fixed 25m silent timeout on SETUP_OK; long pip / script drift risked mid-setup destroy after probe fix 1190682"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-10-16T13:25:46-03:00"
occurrences: 1
error_signature: "weighted sft watchdog used line>=<n> setup_failed gate and fixed <n>m silent timeout on setup_ok; long pip / script drift risked mid-setup destroy after probe fix <n>"
---

## Occurrence 1 — 2026-10-16T13:25:46-03:00

**Error:**
weighted SFT watchdog used line>=470 SETUP_FAILED gate and fixed 25m silent timeout on SETUP_OK; long pip / script drift risked mid-setup destroy after probe fix 1190682

**Fix:**
Shared sft_setup_markers.sh: actionable on reason= or SETUP_FAILED after last SETUP_PINS_OK/SETUP_PHASE=pins_ok. Phase markers + reason=trap phase= in sft_remote_setup. Watchdog extends silent deadline while sft_setup.log advances (stale 300s, cap 90m). Main 51cebd1.
