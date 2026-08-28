---
store_path: pretraining/cpt-v2-additional-failure-modes
title: "CPT v2 other causes of poor results besides token budget"
summary: "C v4 uniform ~+2% PPL on all domain buckets is not only “too few tokens + no embed LoRA.” Other mechanisms that match the evidence:"
priority: high
tags: [cpt, kaggle, ppl, packing, qwen35, holdout]
schema_version: 1.3
last_updated: "2026-08-26T13:51:42-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/07_build_theology_mix.py, continued_pretrain/scripts/test_manual_pack.py, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# Additional CPT failure modes (beyond token budget / frozen embeds)

C v4 uniform ~+2% PPL on all domain buckets is not only “too few tokens + no embed LoRA.” Other mechanisms that match the evidence:

## High — harmful early LoRA (not just undertraining)

B `eval_spurgeon_loss` rose 2.568→2.602→2.607 at 25/50/75. Best ckpt is still worse than base on C. Greedy probes loop (repetition 0.29–0.82). Trainable 42.5M attn/MLP LoRA (0.93%) at LR ~2e-5 on a base that already has puritan PPL 6.2. The adapter **perturbed** the LM; it did not specialize.

## High — packed train ≠ C eval task

**B v6–v12 (Kaggle):** `build_manual_packed_dataset` concatenated then hard-cut 2048. Attention mask was all-ones (no packing isolation). Train CE included mid-doc cold starts and cross-EOS context. C `eval_ppl` scores independent docs, first 2048 only, `add_special_tokens=False`. D2 `[0,2,1,2,1]`: a 0-EOS row is a mid-document window. Confession C tokens 20480/10 = 2048 exactly — every confession holdout doc truncated.

Δ% vs base is still fair (same protocol). Absolute PPL is not “full-doc LM PPL.”

**Local (2026-08-26, unpushed):** `pack_document_isolated` in `_gen_sota_notebooks.py`. Greedy EOS-aligned pack (no leftover-A + start-of-B splices). Multi-doc rows only when both fit; first token of later docs `labels=-100`. Long docs split at 2048 with continuation prefix ignored. `packing=False` (GatedDeltaNet cannot use 2D segment masks / native varlen). D1 no longer FAILs when packed rows ≈ raw docs. D2 gates post-EOS ignore_index. Test: `continued_pretrain/scripts/test_manual_pack.py`. **Not on Kaggle until the next B push.**

## Medium — Qwen3.5 hybrid + float32 on 4-bit

B log: “Using float32” / “cannot work with float16.” `load_in_4bit=True` train and C. Hybrid linear_attention + VL Processor. Tied embeds, vocab ~248k. Noisy CPT path; small LoRA can look like uniform noise.

## Medium — Spurgeon weight 0.164 = undersample

`oversample()` with weight&lt;1 **subsamples by chars**. ~84% of Spurgeon chunks never enter the mix. Share 40.5% is after dropping most Spurgeon, not “we trained on all sermons.”

**Local (2026-08-26, mix not rebuilt):** `07_build_theology_mix.py --keep-all-spurgeon` (default True) keeps every Spurgeon train chunk and oversamples other domain buckets (`--max-other-weight` default 5) to hold the share target. Expect ~5× mix chars if rebuilt. `--no-keep-all-spurgeon` restores the old drop. **Do not upload a new Kaggle corpus until size/shares are reviewed.**

## Medium — tiny holdouts (measurement)

Puritan 20 docs / 135 KB; confession 10 / 71 KB; general 10. B early-stop used 4 docs/bucket. Gate can FAIL on noise; general +3.8% especially fragile.

## Low / wrong sign

OCR PASS; F1 chunking PASS; mix not Spurgeon-only. Chunk holdouts (`take_holdout` samples chunks) can **leak** siblings into train — that would **help** holdout PPL, not explain +2% worse. Greedy probe loops ≠ PPL (no repetition penalty at eval).

## Confirmed on B v11 (2026-08-26) — drift with embed LoRA at 2e-5

`eval_spurgeon_loss` still rose **2.349 → 2.363 → 2.383** at steps 25/50/75 with `TRAIN_EMBEDDINGS=True`. Early-stop 75; best=ckpt-25. Embed LoRA did **not** stop early drift at body LR 2e-5.

## Confirmed on B v12 (2026-08-26) — drift at 1e-5 too

Same early-stop shape as v6/v11. `eval_spurgeon_loss` **2.340 → 2.345 → 2.361** at steps 25/50/75; wall 2.81 h; best=ckpt-25; SHA256 `ffe193feb33b7fd3a7af745b50e4745998cafcee96c42678c85ef943614b886a`. Body LR **1e-5** did **not** stop the rise by step 50. Do not C; do not push another B on the **stream-pack** recipe. Next B must be isolated pack (local, unpushed).

## Local (2026-08-26) — one_doc_padded is now the generator default

Isolated pack (`manual_isolated`) is **not** the next B: it still concatenates two complete short docs. `_gen_sota_notebooks.py` default is `PACKING_MODE=one_doc_padded` (`pack_one_doc_padded`): one doc or 2048 window per row, `PAD_TO_MAX=False`, GDN LoRA on the padded path, `GPU_PROFILE=t4`. Notebooks regenerated. **Not pushed.** See `pretraining/cpt-v2-one-doc-padded`.
