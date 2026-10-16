---
store_path: failures/sft-remote-setup-sh-7383d17245
title: "sft_remote_setup.sh pre-torch python3 -c import torch | tee under set -euo pipef"
summary: "sft_remote_setup.sh pre-torch python3 -c import torch | tee under set -euo pipefail and ERR trap wrote SETUP_FAILED line=50 even with set +e; pre_torch_rc=$? captured tee not python; watchdog/monitor "
priority: medium
tags: [err-trap, failure, fix, setup, sft, vast, watchdog, weighted]
schema_version: 1.3
last_updated: "2026-10-16T12:48:26-03:00"
occurrences: 2
error_signature: "sft_remote_setup.sh pre-torch python<n> -c import torch | tee under set -euo pipefail and err trap wrote setup_failed line=<n> even with set +e; pre_torch_rc=$? captured tee not python; watchdog<path> treated false setup_failed as real and destroyed vast instance mid-setup"
---

## Occurrence 1 — 2026-10-15T18:46:25-03:00

**Error:**
sft_remote_setup.sh pre-torch python3 -c import torch | tee under set -euo pipefail and ERR trap wrote SETUP_FAILED line=50 even with set +e; pre_torch_rc=$? captured tee not python; watchdog/monitor treated false SETUP_FAILED as real and destroyed Vast instance mid-setup

**Fix:**
Disable ERR trap around expected-fail pre-torch probe and pins_already_ok checks; append to SETUPLOG without piping through tee so $? is python's rc; emit SETUP_PINS_OK after assert_pins; watchdog/monitor actionable_setup_failed only after SETUP_PINS_OK or reason= or line>=470; Save-WeightedEvidence requires real payload and does not print evidence saved when nothing copied; offline fake-python3 probe test.

## Occurrence 2 — 2026-10-16T12:48:26-03:00


Landed main 1190682: trap - ERR around expected-fail probe and pins_already_ok; append SETUPLOG without tee so $? is python; SETUP_PINS_OK after assert_pins; watchdog/monitor actionable_setup_failed only after SETUP_PINS_OK or reason= or line>=470; Save-WeightedEvidence requires real payload and does not print evidence saved when empty; offline fake-python3 probe test.
