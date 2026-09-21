---
store_path: failures/s-n-vast-c-b0dd9b03d4
title: "S6 Vast C-eval FAIL: SHA256 mismatch — EXPECTED was Hub-v2 319d17a3… after sourc"
summary: "S6 Vast C-eval FAIL: SHA256 mismatch — EXPECTED was Hub-v2 319d17a3… after sourcing /workspace/.sft_env from vast_inject_hf_token, while GOT was S6 ckpt-2050 6aab9194…"
priority: medium
tags: [c-eval, cpt, failure, fix, s6, sha256, vast]
schema_version: 1.3
last_updated: "2026-09-18T11:46:03-03:00"
occurrences: 1
error_signature: "s<n> vast c-eval fail: sha<n> mismatch — expected was hub-v<n> <hex>… after sourcing <path> from vast_inject_hf_token, while got was s<n> ckpt-<n> <hex>…"
---

## Occurrence 1 — 2026-09-18T11:46:03-03:00

**Error:**
S6 Vast C-eval FAIL: SHA256 mismatch — EXPECTED was Hub-v2 319d17a3… after sourcing /workspace/.sft_env from vast_inject_hf_token, while GOT was S6 ckpt-2050 6aab9194…

**Fix:**
In vast_remote_c_eval.sh, capture PINNED_ADAPTER_SHA256 before sourcing .sft_env, then unconditionally export EXPECTED_ADAPTER_SHA256=$PINNED_ADAPTER_SHA256 afterward (:- default does not override a set Hub-v2 value). Also wrap fetch scp in ErrorActionPreference Continue so Vast SSH banner on stderr does not abort before destroy.
