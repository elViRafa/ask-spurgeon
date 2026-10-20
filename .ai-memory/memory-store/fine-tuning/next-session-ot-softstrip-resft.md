---
store_path: fine-tuning/next-session-ot-softstrip-resft
title: "Next session: OT soft-strip re-SFT + re-score (needs go)"
summary: "Operator intent: pick up after soft-strip data landed (2026-10-19/20)"
priority: high
tags: [sft, open-theology, handoff, next-session]
schema_version: 1.3
last_updated: "2026-10-20T09:56:53-03:00"
---

# Next session — OT soft-strip → re-SFT → re-score

Operator intent: pick up after soft-strip data landed (2026-10-19/20).

## Ready now

- Soft-strip applied (`soft_strip_open_theology_gold.py`); cite theater stripped from accepted/eval_accepted
- Eval trivia redraw: 4 junk rows → doctrine (`redraw_open_theology_eval_trivia.py`)
- SFT export: train **834** / eval **40** (SHAs in `sft/manifest.json`)
- Honesty jobs planned: 60 in `honesty_jobs.jsonl` — teacher **apply** needs go
- Weighted SFT dry READY; dirty OT sft paths need `-AllowDirtySync` or commit before `-Go`
- Runbooks: `fine_tuning/NEXT_OT_SOFTSTRIP_RESFT.md`, `fine_tuning/NEXT_OT_HONESTY_BATCH.md`
- Prior re-score still `weak_not_useful_yet` (`fine-tuning/open-theology-eval-corpus-chat-rescore-2026-10-19`)

## Do on go

1. Optional: `python fine_tuning/scripts/generate_open_theology_qa.py --honesty --apply --limit 60` → merge honesty_accepted into accepted → soft-strip → export
2. Quote $/hr; `runpod_sft_s8_weighted_orchestrate.ps1 -Go` (cleaned OT; no Hub; `SFT_EXPORT=0`). Forge for long watch.
3. `runpod_sft_s8_weighted_open_theology_eval.ps1 -Go` under `open_theology_chat_corpus_v1`; Gemini judge on PC
4. Destroy pod; compare to 2026-10-19 weak score

## Still not this job

- RAG refusal-slice / Hub / `spurgeon-qa-v2` / `build_qa_mix_v2.py`
