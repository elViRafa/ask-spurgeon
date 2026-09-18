---
store_path: fine-tuning/qa-knowledge-not-persona
title: "SFT/serve: knowledge assistant, not Spurgeon persona"
summary: "SFT/chat must be knowledge assistant about texts, never Spurgeon persona; catechism CONTEXT landed."
priority: high
tags: [sft, qa-mix, persona, spurgeon, puritans, decision]
schema_version: 1.3
last_updated: "2026-08-29T11:07:00-04:00"
evidence: ["config.py:115", "utils/prompts.py:16", fine_tuning/scripts/rewrite_qa_answers_teacher.py, fine_tuning/scripts/qa_rewrite_checks.py, fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2]
summary_hash: 3111e39f906f87e45fdd826d3619f88b
---

# Decision: knowledge assistant, not Spurgeon persona (2026-08-29)

**Decided 2026-08-29.** Live chat is Q&A over texts, not a character. Supersedes the *speaker/persona* half of `fine-tuning/qa-mix-spurgeon-only-decision`.

## Contract
- Speak **about** Spurgeon and the Puritans (knowledge, distinctions, citations). Never speak **as** them.
- Depth first. Light register welcome (scriptural cadence, metaphor, distinction) without costume.
- No vocatives: `Beloved,`, `My beloved`, `Dear friends`, `My brethren`, PT `amados` / `meus queridos irmãos`.
- Ground every claim in CONTEXT. If CONTEXT is silent, refuse plainly.
- Do **not** fill Puritan (or any) answers from parametric memory when CONTEXT has no such headings. Naming Puritans in the prompt is a source class, not a license to invent.

## Canonical prompt
Keep the name `SPURGEON_SFT_SYSTEM_PROMPT`. `SYSTEM_PROMPT_NEUTRAL` is an alias. App uses `build_user_prompt()` / `USER_PROMPT_TEMPLATE` (no third hardcoded copy). Notebooks import the config string at generate time.

## Data
- Do **not** run `build_qa_mix_v2.py` (wipes overlays).
- Remap jsonl system messages; rewrite assistants via teacher before GPU.
- Optional leading-vocative strip on remaining train assistants.
- SFT examples stay Spurgeon-sermon-heavy until RAG returns Puritan chunks. Never train Calvin/Owen as the answering speaker.
- Catechism CONTEXT slice + Chroma ingest landed 2026-08-29 (see `fine-tuning/next-session-handoff`).

## Out of scope until quote gate + operator go
No GPU, no D→E→F run, no EXPORT/GGUF, no full rewrite of all ~2859 originals via teacher.
