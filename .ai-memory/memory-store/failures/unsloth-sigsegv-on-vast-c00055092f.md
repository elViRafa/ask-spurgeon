---
store_path: failures/unsloth-sigsegv-on-vast-c00055092f
title: "Unsloth SIGSEGV on Vast with system pip; conda-forge pytorch-cuda resolved to CP"
summary: "Unsloth SIGSEGV on Vast with system pip; conda-forge pytorch-cuda resolved to CPU"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-16T10:28:27-03:00"
occurrences: 1
error_signature: "unsloth sigsegv on vast with system pip; conda-forge pytorch-cuda resolved to cpu"
---

## Occurrence 1 — 2026-09-16T10:28:27-03:00

**Error:**
Unsloth SIGSEGV on Vast with system pip; conda-forge pytorch-cuda resolved to CPU

**Fix:**
Use Miniforge env + pip install torch cu126 into that env (not system site-packages; avoid conda-forge CPU pytorch). Smoke passed 3 Unsloth CPT steps on Vast 4090.
