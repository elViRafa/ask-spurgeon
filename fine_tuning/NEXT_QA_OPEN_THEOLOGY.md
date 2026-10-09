# Next job — Open theological QA slice (data only, no GPU)

Build a side SFT slice of open theological questions. The frozen RAG mix and
the S8 SFT run stay untouched.

Memories: `fine-tuning/open-theology-qa-next-session`,
`fine-tuning/open-theology-slice-vs-rag`.

## Contract

| Knob | Value |
|------|--------|
| Slice | `open_theology` — no CONTEXT user turn |
| System | `config.THEOLOGY_CHAT_SYSTEM_PROMPT` |
| Train size | 300 jobs (150 Puritan / 100 Spurgeon / 50 confession+catechism) |
| Eval reserve | 40 jobs in `eval_jobs.jsonl` (never in train) |
| Output | `fine_tuning/data/qa_open_theology/` |
| Admin bot | Clerk (`fine_tuning/GROK_BOT_CLERK.md`) |
| Skill | `/qa-generation-ops` |

## Dry (no API)

```powershell
cd C:\Users\rafael\Projetos\search-sermons
python fine_tuning/scripts/plan_open_theology_jobs.py --dry-run
python fine_tuning/scripts/plan_open_theology_jobs.py
python fine_tuning/scripts/generate_open_theology_qa.py --limit 25
python -m pytest fine_tuning/scripts/test_open_theology_qa.py -q
```

Expect plan counts 300 train / 40 eval, generator `DRY COMPLETE (wrote nothing)`,
and pytest green.

## Apply (needs operator go — Clerk may issue after go)

```powershell
cd C:\Users\rafael\Projetos\search-sermons
python fine_tuning/scripts/generate_open_theology_qa.py --apply --limit 25 --provider groq
```

Keys stay in `.env` on the operator PC. Clerk does not paste keys.

Clear a halt only after a prompt or catalog fix:

```powershell
python fine_tuning/scripts/generate_open_theology_qa.py --clear-halt --limit 25
# then, after go:
python fine_tuning/scripts/generate_open_theology_qa.py --apply --limit 25 --provider groq
```

## Halt

Campaign stops when the batch reject rate exceeds 40% (after ≥5 rows) or when
3 consecutive teacher/check failures occur. Fix the teacher prompt or catalog,
then `--clear-halt`.

## Do not

- Edit `qa_mix_train.jsonl` / `qa_test_frozen.jsonl`
- Run `build_qa_mix_v2.py`
- Attach this slice to `NEXT_SFT_S8.md`
- Rent GPU for this job
- Speak as Spurgeon in gold answers
