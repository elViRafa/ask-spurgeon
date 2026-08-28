---
store_path: failures/valueerror-incorrect-image-source-9824630bd3
title: "ValueError: Incorrect image source. Must be a valid URL starting with http:// or"
summary: "ValueError: Incorrect image source"
priority: medium
tags: [cpt, eval, failure, fix, kaggle, processor, qwen3.5]
schema_version: 1.3
last_updated: "2026-08-24T10:19:12-04:00"
occurrences: 1
error_signature: "valueerror: incorrect image source. must be a valid url starting with htt<path> or http<path> ... got sermon <n> | the necessity of increased faith. c_eval tokenizer(text) on qwen<n>.<n> vl processor treats first positional arg as images."
failure_key: valueerror
---

## Occurrence 1 — 2026-08-24T10:19:12-04:00

**Error:**
ValueError: Incorrect image source. Must be a valid URL starting with http:// or https:// ... Got Sermon 32 | The Necessity of Increased Faith. C_eval tokenizer(text) on Qwen3.5 VL Processor treats first positional arg as images.

**Fix:**
Unwrap Processor to inner tokenizer and tokenize with encode/ids_for_text; never pass sermon strings positionally. PPL/probes/MCQ use tokenize_text() returning only input_ids + attention_mask.
