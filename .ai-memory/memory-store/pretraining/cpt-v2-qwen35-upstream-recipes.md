---
store_path: pretraining/cpt-v2-qwen35-upstream-recipes
title: "Qwen3.5 CPT upstream recipes vs T4 pipeline"
summary: "Checked against Unsloth docs, Unsloth issues/PRs, HF transformers packing, and a working Qwen3.5 Unsloth CPT cookbook"
priority: high
tags: [qwen35, unsloth, cpt, packing, qlora, t4]
schema_version: 1.3
last_updated: "2026-08-26T13:37:34-04:00"
evidence: ["continued_pretrain/scripts/_gen_sota_notebooks.py:407", continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# Qwen3.5 CPT — upstream recipes that already work (2026-08)

Checked against Unsloth docs, Unsloth issues/PRs, HF transformers packing, and a working Qwen3.5 Unsloth CPT cookbook. Map to Ask Spurgeon B on Kaggle T4.

## Already in our pipeline
Dual LR (body 1e-5, emb 5e-6); train embed_tokens; RSLoRA/dropout 0; `packing=False`; seq 2048 batch 1; light eval (`prediction_loss_only`, EVAL_DOCS=2). Tied `lm_head` off is correct.

## Do not copy blindly onto T4
- **No QLoRA:** Unsloth Qwen3.5 fine-tune guide — 4-bit not recommended (quant error). Working 4B path is **bf16 LoRA ~10 GB** (`load_in_4bit=False`, `load_in_16bit=True`). T4 is sm_75 (no bf16); Unsloth forces **float32** for this arch, so we used 4-bit to fit. Official recipe needs **L4/A100**.
- **No Unsloth packing on GDN:** issue 4160 / PR 7211 — packing **silently leaks** across samples. Experimental varlen (PR 7249) needs `cu_seqlens`/`seq_idx`; transformers 5.2–5.8 can **drop** `cu_seq_lens_q` (ms-swift 9618). Need transformers ≥5.9 + collator keys.
- Isolated pack that still **concatenates two complete short docs** in one 2048 row still leaks GDN state. Working fail-closed path: **one doc (or one 2048 window) per row, pad**.
- Cookbook GDN LoRA names: `in_proj_qkv`, `in_proj_z`, `out_proj` plus q/k/v/o + MLP. Too-narrow q/k/v/o-only misses linear-attention layers. **Do not** LoRA `in_proj_a`/`in_proj_b` if packing (NaNs).
- Successful CPT cookbooks use **≥100M–1B tokens** with **falling** loss. Our B early-stops at ~0.8M tokens.

## Links
- https://www.unsloth.ai/docs/models/qwen3.5/fine-tune.md
- https://unsloth.ai/docs/basics/continued-pretraining
- https://github.com/unslothai/unsloth/issues/4160
- https://github.com/unslothai/unsloth/pull/7211
- https://github.com/vessl-ai/vessl-cloud-cookbook/blob/main/aqr-finance/train.py
