---
store_path: fine-tuning/sft-hf-inject-fix
title: "SFT HF inject fix — urllib verify, no BOM"
summary: "**Date:** 2026-09-02 ~18:45 ET"
priority: high
tags: [sft, runpod, hf-token, fix]
schema_version: 1.3
last_updated: "2026-09-02T18:43:31-04:00"
review_status: stale
---

**Date:** 2026-09-02 ~18:45 ET

## Root cause
`sft_inject_hf_token.ps1` failed because:
1. First design verified with `huggingface_hub` before `sft_remote_setup.sh` installs it.
2. Rewrite with curl/bash failed because PowerShell expanded `$HF_TOKEN` to empty in the SSH command.

## Fix
- Write token via remote Python (base64 decode + repr for safe `.sft_env`).
- Verify with `urllib.request` to HF whoami-v2 (stdlib only).
- Session JSON: read with `utf-8-sig`; PowerShell `Save-SftSession` writes UTF-8 no BOM.
- Watcher already force-deletes pod on orchestrate failure.

## Live result
Pod `gt5ureujk6c8dh` provisioned; inject PASS; `train_sft_sota.py` PID 1509; monitor PID 24820; capacity watcher exited `state=training`.
