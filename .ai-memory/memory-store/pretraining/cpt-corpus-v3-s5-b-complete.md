---
store_path: pretraining/cpt-corpus-v3-s5-b-complete
title: "CPT corpus v3 S5 B complete — best step 325"
summary: "GPU `pul3xia882ub5r` **deleted**"
priority: high
tags: [cpt, corpus-v3, s5, runpod, training]
schema_version: 1.3
last_updated: "2026-08-27T22:06:43-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/cpt_train.log, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_run_config.json, continued_pretrain/CORPUS_V3_S5_C_CHECKLIST.md]
---

# CPT corpus v3 S5 B COMPLETE (2026-08-27/28)

GPU `pul3xia882ub5r` **deleted**. Volume `7hb931c5oe` kept (still unused). **Do not C yet** until the operator approves. Do not merge. Do not overwrite Hub `…-cpt-lora-v2`. Do not re-run A/mix/Wave 3.

## Result
- Early-stop patience 2 at **375 / 4128**. Best **325**, `eval_spurgeon=2.254118`
- Abort-at-50 **pass**: 2.292415 @ 25 → 2.290856 @ 50
- Train loss 1.983; wall **0.93 h**; packed 51417 docs → 66045 rows; `tokens_per_epoch_est` ~90.28M; ~8.2M tokens seen
- Recipe: Ampere bf16, `one_doc_padded`, r=32, GDN LoRA, `TRAIN_EMBEDDINGS=True`, `PREV_RUN_CHECKPOINT` empty
- Adapter SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303` (matches checkpoint-325)
- Local: `continued_pretrain/kaggle/runpod_cpt_v3/` (junction `theology_cpt_lora` → `D:\\search-sermons-cpt\\runpod_cpt_v3\\theology_cpt_lora`)
- Fallback Hub LoRA unchanged: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`

## eval_spurgeon by step
25: 2.292, 50: 2.291, 75: 2.282, 100: 2.279, 125: 2.276, 150: 2.275, 175: 2.265, 200: 2.264, 225: 2.264, 250: 2.261, 275: 2.257, 300: 2.257, **325: 2.254**, 350: 2.259, 375: 2.257.

## Infra that actually worked
- MCP `create-pod` **cannot** attach `networkVolumeId` (`mounts: {}`). This B trained on **75 GB container disk** + scp off, same as v2 B/C.
- Cursor MCP OAuth token is **not** a REST `RUNPOD_API_KEY`. runpodctl volume-mount path still blocked until a real API key exists.
- Community 4090 US-IL-1 was empty; Secure 4090 **$0.74/hr**. SSH `~/.ssh/runpod_cpt`.
- `eval_cpt_sota.py` default `EXPECTED_ADAPTER_SHA256` is the **v2** hash. v3 C **must** export the ef4df3a3… hash or `--preflight` fails.

## Next (approval required)
C on this **new** adapter vs its own Ampere bf16 base. Holdouts from `kaggle/a_output_v3` (not v2 `a_output`). Checklist: `[REDACTED_SECRET].md`. Keep Hub v2 if C is worse than v2 Ampere scorecard. Future longer-epoch B: `pretraining/cpt-future-b-early-stop-scale`.

After C, more-tokens continue playbook: continued_pretrain/NEXT_CPT_MORE_TOKENS.md (store pretraining/cpt-next-b-more-tokens-playbook). Optimizer was not copied; cannot HF-resume. Next session is C, not a retrain.
