---
store_path: fine-tuning/sft-improve-refusal-slice-first
title: "Improve SFT via harder RAG refusal slice, not CPT"
summary: "Weighted S8 F §5 failed **only** on refusal (~0.46; ~fn27/tp23)"
priority: high
tags: [sft, refusal, qa-mix, decision]
schema_version: 1.3
last_updated: "2026-10-17T21:09:02-03:00"
evidence: [fine-tuning/qa-mix-size-vs-refusal, fine-tuning/next-session-sft-f-gates-local-adapter, fine_tuning/eval_results/post_sft_eval_s8_weighted_human_review.md]
---

# Improve fine-tuning after S8 weighted F-gate fail

Weighted S8 F §5 failed **only** on refusal (~0.46; ~fn27/tp23). Groundedness ~4.12, stop/echo/corrupt OK. Do **not** jump to CPT or Hub export.

## Preferred knob (re-SFT)
1. Harden the **RAG refusal slice** under the same `SPURGEON_SFT_SYSTEM_PROMPT`:
   - near-miss CONTEXT (looks related, does not answer)
   - anachronism / CPT-knowable facts the chunks do not support
   - optional oversample / higher slice weight
2. Do **not** grow the whole QA mix first — more answerable rows dilute ~11% refusal share (`fine-tuning/qa-mix-size-vs-refusal`).
3. Keep speakers Spurgeon-sermon-heavy; gold refusals must explicitly teach "not in CONTEXT".
4. Re-run F gates; export only if refusal ≥ 0.85 and other gates still pass. Judge: Gemini (Groq 403).

## Secondary
- Gold/quote quality (ungrounded quotes) is a separate knob from row count.
- Open-theology held-out (`open_theology_eval.jsonl`) is scored **later**; more open-theology train rows do not fix RAG refusal FNs.

## Not next
- New CPT resume for this miss
- Promote `spurgeon-qa-v2` / overwrite Hub GGUF
- Treating open theology as a substitute for RAG refusal discipline
