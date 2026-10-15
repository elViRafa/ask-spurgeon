---
store_path: fine-tuning/sft-remote-crlf-brief-2026-10-14
title: "Weighted SFT: strip CR from SSH remotes + 10m loading timeout (DONE)"
summary: "Landed on main `604fca5` (fix) + `7dfaca8` (this brief)"
priority: medium
tags: [sft, weighted, ssh, crlf, vast, done]
schema_version: 1.3
last_updated: "2026-10-15T12:31:48+00:00"
evidence: [fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1, fine_tuning/scripts/test_sft_s8_weighted_plan.py]
---

# Brief — remote SSH CRLF + loading timeout (2026-10-14) DONE

Landed on main `604fca5` (fix) + `7dfaca8` (this brief). Do not re-open unless a new GPU bash `$'\r'` failure appears.

## Done

1. `Invoke-WeightedSsh` strips every `\r` before ssh (`$Remote = $Remote -replace "`r", ""`).
2. Tests: `test_orchestrator_strips_cr_from_remote_ssh_scripts`, `test_orchestrator_loading_timeout_about_ten_minutes`.
3. `LoadingTimeoutMinutes = 10` — abandon wait if train never appears (~10m, not ~40m idle polls).
4. Did not stage `fine_tuning/data/qa_open_theology/`.
5. Pushed to `github.com/elViRafa/ask-spurgeon` main via deploy key (Cloud Agent Runtime Secrets did not inject mid-session).

## Why

Windows PowerShell here-strings keep CRLF; bash on the GPU treats `\r` as part of the token. Same class as CPT Isolation C CRLF (`0988137`).

## Evidence

- commits: `604fca5`, `7dfaca8`
