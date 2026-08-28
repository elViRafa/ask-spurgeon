---
store_path: pretraining/cpt-corpus-expansion-2026-08
title: "CPT corpus expansion (Puritans/Edwards)"
summary: "Grew non-Spurgeon domain text so Spurgeon in-mix could rise while keeping ~45% share"
priority: high
tags: [pretraining, cpt, corpus, puritans, edwards]
schema_version: 1.3
last_updated: "2026-08-24T22:54:43-04:00"
evidence: [data/puritans/PROVENANCE.md, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# CPT corpus expansion (2026-08-24)

Grew non-Spurgeon domain text so Spurgeon in-mix could rise while keeping ~45% share.

## Results

| Metric | Before | After |
|--------|--------|-------|
| Raw Puritans | ~18 MB | ~34.4 MB |
| Mix chars | ~27.4M | ~51.5M |
| Verified tokens | ~8.2M | ~15.6M |
| Docs | 4401 | 8245 |
| Spurgeon weight | 0.087 | 0.164 |

Shares remain on target: Spurgeon ~40.5%, Puritan ~40.9%, confession ~5%, Bible ~3.6%, general ~10%.

## New PD sources (OCR PASS)

Watson All Things for Good (CCEL), Brooks Mute Christian, Sibbes Soul's Conflict, Edwards Freedom of the Will + Justification, Charnock Existence & Attributes, Boston Crook in the Lot, Flavel Fountain of Life, Owen Goold vol.10, Henry exposition vol.5, Hodge ST vol.1.

## Tooling

- Extended 10_fetch_puritans.py CATALOG + OCR quality gate
- 17_build_general_replay.py rebuilds Gutenberg classics replay
- Recipe v4 validated locally; config JSON aligned
- Packaged + uploaded theology-cpt-corpus; A refreshed theology-cpt-dataset (8245 docs)

## Do not

- Force full Spurgeon without more non-Spurgeon mass
- Inflate Bible share via repetition
- Merge CPT until section 5 holdout PPL gate passes on v4+expanded retrain
