---
store_path: failures/typeerror-sfttrainer-init-got-aa61ff7a3c
title: "TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_tex"
summary: "TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_text_field' (TRL>=0.18/0.24 with UnslothSFTTrainer **kwargs forward)"
priority: medium
tags: [failure, fix, gate0, sft, trl, unsloth, vast]
schema_version: 1.3
last_updated: "2026-09-05T22:25:35-04:00"
occurrences: 1
error_signature: "typeerror: sfttrainer.__init__() got an unexpected keyword argument <val> (trl>=<n>.<n><path> with unslothsfttrainer **kwargs forward)"
failure_key: typeerror
review_status: stale
---

## Occurrence 1 — 2026-09-05T22:25:35-04:00

**Error:**
TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_text_field' (TRL>=0.18/0.24 with UnslothSFTTrainer **kwargs forward)

**Fix:**
Never pass dataset_text_field/packing/max_seq_length to SFTTrainer. Put them on SFTConfig only; use _filter_kwargs so Unsloth **kwargs cannot forward obsolete keys to TRL. Also set SFTConfig eos_token/pad_token to real vocab tokens (<|endoftext|>) and overwrite Unsloth <EOS_TOKEN>/<|vision_pad|> placeholders before trainer init; drop messages column and keep ChatML text + train_on_responses_only.
