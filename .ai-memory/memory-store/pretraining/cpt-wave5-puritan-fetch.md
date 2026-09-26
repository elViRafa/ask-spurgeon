---
store_path: pretraining/cpt-wave5-puritan-fetch
title: "Wave 5 Puritan fetch complete; mix still deferred"
summary: "**Status:** Catalog + fetch + long-s normalize done"
priority: medium
tags: [cpt, wave5, puritans, corpus, phase-b]
schema_version: 1.3
last_updated: "2026-09-23T09:19:24-03:00"
evidence: [continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/data/corpus_v3_catalog.json, continued_pretrain/NEXT_CPT_S7.md, data/puritans/PROVENANCE.md]
---

# Wave 5 Puritan fetch (2026-09-23)

**Status:** Catalog + fetch + long-s normalize done. **No** mix rebuild / `a_output_v4` / CPT train.

## Landed (9/9, 0 fail)

| Key | Path | Source | Chars |
|-----|------|--------|-------|
| ambrose_looking_unto_jesus | data/puritans/ambrose/looking_unto_jesus.txt | EEBO-TCP A25241 | 2,821,289 |
| swinnock_works | data/puritans/swinnock/works_1665.txt | EEBO-TCP A62040 | 1,645,784 |
| swinnock_incomparableness | data/puritans/swinnock/incomparableness_of_god.txt | EEBO-TCP A62054 | 359,563 |
| venning_plague_of_plagues | data/puritans/venning/plague_of_plagues.txt | EEBO-TCP A64834 | 601,046 |
| binning_sinners_sanctuary | data/puritans/binning/sinners_sanctuary.txt | EEBO-TCP A28173 | 740,940 |
| preston_breastplate | data/puritans/preston/breastplate_of_faith_and_love.txt | EEBO-TCP A09950 | 934,050 |
| durham_unsearchable_riches | data/puritans/durham/unsearchable_riches_of_christ.txt | EEBO-TCP B02840 | 686,701 |
| vincent_unseen_christ | data/puritans/vincent/true_christians_love_of_the_unseen_christ.txt | EEBO-TCP A64995 | 271,893 |
| guthrie_great_interest | data/puritans/guthrie/christians_great_interest.txt | CCEL guthrie/interest2 | 412,795 |

Total **8,474,061 chars** (~8.5 MB). Long-s already 0 after fetch; `normalize_early_modern_orthography.py` rewrote 0 files.

## Skipped (plan)
- Gillespie Aaron's Rod (polity)
- Extra titles by authors already on disk
- Confession S5 (Shaw / Sum of Saving Knowledge): 6% of added mix is only ~0.5 MB; confession disk still over cap
- Vincent WSC / Fisher / Savoy near-dupes

## Do not
- Rebuild mix / pack `a_output_v4` until operator starts Phase B mix
- Redraw puritan/confession holdouts (keep `holdouts_pinned_v3`)
- Fetch S5, scrape Banner/Heritage/Puritan Publications
