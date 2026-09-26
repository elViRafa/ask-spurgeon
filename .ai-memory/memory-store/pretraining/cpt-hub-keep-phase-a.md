---
store_path: pretraining/cpt-hub-keep-phase-a
title: "Do not Hub-overwrite with Phase B ddbbee3a"
summary: "Do **not** upload Phase B C-winner `ddbbee3a` to Hugging Face and do **not** make it the new Hub version"
priority: high
tags: [cpt, s7, hub, ddbbee3a, decision]
schema_version: 1.3
last_updated: "2026-09-26T08:12:05-03:00"
evidence: [pretraining/cpt-s7-phase-b-isolation-c, pretraining/cpt-hub-s7-overwrite]
---

## Operator decision 2026-09-26

Do **not** upload Phase B C-winner `ddbbee3a` to Hugging Face and do **not** make it the new Hub version.

Hub production stays `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…`.

Why: C deltas vs Hub are a few hundredths of PPL (12.45→12.39 / 5.52→5.50 / 5.27→5.25). §5 is still open (−8.9% / −6.4% vs −15%). Overwriting would drop the Hub baseline the next C must beat.

`ddbbee3a` is the local **init** for the `a_output_v6` holdout-sibling replay only. Promote after a later C wins both Puritan and confession without Spurgeon past ~13.3.
