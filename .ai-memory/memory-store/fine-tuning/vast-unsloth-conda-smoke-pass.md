---
store_path: fine-tuning/vast-unsloth-conda-smoke-pass
title: "Vast Unsloth CPT smoke PASS with Miniforge conda env"
summary: "**Verdict:** **PASS** (`CPT_UNSLOTH_SMOKE_PASS steps=3`)"
priority: medium
tags: [vast, unsloth, conda, cpt, smoke, pass]
schema_version: 1.3
last_updated: "2026-09-16T10:28:25-03:00"
---

# Vast Unsloth CPT smoke via Miniforge — PASS

**Date:** 2026-09-16
**Verdict:** **PASS** (`CPT_UNSLOTH_SMOKE_PASS steps=3`)

## What worked
- Image: `nvidia/cuda:12.4.1-devel-ubuntu22.04` (SSH-safe)
- **Miniforge** env `unsloth_smoke` (Python 3.11)
- torch **2.11.0+cu126 via pip inside the conda env** (not system pip; not conda-forge CPU pytorch)
- unsloth + trl/peft via pip in that env
- `unset LD_LIBRARY_PATH`
- 3 train steps completed; loss decreased; instance destroyed

## What failed earlier
- System pip on same image → SIGSEGV 139
- `unset LD_LIBRARY_PATH` alone → still SIGSEGV
- Official Unsloth Docker → SSH unusable on Vast
- First conda attempt: `conda install pytorch-cuda=12.4` resolved to **CPU** pytorch → AssertionError

## Implication
Vast + Unsloth CPT is viable **if** training runs inside a clean conda/miniforge env with CUDA torch installed into that env. System-site pip Unsloth remains broken.

Scripts: `vast_cpt_smoke_conda.ps1`, `vast_cpt_smoke_remote_conda.sh`
Log: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke_conda.log`
