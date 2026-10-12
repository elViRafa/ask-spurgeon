---
store_path: fine-tuning/open-theology-slice-vs-rag
title: "Open theological QA is a new slice; RAG mix stays"
summary: "Operator decision 2026-10-09: the product is a RAG assistant and a theological Puritan/Spurgeon LLM"
priority: high
tags: [sft, qa-mix, puritan, spurgeon, decision]
schema_version: 1.3
last_updated: "2026-10-09T10:24:55-03:00"
evidence: ["config.py:149", fine_tuning/data/qa_mix_manifest.json, fine_tuning/NEXT_SFT_S8.md]
---

Operator decision 2026-10-09: the product is a RAG assistant and a theological Puritan/Spurgeon LLM. The chat behavior is a new SFT slice, planned in a later session.

Full planning brief: `fine-tuning/open-theology-qa-next-session`.

Locked for that plan:

- Add a few hundred open theological rows. User message has no CONTEXT block.
- Knowledge-assistant voice about Spurgeon and the Puritans. Never as them.
- Gold stays inside the CPT corpus.
- Do not edit the 3264-row RAG mix. Do not run `build_qa_mix_v2.py`.
- Do not fold the new rows into the 50/50 frozen refusal test.
- The second system prompt is undecided; the RAG prompt in `config.py` stays answer-from-CONTEXT only.
- S8 SFT on the frozen mix (`fine_tuning/NEXT_SFT_S8.md`) does not include this slice.
