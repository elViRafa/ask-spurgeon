---
store_path: pretraining/cpt-next-session-handoff
title: "Next CPT: v6 replay from ddbbee3a; Hub stays Phase A"
summary: "- `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…`"
priority: high
tags: [cpt, s7, handoff, replay, v6]
schema_version: 1.3
last_updated: "2026-09-26T08:12:16-03:00"
evidence: [pretraining/cpt-s7-holdout-sibling-replay, pretraining/cpt-s7-phase-b-isolation-c, pretraining/cpt-hub-keep-phase-a]
---

## Next session — isolation C done; replay pack ready; no GPU until go

### Production Hub (unchanged)
- `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…`
- Operator 2026-09-26: do **not** promote `ddbbee3a`

### Done
- Phase B plateaued 750/955. Nested s5best `ddbbee3a` (step 600). HF best `6d003041` (step 700).
- Isolation C on `ddbbee3a`: 12.39 / 5.50 / 5.25 (§5 FAIL). Instance `52296492` destroyed.
- Holdout-sibling pack ready: `mix_v6` / `a_output_v6` SHA `2d5a99c1…`

### Do next (operator go)
1. `vast_cpt_s7_orchestrate.ps1` then `-Go -StartMonitor` — copies v6, inits nested `ddbbee3a`, new Adam, halt without mix-val.
2. Session/results: `vast_cpt_s7_replay` (do not overwrite Phase B fetch).
3. After train: isolation C on the replay winner. Promote Hub only if Puritan+confession hit −15% and Spurgeon stays under ~13.3.

### Do not
- Retrain `a_output_v5`. Raise LR. HF-resume. New-authors-only. Redraw holdouts. Fetch Shaw/SSK.
- Overwrite Hub / v3 / v4 / v5.
- Treat top-level `fetch/theology_cpt_lora_s5best/` as Phase B (that file is still `06354dfc`).

## Pending
Replay GPU is **blocked on operator go**. Pack and wiring exist; do not rent until then.
