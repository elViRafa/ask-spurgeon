# CPT corpus v3 — S5 handoff

**S5 B is done** (2026-08-27/28). **Next session default = C eval.** Create a GPU only when that chat says go. Do **not** retrain in the C session.

C checklist: [`CORPUS_V3_S5_C_CHECKLIST.md`](CORPUS_V3_S5_C_CHECKLIST.md).  
B send-to-run (historical): [`CORPUS_V3_S5_RUN_CHECKLIST.md`](CORPUS_V3_S5_RUN_CHECKLIST.md).  
Runbook: [`RUNPOD_RUNBOOK.md`](RUNPOD_RUNBOOK.md).  
Adapter: [`kaggle/runpod_cpt_v3/README.md`](kaggle/runpod_cpt_v3/README.md).

Do **not** retrain in the C session. Do **not** push Kaggle. Do **not** merge. Do **not** overwrite Hub LoRA.

More-tokens B (later, if C warrants it): [`NEXT_CPT_MORE_TOKENS.md`](NEXT_CPT_MORE_TOKENS.md).

Full plan: [`CORPUS_V3_EXPANSION_PLAN.md`](CORPUS_V3_EXPANSION_PLAN.md)  
Mix (source of truth): [`data/theology_mix_manifest.json`](data/theology_mix_manifest.json)

---

## First actions (next agent)

1. Read [`CORPUS_V3_S5_C_CHECKLIST.md`](CORPUS_V3_S5_C_CHECKLIST.md) + this file. Do **not** re-run Wave 3, mix, local A, or B.
2. Run **S5 C** when the operator says go in that chat:
   - Score `kaggle/runpod_cpt_v3/theology_cpt_lora` SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`
   - Holdouts from `kaggle/a_output_v3` (not `kaggle/a_output`)
   - `EXPECTED_ADAPTER_SHA256` **must** be the v3 hash (`eval_cpt_sota.py` still defaults to v2)
   - Ampere bf16, `RUN_MERGE=False`
   - Keep Hub `…-cpt-lora-v2` if this C is worse than the v2 Ampere scorecard
3. After C, decide more-tokens B from [`NEXT_CPT_MORE_TOKENS.md`](NEXT_CPT_MORE_TOKENS.md). Do not start that B in the C session.

Windows: set `PYTHONIOENCODING=utf-8`.

---

## S5 B DONE (do not re-run)

| Metric | Value |
|--------|--------|
| Stop | Early-stop patience 2 at **375 / 4128** (not abort-at-50, not OOM) |
| Best | step **325**, `eval_spurgeon` **2.254118** |
| Tokens seen | ~8.2M of ~90.3M packed-epoch estimate |
| Train loss / wall | 1.983 / 0.93 h |
| Adapter SHA256 | `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303` |
| GPU | `pul3xia882ub5r` **deleted** |
| Volume | `7hb931c5oe` kept, unused (MCP dropped the mount) |

Abort-at-50 **passed** (2.292 @ 25 → 2.291 @ 50). Pack: `one_doc_padded`, 51417 docs → 66045 rows. Recipe: r=32, GDN LoRA, embed FT, Ampere bf16.

Why 375/4128 is not “dataset done”: stop key is 2 Spurgeon docs, patience 2 × eval every 25 = 50 steps after last best. Same ~8–10M tokens as the v2 probe. `eval_mix` was still falling. Future B notes live in memory `pretraining/cpt-future-b-early-stop-scale`.

---

## S4 mix (unchanged; do not rebuild)

From `theology_mix_manifest.json` (`created_at` 2026-08-27T19:58:31Z):

| Metric | Value |
|--------|--------|
| `spurgeon_weight` | **1.068846** |
| Verified tokens | **91,307,937** |
| HF rows (local A) | **51417 train / 520 val** |
| Mix SHA256 | `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973` |

Char shares: Spurgeon **40.2%**, Puritan **45.7%**, confession **5.5%**, Bible **1.4%**, general **7.2%**. Packing **`one_doc_padded`**.

---

## Locks

- Fallback LoRA: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`  
  SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Kaggle STOP. No Hub overwrite. No merge.
- Do **not** re-fetch Wave 3. Do **not** copy `kaggle/a_output` for C.

v2 Ampere C keep-bar (if v3 C is worse, keep Hub v2): spurgeon 13.28 (−7.25%), puritan 5.68 (−5.05%), confession 6.73 (−6.98%), general 13.20 (−1.73%).

---

## Paste into the next chat

```
S5 C send-to-run. B is done (best 325, early-stop 375). No retrain, no merge, no Hub overwrite, no Kaggle, no re-C of v2.

Score kaggle/runpod_cpt_v3/theology_cpt_lora SHA256 ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303.
Holdouts from kaggle/a_output_v3 (NOT a_output). MCQ data/catechism_mcq.json.
export EXPECTED_ADAPTER_SHA256 to the v3 hash (script default is still v2).
Ampere bf16, RUN_MERGE=False. Scp metrics to kaggle/runpod_cpt_v3/. Delete GPU.
Keep Hub …-cpt-lora-v2 if this C is worse than v2 Ampere scorecard.

After C, more-tokens continue is a later decision: continued_pretrain/NEXT_CPT_MORE_TOKENS.md
Checklist: continued_pretrain/CORPUS_V3_S5_C_CHECKLIST.md
Handoff: continued_pretrain/CORPUS_V3_S5_HANDOFF.md
```
