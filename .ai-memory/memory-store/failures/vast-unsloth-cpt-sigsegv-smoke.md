---
store_path: failures/vast-unsloth-cpt-sigsegv-smoke
title: "Vast Unsloth CPT+LoRA smoke SIGSEGV (exit 139)"
summary: "**Verdict:** **FAIL** — same class of crash as SFT Unsloth on Vast"
priority: medium
tags: [vast, unsloth, cpt, superseded]
schema_version: 1.3
last_updated: "2026-09-16T10:32:23-03:00"
---

# Vast Unsloth CPT+LoRA smoke — SIGSEGV

**Date:** 2026-09-16
**Verdict:** **FAIL** — same class of crash as SFT Unsloth on Vast.

## Setup
- Offer ~$0.47/hr RTX 4090 full GPU (`gpu_frac>=1`, `cuda_max_good>=12.6`)
- Image `nvidia/cuda:12.4.1-devel-ubuntu22.04`
- torch `2.11.0+cu126`, Unsloth 2026.9.4, Qwen3.5-4B-Base bf16 LoRA r=16
- Scripts: `continued_pretrain/scripts/smoke_vast_unsloth_cpt.py`, `vast_cpt_smoke_remote.sh`, `vast_cpt_smoke.ps1`

## Observation
- Import, `FastLanguageModel`, LoRA attach, tokenize — OK
- `trainer.train()` first step → **Segmentation fault, exit 139**
- Log marker: `CPT_UNSLOTH_SMOKE_FAIL sigsegv_exit_139`
- Local copy: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke.log`

## Implication
- **Vast + PEFT LoRA (SFT path):** known good
- **Vast + Unsloth CPT LoRA:** not viable for S6 resume on Vast
- Prefer Runpod (or PEFT CPT port) for Unsloth CPT; do not rent Vast for Unsloth CPT training

# Vast Unsloth CPT — use Miniforge (resolved)

**Update 2026-09-16:** Earlier implication “do not use Unsloth CPT on Vast” is **superseded** for the Miniforge path.

- System pip / official Unsloth Docker: still fail (SIGSEGV / SSH)
- **Miniforge + torch cu126 pip-in-env:** smoke PASS — see `fine-tuning/vast-unsloth-conda-smoke-pass`
- Next: wire full S6 continue-B to that recipe, or unblock Runpod
