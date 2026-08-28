---
store_path: bugs/qwen35-processor-text-as-image
title: "Qwen3.5 processor text-as-image in C_eval"
summary: "C v2 found the adapter then crashed in PPL on the first Spurgeon holdout:"
priority: high
tags: [kaggle, qwen3.5, processor, cpt, eval]
schema_version: 1.3
last_updated: "2026-08-24T10:19:14-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/test_kaggle_path_resolve.py]
---

# Qwen3.5 VL processor treats sermon text as image (C_eval)

C v2 found the adapter then crashed in PPL on the first Spurgeon holdout:
`ValueError: Incorrect image source ... Got Sermon 32 | The Necessity of Increased Faith`

Cause: Unsloth returns a multimodal Processor whose `__call__(images, text, ...)` first positional arg is **images**. `tokenizer(text)` feeds the sermon into `load_image`.

Fix in C_eval: unwrap `.tokenizer`, `ids_for_text` / `tokenize_text` (input_ids + attention_mask only). Smoke-test with that sermon title after load.
