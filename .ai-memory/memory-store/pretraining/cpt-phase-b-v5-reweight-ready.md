---
store_path: pretraining/cpt-phase-b-v5-reweight-ready
title: "Phase B v5 reweight packed; no GPU"
summary: "**Status:** Reweight mix built + verified + packed"
priority: high
tags: [cpt, phase-b, a-output-v5, reweight, wave5, downame]
schema_version: 1.3
last_updated: "2026-09-23T11:47:14-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json, continued_pretrain/data/mix_v5/theology_mix_manifest.json, continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/scripts/07_build_theology_mix.py]
---

# Phase B continue pack a_output_v5 ready (2026-09-23)

**Status:** Reweight mix built + verified + packed. **No GPU / no rent / no Hub overwrite.**

## Identity
- Path: `continued_pretrain/kaggle/a_output_v5`
- Mix txt: `continued_pretrain/data/mix_v5/theology_mix_train.txt`
- `mix_sha256`: `61e830575138935cdf6c1b029a3128e096ff4e3633e44a464b3957b9d6e78285`
- Frozen uniform v4: `a_output_v4` SHA `37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81`
- Frozen Phase A v3: `a_output_v3` SHA `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`

## Counts
- Train docs 15,420 (HF 15,265 / val 155)
- Verified tokens ~25.1M (Qwen3.5-4B-Base, ratio 0.2701)
- New-author one pass: 2,454 docs / 13.9M chars = **15.0%**
- Shares: puritan 54.2% / spurgeon 33.8% / general 6.3% / confession 4.5% / bible 1.3%
- Holdouts pinned v3 (20 / 10 / 298)

## Continue knobs
- Init Hub / local S7 s5best `06354dfc…`, new Adam, `PREV_RUN_CHECKPOINT=`
- `CONTINUE_MAX_STEPS=955` (one packed epoch, batch 16)
- `EARLY_STOP_MIN_STEPS=400`
- Composite seeds: spurgeon 2.4987 / puritan 1.751 / confession 1.668. **No eval_mix_loss seed.**

## Do not
- Overwrite v3 or v4
- Copy uniform v4 for GPU
- Train new-authors-only
- Fetch confession S5
- Redraw holdouts
- Rent until operator go
