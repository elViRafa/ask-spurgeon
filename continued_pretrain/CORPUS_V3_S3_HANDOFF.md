# CPT corpus v3 — S3 DONE (fetch + mix, no training)

**S3 is done. Next session = S4 (share-band review / optional confession lift) or S5 with your approval.** Still **no B.**

Do **not** train. Do **not** start B/C. Do **not** push Kaggle. Do **not** merge. Do **not** overwrite Hub LoRA.

Full plan: [`CORPUS_V3_EXPANSION_PLAN.md`](CORPUS_V3_EXPANSION_PLAN.md)  
Next: [`CORPUS_V3_S4_HANDOFF.md`](CORPUS_V3_S4_HANDOFF.md)  
Catalog: [`data/corpus_v3_catalog.json`](data/corpus_v3_catalog.json)  
Mix (source of truth): [`data/theology_mix_manifest.json`](data/theology_mix_manifest.json)

---

## S3 DONE (Wave 3 commentary + mix, no training)

From `theology_mix_manifest.json` (`created_at` 2026-08-27T19:23:59Z):

| Metric | S2 | S3 |
|--------|----|----|
| `spurgeon_weight` | 0.9310 | **0.9916** |
| `spurgeon_keep_all` | true | **true** |
| `other_bucket_weight` | 1.0741 | **1.0085** (`other_weight_capped` false; ≤ 1.5) |
| `train_docs` | 48841 | **49787** |
| `train_chars` | 295.1M | **303.7M** |
| Verified tokens | 86.18M | **86,960,259** (86.96M, Qwen3.5-4B-Base, ratio 0.285606) |

Char shares: Spurgeon **41.9%**, Puritan **47.7%**, confession **1.8%**, Bible **1.4%**, general **7.2%**.

Henry exposition still **excluded**. Packing still `one_doc_padded`. Mix rebuilt with `--keep-all-spurgeon --max-other-weight 1.5`.

Wave 3 **9/9 keys**. Chaderton / John Rogers **skipped** (no clean PD keyed; would be treatise mass). Commentary cap **12.0 / 15 MB**.

| Set | Files | Bytes |
|-----|-------|-------|
| Hodge biblical | Romans, 1 Cor, 2 Cor, Ephesians | 5.0 MB |
| Calvin selected | Romans, 1 Cor, 2 Cor, Gal–Eph, Catholic epistles | 7.0 MB |
| Combined | 9 files | **12.0 MB** |

Hodge Romans/Corinthians from IA `_djvu.txt` (CCEL has no Hodge Romans txt). Hodge Ephesians + all Calvin from CCEL cache. No Banner/Heritage/Puritan Publications bodies. No more Henry exposition.

Shelf (puritans + hymns + systematic): **229.7 MB** (`data/puritans` 221.1 MB / 150 files).

---

## Locks (unchanged)

- Packing recipe: **`one_doc_padded`**
- `--keep-all-spurgeon` **ON** while `other_bucket_weight` stays **≤ 1.5**
- Fallback LoRA: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`  
  SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Kaggle STOP. No Hub overwrite. No merge.

---

## Traps (Windows / mix)

- Mix rebuild **must** pass `--max-other-weight 1.5` (script default is 5). Fetcher `--rebuild-mix` now passes 1.5; still prefer the explicit `07` command.
- Windows cp1252: Unicode `→` in `07_build_theology_mix.py` prints crashed the S3 mix; prints now use ASCII `->`. Set `PYTHONIOENCODING=utf-8` on this console anyway.

---

## What S4 is (and is not)

Plan S4 (mix + `06_verify_tokens`) **already ran inside S3** because unique text landed. Do **not** re-fetch Wave 3. Do **not** add more commentary (cap used). Do **not** grow Puritan treatise mass.

Confession **1.8%** and Bible **1.4%** remain below the 3–6% / 2–4% bands. Optional S4 lever: more confession/ST (not treatises, not Henry). Then **stop** unless you approve S5/B.
