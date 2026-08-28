---
store_path: pretraining/cpt-v2-isolated-pack-review
title: "Isolated-pack review: leftover splice fixed"
summary: "Did **not** push Kaggle, run C, or merge"
priority: high
tags: [cpt, packing, kaggle, review]
schema_version: 1.3
last_updated: "2026-08-26T08:47:40-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/test_manual_pack.py, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# Isolated-pack defect review (2026-08-26)

Did **not** push Kaggle, run C, or merge. Mix was **not** rebuilt (Kaggle corpus still Spurgeon weight 0.164).

## Fixed (high confidence)

- **Leftover-A + start-of-B splice:** `pack_document_isolated` left the last window of a doc longer than 2048 in `cur_ids`, then packed the next *short* doc onto that tail. That is the old stream-pack failure mode. Fix: each split-doc window is flushed as its own row; only *complete* docs that both fit share a row. First token of later docs still `labels=-100`.
- **Collator:** UnslothTrainer now gets `DataCollatorForSeq2Seq` (`label_pad_token_id=-100`) so labels are not cloned from `input_ids`. Transformers LM collator would undo isolation and, with Qwen `pad==eos`, zero EOS CE.
- **D2:** scans **all** packed rows (not first 100); NOTE if no post-EOS token (gate did not fire); FAIL if collator wipes post-EOS `-100`.
- **Tests:** leftover-of-long-A vs next doc; no dropped tokens; HF-shift target at B0 is `-100`; collator-clone footgun documented.
- **MAX_STEPS:** clamp **down** only. Status's “~511” was wrong while `MAX_STEPS=476`. Isolated pack can have *more* rows than stream pack, so 476 may be &lt; one epoch.

Notebooks regenerated from `_gen_sota_notebooks.py`.

## Still true (must not regress)

`TRAIN_EMBEDDINGS=True`, `LR=1e-5`, `EVAL_DOCS=2`, spurgeon-only eval, dtype hook, `save_only_model`, `SAVE_TOTAL_LIMIT=1`, `packing=False`, `PACKING_MODE=manual_isolated`.

## Left / not bugs

- D1 packed-rows ≈ raw-docs is NOTE not FAIL (intent).
- All-ones attention across packed *complete* short docs (GatedDeltaNet cannot isolate).
- Mix `--keep-all-spurgeon` exists in `07_build_theology_mix.py`; **corpus on Kaggle still subsampled**.
- D1 max-length check samples ~200 rows (packer cannot emit &gt;2048).
- Eval rise / C v4 FAIL is unchanged; isolated pack does not by itself make C safe.

## B push

Packing path is defect-clean enough to push **after a human reads D1/D2 on the live kernel**. Do not C. Do not merge.
