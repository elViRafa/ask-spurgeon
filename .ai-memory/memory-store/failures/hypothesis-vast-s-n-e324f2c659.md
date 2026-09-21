---
store_path: failures/hypothesis-vast-s-n-e324f2c659
title: "Hypothesis: Vast S6 C +27.9% spurgeon PPL caused by untied embed/lm_head (ensure"
summary: "Hypothesis: Vast S6 C +27.9% spurgeon PPL caused by untied embed/lm_head (ensure_weight_tying=false)"
priority: medium
tags: [c-eval, cpt, failure, fix, peft, s6, tying]
schema_version: 1.3
last_updated: "2026-09-18T20:31:31-03:00"
occurrences: 1
error_signature: "hypothesis: vast s<n> c +<n>.<n>% spurgeon ppl caused by untied embed<path> (ensure_weight_tying=false)."
---

## Occurrence 1 — 2026-09-18T20:31:31-03:00

**Error:**
Hypothesis: Vast S6 C +27.9% spurgeon PPL caused by untied embed/lm_head (ensure_weight_tying=false).

**Fix:**
Added maybe_sync_tied_lm_head to eval_cpt_sota.py; re-C showed same_storage=0 but max_abs_delta≈0.002; after embed→lm_head copy PPL still 18.31 (+27.9%). Tying is NOT the regression cause. Keep Hub v2; treat Aug-28 13.34-for-6aab as unproven.
