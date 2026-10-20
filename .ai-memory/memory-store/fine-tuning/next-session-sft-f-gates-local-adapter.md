---
store_path: fine-tuning/next-session-sft-f-gates-local-adapter
title: "Next after F gates fail: refusal knob not export"
summary: "F §5 on local Unsloth adapter **failed** only on refusal (0.46)"
priority: high
tags: [sft, f-gates, handoff, refusal]
schema_version: 1.3
last_updated: "2026-10-17T21:09:03-03:00"
evidence: [fine_tuning/eval_results/post_sft_eval_s8_weighted.json, fine-tuning/sft-s8-weighted-f-gates-2026-10-17]
---

# Next session after weighted S8 F gates

## Stopped here (2026-10-17)
F §5 on local Unsloth adapter **failed** only on refusal (0.46). Groundedness 4.12 OK. **No Hub/Ollama promote.**

## Canonical LoRA (still on PC)

## Next task
1. One knob: improve **refusal** (slice weight / mix / retrain) — not another full export path.
2. Re-run F gates after the knob; export only if refusal ≥ 0.85 and other gates still pass.
3. Judge with **Gemini** (`SFT_EVAL_JUDGE_PROVIDER=gemini`); Groq 403s.
4. After any RunPod job: verify destroy with **`runpodctl pod list`** (MCP list can miss orphans).

## Not next
- Promote `spurgeon-qa-v2` / Hub GGUF overwrite.
- Re-rent GPU for export-only.

## Side-chat clarification (2026-10-17 evening)
- Open-theology eval was **not** run for this adapter — see `fine-tuning/open-theology-eval-not-scored-s8-weighted`.
- Improvement playbook: `fine-tuning/sft-improve-refusal-slice-first` (harder RAG refusal → re-SFT → F gates → export → then open-theology score).
