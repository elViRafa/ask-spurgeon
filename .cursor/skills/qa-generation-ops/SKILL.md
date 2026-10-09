---
name: qa-generation-ops
description: >-
  Administer Ask Spurgeon open-theology QA generation campaigns. Use when
  planning or applying teacher batches, reading qa_open_theology status,
  or when Grok Bot Clerk manages QA generation. Not for RAG mix rebuilds
  or GPU training.
---

# QA generation ops (Clerk path)

You administer the **open-theology QA campaign**. You do not rent GPUs and
you do not rebuild the RAG mix.

Repo: `https://github.com/elViRafa/ask-spurgeon.git`

## Pipeline

```text
plan_open_theology_jobs.py
  → fine_tuning/data/qa_open_theology/{catalog,jobs,eval_jobs,status}
  → generate_open_theology_qa.py (dry)
  → operator go
  → generate_open_theology_qa.py --apply --limit N
  → accepted.jsonl (side slice; not merged into qa_mix_train)
```

Runbook: `fine_tuning/NEXT_QA_OPEN_THEOLOGY.md`
Bot profile: `fine_tuning/GROK_BOT_CLERK.md`

## Frozen — do not touch

- `fine_tuning/data/qa_mix_train.jsonl` (3264 RAG rows)
- `fine_tuning/data/qa_test_frozen.jsonl`
- `build_qa_mix_v2.py` (wipes overlays)
- S8 SFT job (`fine_tuning/NEXT_SFT_S8.md`) — separate; does not include this slice

## Always allowed (no go)

- Read `fine_tuning/data/qa_open_theology/status.json`
- Dry: `python fine_tuning/scripts/generate_open_theology_qa.py --limit 25`
- Plan dry: `python fine_tuning/scripts/plan_open_theology_jobs.py --dry-run`
- Pytest: `python -m pytest fine_tuning/scripts/test_open_theology_qa.py -q`

## Needs operator go

- `generate_open_theology_qa.py --apply`
- Re-running the planner when accepted rows already exist (wipes the queue shape)
- Clearing a halt after a prompt/catalog fix (`--clear-halt`)

## Halt rules

Stop the campaign when:

- Batch reject rate exceeds 40% (after ≥5 rows in the run), or
- 3 consecutive teacher/check failures (`CONSECUTIVE_FAIL_ABORT`)

A halt is a **prompt or catalog fix**, not a silent retry loop.

## Row contract (open theology)

- System = `config.THEOLOGY_CHAT_SYSTEM_PROMPT` (no CONTEXT wording)
- User = question only (no CONTEXT block, no "answer based ONLY")
- Knowledge voice; reuse `caricature_errors` (no Beloved / preacher roleplay)
- Gold cites the catalog heading and includes one verbatim passage quote
- Train rows are answerable (not refusals)
- Sources skip `mix_v7` holdouts

## Status format

```text
QA open-theology
  accepted: N
  rejected: N
  remaining: N
  halted: yes/no (reason)
  next: job_id
  last_error: ...
```

## Hard do-nots

- Merge into `qa_mix_train.jsonl` or `qa_test_frozen.jsonl`
- Author Q&A pairs in chat instead of the teacher script
- Log API keys
- Rent GPU / Hub upload / GGUF
- Speak as Spurgeon in prompts or gold
