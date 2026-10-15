---
store_path: failures/weighted-sft-exit-n-a8a9957108
title: "Weighted SFT exit 139 SIGSEGV at step 0 first forward on two Vast hosts; torchao"
summary: "Weighted SFT exit 139 SIGSEGV at step 0 first forward on two Vast hosts; torchao loading cpython-310 .so under Python 3.11 via --break-system-packages mixing image site-packages"
priority: medium
tags: [failure, fix, pins, sft, sigsegv, smoke, vast, venv, weighted]
schema_version: 1.3
last_updated: "2026-10-15T14:21:09-03:00"
occurrences: 1
error_signature: "weighted sft exit <n> sigsegv at step <n> first forward on two vast hosts; torchao loading cpython-<n> .so under python <n>.<n> via --break-system-packages mixing image site-packages"
---

## Occurrence 1 — 2026-10-15T14:21:09-03:00

**Error:**
Weighted SFT exit 139 SIGSEGV at step 0 first forward on two Vast hosts; torchao loading cpython-310 .so under Python 3.11 via --break-system-packages mixing image site-packages

**Fix:**
Isolated /workspace/sft_venv (or Miniforge conda fallback), unset LD_LIBRARY_PATH, pin Sep 6 GATE-0 stack via sft_gate0_sep6_constraints.txt, assert pins + write sft_pip_freeze.txt, PYTHONFAULTHANDLER/-X faulthandler, 2-step smoke on longest rows before full train with expandable_segments then seq 2048 retries, harden Save-WeightedEvidence with status.txt/listing/scp fallback
