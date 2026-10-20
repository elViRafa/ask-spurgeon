---
store_path: fine-tuning/open-theology-eval-corpus-chat-rescore-2026-10-19
title: "OT corpus-chat re-score 2026-10-19: still weak"
summary: "**Go completed.** Same 40 held-out rows under `open_theology_chat_corpus_v1` / cite-optional system prompt"
priority: high
tags: [sft, open-theology, eval, corpus-chat]
schema_version: 1.3
last_updated: "2026-10-19T09:43:26-03:00"
---

# OT corpus-chat re-score (2026-10-19)

**Go completed.** Same 40 held-out rows under `open_theology_chat_corpus_v1` / cite-optional system prompt. Adapter SHA256 `e891731c9a71cb78c41f3cf8e1b7bbab54ea84c2ee4371d9105d773ae616f9dd`.

## Run

- Host: RunPod Secure RTX 4090 `lx2b2qymrrrgqj` US-IL-1 @ **$0.89/hr**
- Wall: ~748s (~12.5 min); merge reused `spurgeon_qa_s8w_merged_hf`
- Orchestrator: `runpod_sft_s8_weighted_open_theology_eval.ps1 -Go` → `ORCH_EXIT=0`
- Pod deleted; MCP + `runpodctl` list empty
- Report: `fine_tuning/eval_results/open_theology_eval_s8_weighted.json` (schema `open_theology_eval_1.1`)
- Judge: Gemini `gemini-3.5-flash-lite` (40/40)

## Verdict

- `useful_theology_chat=false` / `weak_not_useful_yet`
- `release_gate=false` (expected; export still RAG refusal)
- Pass: persona 0.0, false_refusal 0.025, persona_leakage mean 5.0
- Fail: correctness mean **2.525**, honesty mean **2.525** (need ≥3.5)
- Diagnostics (not gates): quote_in_passage 0.075, heading_cited 0.0, citation_fidelity mean 2.5

## Read

New prompt did **not** make the slice useful. Invented works / wrong sermon titles / generic doctrine still dominate judge failures — invent-cite persists even with cite optional. Persona/refusal side is fine.

## Next FT knob

Still **`rag_refusal_slice`** for Hub/Ollama export (`fine-tuning/sft-improve-refusal-slice-first`). Optional later OT work: soft-strip cite theater from gold / doctrinal redraw — only after refusal path if operator wants OT usefulness improved separately. OOC 8-row slice not scored this run.

## Invent-cite detail (Forge)

Cite-optional did not stop invented quotations: **20/40** quote a span not in the source passage, **17/40** quote nothing, **3/40** quote text actually in the passage. Heading cited: 0/40. Judge notes also name fabricated titles. Correctness/honesty fail — miss is not citations-only.

Remote `evaluate.py` exited 1 on RAG F-gates for this answerable set; gen file still written (`OT_GEN_OK`); orchestrator accepted it.
