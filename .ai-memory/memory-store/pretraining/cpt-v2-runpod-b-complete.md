---
store_path: pretraining/cpt-v2-runpod-b-complete
title: "CPT v2 Runpod B complete — best step 400, adapter local"
summary: "Fresh Ampere bf16 LoRA (not a Kaggle 4-bit resume)"
priority: high
tags: [cpt, runpod, training]
schema_version: 1.3
last_updated: "2026-08-27T08:21:39-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_run_config.json, continued_pretrain/kaggle/runpod_cpt_v2/cpt_train.log, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# CPT v2 Runpod B — COMPLETE 2026-08-27

Fresh Ampere bf16 LoRA (not a Kaggle 4-bit resume). GPU pod `3aift60lb2tr68` **deleted**. Adapter lives only in the repo copy below (volume was never mounted).

## Locked result
- Base: `unsloth/Qwen3.5-4B-Base`; r=32; GDN `in_proj_qkv` / `in_proj_z` / `out_proj`; `TRAIN_EMBEDDINGS=True`; `TRAIN_LM_HEAD=False`
- Pack: `one_doc_padded`, `PAD_TO_MAX=False`, 8162 docs → 10779 rows, `MAX_STEPS=674`, `multi_doc_rows=0`
- Abort-at-50: **pass** — eval_spurgeon 2.28797 @ 25 → 2.28556 @ 50
- Early-stop patience 2 at **450**. Best **400**, metric 2.248331
- Train loss 1.989; ~0.98 h; ~7.4 s/step on 4090; ~20 GB VRAM
- SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Local: `continued_pretrain/kaggle/runpod_cpt_v2/` (lora, `cpt_train.log`, `theology_cpt_run_config.json`, `checkpoint-400-trainer_state.json` only — **no optimizer ckpts**)

## eval_spurgeon by step
25: 2.288, 50: 2.286, 75: 2.278, 100: 2.272, 125: 2.265, 150: 2.260, 175: 2.259, 200: 2.259, 225: 2.255, 250: 2.255, 275: 2.252, 300: 2.251, 325: 2.250, 350: 2.249, 375: 2.249, **400: 2.248**, 425: 2.249, 450: 2.249.

mix eval also fell ~2.091 → 2.043.

## Infra leftovers
- Volume `7hb931c5oe` US-IL-1 50 GB STANDARD — empty (MCP ignored `networkVolumeId`)
- Secure 4090 because community stock was gone
- Generator typo fixed: `is_hf_holdout_root` (not `_is_hf_holdout_root`)
