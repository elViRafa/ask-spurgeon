---
store_path: pretraining/cpt-v2-runpod-two-session-plan
title: "CPT v2 plan: B and C done — no merge"
summary: "User order: **(1) prep code** done → **(2) analyze / check** done → **(3) Runpod CPT B** done → **(4) C eval** done (no merge)"
priority: high
tags: [cpt, runpod, handoff, plan]
schema_version: 1.3
last_updated: "2026-08-27T09:49:08-04:00"
evidence: [pretraining/cpt-v2-c-eval-runpod-complete, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
---

# CPT v2 — session plan (updated 2026-08-27 after Runpod C)

User order: **(1) prep code** done → **(2) analyze / check** done → **(3) Runpod CPT B** done → **(4) C eval** done (no merge).

## Session 4 — C eval (DONE 2026-08-27)
Community 4090 Ampere bf16. Probe PPL beats own base (spurgeon −7.2%). §5 −15% miss. `RUN_MERGE=False`. GPU deleted.

## Next
Do not re-C. Do not merge. Decide mix/tokens vs LoRA-only ship.

## Paste
```
Next session = after Runpod C. Do NOT merge. Do NOT re-C this adapter.
Read: memory pretraining/cpt-v2-c-eval-runpod-complete
      continued_pretrain/CPT_V2_KAGGLE_STATUS.md
```

## Session 5 — keep LoRA + private Hub (DONE 2026-08-27)
Documented snapshot + uploaded private repo `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`. Scorecard: memory `pretraining/cpt-v2-session-2026-08-27-results`. Still no merge.
