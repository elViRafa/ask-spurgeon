---
store_path: grok/clerk-qa-generation
title: "Grok Bot Clerk for open-theology QA generation"
summary: "Clerk is the third Grok Bot teammate (alongside Forge and Foundry)"
priority: high
tags: [grok, clerk, qa-generation, sft]
schema_version: 1.3
last_updated: "2026-10-09T10:38:09-03:00"
evidence: [fine_tuning/GROK_BOT_CLERK.md, .cursor/skills/qa-generation-ops/SKILL.md, fine_tuning/NEXT_QA_OPEN_THEOLOGY.md]
---

Clerk is the third Grok Bot teammate (alongside Forge and Foundry).

- Profile: `fine_tuning/GROK_BOT_CLERK.md`
- Skill: `.cursor/skills/qa-generation-ops/SKILL.md`
- Job: administer `fine_tuning/data/qa_open_theology/` status and batches.
- Allowed without go: status / dry generate.
- Needs go: `--apply`.
- Never: `build_qa_mix_v2.py`, edit RAG mix, GPU rent, Hub upload, paste API keys.
- Create in the Grok Bot app (no create API from Cursor).
