---
store_path: pretraining/cpt-phase-b-mix-a-output-v4
title: "Phase B mix a_output_v4 packed; no GPU"
summary: "**Status:** Mix rebuilt + verified + packed"
priority: high
tags: [cpt, phase-b, mix, a-output-v4, wave5]
schema_version: 1.3
last_updated: "2026-09-23T09:26:48-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/data/corpus_v3_catalog.json]
---

# Phase B mix a_output_v4 ready (2026-09-23)

**Status:** Mix rebuilt + verified + packed. **No GPU / CPT train.**

## Identity
- Path: `continued_pretrain/kaggle/a_output_v4`
- `mix_sha256`: `37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81`
- Frozen S7 mix: `a_output_v3` SHA `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973` (untouched)

## Counts
- Train docs 54,799 (HF 54,251 / val 548)
- Verified tokens ~94.7M (Qwen3.5-4B-Base, ratio 0.2848)
- Shares: puritan 47.8% / spurgeon 38.4% / general 7.2% / confession 5.3% / bible 1.3%
- Holdouts pinned v3: puritan 20 + confession 10 fingerprints match
- Henry exposition excluded

## In train
Downame + wave 5 (Ambrose, Swinnock ×2, Venning, Binning, Preston, Durham, Vincent, Guthrie).

## Do not
- Overwrite `a_output_v3`
- Redraw holdouts
- Fetch confession S5
- Start GPU until operator says go (init Hub S7 s5best `06354dfc…` on this mix)
