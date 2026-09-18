---
store_path: failures/vast-gate-n-sft-ca7b8e4d3c
title: "Vast GATE-0 SFT crashed: TRL SFTTrainer ValueError eos_token '<EOS_TOKEN>' not i"
summary: "Vast GATE-0 SFT crashed: TRL SFTTrainer ValueError eos_token '<EOS_TOKEN>' not in vocab (Unsloth TokenizersBackend placeholder)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-05T21:24:43-04:00"
occurrences: 1
error_signature: "vast gate-<n> sft crashed: trl sfttrainer valueerror eos_token <val> not in vocab (unsloth tokenizersbackend placeholder). also earlier typeerror dataset_text_field on sfttrainer with newer trl."
failure_key: "valueerror|gate-0"
---

## Occurrence 1 — 2026-09-05T21:24:43-04:00

**Error:**
Vast GATE-0 SFT crashed: TRL SFTTrainer ValueError eos_token '<EOS_TOKEN>' not in vocab (Unsloth TokenizersBackend placeholder). Also earlier TypeError dataset_text_field on SFTTrainer with newer TRL.

**Fix:**
Force pad/eos to <|endoftext|> on outer+inner tokenizer always; re-apply after get_peft_model; SFTConfig eos/pad_token + filter kwargs so Unsloth does not forward obsolete trainer args. Re-rent after fix.
