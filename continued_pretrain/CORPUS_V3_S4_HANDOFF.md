# CPT corpus v3 — S4 DONE (confession/ST lift + mix, no training)

**S4 is done. Next session = S5 with your approval (Runpod B).** Still **no B** unless you say so.

Do **not** train. Do **not** start B/C. Do **not** push Kaggle. Do **not** merge. Do **not** overwrite Hub LoRA.

Full plan: [`CORPUS_V3_EXPANSION_PLAN.md`](CORPUS_V3_EXPANSION_PLAN.md)  
Next: [`CORPUS_V3_S5_HANDOFF.md`](CORPUS_V3_S5_HANDOFF.md)  
Catalog: [`data/corpus_v3_catalog.json`](data/corpus_v3_catalog.json)  
Mix (source of truth): [`data/theology_mix_manifest.json`](data/theology_mix_manifest.json)

---

## S4 DONE (unique confession/ST + mix, no training)

From `theology_mix_manifest.json` (`created_at` 2026-08-27T19:58:31Z):

| Metric | S3 | S4 |
|--------|----|----|
| `spurgeon_weight` | 0.9916 | **1.0688** |
| `spurgeon_keep_all` | true | **false** (weight > 1; all sermons used, tiny Spurgeon oversample) |
| `other_bucket_weight` | 1.0085 | **1.0** (not capped) |
| `train_docs` | 49787 | **51937** |
| `train_chars` | 303.7M | **316.5M** |
| Verified tokens | 86.96M | **91,307,937** (91.31M, Qwen3.5-4B-Base, ratio 0.287726) |

Char shares: Spurgeon **40.2%**, Puritan **45.7%**, confession **5.5%**, Bible **1.4%**, general **7.2%**.

Confession **5.5%** is inside the 3–6% band (S3 was 1.8%). Henry exposition still **excluded**. Packing still `one_doc_padded`. Mix rebuilt with `--keep-all-spurgeon --max-other-weight 1.5`. Local preflight: **PASS_WITH_WARNINGS** (confession/Spurgeon in band; Puritan 45.7% just over 45% gate; Bible 1.4% and general 7.2% still below).

`--keep-all-spurgeon` was passed. Computed weight crossed 1.0 because unique confession/ST grew, so the other-bucket oversample branch did **not** run (`other_bucket_weight` 1.0). That is the intended end-state of the expansion: use all Spurgeon rather than drop sermons.

S4 fetch **12/12**. No Wave 3 re-fetch. No new commentary. Puritan shelf unchanged (150 files / 221.1 MB).

| Set | Path | Notes |
|-----|------|--------|
| Gill *Body of Doctrinal Divinity* | `systematic/gill_body_of_doctrinal_divinity.txt` | CCEL cache, 4.6 MB |
| Dabney *Syllabus and Notes* | `systematic/dabney_systematic_theology.txt` | IA `syllabusnotesofc00dabn` |
| Shedd *Dogmatic Theology* vols 1–3 | `systematic/shedd_dogmatic_theology_vol*.txt` | IA `dogmatictheology01/02shed`; vol.3 Cornell `cu31924092342553` (Princeton vol.3 401) |
| A.A. Hodge *Outlines* (1878) | `systematic/aa_hodge_outlines_of_theology.txt` | IA `outlinesoftheolo1878hodg` |
| Witsius *Economy of the Covenants* vols 1–2 | `systematic/witsius_economy_of_the_covenants_vol*.txt` | IA `oeconomyofcovena01/02wits` |
| Boyce *Abstract of Systematic Theology* | `systematic/boyce_abstract_of_systematic_theology.txt` | IA `abstractofsystem00boyc` |
| Second Helvetic | `reformed/second_helvetic_confession.txt` | Schaff Creeds III English appendix (CCEL `anonymous/helvetic` cache 404) |
| Scots Confession 1560 | `reformed/scots_confession_1560.txt` | CCEL `scotconf` |
| Canons of Dort | `reformed/canons_of_dort.txt` | Schaff Creeds III Dort page only (not full vol. 3) |

**Not fetched:** Turretin English (P&R/Dennison 1992–97 in copyright). Heidelberg + Belgic stay holdout-only. No Henry. No Banner/Heritage bodies.

`data/confessions/` **30.7 MB** / 21 files (was 12.6 MB / 9). Puritans + hymns + systematic **247.4 MB**.

---

## Locks (unchanged)

- Packing recipe: **`one_doc_padded`**
- Mix rebuild must still pass `--keep-all-spurgeon --max-other-weight 1.5` (script default other-weight is 5)
- Fallback LoRA: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`  
  SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Kaggle STOP. No Hub overwrite. No merge.
- Do **not** re-fetch Wave 3. Do **not** add more commentary. Do **not** grow Puritan treatise mass.

---

## Traps (Windows / mix)

- Mix rebuild **must** pass `--max-other-weight 1.5` (script default is 5). `11_fetch_confessions.py --rebuild-mix` now passes 1.5 + replay 0.10; still prefer the explicit `07` command.
- Windows: set `PYTHONIOENCODING=utf-8`. Mix prints use ASCII `->`.
- Do **not** dump Schaff *Creeds* vol. 3 wholesale — it contains Heidelberg and Belgic. Dort/Helvetic were fetched as **single-page** CCEL HTML.

---

## What S5 is (and is not)

Mix + `06_verify_tokens` **already ran inside S4**. Do **not** rebuild unless new unique text lands.

S5 is **training**: Runpod B on this mix, same pack recipe, C only on the **new** adapter. Needs **explicit approval**. Bible 1.4% and general 7.2% remain below band — optional later, not a B blocker.
