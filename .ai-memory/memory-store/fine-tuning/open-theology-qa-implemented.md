---
store_path: fine-tuning/open-theology-qa-implemented
title: "Open theology QA slice tooling ready for Clerk"
summary: "Implemented the open-theology SFT side slice (2026-10-09)"
priority: high
tags: [sft, qa-mix, open-theology, grok, clerk]
schema_version: 1.3
last_updated: "2026-10-09T10:38:07-03:00"
evidence: [config.py, fine_tuning/scripts/plan_open_theology_jobs.py, fine_tuning/scripts/generate_open_theology_qa.py, fine_tuning/GROK_BOT_CLERK.md, fine_tuning/NEXT_QA_OPEN_THEOLOGY.md]
---

Implemented the open-theology SFT side slice (2026-10-09). RAG mix stays frozen.

## Delivered

- `THEOLOGY_CHAT_SYSTEM_PROMPT` in `config.py` (no CONTEXT; RAG prompt unchanged).
- Planner `fine_tuning/scripts/plan_open_theology_jobs.py`: 300 train + 40 eval jobs under `fine_tuning/data/qa_open_theology/`, skips mix_v7 holdouts.
- Generator `generate_open_theology_qa.py` (dry by default; `--apply` needs go).
- Checks in `open_theology_qa_checks.py` (CONTEXT leak, vocative, quote, citation).
- Clerk bot profile `fine_tuning/GROK_BOT_CLERK.md`, skill `.cursor/skills/qa-generation-ops/SKILL.md`, runbook `fine_tuning/NEXT_QA_OPEN_THEOLOGY.md`.
- Pytest `test_open_theology_qa.py` 15 passed.

## Next

Operator creates Clerk in Grok Bot from `GROK_BOT_CLERK.md`. After go: `python fine_tuning/scripts/generate_open_theology_qa.py --apply --limit 25 --provider groq`.

Do not merge into `qa_mix_train.jsonl` or attach to S8 SFT.
