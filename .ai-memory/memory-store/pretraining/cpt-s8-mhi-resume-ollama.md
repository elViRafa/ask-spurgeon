---
store_path: pretraining/cpt-s8-mhi-resume-ollama
title: "S8 merged CPT loaded in Ollama as spurgeon-cpt-s8"
summary: "Loaded the S8 m_hi resume merged 16-bit HF into local Ollama on 2026-10-07"
priority: high
tags: [cpt, s8, ollama, gguf]
schema_version: 1.3
last_updated: "2026-10-07T16:11:17-03:00"
evidence: ["D:/models/spurgeon-cpt-s8/spurgeon-cpt-s8.Q8_0.gguf", continued_pretrain/scripts/smoke_test_ollama_cpt.py]
---

Loaded the S8 m_hi resume merged 16-bit HF into local Ollama on 2026-10-07.

| Field | Value |
|-------|--------|
| Ollama name | `spurgeon-cpt-s8` (does not replace `spurgeon-cpt`) |
| GGUF | `D:\models\spurgeon-cpt-s8\spurgeon-cpt-s8.Q8_0.gguf` (~4.17 GB) |
| Convert | llama.cpp `convert_hf_to_gguf.py --outtype q8_0 --no-nextn` |
| Source HF | `fine_tuning/models/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit` |
| Smoke | `smoke_test_ollama_cpt.py --model spurgeon-cpt-s8` — 9/9 PASS |

`--no-nextn` is required: without it GGUF sets `block_count=33` but only has blk.0–31, and Ollama fails looking for `blk.32.attn_norm.weight`.

Ollama 0.35 safetensors `-q int4` path wants MLX on this Windows box — use GGUF instead.

Try: `ollama run spurgeon-cpt-s8`
