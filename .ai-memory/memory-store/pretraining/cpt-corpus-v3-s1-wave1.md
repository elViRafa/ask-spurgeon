---
store_path: pretraining/cpt-corpus-v3-s1-wave1
title: "CPT corpus v3 S1 Wave 1 fetch + mix"
summary: "**No B, no C, no Runpod GPU, no Kaggle push, no merge, no Hub overwrite.**"
priority: high
tags: [cpt, corpus, wave1, mix, puritans]
schema_version: 1.3
last_updated: "2026-08-27T11:02:21-04:00"
evidence: [continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/scripts/07_build_theology_mix.py, continued_pretrain/data/theology_mix_manifest.json, data/puritans/PROVENANCE.md, data/confessions/PROVENANCE.md]
---

# CPT corpus v3 S1 — Wave 1 fetch + mix (2026-08-27)

**No B, no C, no Runpod GPU, no Kaggle push, no merge, no Hub overwrite.**

## Mix policy shipped
- Denylist in `07_build_theology_mix.py`: default `--exclude-glob` skips `henry/exposition*` (file stays on disk). Manifest `exclude_globs` confirms.
- Hodge ST vol.1 moved `data/puritans/hodge/` → `data/confessions/systematic/`; vols 2–3 fetched there. Confession/ST bucket, not Puritan mass.
- Hymns folded into the Puritan bucket from `data/hymns/`.
- Calvin treatises/sermons under `data/puritans/calvin/` (Institutes stay in confessions).

## Disk after Wave 1
~165.6 MB txt under puritans + hymns + systematic (was ~34.4 MB). **+~131 MB** unique. Henry exposition 5.1 MB still on disk, **not** in mix.

Largest new shelves: Manton 41.7 MB (20/22 vols), Owen Goold remaining 27 MB, Sibbes complete works, Brooks remaining vols, Goodwin 1–4, Edwards extra, Hodge ST 2–3, Calvin tracts, Rutherford Letters + Lex Rex, Herbert, Watts + Olney.

**S2 leftovers (IA 503/403 or bad Gutenberg IDs):** Burroughs Rare Jewel + Gospel Worship; Perkins Golden Chain + cases; Flavel remaining complete-works vols; Watson Godly Man's Picture; Henry Method of Prayer; Manton vols 12+22; Scottish Psalter 1650.

## Mix rebuilt (`--no-keep-all-spurgeon`)
`--target-spurgeon-share 0.45 --replay-frac 0.10 --replay-txt continued_pretrain/data/replay/general_replay.txt`

| Metric | v2 (old) | v3 S1 |
|--------|----------|-------|
| spurgeon_weight | 0.164 | **0.6586** |
| train chars | 51.5M | 203.1M |
| verified tokens (Qwen3.5-4B-Base) | 15.6M | **57.60M** |
| docs | 8245 | 32878 |
| Henry in mix | yes | **no** |

Shares: Spurgeon 41.3%, Puritan 45.7% (above 30–40 band until more Spurgeon is kept), confession 2.7%, Bible 2.1%, general 8.2%. `keep-all` other_weight would be ~1.52 (>1.5) — correctly not used.

Do not train until operator approval (plan S5).
