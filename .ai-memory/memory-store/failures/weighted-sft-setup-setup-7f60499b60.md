---
store_path: failures/weighted-sft-setup-setup-7f60499b60
title: "weighted SFT setup SETUP_FAILED rc=1 because torchao 0.18 cp310-abi3 wheel has c"
summary: "weighted SFT setup SETUP_FAILED rc=1 because torchao 0.18 cp310-abi3 wheel has cpython-310 .so inside sft_venv; pins and torch.cuda already OK"
priority: medium
tags: [failure, fix, setup, sft, torchao, vast]
schema_version: 1.3
last_updated: "2026-10-16T15:48:06-03:00"
occurrences: 1
error_signature: "weighted sft setup setup_failed rc=<n> because torchao <n>.<n> cp<n>-abi<n> wheel has cpython-<n> .so inside sft_venv; pins and torch.cuda already ok"
---

## Occurrence 1 — 2026-10-16T15:48:06-03:00

**Error:**
weighted SFT setup SETUP_FAILED rc=1 because torchao 0.18 cp310-abi3 wheel has cpython-310 .so inside sft_venv; pins and torch.cuda already OK

**Fix:**
sft_remote_setup.sh warns for cpython-310 .so inside the isolated venv and still exits if torchao loads from /usr/local or /usr/lib
