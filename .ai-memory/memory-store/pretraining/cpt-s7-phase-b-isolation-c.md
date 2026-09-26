---
store_path: pretraining/cpt-s7-phase-b-isolation-c
title: "Phase B isolation C: 12.39 / 5.50 / 5.25; §5 FAIL"
summary: "Nested §5 export step 600 SHA `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214` on Unsloth **2026.8.22 + torch 2.8**"
priority: high
tags: [cpt, s7, c-eval, phase-b, ddbbee3a, vast]
schema_version: 1.3
last_updated: "2026-09-26T08:12:03-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_b_c/theology_cpt_eval_metrics.json, continued_pretrain/scripts/vast_cpt_s7_c_eval.ps1]
---

## Phase B isolation C COMPLETE (2026-09-23)

Nested §5 export step 600 SHA `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214` on Unsloth **2026.8.22 + torch 2.8**. Vast instance `52296492` destroyed after fetch. Artifacts: `kaggle/runpod_cpt_v3/vast_cpt_s7_b_c/`.

Do **not** eval the top-level `fetch/theology_cpt_lora_s5best/` file — that is still Phase A `06354dfc`.

### Scorecard (pinned v3 holdouts, Ampere bf16)

| Bucket | Base | Phase B C | Δ% | Hub `06354dfc` |
|--------|------|-----------|-----|----------------|
| spurgeon | 14.31 | **12.39** | **−13.42%** | 12.45 (−13.0%) |
| puritan | 6.03 | **5.50** | **−8.88%** | 5.52 (−8.6%) |
| confession | 5.61 | **5.25** | **−6.37%** | 5.27 (−6.0%) |
| general | 12.05 | 11.88 | −1.34% | 11.95 |

Train probe Spurgeon@16: ppl 11.83 (−11.09% vs base 13.30). MCQ: WSC 0.74 / Heidelberg 0.45.

### Gate
§5 −15% Puritan+confession: **FAIL**. Slightly better than Hub on all three; not a promote. Optional C on HF-best `6d003041` was skipped — one adapter is enough for the gate.
