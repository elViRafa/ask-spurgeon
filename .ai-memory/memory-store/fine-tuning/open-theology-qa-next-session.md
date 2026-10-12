---
store_path: fine-tuning/open-theology-qa-next-session
title: "Next session: plan open theological QA slice"
summary: "Operator intent: the model should be a theological Puritan/Spurgeon LLM as well as a RAG assistant"
priority: high
tags: [sft, qa-mix, puritan, spurgeon, handoff]
schema_version: 1.3
last_updated: "2026-10-09T10:24:53-03:00"
evidence: ["config.py:149", fine_tuning/data/qa_mix_manifest.json, fine_tuning/NEXT_SFT_S8.md, fine_tuning/eval_results/post_sft_eval.json]
---

# Open theological QA — planning handoff (2026-10-09)

Operator intent: the model should be a theological Puritan/Spurgeon LLM as well as a RAG assistant. Plan the new QA data in a later session. Do not generate the rows in the session that only saved this note. No GPU.

## What to add

A new SFT slice of open theological questions. A few hundred rows is the first slice.

- The assistant speaks about Spurgeon and the Puritans (distinctions, doctrines, citations). It does not speak as Spurgeon, Owen, Calvin, or any Puritan.
- No vocatives: Beloved, My beloved, Dear friends, My brethren, amados, meus queridos irmãos. No first-person preacher roleplay.
- The user message has no CONTEXT block and does not say "answer based ONLY on the context."
- Gold answers stay inside the CPT corpus (Spurgeon sermons, Puritan works, confessions/catechisms). Cite a work the corpus actually contains.
- This slice has its own later eval. Do not merge it into `qa_test_frozen.jsonl` (50 answerable / 50 refusal). That test measures the RAG refusal gate.

## What stays frozen

| Item | Value |
|------|--------|
| RAG train | 3264 rows in `fine_tuning/data/qa_mix_train.jsonl` |
| Slices | answerable 2793, refusal 370 (11.34%), multiturn 100, catechism overlay 241 |
| Val / frozen test | 153 / 100 |
| Manifest | `fine_tuning/data/qa_mix_manifest.json` version `qa_mix_v2` |
| RAG prompt | `SPURGEON_SFT_SYSTEM_PROMPT` in `config.py` (about line 149): answer only from CONTEXT; refuse when CONTEXT is silent |
| Rebuild | Do not run `build_qa_mix_v2.py`. It wipes overlays. |

Leave those RAG rows unchanged. Dropping open Puritan answers into the CONTEXT template trains "refuse" and "answer from memory" on the same prompt. GATE-0 already missed 23/50 refusals that way (tp 27, fp 1, tn 49, fn 23, recall 0.54, precision 0.96).

## Why a second prompt is an open decision

`fine-tuning/qa-prompt-type-decision` locked one system string for the RAG app. This slice cannot reuse that string, because the string forbids answering from memory. The planning session writes the theology-chat system prompt and says when the app sends it. The RAG path keeps the current string.

## Order

1. S8 SFT on the frozen RAG mix is already dry-ready (`fine_tuning/NEXT_SFT_S8.md`). Base is `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`. Hub LoRA v2 `06354dfc` stays. That run does not include this slice.
2. This data plan is the following job.
3. CPT already holds the domain language. Isolation C on adapter `22698039`: Spurgeon PPL 11.88 (−17.0%), Puritan 5.26 (−12.8%), confession 5.01 (−10.7%), general 12.50 (+3.8% vs base). Puritan loss 1.6605 vs gate 1.6349. Do not resume CPT to create this chat behavior.

## Related memories

- `fine-tuning/qa-knowledge-not-persona`
- `fine-tuning/qa-prompt-type-decision`
- `fine-tuning/qa-mix-spurgeon-only-decision`
- `fine-tuning/qa-mix-size-vs-refusal`
- `pretraining/cpt-s8-next-is-sft`
