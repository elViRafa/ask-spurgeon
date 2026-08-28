---
store_path: pretraining/cpt-future-b-early-stop-scale
title: "Future CPT B: early-stop does not scale with mix size"
summary: "S5 B (corpus v3, 2026-08-27/28) did **not** consume the 91M-token mix"
priority: high
tags: [cpt, early-stop, recipe, corpus-v3]
schema_version: 1.3
last_updated: "2026-08-27T22:06:01-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_run_config.json, continued_pretrain/kaggle/runpod_cpt_v3/cpt_train.log, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/configs/train_config_cpt_theology_sota.json]
---

# Future CPT B — early-stop vs mix size

S5 B (corpus v3, 2026-08-27/28) did **not** consume the 91M-token mix. HuggingFace `QuietEarlyStoppingCallback` (patience **2**, `eval_steps=25`, metric `eval_spurgeon_loss`) halted at **375 / 4128** steps (~9% of one packed epoch, **~8.2M tokens**). Best step **325**, `eval_spurgeon=2.254118`.

This is the same absolute-token neighborhood as the v2 probe (stopped 450/674, **~9.9M** of 14.8M). Larger mix made the **same** stop look early as a percentage. 4128 is a **ceiling** (`ceil(packed_rows/16)`), not a consume-the-dataset target.

## Why the 2-sermon probe flattened

- `EVAL_DOCS_PER_BUCKET=2` (VRAM hatch). Stop key is **two** Spurgeon docs, not the 520-row val set and not unread Puritan/confession mass.
- `eval_spurgeon` 2.292 → 2.254 then ±0.005 noise. Patience 2 = **50 steps** after last best, regardless of remaining rows.
- `eval_mix` was **still falling** at 375 (2.031 → 2.029). Unread data was not proven useless.
- Abort-at-50 is a **separate** credit guard (passed: 2.292 @ 25 → 2.291 @ 50). Do not confuse it with early-stop.

## Do this on a future full-mix B (needs approval; do not stealth-change S5 C)

Before another GPU B that is supposed to **see** ~90M tokens:

1. Add a **min_steps / min_tokens floor** before patience can fire (e.g. not before ~10M tokens, or not before 0.4–0.5 packed epoch), **or**
2. Scale patience with `packed_epoch_steps / eval_steps` (patience 2 was written when max_steps was ~674).
3. Do not treat 2-doc `eval_spurgeon` CE as “dataset consumed.” Either raise `EVAL_DOCS_PER_BUCKET` on 24 GB, add a secondary mix metric, or log that the probe can saturate while mix loss still falls.
4. Keep `QuietEarlyStoppingCallback` (skip patience increment when the current eval dict lacks `eval_spurgeon_loss`). Keep `one_doc_padded`, r=32, GDN LoRA, embed FT, abort-at-50.

## Do not

- Re-run S5 B with a longer patience **instead of C**. Next step for **this** adapter is C (approval required).
- Assume 91% of the mix was redundant. Most of it was never seen.
- Compare B `eval_spurgeon` 2.254 vs v2 2.248 as a merge gate (tiny eval CE, different mixes).

Repo playbook for a later more-tokens B (after C, not instead of C): continued_pretrain/NEXT_CPT_MORE_TOKENS.md and store pretraining/cpt-next-b-more-tokens-playbook. Preferred path is load S5 LoRA + lower LR + early-stop floor; optimizer was not copied so HF resume is impossible. Next session is C, not this B.
