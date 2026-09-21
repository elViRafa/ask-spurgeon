---
store_path: pretraining/cpt-s6-c-eval-complete
title: "S6 C-eval: Vast false FAIL; isolation PASS 12.85"
summary: "Path: `vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/`"
priority: low
tags: [cpt, s6, c-eval, hub-v2, stack-isolation]
schema_version: 1.3
last_updated: "2026-09-20T19:01:32-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/theology_cpt_eval_metrics.json, pretraining/cpt-s6-c-eval-regression-diagnosis]
---

# S6 C-eval COMPLETE — Vast false FAIL; stack-isolation PASS

## Adapter
Path: `vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/`  
SHA256: `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` (ckpt-2050)

## Vast C (Unsloth 2026.9.6 / torch 2.11) — do not trust for Hub decision
spurgeon 18.31 (**+27.9%**). Probe FAIL. Artifacts: `vast_cpt_s6/c_eval/`.

## Stack-isolation C (Unsloth 2026.8.22 / torch 2.8) — canonical for this SHA
spurgeon **12.85 (−10.2%)**, puritan −7.2%, confession −6.0%, general −1.8%. Probe **PASS**. §5 −15% still FAIL.  
Full: `pretraining/cpt-s6-stack-isolation-c`. Artifacts: `kaggle/runpod_cpt_v3/stack_isolation_c/`.

## Hub
Still keep `…-theology-cpt-lora-v2` until **explicit** overwrite approve (S6 beats Hub v2 13.28 on isolation scorecard).
