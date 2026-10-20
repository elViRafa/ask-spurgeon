---
store_path: fine-tuning/open-theology-chat-corpus-contract
title: "Open-theology chat = corpus knowledge assistant (cite optional)"
summary: "- **Is:** a second product beside live RAG — a general theology LLM of the Spurgeon / Puritan / confession **CPT corpus**, knowledge-assistant voice, no preacher roleplay"
priority: high
tags: [sft, open-theology, product, contract, eval]
schema_version: 1.3
last_updated: "2026-10-19T09:23:56-03:00"
evidence: [config.py, fine_tuning/scripts/evaluate_open_theology.py, fine_tuning/scripts/open_theology_qa_checks.py, fine_tuning/eval_results/open_theology_eval_s8_weighted.json, fine_tuning/data/qa_open_theology/sft/manifest.json]
---

# Open-theology chat product contract (2026-10-19)

## Verdict: what it is / is not

- **Is:** a second product beside live RAG — a general theology LLM of the Spurgeon / Puritan / confession **CPT corpus**, knowledge-assistant voice, no preacher roleplay.
- **Is not:** a citation engine, not RAG, not an open book for every catalog entry number, and **not** an export unlock.
- **RAG capacity unchanged:** live app keeps `SPURGEON_SFT_SYSTEM_PROMPT` + CONTEXT; F §5 refusal remains the only Hub/Ollama gate (currently 0.46).
- **Next release knob:** still RAG refusal-slice (`fine-tuning/sft-improve-refusal-slice-first`).

## Contract text

`THEOLOGY_CHAT_SYSTEM_PROMPT` now: answer from corpus doctrine; catalog heading / verbatim quote **optional** (accurate if present); refuse briefly when OOC; never invent works / sermon numbers / quotes / authors.

System string remapped on OT JSONL only (train 834, eval 40, accepted, eval_accepted). Assistant gold unchanged. Manifest `system_prompt_sha256` = `f2e68223ac3c7f98fd3e0eee1cfa9154d6c06779e4477ae9f0610636b4ea53b6`. Contract id: `open_theology_chat_corpus_v1`.

## Eval gates (schema `open_theology_eval_1.1`)

**Pass/fail:** persona ≤0.05, false_refusal ≤0.10 (narrow OT predicate — no RAG `insufficient` FP), Gemini correctness/honesty ≥3.5, persona_leakage ≥4.0.

**Diagnostics only:** `quote_in_passage_rate`, `heading_cited_rate`, judge `citation_fidelity`.

`release_gate` always false. OOC held-out: `fine_tuning/data/qa_open_theology/sft/open_theology_eval_ooc.jsonl` (8 rows, unscored until GPU go).

## Mix note (stale runbook)

Weighted S8 preflight used **834** OT rows + 3264 RAG = **4098** mix (`OPEN_THEOLOGY_ROWS 834`). Next-session docs that say 558/3822 are stale.

## What we did not do

No GPU re-score, no gold soft-strip, no teacher regenerate, no RAG mix edit, no `build_qa_mix_v2.py`, no Hub/`spurgeon-qa-v2` promote, no refusal retrain.

## Next (operator go)

1. Re-score same 40 under new system string (Secure 4090 last quoted **$0.89/hr**) then Gemini judge on PC.
2. Refusal-slice FT remains the export path.
3. Later: soft-strip cite theater from gold / doctrinal eval redraw only if new-prompt score still shows invent-cite.

## Operator next (2026-10-19 evening)

Next sessions start at **go for OT re-score** — handoff: `fine-tuning/next-session-ot-corpus-chat-rescore`. Contract + tooling are landed; GPU re-score of the same 40 under the new prompt is the next OT step. Export gate still RAG refusal-slice.
