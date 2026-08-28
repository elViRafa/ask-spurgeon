# CPT corpus v3 — S2 DONE (this session finished fetch + mix)

**S2 is done. Next session = S3.** Still **no B.**

Do **not** train. Do **not** start B/C. Do **not** push Kaggle. Do **not** merge. Do **not** overwrite Hub LoRA.

Full plan: [`CORPUS_V3_EXPANSION_PLAN.md`](CORPUS_V3_EXPANSION_PLAN.md)  
Next: [`CORPUS_V3_S3_HANDOFF.md`](CORPUS_V3_S3_HANDOFF.md)  
Catalog: [`data/corpus_v3_catalog.json`](data/corpus_v3_catalog.json)  
Mix (source of truth): [`data/theology_mix_manifest.json`](data/theology_mix_manifest.json)

---

## S2 DONE (fetch + mix rebuilt, no training)

From `theology_mix_manifest.json` (`created_at` 2026-08-27T17:47:00Z):

| Metric | S1 | S2 |
|--------|----|----|
| `spurgeon_weight` | 0.6586 | **0.9310** |
| `spurgeon_keep_all` | false | **true** |
| `other_bucket_weight` | 1.0 | **1.0741** (`other_weight_capped` false; ≤ 1.5 so keep-all is allowed) |
| `train_docs` | 32878 | **48841** |
| `train_chars` | 203.1M | **295.1M** |
| Verified tokens | 57.60M | **86,182,467** (86.18M, Qwen3.5-4B-Base, ratio 0.29129) |

Char shares: Spurgeon **43.1%**, Puritan **46.1%**, confession **1.8%**, Bible **1.5%**, general **7.4%**.

Henry exposition still **excluded**. Packing still `one_doc_padded`.

Retries **7/7 keys**. Wave 2 **30/30 keys**. Shelf (puritans + hymns + systematic): **217.7 MB**.

---

## Locks (unchanged)

- Packing recipe: **`one_doc_padded`**
- Fallback LoRA: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`  
  SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Kaggle STOP. No Hub overwrite. No merge.

---

## Paste into the next chat

See [`CORPUS_V3_S3_HANDOFF.md`](CORPUS_V3_S3_HANDOFF.md).
