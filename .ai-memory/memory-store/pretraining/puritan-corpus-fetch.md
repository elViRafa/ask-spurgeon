---
store_path: pretraining/puritan-corpus-fetch
title: "Puritan PD corpus fetch (Archive.org)"
summary: "Puritan PD corpus fetch (Archive.org)"
priority: high
tags: [pretraining, data, puritans, archive-org]
schema_version: 1.3
last_updated: "2026-07-13T10:19:03-04:00"
evidence: [data/puritans/PROVENANCE.md, continued_pretrain/scripts/10_fetch_puritans.py]
review_status: stale
---

# Puritan PD corpus (2026-07-13)

Fetched public-domain OCR into `data/puritans/` (~18 MB) from Internet Archive DjVuTXT + a few Gutenberg Bunyan files. Title-verified where possible; early-modern OCR can be noisy (esp. Sibbes Bruised Reed).

## Authors on disk

Owen (4 works), Watson (Body of Divinity), Sibbes (Bruised Reed), Brooks (Precious Remedies + Complete Works vol 3), Baxter (Saints Rest + Reformed Pastor), Bunyan (4), Flavel (2), Gurnall (Complete Armour), Edwards (Religious Affections).

## Tooling

- `scripts/10_fetch_puritans.py` — re-fetch with verified IA `/download/` URLs + SSL workaround.
- Provenance table: `data/puritans/PROVENANCE.md`.

## Mix after rebuild

~22M chars / ~5.5M tokens: spurgeon 45% / puritan 51% / bible 4% / confession ~0%. Still need more confessions + FineWeb replay for targets.
