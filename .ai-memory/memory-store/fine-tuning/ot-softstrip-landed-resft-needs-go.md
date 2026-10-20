---
store_path: fine-tuning/ot-softstrip-landed-resft-needs-go
title: "OT soft-strip + eval redraw landed; re-SFT needs go"
summary: "- `soft_strip_open_theology_gold.py`: drop heading cites + fabricated quotes; cleanup outside quotes only (preserve `Christ ;` inside quotes)"
priority: medium
tags: [sft, open-theology, soft-strip, handoff]
schema_version: 1.3
last_updated: "2026-10-19T15:12:12-03:00"
---

# OT soft-strip landed (2026-10-19)

## Done

- `soft_strip_open_theology_gold.py`: drop heading cites + fabricated quotes; cleanup outside quotes only (preserve `Christ ;` inside quotes)
- Applied to accepted 838 + eval_accepted 40 (check_fail=0)
- Eval trivia redraw: 4 junk URL/entry rows → doctrinal Q&A from same works (`redraw_open_theology_eval_trivia.py`)
- Re-export: train 834 / eval 40; train SHA `157ba263…`, eval SHA `9f10f533…`
- Honesty plan: 60 jobs in `honesty_jobs.jsonl`; teacher apply needs go (`NEXT_OT_HONESTY_BATCH.md`)
- Weighted SFT dry READY; dirty OT sft files need `-AllowDirtySync` or commit before `-Go`

## Needs go

1. Optional: `--honesty --apply --limit 60` then merge + soft-strip + export
2. `runpod_sft_s8_weighted_orchestrate.ps1 -Go` (cleaned OT)
3. `runpod_sft_s8_weighted_open_theology_eval.ps1 -Go` re-score

Runbook: `fine_tuning/NEXT_OT_SOFTSTRIP_RESFT.md`

## Not this track

RAG refusal / Hub / build_qa_mix_v2
