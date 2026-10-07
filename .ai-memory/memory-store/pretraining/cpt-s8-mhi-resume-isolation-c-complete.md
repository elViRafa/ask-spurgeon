---
store_path: pretraining/cpt-s8-mhi-resume-isolation-c-complete
title: "S8 m_hi resume Isolation C: 11.88/5.26/5.01; section 5 miss"
summary: "Pre-run estimate was puritan loss about 1.673"
priority: low
tags: [cpt, s8, isolation-c, scorecard, section-5]
schema_version: 1.3
last_updated: "2026-10-07T08:49:32-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume_c/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume_c/result.txt]
---

# S8 m_hi resume Isolation C complete (2026-10-07)

Eval finished rc=0. Fetched 2026-10-07 08:37 America/Sao_Paulo into `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume_c/`. Adapter SHA `2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207` (step 2250). Merge parent `a70fded8` rebuilt on the pod. Stack Unsloth 2026.8.22 + torch 2.8.0+cu126. Holdout token counts match every prior C (spurgeon 70369/50, puritan 36665/20, confession 19716/10, general 16415/10).

## Verdict

Section 5 **MISS**. Puritan loss **1.6605** vs gate **1.6349** (gap 0.0256 nats, about −12.8% PPL vs −15%). Spurgeon is better than the stock base, so that half of the gate passes. Hub stays Phase A `06354dfc`. Do not promote.

Pre-run estimate was puritan loss about 1.673. Actual beat the estimate and still missed.

## Scorecard (PPL, lower better)

| Bucket | Untrained base | Hub Phase A 06354dfc | This C 22698039 |
|--------|----------------|----------------------|-----------------|
| spurgeon | 14.31 | 12.45 (−13.0%) | **11.88 (−17.0%)** |
| puritan | 6.03 | 5.52 (−8.6%) | **5.26 (−12.8%)** |
| confession | 5.61 | 5.27 (−6.0%) | **5.01 (−10.7%)** |
| general | 12.05 | 11.95 (−0.8%) | **12.50 (+3.8%)** |

Also beats prior best local C (P0 `a70fded8`: 12.33 / 5.46 / 5.19 / 11.84) on the three theology buckets. General is worse than both Hub and P0, and worse than the untrained base.

MCQ: WSC 70%→76%, Heidelberg 43%→48% (Hub was 74% / 45%). Train-probe Spurgeon@16: 11.44 vs base 13.30 (−14.0%; Hub was −10.6%).

## Do not

- Hub-push
- Treat general +3.8% as noise; token counts match prior C runs
- Start another train without operator go
