---
store_path: pretraining/cpt-v2-c-eval-gate-verdict
title: "CPT v2 C_eval gate FAIL (C v4 scored ckpt-25)"
summary: "**FAIL — do not merge.** C v4 COMPLETE on B v6 **best** LoRA (checkpoint-25), not a last-step accident"
priority: high
tags: [kaggle, cpt, handoff, gate]
schema_version: 1.3
last_updated: "2026-08-25T10:20:50-04:00"
evidence: [continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md, continued_pretrain/kaggle/c_output/theology_cpt_eval_metrics.json, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# CPT v2 C_eval gate verdict (2026-08-25, analysis addendum)

**FAIL — do not merge.** C v4 COMPLETE on B v6 **best** LoRA (checkpoint-25), not a last-step accident.

## Adapter identity
SHA256 of `adapter_model.safetensors` is identical for:
- B `checkpoints_sota/checkpoint-25`
- B `theology_cpt_lora`
- C `theology_cpt_lora_final`

`checkpoint-50` / `checkpoint-75` differ and are worse on B `eval_spurgeon_loss`. **Do not** spend a C session on `ADAPTER_OVERRIDE=checkpoint-25`.

## Δ PPL vs base (%)
spurgeon +2.0 | puritan +2.2 | confession +1.9 | general +3.8

- Spurgeon/puritan/confession: worse than base → FAIL
- General within +10% → PASS alone
- Uniform ~+0.02 nats = LoRA noise, not domain learning

## Why (not P1)
Scored ckpt is step 25 ≈ **0.82M tokens** (~5.5% of a 14.9M packed epoch). Recipe was VRAM fallback: r=32, **TRAIN_EMBEDDINGS=False**, MAX_STEPS cap 100. §5 −15% puritan/confession was written for embed CPT × ~1 epoch.

## MCQ
WSC 70%→76% (+6) | Heidelberg 38.1%→42.9% (+4.8, need +10). MCQ alone does not ship.

## Next
B v7: batch 1×16, TRAIN_EMBEDDINGS=True, MAX_STEPS ≈ one packed epoch, quieter early-stop. C **only after** B v7. Do not merge until §5 PPL PASS.
