---
store_path: failures/bash-on-vast-gpu-3988e6eb63
title: "bash on Vast GPU fails remote multi-line SSH scripts with $'\\r' / CRLF from Wind"
summary: "bash on Vast GPU fails remote multi-line SSH scripts with $'\\r' / CRLF from Windows PowerShell here-strings in Invoke-WeightedSsh (weighted SFT S8)"
priority: medium
tags: [crlf, failure, fix, powershell, sft, ssh, vast, weighted]
schema_version: 1.3
last_updated: "2026-10-15T12:31:48+00:00"
occurrences: 1
error_signature: "bash on vast gpu fails remote multi-line ssh scripts with $<val> / crlf from windows powershell here-strings in invoke-weightedssh (weighted sft s<n>)"
---

## Occurrence 1 — 2026-10-15T12:31:48+00:00

**Error:**
bash on Vast GPU fails remote multi-line SSH scripts with $'\r' / CRLF from Windows PowerShell here-strings in Invoke-WeightedSsh (weighted SFT S8)

**Fix:**
In vast_sft_s8_weighted_orchestrate.ps1 Invoke-WeightedSsh: $Remote = $Remote -replace "`r", "" before ssh. Add tests asserting strip + LF-only orchestrator/remote .sh. LoadingTimeoutMinutes=10 for train-start wait. Pushed 604fca5.
