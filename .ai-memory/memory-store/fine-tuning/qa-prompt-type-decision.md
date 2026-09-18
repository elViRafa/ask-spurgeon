---
store_path: fine-tuning/qa-prompt-type-decision
title: "One prompt; diversify task slices"
summary: "**Locked after live verify.** Improves SFT via example-type diversity, not multiple prompts"
priority: high
tags: [sft, qa-mix, decision, prompts]
schema_version: 1.3
last_updated: "2026-08-30T21:26:18-04:00"
evidence: ["config.py:115", "utils/prompts.py:16", fine-tuning/qa-knowledge-not-persona, fine-tuning/qa-prompt-strategy-verify]
---

# Decision: one QA prompt; diversify task slices (2026-08-30)

**Locked after live verify.** Improves SFT via example-type diversity, not multiple prompts.

## Do

1. Keep a single canonical system string: `SPURGEON_SFT_SYSTEM_PROMPT` (= `SYSTEM_PROMPT_NEUTRAL`) across train / val / test / app / Modelfile.
2. Keep a single user wrapper: `USER_PROMPT_TEMPLATE` (`CONTEXT` + headed chunks + `QUESTION:`).
3. Expand **task slices** under that contract, in order:
   - **Catechism CONTEXT → ~8%** (~241 of current train; need ~+151). Prefer more confession/catechism doc types with headers matching `format_context` catechism branch — not a second system prompt.
   - **Multi-turn 2–5%** (60–151 rows): 2-turn grounded follow-ups matching `build_chat_messages` history behavior.
   - Optional: more question phrasings (compare / distinguish / "what does Spurgeon teach") inside the same template.
4. Teacher rewrite remains optional further lift; soft gates already MET (quote 21.5%, teacherish 553).

## Do not

- Multiple system prompts in the SFT mix (persona + neutral + specialist + strict + concise).
- Alpaca or alternate user wrappers.
- Bake `get_system_prompt(variant=strict|concise)` into train jsonl unless serve always sends that variant.
- Train Calvin/Owen as answering speakers.
- Run `build_qa_mix_v2.py` (wipes overlays) without an overlay-safe rebuild path + operator go.
- Start GPU D→E→F without operator go.

## Why

Train/serve prompt mismatch was a primary F5 failure mode. The live app always sends one system + one user shape; slice diversity teaches refusal, second doc-type grounding, and follow-ups without forking that contract.
