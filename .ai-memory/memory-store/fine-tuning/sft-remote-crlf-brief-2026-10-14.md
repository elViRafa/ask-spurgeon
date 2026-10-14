---
store_path: fine-tuning/sft-remote-crlf-brief-2026-10-14
title: "Weighted SFT: strip CR from SSH remotes + 10m loading timeout"
summary: "Invoke-WeightedSsh must strip \\r from every remote script; assert no CR in remote scripts; ~10 min loading timeout before train appears."
priority: high
tags: [sft, weighted, ssh, crlf, vast]
schema_version: 1.3
last_updated: "2026-10-14"
evidence: ["fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1", "fine_tuning/scripts/test_sft_s8_weighted_plan.py"]
---

# Brief — remote SSH CRLF + loading timeout (2026-10-14)

## Do

1. In `vast_sft_s8_weighted_orchestrate.ps1` / `Invoke-WeightedSsh`, strip `\r` from every remote script sent over ssh (Windows here-strings keep CRLF; bash treats `\r` as part of the token).
2. Add a test asserting no `\r` in remote scripts (orchestrator LF-only + strip contract + remote `.sh` files).
3. Add a ~10 min "loading" timeout: if the train process never appears after launch, stop waiting (~10m, not ~40m idle polls).
4. Do **not** stage `fine_tuning/data/qa_open_theology/`.
5. Commit and push to `main`.

## Why

Sparse-checkout sync and launch send multi-line bash via `Invoke-WeightedSsh`. On Windows, PowerShell here-strings preserve CRLF, so the GPU sees `$'\r'` and fails. Same class of bug as CPT Isolation C CRLF (`0988137`).
