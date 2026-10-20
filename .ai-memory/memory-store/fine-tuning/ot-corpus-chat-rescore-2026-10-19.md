---
store_path: fine-tuning/ot-corpus-chat-rescore-2026-10-19
title: "OT corpus-chat re-score still weak; invent-cite remains"
summary: "New prompt re-score under `THEOLOGY_CHAT_SYSTEM_PROMPT` (cite optional)"
priority: high
tags: [sft, open-theology, eval, s8-weighted, gemini]
schema_version: 1.3
last_updated: "2026-10-19T09:43:06-03:00"
evidence: [fine_tuning/eval_results/open_theology_eval_s8_weighted.json, fine_tuning/eval_results/open_theology_eval_s8_weighted.gen.json]
---

# Open-theology corpus-chat re-score (2026-10-19)

New prompt re-score under `THEOLOGY_CHAT_SYSTEM_PROMPT` (cite optional). Distinct from the 2026-10-18 cite-contract score.

- Pod: Runpod Secure RTX 4090 `lx2b2qymrrrgqj` US-IL-1, $0.89/hr, SSH `203.57.40.56`, wall 748s. Destroyed. `runpodctl pod list` and MCP list-pods empty.
- Adapter SHA256 `e891731c9a71cb78c41f3cf8e1b7bbab54ea84c2ee4371d9105d773ae616f9dd`
- Report: `fine_tuning/eval_results/open_theology_eval_s8_weighted.json` schema `open_theology_eval_1.1`, contract `open_theology_chat_corpus_v1`, n=40, Gemini `gemini-3.5-flash-lite`
- `useful_theology_chat=false` (`weak_not_useful_yet`). `release_gate=false`. Does not unlock Hub/Ollama.
- Mechanical: persona 0.0, false_refusal 0.025 (1/40), format_ok 0.975
- Judge means: correctness 2.525, honesty 2.525, persona_leakage 5.0, citation_fidelity 2.5 (diagnostic)
- Cite diagnostics: quote_in_passage_rate 0.075 (3/40), heading_cited_rate 0.0. Of 40 rows, 20 quoted a span not in the passage, 17 quoted nothing, 3 quoted in-passage text. Invent-cite is still a problem under the optional-cite prompt.
- OOC 8-row slice not run (not wired into the orchestrator).
- Next export knob remains RAG refusal, not this score.
