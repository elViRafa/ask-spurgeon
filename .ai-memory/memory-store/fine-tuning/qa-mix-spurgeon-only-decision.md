---
store_path: fine-tuning/qa-mix-spurgeon-only-decision
title: "SFT QA stays Spurgeon-only (decision)"
summary: "**Decided 2026-08-29** after operator question on mixing writers in QA SFT data"
priority: high
tags: [sft, qa-mix, decision, spurgeon]
schema_version: 1.3
last_updated: "2026-08-29T09:53:15-04:00"
---

# Decision: SFT QA mix stays Spurgeon-only (main slice)

**Decided 2026-08-29** after operator question on mixing writers in QA SFT data.

## Decision
Keep **SFT QA data Spurgeon-only** for the primary mix. Do **not** train the assistant as Calvin/Edwards/etc.

Optional later (F5 gap, not required for dry-run): **~8% catechism/confession as CONTEXT** with Spurgeon still as speaker — teaches grounded reading of a second doc type, not multi-author persona.

## Why
- Serve contract is Spurgeon-from-sermons: `SPURGEON_SFT_SYSTEM_PROMPT`, `[Sermon N]` headers, RAG index = `chspurgeon-sermons` only.
- Mixing other writers as speakers causes persona bleed, train/serve mismatch, citation confusion.
- **CPT** already mixes Spurgeon + Puritans + confessions (domain language). **SFT** should match the live app answer format.

## Do not
- Equal-weight Edwards / Lloyd-Jones / Henry as answering authors
- Put Puritan/confession chunks in user CONTEXT unless retrieval will return them
- Alpaca-style generic-assistant replay (dilutes persona)

## Current data
qa_mix_v2 is Spurgeon-only; F5 gap "No catechism/confession slice (~8%)" remains intentional until RAG indexes those texts or operator asks for the 8% CONTEXT slice.

## Supersession (2026-08-29) — speaker/persona

The *speaker/persona* half of this decision is **superseded** by `fine-tuning/qa-knowledge-not-persona`.

Still valid:
- Keep SFT *examples* Spurgeon-sermon-heavy until RAG returns Puritan/confession chunks.
- Do **not** train Calvin/Edwards/Owen as the answering speaker.
- Do **not** put Puritan chunks in user CONTEXT unless retrieval will return them.
- CPT remains the place other writers' *language* is absorbed.

Changed:
- The assistant is a knowledge Q&A speaker, not Spurgeon-as-character.
- `SPURGEON_SFT_SYSTEM_PROMPT` is no longer "You are Charles Haddon Spurgeon".
- Alpaca-style generic replay is still unwanted; the replacement is a grounded knowledge voice, not a sterile modern-assistant ban on all register.
