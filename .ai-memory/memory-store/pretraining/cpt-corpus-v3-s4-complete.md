---
store_path: pretraining/cpt-corpus-v3-s4-complete
title: "CPT corpus v3 S4 complete (confession/ST lift, no training)"
summary: "S4 fetch + mix rebuild finished 2026-08-27"
priority: high
tags: [cpt, corpus-v3, s4, mix, tokens, confession]
schema_version: 1.3
last_updated: "2026-08-27T17:01:34-04:00"
evidence: [continued_pretrain/CORPUS_V3_S4_HANDOFF.md, continued_pretrain/CORPUS_V3_S5_HANDOFF.md, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/scripts/11_fetch_confessions.py]
---

S4 fetch + mix rebuild finished 2026-08-27. No B/C, no Kaggle, no merge, no Hub LoRA overwrite. Do not re-fetch Wave 3. Do not add more commentary. Do not grow Puritan treatise mass.

S4 unique PD confession/ST **12/12**: Gill doctrinal (CCEL), Dabney syllabus, Shedd Dogmatic 1-3, A.A. Hodge Outlines 1878, Witsius Covenants 1-2, Boyce Abstract, Second Helvetic (Schaff creeds3.v.ix.html), Scots 1560, Canons of Dort (Schaff Dort page only). Turretin English **skipped** (P&R/Dennison copyright). Heidelberg/Belgic still holdout-only.

Manifest `created_at` 2026-08-27T19:58:31Z:
- spurgeon_weight **1.068846**, spurgeon_keep_all **false** (weight > 1; all sermons used), other_bucket_weight **1.0**
- train_docs **51937**, train_chars **316,512,374**
- verified tokens **91,307,937** (Qwen3.5-4B-Base, sample ratio 0.287726)
- shares S **40.2** / P **45.7** / C **5.5** / B **1.4** / G **7.2**

Confession **5.5%** is in the 3-6% band (S3 was 1.8%). Mix rebuilt with `--keep-all-spurgeon --max-other-weight 1.5`. Henry exposition still denylisted. Packing `one_doc_padded`. Puritans unchanged 221.1 MB / 150 files. `data/confessions/` 30.7 MB / 21 files. Preflight PASS_WITH_WARNINGS (Puritan 45.7% just over 45%; Bible/general still low).

Fallback LoRA: rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 SHA256 319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478

Next = S5 Runpod B with operator approval. Handoff: `continued_pretrain/CORPUS_V3_S5_HANDOFF.md`.
