---
store_path: pretraining/cpt-eval-stack-pin-s5
title: "CPT C-eval must use Unsloth 2026.8.22 + torch 2.8"
summary: "Recovered from S5 `continued_pretrain/kaggle/runpod_cpt_v3/cpt_eval.log`:"
priority: high
tags: [cpt, eval, unsloth, torch, pin, s5, hub-v2]
schema_version: 1.3
last_updated: "2026-09-20T19:01:29-03:00"
---

# CPT C-eval stack pin (S5 / Hub-v2 parity)

## Required for trustworthy CPT C of Qwen3.5-4B embed-FT LoRA
Recovered from S5 `continued_pretrain/kaggle/runpod_cpt_v3/cpt_eval.log`:

| Package | Pin |
|---------|-----|
| Unsloth | **2026.8.22** (`unsloth[colab-new]==2026.8.22`; Hub-v2 C used 2026.8.21) |
| torch | **2.8.0+cu126** (or image `2.8.0+cu128`) |
| torchvision | **0.23.0** (must match torch 2.8; 0.26 expects 2.11) |
| torchaudio | **2.8.0** |
| xformers | **omit** when pinning torch 2.8 (Unsloth 2026.8.22 may pull xformers wanting torch≥2.10) |
| Env | `UNSLOTH_SKIP_TORCHVISION_CHECK=1` if needed; `REQUIRE_AMPERE=1`; `load_in_4bit=False` |

## Do not use for C of S6 SHA `6aab…`
Unsloth **2026.9.6** + torch **2.11** produced false FAIL spurgeon **18.31 (+27.9%)**. Same weights on the pin above: **12.85 (−10.2%)**.

## Automation
- Env override: `UNSLOTH_PIP_SPEC` in `eval_cpt_sota.py`
- Train-probe slice: `CPT_EVAL_TRAIN_PROBE_DOCS=16`
- Scripts: `vast_remote_stack_isolation_c.sh`, `runpod_remote_stack_isolation_c.sh`

Evidence: `pretraining/cpt-s6-stack-isolation-c`.
