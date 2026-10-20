---
store_path: failures/groq-sft-judge-http-95f134cf88
title: "Groq SFT judge HTTP 403 error code 1010 blocks evaluate.py --judge"
summary: "Groq SFT judge HTTP 403 error code 1010 blocks evaluate.py --judge"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-10-17T20:18:12-03:00"
occurrences: 1
error_signature: "groq sft judge http <n> error code <n> blocks evaluate.py --judge"
---

## Occurrence 1 — 2026-10-17T20:18:12-03:00

**Error:**
Groq SFT judge HTTP 403 error code 1010 blocks evaluate.py --judge

**Fix:**
Use SFT_EVAL_JUDGE_PROVIDER=gemini for --judge / --judge-existing-report. Keep SFT_JUDGE_REMOTE=0 so RunPod only runs HF generation; judge locally.
