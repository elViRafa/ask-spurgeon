---
store_path: failures/timeouterror-ssh-proxy-known-1fc3894a4a
title: "TimeoutError: SSH proxy known but container unreachable for pod re5vcu9ojlpw4q ("
summary: "TimeoutError: SSH proxy known but container unreachable for pod re5vcu9ojlpw4q (likely bad GPU host / GPU requires reset) during weighted Unsloth SFT provision on Secure 4090 US-IL-1"
priority: medium
tags: [bad-host, failure, fix, runpod, sft, ssh]
schema_version: 1.3
last_updated: "2026-10-20T10:14:36-03:00"
occurrences: 1
error_signature: "timeouterror: ssh proxy known but container unreachable for pod re<n>vcu<n>ojlpw<n>q (likely bad gpu host / gpu requires reset) during weighted unsloth sft provision on secure <n> us-il-<n>"
failure_key: "timeouterror|il-1"
---

## Occurrence 1 — 2026-10-20T10:14:36-03:00

**Error:**
TimeoutError: SSH proxy known but container unreachable for pod re5vcu9ojlpw4q (likely bad GPU host / GPU requires reset) during weighted Unsloth SFT provision on Secure 4090 US-IL-1

**Fix:**
Orchestrator auto-destroyed the bad pod (POD_DELETED). Retry -Go -CloudType SECURE -AllowDirtySync; Community 4090 had no stock (500). Quote Secure 4090 $0.89/hr.
