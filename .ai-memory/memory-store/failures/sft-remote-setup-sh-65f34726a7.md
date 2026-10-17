---
store_path: failures/sft-remote-setup-sh-65f34726a7
title: "unsloth_zoo ImportError Please install Unsloth via pip install unsloth during PI"
summary: "sft_remote_setup.sh assert_pins bare import unsloth under set -euo pipefail failed with unsloth_zoo ImportError Please install Unsloth via pip install unsloth despite pip list showing unsloth 2026.9.2"
priority: medium
tags: [failure, fix, runpod, setup, sft, unsloth]
schema_version: 1.3
last_updated: "2026-10-17T17:33:21-03:00"
occurrences: 2
error_signature: "sft_remote_setup.sh assert_pins bare import unsloth under set -euo pipefail failed with unsloth_zoo importerror please install unsloth via pip install unsloth despite pip list showing unsloth <n>.<n>.<n> and unsloth_zoo <n>.<n>.<n>; setup exited <n>; no smoke<path>; local launcher without -startmoni"
failure_key: importerror
---

## Occurrence 1 — 2026-10-15T16:20:25-03:00

**Error:**
sft_remote_setup.sh assert_pins bare import unsloth under set -euo pipefail failed with unsloth_zoo ImportError Please install Unsloth via pip install unsloth despite pip list showing unsloth 2026.9.2 and unsloth_zoo 2026.9.1; setup exited 1; no smoke/train; local launcher without -StartMonitor left Vast instance idle ~30 min billing; torchao cpython-310 .so warnings under py3.11 venv from image dist-packages leak

**Fix:**
Gate unsloth/unsloth_zoo install+import to SFT_BACKEND=unsloth only (weighted peft path skips). Harden isolated venv (no system-site-packages, PYTHONNOUSERSITE, refuse image dist-packages on sys.path). Drop pip -q. CUDA/LD diagnostics before first unset LD_LIBRARY_PATH. ERR trap writes SETUP_FAILED line=N. Remote sft_setup_fail_watchdog.sh evidence+self-destroy. Orchestrator: -Go implies -StartMonitor, Start-Transcript, launch try/catch Invoke-DestroyOnFail, monitor breaks fast on SETUP_FAILED/SMOKE_BEFORE_TRAIN_FAILED.

## Occurrence 2 — 2026-10-17T17:33:21-03:00

unsloth_zoo ImportError Please install Unsloth via pip install unsloth during PIN ASSERT despite unsloth 2026.9.2 already installed in sft_venv

In sft_remote_setup.sh assert_pins, import unsloth before adding unsloth_zoo to the version checks loop. unsloth_zoo refuses import unless unsloth is already loaded.
