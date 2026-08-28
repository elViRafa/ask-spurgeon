---
store_path: pretraining/cpt-v2-c-eval-runpod-complete
title: "CPT v2 Runpod C complete — probe PPL beats bf16 base"
summary: "Community RTX 4090 Ampere bf16"
priority: high
tags: [cpt, runpod, c-eval]
schema_version: 1.3
last_updated: "2026-08-27T09:01:07-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v2/cpt_eval.log, continued_pretrain/scripts/eval_cpt_sota.py]
---

# CPT v2 Runpod C eval — COMPLETE 2026-08-27

Community RTX 4090 Ampere bf16. Pod `rf2dayesihddon` **deleted**. `RUN_MERGE=False`. No network volume (MCP cannot attach `7hb931c5oe`).

## Adapter scored
`continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_lora` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478` (B best ckpt-400, embed-FT + GDN).

## Scorecard vs this run’s bf16 base
Do not mix with C v4 T4 4-bit PPL.

| Bucket | Base | v2 | %Δ |
|--------|------|-----|-----|
| spurgeon | 14.31 | 13.28 | −7.2% |
| puritan | 5.99 | 5.68 | −5.0% |
| confession | 7.24 | 6.73 | −7.0% |
| general | 13.43 | 13.20 | −1.7% |

Probe (beat base): **PASS** all four. §5 −15% on puritan/confession: **FAIL**. MCQ WSC 70→74; Heidelberg 40.5→45.2 (need +10).

Artifacts: `kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json`, `kaggle/runpod_cpt_v2/cpt_eval.log`.

Code: `eval_cpt_sota.py` (`--preflight`, `--install --break-system-packages`, HF_HOME, SHA256 pin, two model loads).
