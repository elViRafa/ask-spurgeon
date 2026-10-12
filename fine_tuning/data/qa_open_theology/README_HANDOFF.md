# Open-theology QA slice: handoff for fine-tuning (2026-10-12)

Status: train split READY. Eval split partial (9/40; 31 pending on Groq daily quota, hourly retry running).

## Files to use
- `accepted.jsonl`: TRAIN, 569 rows (puritan 286, spurgeon 191, confession 92). Teacher groq openai/gpt-oss-120b (+18 gemini-2.5-flash).
- `eval_accepted.jsonl`: EVAL, 9 rows so far (target 40). Do not train on these.
- Ignore: `rejected.jsonl` (31), `requeued_from_rejected.jsonl`, `*.bak-*`, `jobs*.jsonl`, `catalog.json`, status files.

## Row format (chat SFT)
`{"job_id", "slice":"open_theology", "teacher", "model", "created_at", "messages":[system,user,assistant], "meta":{bucket, work_id, heading, passage, source_path, slice, job_id}}`
Train on `messages` only. `meta.passage` is the source excerpt (grounding/debug, not a training input).

## Checks done
- All rows are system/user/assistant; 0 duplicate job_ids; 0 duplicate questions.
- Eval vs train: 0 shared questions, 0 shared work_id, 0 shared passages (no leakage).
- Answers carry a verbatim quote + bracketed catalog heading (enforced by open_theology_qa_checks.py). Median answer ~530 chars.
- Known soft issue: ~69 train answers say "the passage/excerpt" (meta wording). Optional: filter or regenerate; decision pending.
- Pending decision: drop confession-003, confession-023, puritan-087, spurgeon-083.

## Rules
- Separate slice: do NOT merge into qa_mix_train.jsonl, qa_test_frozen.jsonl, or the RAG mix; do not run build_qa_mix_v2.py for it.
- Load it as its own dataset in the SFT recipe (e.g. weighted alongside the existing mix).
