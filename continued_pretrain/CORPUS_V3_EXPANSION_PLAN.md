# CPT corpus v3 — mix rebuild plan (no training this round)

**S4 (2026-08-27): complete.** Unique PD confession/ST **12/12**. Mix rebuilt: `spurgeon_weight` **1.0688** (keep-all branch off because weight > 1; all sermons used), `other_bucket_weight` **1.0**, **91.31M** verified tokens (Qwen3.5-4B-Base), **51937** docs, **316.5M** chars. Shares S **40.2** / P **45.7** / C **5.5** / B **1.4** / G **7.2**. Confession now in the 3–6% band. Henry exposition still excluded. `data/confessions/` **30.7 MB**. **No B.**

**Next session = S5 with approval** (Runpod B). Still **no B** until approval. One-pager: [`CORPUS_V3_S5_HANDOFF.md`](CORPUS_V3_S5_HANDOFF.md). S4 recap: [`CORPUS_V3_S4_HANDOFF.md`](CORPUS_V3_S4_HANDOFF.md). Mix: [`data/theology_mix_manifest.json`](data/theology_mix_manifest.json).

**Fallback adapter (keep):** `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`
SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`

Do not start B/C. Do not re-fetch Wave 3. Do not add commentary. Do not grow Puritan treatises. Mix rebuild must pass `--max-other-weight 1.5` (script default is 5). Windows: `PYTHONIOENCODING=utf-8`. Packing stays `one_doc_padded`.

| Session | Status | Train? |
|---------|--------|--------|
| S0–S3 | Done (Wave 1–3 + mixes) | No |
| S4 | Done: C 5.5% in band, 91.31M tokens | No |
| S5 | Runpod B only with explicit approval | Only if you say so |

Kaggle STOP. Next GPU: Runpod volume `7hb931c5oe`. New dataset name so Hub LoRA still maps to the old mix. Heidelberg/Belgic holdout-only. No Turretin English.

