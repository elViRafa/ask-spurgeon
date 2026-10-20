---
store_path: fine-tuning/open-theology-eval-not-scored-s8-weighted
title: "Open-theology held-out scored weak on S8 weighted"
summary: "**Scored.** Verdict: **weak_not_useful_yet** (`useful_theology_chat=false`)"
priority: high
tags: [sft, open-theology, eval, s8-weighted]
schema_version: 1.3
last_updated: "2026-10-19T09:01:41-03:00"
evidence: [fine_tuning/eval_results/open_theology_eval_s8_weighted.json, fine_tuning/eval_results/open_theology_eval_s8_weighted_human_summary.md, fine_tuning/eval_results/post_sft_eval_s8_weighted.json]
---

# Open-theology eval (S8 weighted, 2026-10-18)

**Scored.** Verdict: **weak_not_useful_yet** (`useful_theology_chat=false`). `release_gate=false` — does **not** unlock Hub/Ollama. RAG refusal (F §5 0.46) remains the export gate.

## Adapter
- Path: `fine_tuning/kaggle/runpod_sft_s8_weighted/sft_s8_weighted/adapter/lora/`
- SHA256: `e891731c9a71cb78c41f3cf8e1b7bbab54ea84c2ee4371d9105d773ae616f9dd`
- Base: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`

## Held-out
- `fine_tuning/data/qa_open_theology/sft/open_theology_eval.jsonl` (40 rows)
- System: `THEOLOGY_CHAT_SYSTEM_PROMPT` (no CONTEXT)

## Mechanical (n=40)
| Metric | Rate |
|--------|------|
| persona_violation_rate | **0.0** |
| quote_in_passage_rate | **0.15** |
| heading_cited_rate | **0.0** |
| false_refusal_rate | 0.1 |
| format_ok_rate | 1.0 |
| corrupt_rate | 0.0 |

## Gemini absolute judge (`gemini-3.5-flash-lite`)
| Dimension | Mean |
|-----------|------|
| correctness | **1.475** |
| citation_fidelity | **1.125** |
| persona_leakage | **4.7** (clean knowledge voice) |
| honesty | **1.325** |

## Failure pattern
Persona is fine; the model invents works/quotes/authors (wrong Puritan attributed to Spurgeon or Rutherford; fake titles like "The Joy of the Lord", "The Worth of a Word"). Zero catalog heading matches against gold headings. Quote⊂passage only 6/40.

## Ops
- Commands: `runpod_sft_s8_weighted_open_theology_eval.ps1 -Go` (Secure 4090 @ $0.89/hr); local `evaluate_open_theology.py --judge`
- Pod `cdg8ygmckh3esv` destroyed; `runpodctl pod list` empty; MCP `list-pods` empty
- Reports: `fine_tuning/eval_results/open_theology_eval_s8_weighted.json` + `_human_summary.md`

## Next FT knob
Keep **RAG refusal-slice** first (export still blocked). OT chat needs teacher/data or mix follow-up **after** refusal ≥0.85 — not instead of it. More open-theology train rows alone do not fix RAG FNs.

## Contract change (2026-10-19)

The 2026-10-18 scores above were under the **old mandatory heading+quote** chat contract. Product decision: `fine-tuning/open-theology-chat-corpus-contract` (`open_theology_chat_corpus_v1`). Cite/quote are optional; eval schema `open_theology_eval_1.1` drops them as pass/fail. Do **not** compare a future re-score to the 2026-10-18 cite-contract numbers without noting the contract change. Re-score of the same 40 under the new system string needs operator **go** (last Secure 4090 ~$0.89/hr). Export gate unchanged: RAG refusal slice.
