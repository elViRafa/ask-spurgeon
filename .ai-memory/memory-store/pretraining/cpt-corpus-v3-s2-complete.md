---
store_path: pretraining/cpt-corpus-v3-s2-complete
title: "CPT corpus v3 S2 complete (fetch + mix, no training)"
summary: "S2 fetch + mix rebuild finished 2026-08-27"
priority: high
tags: [cpt, corpus-v3, s2, mix, tokens]
schema_version: 1.3
last_updated: "2026-08-27T13:57:33-04:00"
evidence: [continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/CORPUS_V3_S2_HANDOFF.md, continued_pretrain/CORPUS_V3_S3_HANDOFF.md, continued_pretrain/data/corpus_v3_catalog.json]
---

S2 fetch + mix rebuild finished 2026-08-27. No B/C, no Kaggle, no merge, no Hub LoRA overwrite.

Manifest `created_at` 2026-08-27T17:47:00Z:
- spurgeon_weight **0.931006**, spurgeon_keep_all **true**, other_bucket_weight **1.074107** (not capped; ≤ 1.5 so keep-all is allowed)
- train_docs **48841**, train_chars **295,083,379**
- verified tokens **86,182,467** (Qwen3.5-4B-Base, sample ratio 0.29129)
- shares S **43.1** / P **46.1** / C **1.8** / B **1.5** / G **7.4**

Wave 1 retries 7/7 keys. Wave 2 30/30 catalog keys. Shelf puritans+hymns+systematic **217.7 MB** (`data/puritans` at repo root, gitignored). Henry exposition still denylisted (`henry/exposition*`). Packing `one_doc_padded`.

Keep-all ON is a change vs S1 (S1 other-weight ~1.52, keep-all off). Confession 1.8% and Bible 1.5% are below band because Puritan mass grew — S3 must not add more treatises as the growth engine.

Fallback LoRA: rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 SHA256 319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478

Next = S3. Handoff: `continued_pretrain/CORPUS_V3_S3_HANDOFF.md`.
