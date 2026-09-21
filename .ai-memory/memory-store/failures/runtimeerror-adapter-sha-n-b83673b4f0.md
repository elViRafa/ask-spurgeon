---
store_path: failures/runtimeerror-adapter-sha-n-b83673b4f0
title: "RuntimeError: adapter SHA256 mismatch: got ef4df3a3… (S5 LoRA) want 319d17a3… (H"
summary: "RuntimeError: adapter SHA256 mismatch: got ef4df3a3… (S5 LoRA) want 319d17a3… (Hub v2)"
priority: medium
tags: [cpt, failure, fix, s6, sft_env, sha256, vast]
schema_version: 1.3
last_updated: "2026-09-18T07:38:55-03:00"
occurrences: 1
error_signature: "runtimeerror: adapter sha<n> mismatch: got <hex>… (s<n> lora) want <hex>… (hub v<n>). vast cpt continue-b crashed immediately because vast_inject_hf_token.ps<n> writes expected_adapter_sha<n>=hub-v<n> into <path>, and vast_cpt_remote_continue_b.sh sourced .sft_env after exporting the s<n> sha, overw"
failure_key: runtimeerror
---

## Occurrence 1 — 2026-09-18T07:38:55-03:00

**Error:**
RuntimeError: adapter SHA256 mismatch: got ef4df3a3… (S5 LoRA) want 319d17a3… (Hub v2). Vast CPT continue-B crashed immediately because vast_inject_hf_token.ps1 writes EXPECTED_ADAPTER_SHA256=Hub-v2 into /workspace/.sft_env, and vast_cpt_remote_continue_b.sh sourced .sft_env after exporting the S5 SHA, overwriting it.

**Fix:**
Re-export EXPECTED_ADAPTER_SHA256=S5 (ef4df3a3…) AFTER sourcing .sft_env in vast_cpt_remote_continue_b.sh. On the live pod also sed-fixed .sft_env, moved the failed log aside, and relaunched. Training then passed INIT_ADAPTER SHA256 OK and resumed checkpoint-2050.
