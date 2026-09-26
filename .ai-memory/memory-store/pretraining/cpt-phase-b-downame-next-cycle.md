---
store_path: pretraining/cpt-phase-b-downame-next-cycle
title: "Phase B mix a_output_v4 packed"
summary: "**Status:** Fetch + catalog + holdout-pin code done"
priority: medium
tags: [cpt, phase-b, downame, ocr]
schema_version: 1.3
last_updated: "2026-09-23T09:26:50-03:00"
evidence: [continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/scripts/11_fetch_confessions.py, continued_pretrain/scripts/07_build_theology_mix.py, data/puritans/downame/christian_warfare.txt, data/puritans/downame/guide_to_godliness.txt, continued_pretrain/data/holdouts_pinned_v3]
---

# Phase B corpus prep — Downame landed (mix still deferred)

**Status:** Fetch + catalog + holdout-pin code done. **No** `07` mix / `a_output_v4` until Phase A finishes.

## Done (2026-09-22)

### Downame (wave 4)
- `data/puritans/downame/christian_warfare.txt` — EEBO-TCP `A20752` (~1.65M chars)
- `data/puritans/downame/guide_to_godliness.txt` — EEBO-TCP `A20762` (~4.06M chars)
- Catalog: `10_fetch_puritans.py` `_wave4_catalog()`; PROVENANCE Wave 4 section

### Confession S5 (catalog only — not on disk)
- Wired in `11_fetch_confessions.py` as `S5_CATALOG` + `--s5`:
  - `shaw_exposition_wcf` (IA `expositionofconf00shaw`)
  - `sum_of_saving_knowledge` (Reformed Standards / Wikisource)
- **Skipped fetch:** after Downame, confession disk ~30.7 MB still exceeds max ≈27.3 MB at `--max-confession-share 0.06` (headroom **−3.39 MB**). Adding S5 would worsen random S4 systematic eviction under `_cap_bucket_to_final_share`.

### Holdout pin
- Snapshot: `continued_pretrain/data/holdouts_pinned_v3/`
- `07_build_theology_mix.py` pins `puritan_holdout.txt` / `confession_holdout.txt` when present (fingerprint = first 200 chars), same pattern as Spurgeon. Downame stays train-only.

### Rejected near-dupes (do not reopen)
Savoy, Vincent WSC exposition, Fisher catechism — WCF/WSC near-duplicates under paragraph dedup.

## After Phase A

```text
python continued_pretrain/scripts/07_build_theology_mix.py --target-spurgeon-share 0.45 --keep-all-spurgeon --max-other-weight 1.5 --max-confession-share 0.06 --replay-frac 0.10 --replay-txt continued_pretrain/data/replay/general_replay.txt
python continued_pretrain/scripts/06_verify_tokens.py --mix
python continued_pretrain/scripts/18_prep_hf_dataset.py --out-dir continued_pretrain/kaggle/a_output_v4
```

Playbook: `continued_pretrain/NEXT_CPT_S7.md` (Later — Phase B).

## Do not
- Rebuild mix / overwrite `a_output_v3` during Phase A
- Fetch S5 while headroom is negative
- Redraw puritan/confession holdouts
- Raise confession cap to force Shaw in

## Long-s normalization (2026-09-22)

EEBO-TCP long-s (`ſ`→`s`) applied on disk for Downame **and** 21 other Puritan files + `wcf_catechisms_1756.txt` (23 shelf files had ~2–3% long-s; Ames/modern IA reprints were already clean). Cleaners updated in `10_fetch_puritans`, `11_fetch_confessions`, and `07` mix. Helper: `continued_pretrain/scripts/normalize_early_modern_orthography.py`.

## Wave 5 landed 2026-09-23 (mix still deferred)

Nine new-author practical-divinity texts on disk (~8.47M chars). Catalog `_wave5_catalog()` in `10_fetch_puritans.py`. Confession S5 still skipped (headroom). Next is mix → `a_output_v4` when operator starts Phase B mix — do not rebuild yet.

## Phase B mix landed (2026-09-23)

`a_output_v4` SHA `37a3ba50…` packed. Holdouts still pinned. Mix rebuild no longer deferred.
