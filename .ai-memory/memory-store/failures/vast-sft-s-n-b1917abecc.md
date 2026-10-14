---
store_path: failures/vast-sft-s-n-b1917abecc
title: "vast_sft_s8_weighted_orchestrate.ps1 died after provision: vast_common.ps1 Error"
summary: "vast_sft_s8_weighted_orchestrate.ps1 died after provision: vast_common.ps1 ErrorActionPreference=Stop turns ssh first-connect Permanently added warning into terminating error in vast_wait_ssh.ps1 befo"
priority: medium
tags: [failure, fix, powershell, ssh, vast]
schema_version: 1.3
last_updated: "2026-10-14T10:00:17-03:00"
occurrences: 1
error_signature: "vast_sft_s<n>_weighted_orchestrate.ps<n> died after provision: vast_common.ps<n> erroractionpreference=stop turns ssh first-connect permanently added warning into terminating error in vast_wait_ssh.ps<n> before lastexitcode check; same risk on invoke-vastai <n>>&<n>."
---

## Occurrence 1 — 2026-10-14T10:00:17-03:00

**Error:**
vast_sft_s8_weighted_orchestrate.ps1 died after provision: vast_common.ps1 ErrorActionPreference=Stop turns ssh first-connect Permanently added warning into terminating error in vast_wait_ssh.ps1 before LASTEXITCODE check; same risk on Invoke-Vastai 2>&1.

**Fix:**
Add -o LogLevel=ERROR to Get-VastSshArgs and vast_wait_ssh probe. Wrap ssh and Invoke-Vastai native calls with ErrorActionPreference=Continue then check exit code. Keep LF line endings on both ps1 files.
