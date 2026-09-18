---
store_path: fine-tuning/qa-gold-rewrite-pilot
title: "SFT QA gold rewrite pilot (20 rows, merged)"
summary: "**Status:** Complete and **merged** into `qa_mix_train.jsonl`"
priority: high
tags: [sft, qa-mix, gold, rewrite]
schema_version: 1.3
last_updated: "2026-08-28T22:16:08-04:00"
evidence: [fine_tuning/scripts/merge_qa_gold_rewrite.py, fine_tuning/data/qa_mix_manifest.json, fine_tuning/data/qa_rewrite_pilot/pilot_manifest.json]
---

# SFT QA gold rewrite pilot (20 rows, 2026-08-29)

**Status:** Complete and **merged** into `qa_mix_train.jsonl`. Mechanical review PASS. Val and frozen test untouched.

## Overlay
- 16 answerable + 4 refusal (seed 3407, short originals preferred).
- Teacher: cursor-session. Inline quotes + `[Sermon N]` only when the header is in CONTEXT.
- Pilot-11: original Lord's Table claim dropped — not in the v2 chunk.

## Files
- `fine_tuning/data/qa_rewrite_pilot/` — sample.json, `qa_gold_rewrite_pilot.jsonl`, `pilot_manifest.json`

## Mix
- `qa_mix_manifest.json` `gold_overlay.rows=20`
- Zip rebuilt: `spurgeon-qa-mix-v1.zip` (~11.75 MB). Re-upload before D/E/F.
- `13_sft_local_readiness.py` PASS.
