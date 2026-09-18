---
store_path: failures/powershell-n-n-parsererror-b9e9a8ea15
title: "PowerShell 5.1 ParserError: string has no terminator when a UTF-8 em-dash sits i"
summary: "PowerShell 5.1 ParserError: string has no terminator when a UTF-8 em-dash sits inside double quotes in a .ps1 without BOM"
priority: medium
tags: [encoding, failure, fix, powershell, scripts, vast]
schema_version: 1.3
last_updated: "2026-09-16T11:02:02-03:00"
occurrences: 1
error_signature: "powershell <n>.<n> parsererror: string has no terminator when a utf-<n> em-dash sits inside double quotes in a .ps<n> without bom"
failure_key: "parsererror|utf-8"
---

## Occurrence 1 — 2026-09-16T11:02:02-03:00

**Error:**
PowerShell 5.1 ParserError: string has no terminator when a UTF-8 em-dash sits inside double quotes in a .ps1 without BOM

**Fix:**
Use ASCII -- in PowerShell scripts instead of Unicode em-dashes. Windows PowerShell 5.1 reads UTF-8 without BOM as ANSI and byte 0x94 inside the em-dash closes the string.
