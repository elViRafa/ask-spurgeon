---
store_path: pretraining/cpt-v2-lora-snapshot
title: "CPT v2 keepable LoRA snapshot (best-400, private Hub)"
summary: "Runpod B best **step 400** adapter is documented so a later mix/token run can fail without losing this training"
priority: high
tags: [cpt, lora, runpod, handoff]
schema_version: 1.3
last_updated: "2026-08-27T09:50:01-04:00"
evidence: [continued_pretrain/scripts/upload_cpt_lora_to_hf.py]
---

# CPT v2 keepable LoRA snapshot

Runpod B best **step 400** adapter is documented so a later mix/token run can fail without losing this training.

## Where
- Session scorecard: SESSION RESULTS markdown in `continued_pretrain/kaggle/runpod_cpt_v2/`
- Snapshot index and identity JSON live in that same folder
- Model card / Unsloth load snippet: the README inside `theology_cpt_lora/`
- SHA256 of `adapter_model.safetensors`: `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`

Weights (~1.45 GB) stay on local disk (gitignored safetensors under continued_pretrain). Not merged, not GGUF.

## Load
Unsloth FastLanguageModel.from_pretrained with load_in_4bit=False on Ampere/Ada. Qwen3.5 VL processor: tokenize with text= only. Do not C/infer this adapter on T4 4-bit. Do not use Kaggle B v6 checkpoint-25.

## Hugging Face (2026-08-27)
Private repo `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` uploaded after SHA256 check. Still not merged, not public. Re-upload: `python continued_pretrain/scripts/upload_cpt_lora_to_hf.py`
