---
store_path: pretraining/cpt-corpus-v3-s1-complete
title: "CPT corpus v3 S1 complete (mix verified, no training)"
summary: "**No B, no C, no Wave 2 fetch, no Runpod GPU, no Kaggle push, no merge, no Hub overwrite.**"
priority: high
tags: [cpt, corpus, s1, mix, no-train]
schema_version: 1.3
last_updated: "2026-08-27T11:06:09-04:00"
evidence: [continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/CORPUS_V3_EXPANSION_PLAN.md, continued_pretrain/CPT_V2_KAGGLE_STATUS.md, data/confessions/systematic/systematic_theology_vol1.txt]
---

# CPT corpus v3 S1 complete (2026-08-27 follow-up verify)

**No B, no C, no Wave 2 fetch, no Runpod GPU, no Kaggle push, no merge, no Hub overwrite.**

Verified against `continued_pretrain/data/theology_mix_manifest.json` (created_at 2026-08-27T14:56:16Z). Numbers match the S1 claim.

## Actual mix
- `spurgeon_weight`: **0.658552** (display **0.6586**)
- `verified_tokens.train_estimated_tokens`: **57,603,516** (**57.60M**), tokenizer Qwen3.5-4B-Base, sample_ratio 0.282874
- `train_docs`: **32878**
- `train_chars`: **203,110,613** (**203.1M**)
- Char shares: Spurgeon 41.3%, Puritan 45.7%, confession 2.7%, Bible 2.1%, general 8.2%

## Henry / Hodge
- Henry exposition **not in mix**: `exclude_globs` `henry/exposition*` and `**/henry/exposition*`. File still on disk: `data/puritans/henry/exposition_vol5.txt` (~4.87 MB) plus `communicants_companion.txt` (~0.7 MB).
- Hodge ST under `data/confessions/systematic/`: `systematic_theology_vol1.txt` (1.94 MB), `vol2` (2.24 MB), `vol3` (2.67 MB). Empty leftover dir `data/puritans/hodge/`.

## On-disk shelves (txt)
- `data/puritans`: **150.2 MB** (97 files)
- `data/hymns`: **0.9 MB** (2 files; Watts + Olney)
- `data/confessions`: **12.0 MB** (11 files; systematic 6.8 MB of that)

## S2 leftovers (not fetched)
- Burroughs Rare Jewel / Gospel Worship
- Perkins Golden Chain
- Flavel complete-works vols
- Watson Godly Man's Picture
- Henry Method of Prayer
- Manton vols 12 and 22
- Scottish Psalter 1650

Do not train until operator approval (plan S5).
