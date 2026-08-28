---
store_path: pretraining/cpt-corpus-v3-s5-c-ready
title: "CPT corpus v3 S5 C — done; do not re-C"
summary: "Canonical write-up: `pretraining/cpt-corpus-v3-s5-c-complete`"
priority: high
tags: [cpt, corpus-v3, s5, eval, runpod]
schema_version: 1.3
last_updated: "2026-08-27T23:33:00-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/NEXT_CPT_MORE_TOKENS.md]
---

# CPT corpus v3 S5 C — DONE (2026-08-28)

C already ran. GPU deleted. Do not re-C this adapter. Do not merge. Do not overwrite Hub `...-cpt-lora-v2`.

Canonical write-up: `pretraining/cpt-corpus-v3-s5-c-complete`. Artifacts: `continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json`.

Probe vs this C Ampere base: **PASS**. §5 −15%: **FAIL**. Keep Hub v2. Next GPU only if the operator wants a lower-LR more-tokens continue (`continued_pretrain/NEXT_CPT_MORE_TOKENS.md`). Optimizer was never copied; no HF resume.
