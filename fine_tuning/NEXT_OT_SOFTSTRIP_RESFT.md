# OT soft-strip data landed — re-SFT + re-score (needs go)

Data path complete 2026-10-19. GPU rent blocked until operator says **go**.

## Landed (no go)

- Soft-strip cite theater on `accepted.jsonl` / `eval_accepted.jsonl`
  (`soft_strip_open_theology_gold.py --apply`)
- Trivia/URL-index eval redraw (4 rows) → doctrinal Q&A from same works
- Re-export: train **834**, eval **40**
  - train SHA256 `157ba2636d7360aa3ed9e5c6872ca6e8ddfa126f30058fbf5630fe41bb2a18c7`
  - eval SHA256 `9f10f533c3652e158dedd972d0ed15f1cf2e2ad07621dddf2aa6a0e3f67c2483`
- Honesty jobs planned (60): `honesty_jobs.jsonl` — teacher **apply** still needs go
  (see `NEXT_OT_HONESTY_BATCH.md`)

## Go order (recommended)

1. Optional honesty teacher:  
   `python fine_tuning/scripts/generate_open_theology_qa.py --honesty --apply --limit 60`  
   then append `honesty_accepted.jsonl` into `accepted.jsonl`, soft-strip, re-export.
2. Weighted SFT (cleaned OT + frozen RAG mix):  
   dry already OK →  
   `.\fine_tuning\scripts\runpod_sft_s8_weighted_orchestrate.ps1 -Go`  
   (or Vast PEFT fallback). New adapter dir; no Hub overwrite; `SFT_EXPORT=0`.
3. OT re-score under same contract:  
   `.\fine_tuning\scripts\runpod_sft_s8_weighted_open_theology_eval.ps1 -Go`  
   Secure 4090 last ~$0.89/hr. Compare to 2026-10-19 `weak_not_useful_yet`.

## Not this track

- RAG refusal-slice / Hub / `spurgeon-qa-v2`
- `build_qa_mix_v2.py`
