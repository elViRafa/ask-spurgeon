---
store_path: fine-tuning/next-session-ot-corpus-chat-rescore
title: "OT corpus-chat re-score DONE (2026-10-19)"
summary: "**Status (2026-10-19):** DONE"
priority: medium
tags: [sft, open-theology, handoff, eval, next-session]
schema_version: 1.3
last_updated: "2026-10-19T09:41:57-03:00"
evidence: [fine-tuning/open-theology-chat-corpus-contract, fine_tuning/scripts/runpod_sft_s8_weighted_open_theology_eval.ps1, fine_tuning/kaggle/runpod_sft_s8_weighted/sft_s8_weighted/adapter/lora/]
---

# Next session — open-theology corpus-chat re-score

**Status (2026-10-19):** DONE. See `fine-tuning/open-theology-eval-corpus-chat-rescore-2026-10-19`.

## Result (short)

- Still `weak_not_useful_yet` / `useful_theology_chat=false` under new cite-optional prompt
- Correctness/honesty ~2.53; persona + false_refusal OK
- Invent-cite persists (diagnostic cite rates near floor)
- Pod destroyed; report at `fine_tuning/eval_results/open_theology_eval_s8_weighted.json`

## Next operator pick (not this OT job)

1. **Export path:** RAG refusal-slice FT — `fine-tuning/sft-improve-refusal-slice-first` / `fine-tuning/next-session-sft-f-gates-local-adapter`
2. Optional later OT: gold soft-strip / teacher regen only if pursuing OT usefulness separately (invent-cite confirmed under new prompt)
3. Optional: score `open_theology_eval_ooc.jsonl` (8 rows) — not run on this go

Do not treat OT score as Hub unlock.
