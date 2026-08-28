---
store_path: pretraining/cpt-corpus-v3-s3-complete
title: "CPT corpus v3 S3 complete (Wave 3 + mix, no training)"
summary: "S3 fetch + mix rebuild finished 2026-08-27"
priority: high
tags: [cpt, corpus-v3, s3, mix, tokens, commentary]
schema_version: 1.3
last_updated: "2026-08-27T15:28:08-04:00"
evidence: [continued_pretrain/CORPUS_V3_S3_HANDOFF.md, continued_pretrain/CORPUS_V3_S4_HANDOFF.md, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/scripts/07_build_theology_mix.py]
---

S3 fetch + mix rebuild finished 2026-08-27. No B/C, no Kaggle, no merge, no Hub LoRA overwrite.

Wave 3 **9/9**. Chaderton and John Rogers **skipped**. Commentary cap **12.0 / 15 MB**: Hodge biblical 5.0 MB (Romans IA commentaryepist00hodg, 1 Cor expositionoffirs00hodg, 2 Cor expositionofseco00hodg, Ephesians CCEL); selected Calvin 7.0 MB (CCEL calcom38 Romans, 39 1 Cor, 40 2 Cor, 41 Gal-Eph, 45 Catholic epistles). Not the full Calvin dump. No Henry exposition added. Fetcher gates COMMENTARY_CAP_BYTES=15e6 and per-file max_chars 3.5M.

Manifest `created_at` 2026-08-27T19:23:59Z:
- spurgeon_weight **0.991563**, spurgeon_keep_all **true**, other_bucket_weight **1.008509** (not capped; ≤ 1.5)
- train_docs **49787**, train_chars **303,679,713**
- verified tokens **86,960,259** (Qwen3.5-4B-Base, sample ratio 0.285606)
- shares S **41.9** / P **47.7** / C **1.8** / B **1.4** / G **7.2**

Henry exposition still denylisted. Packing `one_doc_padded`. Mix rebuilt with `--keep-all-spurgeon --max-other-weight 1.5`. Shelf puritans+hymns+systematic **229.7 MB**.

Windows: mix print used Unicode → and crashed cp1252; prints now ASCII `->`. Fetcher `--rebuild-mix` now passes `--max-other-weight 1.5`.

Fallback LoRA: rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 SHA256 319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478

Next = S4 optional confession lift (mix+verify already ran). Handoff: `continued_pretrain/CORPUS_V3_S4_HANDOFF.md`.
