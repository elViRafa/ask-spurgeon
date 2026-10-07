---
store_path: fine-tuning/sft-stop-token-phases
title: "SFT stop-token phased verification"
summary: "Phased stop-token contract for Qwen3.5 SFT v2:"
priority: high
tags: [sft, stop-tokens, qwen35]
schema_version: 1.3
last_updated: "2026-09-02T09:47:29-04:00"
review_status: stale
---

Phased stop-token contract for Qwen3.5 SFT v2:
- Turn stop: `<|im_end|>` (248046); native eos `<|endoftext|>` (248044); pad must not equal im_end.
- Runbook: `fine_tuning/STOP_TOKEN_PHASES.md`
- Script: `fine_tuning/scripts/verify_sft_stop_tokens.py` (phases 0–5)
- Shared utils: `fine_tuning/scripts/sft_stop_token_utils.py`

Phase gates:
- 0–1: local pre-GPU (tokenizer + training template); wired into `13_sft_local_readiness.py`
- 2: CPT merged base greedy probe on pod after merge (`sft_remote_merge.sh`)
- 3: post-eval stop metrics in `eval_sft_sota.py` → `metrics.stop_token`
- 4: exported HF tokenizer audit
- 5: Ollama smoke via `smoke_test_ollama.py` + verify phase 5

Modelfile adds stop for `<|endoftext|>` as fallback. Pod sync includes utils + verify scripts.
