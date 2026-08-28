---
store_path: pretraining/cpt-v2-session-2026-08-27-results
title: "CPT v2 2026-08-27 session results (C + LoRA + private Hub)"
summary: "Canonical write-up is SESSION RESULTS markdown inside `continued_pretrain/kaggle/runpod_cpt_v2/` (same folder as the LoRA and eval JSON)"
priority: high
tags: [cpt, runpod, c-eval, lora, handoff]
schema_version: 1.3
last_updated: "2026-08-27T09:49:53-04:00"
evidence: [continued_pretrain/CPT_V2_KAGGLE_STATUS.md, continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json]
---

# CPT v2 session results 2026-08-27

Canonical write-up is SESSION RESULTS markdown inside `continued_pretrain/kaggle/runpod_cpt_v2/` (same folder as the LoRA and eval JSON).

## Verdict
- Probe bar **PASS**: all four holdout PPLs better than this C's Ampere bf16 base.
- Plan section 5 (-15% puritan/confession) **FAIL**.
- **Do not merge. Do not re-C this adapter. Do not push Kaggle.** Mix still 0.164.

## C PPL (base to adapter, % better)
- spurgeon 14.31 to 13.28 (-7.25%)
- puritan 5.99 to 5.68 (-5.05%)
- confession 7.24 to 6.73 (-6.98%)
- general 13.43 to 13.20 (-1.73%)
MCQ: WSC 70% to 74%; Heidelberg 40.5% to 45.2% (need +10).

## Adapter
- Best step 400; SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Local `theology_cpt_lora` under kaggle/runpod_cpt_v2; Ampere bf16 only; embed_tokens saved.
- Private Hub: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` (uploaded this day after SHA256 check). Weights also on disk, gitignored.
- GPU pod deleted. Volume 7hb931c5oe unused.

## Next
Decide mix rebuild / more tokens vs ship this LoRA as-is. Need runpodctl plus API key to attach the volume on a future GPU.
