# Open-theology honesty / anti-invent batch (needs go)

After soft-strip + eval trivia redraw (2026-10-19). Does **not** merge into
`qa_mix_train.jsonl`. Does **not** rent GPU.

## Ready now

```text
python fine_tuning/scripts/plan_open_theology_honesty_jobs.py --apply --n 60
```

Writes `fine_tuning/data/qa_open_theology/honesty_jobs.jsonl` (60 jobs from
existing accepted passages; junk URL indexes skipped).

Dry teacher:

```text
python fine_tuning/scripts/generate_open_theology_qa.py --honesty --limit 5
```

## Needs operator go

```text
python fine_tuning/scripts/generate_open_theology_qa.py --honesty --apply --limit 60
```

Then merge into the main train slice:

```text
# append honesty_accepted.jsonl rows into accepted.jsonl (dedupe by job_id)
# then:
python fine_tuning/scripts/soft_strip_open_theology_gold.py --apply
python fine_tuning/scripts/export_open_theology_sft.py --apply
```

Halt rules unchanged (reject rate >40% or 3 consecutive fails).

## Not this job

- RAG refusal-slice / Hub export
- Full 834 teacher regenerate
- GPU re-SFT (separate go after honesty merge lands)
