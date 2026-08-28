---
store_path: pretraining/cpt-next-b-more-tokens-playbook
title: "Next CPT B: more mix tokens + agreed eval strategy"
summary: "S5 B stopped at 375/4128 (~8.2M of ~90M)"
priority: high
tags: [cpt, corpus-v3, recipe, early-stop, lr, eval]
schema_version: 1.3
last_updated: "2026-08-28T00:14:16-04:00"
evidence: [continued_pretrain/NEXT_CPT_MORE_TOKENS.md, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/scripts/train_cpt_sota.py]
---

# Next CPT B — continue with more mix tokens (eval strategy agreed)

S5 B stopped at 375/4128 (~8.2M of ~90M). **S5 C is complete.** Preferred continue: near v2 Ampere C, far from §5 −15%. **Eval spec (use this, not 2-doc Spurgeon):** `pretraining/cpt-b-eval-strategy`. Repo: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md`. Do **not** create a GPU until the operator says go.

## C verdict (do not re-C this adapter)
- Probe vs own Ampere base: **PASS** (spurgeon 14.31→13.34, puritan 6.03→5.72, confession 5.61→5.36, general 12.05→11.90).
- §5 −15%: **FAIL**.
- Keep Hub `…-cpt-lora-v2`. v3 saw **less** data than v2 (~8.2M vs ~15.6M).

## Preferred continue (not trainer resume)
Adapter-only SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`. Load LoRA on Qwen3.5-4B-Base, **new Adam**, Ampere bf16. Same mix `a_output_v3`.

Deltas when approved (code is not there yet):
- Body LR ~3e-6–5e-6, emb ~1e-6–2e-6; cosine over continue max_steps.
- **Floor:** `min_steps` ≈ 0.4–0.5 packed epoch (~36–45M). Do not equate this with 25M tokens.
- **Eval:** `EVAL_DOCS_PER_BUCKET` 16–32 (cap at bucket size: confession 10, spurgeon 50). Keep mix + spurgeon; add puritan/confession on 24 GB.
- **Halt:** composite Spurgeon **and** mix flat within epsilon (custom callback). `METRIC_FOR_BEST` stays `eval_spurgeon_loss` (ckpt pick ≠ halt).
- Abort-at-50 **off/loosened on continue only**. Keep one_doc_padded, r=32, GDN, embed FT, QuietEarlyStopping.

New `train()` reshuffles. Volume `7hb931c5oe` via REST v1. Scp optimizer + ckpts.

Do not: mix-only stop; collapsed Reformed PPL; 2-doc Spurgeon stop; fresh 1e-5 from base; rebuild mix; T4 4-bit; overwrite Hub v2 until new C wins.
