---
store_path: pretraining/cpt-v2-next-session-handoff
title: "CPT v2 handoff: C done, LoRA on private Hub, do not merge"
summary: "**Do not re-C this adapter"
priority: high
tags: [cpt, runpod, handoff, c-eval]
schema_version: 1.3
last_updated: "2026-08-27T09:50:01-04:00"
evidence: [continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# CPT v2 next session — after Runpod C (do not merge)

**Do not re-C this adapter. Do not push Kaggle. Do not merge.** Probe PPL **beats** Ampere bf16 base on all four holdouts. Section 5 -15% still **FAIL** (puritan -5.0%, confession -7.0%).

Kaggle B v14 remains STOP. Mix **0.164**. GPU deleted (`rf2dayesihddon`). Volume `7hb931c5oe` still unused.

Full scorecard: memory `pretraining/cpt-v2-session-2026-08-27-results` and SESSION RESULTS markdown under kaggle/runpod_cpt_v2.

## C result (2026-08-27)
- Adapter `theology_cpt_lora`, SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- vs this C's bf16 base: spurgeon 14.31 to 13.28 (-7.2%), puritan 5.99 to 5.68 (-5.0%), confession 7.24 to 6.73 (-7.0%), general 13.43 to 13.20 (-1.7%)
- MCQ: WSC 70% to 74%; Heidelberg 40.5% to 45.2% (need +10)
- `RUN_MERGE=False`

## Keepable LoRA
Local snapshot documented. Private Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`. Ampere bf16 only.

## Next
Decide mix rebuild / more tokens vs shipping this LoRA as-is. Need runpodctl plus API key to attach volume on the next GPU.

## Paste
```
Next session = after Runpod C. Do NOT merge. Do NOT re-C this adapter.
Read: memory pretraining/cpt-v2-session-2026-08-27-results
      continued_pretrain/kaggle/runpod_cpt_v2/ (SESSION RESULTS markdown)
Probe PPL PASS vs Ampere bf16 base; section 5 -15% FAIL. Mix 0.164. Kaggle STOP.
Private Hub rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2
```
