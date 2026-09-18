---
store_path: failures/vast-unsloth-official-image-smoke
title: "Vast official Unsloth image smoke blocked; LD_LIBRARY_PATH still SIGSEGV"
summary: "- Still **SIGSEGV exit 139** at first `trainer.train()` step"
priority: high
tags: [vast, unsloth, smoke, docker, sigsegv]
schema_version: 1.3
last_updated: "2026-09-16T09:47:06-03:00"
---

# Vast Unsloth official-image smoke attempt (2026-09-16)

## Attempted
1. `unsloth/unsloth:core` — SSH never ready (container exits / Vast sshd conflict; #4682 class)
2. `vastai/unsloth-studio:2026.9.2-cuda-12.9-py312` — same SSH failure; orphan `51209859` ran ~2.5h before force-destroy (block GPU for sibling)
3. Fallback cheap mitigation: `nvidia/cuda:12.4.1-devel` + **`unset LD_LIBRARY_PATH`** (PR #6905) on NL 4090 offer `40113383`

## Result of LD_LIBRARY_PATH mitigation
- Still **SIGSEGV exit 139** at first `trainer.train()` step
- Same stack: Unsloth 2026.9.4, torch 2.11.0+cu126, Qwen3.5-4B LoRA, FA/xformers None
- Log: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke.log`

## Conclusion
- Official Unsloth Docker on Vast is **not SSH-operable** with our current `vast_provision`/`--ssh` path
- `unset LD_LIBRARY_PATH` alone does **not** fix Vast Unsloth CPT segfault
- Next untested research fix would be **conda env** (#668) — higher setup cost; or PEFT / Runpod
