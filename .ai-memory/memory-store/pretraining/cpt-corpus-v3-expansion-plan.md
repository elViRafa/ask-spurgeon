---
store_path: pretraining/cpt-corpus-v3-expansion-plan
title: "CPT corpus v3 expansion plan (no training)"
summary: "Runpod C: spurgeon −7.2%, puritan −5.0%, confession −7.0% vs Ampere bf16 base"
priority: high
tags: [cpt, corpus, puritans, mix, plan]
schema_version: 1.3
last_updated: "2026-08-27T10:10:45-04:00"
evidence: [continued_pretrain/CORPUS_V3_EXPANSION_PLAN.md, continued_pretrain/data/corpus_v3_catalog.json, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# CPT corpus v3 expansion plan (2026-08-27)

Plan only. **No B, no C, no merge, no Kaggle push.** Keepable LoRA remains `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` (SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`). New C only after a new adapter.

## Why
Runpod C: spurgeon −7.2%, puritan −5.0%, confession −7.0% vs Ampere bf16 base. §5 −15% FAIL. Heidelberg +4.7 pts (need +10). Mix still **15.6M tokens**, Spurgeon **weight 0.164** (drops ~84% of sermons).

## Recipe lock
Same packing (`one_doc_padded`). Different sampling. Do **not** `--keep-all-spurgeon` until other-bucket oversample would be ≤1.5. Grow unique Puritan/Reformed mass first so weight can rise toward 0.6–1.0.

## Mix policy
- **Drop** `data/puritans/henry/exposition_vol5.txt` (commentary mass).
- **Keep** Hodge ST; add vols 2–3; move under confessions/systematic.
- **Add** Owen Goold remaining, Manton CCEL, Edwards, Calvin treatises/sermons, Herbert, Watts/Olney/Psalter, Rutherford, Alleine, Bayly, Burroughs, Perkins, Goodwin, plus Wave 2 named Puritans.
- Old Hodge/Calvin **commentary** only under a **10–15 MB cap**.
- Banner of Truth / Heritage / Puritan Publications: **titles only**, no body scrape.

## Files
- `[REDACTED_SECRET].md`
- `continued_pretrain/data/corpus_v3_catalog.json`

## Next session = S1 fetch Wave 1. Still no training without approval.
