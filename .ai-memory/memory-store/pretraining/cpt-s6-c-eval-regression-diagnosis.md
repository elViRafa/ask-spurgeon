---
store_path: pretraining/cpt-s6-c-eval-regression-diagnosis
title: "S6 Vast C +27.9% was false FAIL (stack); tying not cause"
summary: "**False FAIL.** Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on Unsloth **2026.8.22 / torch 2.8.0** scores spurgeon **12.85 (−10.2%)**"
priority: medium
tags: [cpt, s6, c-eval, regression, stack-isolation, hub-v2]
schema_version: 1.3
last_updated: "2026-09-20T19:01:23-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/cpt_eval.log, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/theology_cpt_eval_metrics.json, continued_pretrain/scripts/eval_cpt_sota.py]
---

# S6 C-eval regression diagnosis — SUPERSEDED by stack isolation (2026-09-20)

## Resolution
**False FAIL.** Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on Unsloth **2026.8.22 / torch 2.8.0** scores spurgeon **12.85 (−10.2%)**. Canonical write-up: `pretraining/cpt-s6-stack-isolation-c`.

Vast C **18.31 (+27.9%)** under Unsloth 2026.9.6 / torch 2.11 is **not** trustworthy for these weights. Tying sync remains rejected as the cause of that inflated PPL (still useful negative result).

## Original diagnosis (2026-09-19) — historical
Vast C of ckpt-2050 LoRA scored spurgeon **18.31 (+27.9% vs Ampere base ~14.31)**. Embed→lm_head sync did **not** change PPL.

### Controlled tying test (still valid)
- Patch: `maybe_sync_tied_lm_head` in `eval_cpt_sota.py` (`CPT_EVAL_SYNC_TIED_HEAD`).
- Re-C: Vast RTX 4090 Kentucky, instance **51500745** (destroyed).
- Before sync: `same_storage=0`, `max_abs_delta≈0.00195`.
- After sync: `embed_to_lm_head_synced=1`, spurgeon still **18.31 (+27.9%)**.

### Ranked causes — updated
1. **Confirmed** — Vast C-eval stack (Unsloth 2026.9.6 / torch 2.11) mis-scores this embed-FT LoRA. Fixed by re-C on S5 pin.
2. **Meta** — Aug-28 “6aab → 13.34” still unproven as that SHA; stack-isolation now gives **12.85** for `6aab…`.
3. **Rejected as regression cause** — 16-doc vs 50-doc (train probe loss 2.495 matches train 2.4987 on good stack).
4. **Rejected** — Wrong SHA / 4-bit / outer stale S5 LoRA / simple tying copy.

## Policy (post-isolation)
- Do **not** treat Vast +27.9% as ground truth.
- Hub `…-theology-cpt-lora-v2` stays until **explicit** overwrite approve (S6 12.85 beats Hub v2 13.28 on this scorecard).
- No blind new B to “fix C”. Eval CPT only on Unsloth ~2026.8.22 + torch 2.8 for parity with Hub-v2/S5.
