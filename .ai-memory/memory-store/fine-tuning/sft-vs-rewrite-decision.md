---
store_path: fine-tuning/sft-vs-rewrite-decision
title: "SFT vs QA rewrite decision (2026-09-02)"
summary: "- **Pass 1 complete:** all 3244 non-gold train rows attempted once"
priority: high
tags: [fine-tuning, sft, qa-rewrite, decision]
schema_version: 1.3
last_updated: "2026-09-02T08:01:47-04:00"
review_status: stale
---

# SFT vs QA rewrite — decision context (2026-09-02)

## QA rewrite stop point

- **Pass 1 complete:** all 3244 non-gold train rows attempted once.
- **Pass 2 retry-drops optional:** 1778 rows still failing validation (no ok=true).
- Metrics at stop: quote **49.1%**, teacherish **1485**, caricature **0**, ~1438 originalish remaining.

## Implications

| Start dry-run SFT now | Continue rewrite |
|----------------------|------------------|
| Validates D→E→F pipeline on stock base | Marginal quote/faithfulness lift |
| ~45% train still legacy-style answers | Time + provider quota cost |
| Kaggle zip must be repackaged first | Multiturn/catechism tail often fails quote gate |
| Not final CPT-merged model | Delays first eval signal |

## Recommendation recorded

Gates met → **dry-run SFT is low-regret**; rewrite is optimization not blocking. Final production SFT waits CPT S6 + operator go.

## Before GPU

1. `12_package_kaggle_qa_mix.py`
2. Operator explicit go
3. `KAGGLE_RUNBOOK_SFT_V2.md` §2–3 (`USE_CPT_MERGE=False` for dry-run)
