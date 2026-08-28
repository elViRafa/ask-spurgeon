---
store_path: pretraining/cpt-v2-c-eval-root-causes
title: "CPT v2 C_eval root causes"
summary: "Full report: `continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md`"
priority: high
tags: [kaggle, cpt, rc2, rc3, rc4]
schema_version: 1.3
last_updated: "2026-08-24T22:09:47-04:00"
evidence: [continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md, continued_pretrain/kaggle/b_output/b_logs.txt, continued_pretrain/kaggle/c_output/theology_cpt_eval_metrics.json]
---

# CPT v2 C_eval — root cause analysis (2026-08-24)

Full report: `continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md`
Handoff: `continued_pretrain/CPT_V2_KAGGLE_STATUS.md`
Metrics: `continued_pretrain/kaggle/c_output/theology_cpt_eval_metrics.json`

## Gate: FAIL (do not merge)

All holdout PPL worse than base: spurgeon +9%, puritan +11.6%, confession +15.4%, general +17.8%.
Heidelberg MCQ +9.5 pts (gate ≥+10). WSC +2 pts.

## Root causes (priority order)

1. **Packing disabled:** B log `Unsloth: packing=True ignored (processor-based model)`. Qwen3.5 Processor path → 4356 rows, max 2048 tok/doc, ~7.4M tok/epoch — not packed CPT.
2. **Overfitting after step 50:** eval_mix_loss 2.32→2.46; grad_norm rose. Best ckpt still fails holdout PPL in C.
3. **Early-stop mismatch:** B eval only `eval keys=['mix']` (45-doc val), not holdout buckets used in §5.
4. **Qwen3.5 constraints:** tied embeddings (TRAIN_LM_HEAD=False), float32 train, processor breaks packing; C needed ids_for_text for VL processor.
5. **MCQ vs PPL:** short MCQ gains without long-form LM improvement.
6. **Probes:** repetition loops, doctrinal confabulation — adapter drift not Spurgeon quality.

## B reference diagnostics

- train rows 4356, D1 max row 2048, tokens_per_epoch_est 7376550
- tie_word_embeddings true, trainable_embed_or_head []
- LoRA r=64 LR 5e-5, 250 steps T4

## Next session

Fix B for processor/no-packing OR pre-chunk; holdout eval in B; do not merge; optional SFT stock dry-run.

## RC1 fix (local, 2026-08-24)

Implemented in `_gen_sota_notebooks.py` B_training generator (not pushed to Kaggle yet):
- `text_tokenizer` / `ids_for_text` helpers (same as C_eval)
- `build_manual_packed_dataset()` — EOS-separated stream split at 2048
- `MANUAL_PACK=True`, `packing=False`, pass inner `train_tok` to UnslothTrainer
- D1 gate raises if packed rows ≈ raw doc count
- run_config records `manual_pack`, `packing_mode`, `raw_doc_count`

Regenerate: `python continued_pretrain/scripts/_gen_sota_notebooks.py`

## RC2–RC4 local fixes (2026-08-24, not pushed)

- **RC2:** r=32, LR 2e-5, emb LR 5e-6, MAX_STEPS=100, EVAL/SAVE=25, SAVE_TOTAL_LIMIT=4
- **RC3:** `_find_hf_holdout_root()` (never corpus .txt); require spurgeon HF; `METRIC_FOR_BEST=eval_spurgeon_loss`; `EarlyStoppingCallback(patience=2)`
- **RC4:** Qwen3.5 constraint docs; D4 warn if TRAIN_EMBEDDINGS but no trainable embed params
- **C:** `ADAPTER_OVERRIDE`; probe trigram repetition warnings (RC6 signal)
- Regenerate notebooks only — no Kaggle push

## Next session (replace older Next session blurb)

Local RC1–RC4 done; notebooks regenerated; **not pushed**. See `pretraining/cpt-v2-next-session-handoff`.
When asked: push B → train with HF theology_holdouts → C eval → ship only on §5 PPL. Do not merge until gate passes.
