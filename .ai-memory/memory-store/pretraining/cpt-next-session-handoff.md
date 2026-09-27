---
store_path: pretraining/cpt-next-session-handoff
title: "Next CPT: continue from replay 0289f1c9; Hub stays Phase A"
summary: "- Next init SHA `0289f1c9…` from replay s5best (checkpoint-550); Hub stays Phase A `06354dfc…`"
priority: high
tags: [cpt, s7, handoff, replay, v6, continue-from]
schema_version: 1.3
last_updated: "2026-09-26T20:31:48-03:00"
evidence: [pretraining/cpt-s7-replay-isolation-c-complete, pretraining/cpt-s7-holdout-sibling-replay, pretraining/cpt-hub-keep-phase-a, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/CONTINUE_FROM.json]
---

## Next session — replay B+C done; continue from 0289f1c9; no GPU until go

### Production Hub (unchanged)
- `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…`
- Do **not** promote `0289f1c9` or `ddbbee3a`

### Continue-from pin (local)
- SHA256: `0289f1c9af70615ef4dca58b3e2d7dabc3eefef96c8bdf92bff0933689adeb55`
- Checkpoint: `checkpoint-550` / `theology_cpt_lora_s5best`
- Marker: `vast_cpt_s7_replay/CONTINUE_FROM.json`
- Adapter: `vast_cpt_s7_replay/fetch/theology_cpt_lora_s5best/`
- **Next CPT init = this adapter, new Adam** (do not HF-resume optimizer)

### Done
- Holdout-sibling replay Phase B early-stopped at step 550 (`0289f1c9`).
- Isolation C on replay s5best: Spurgeon 12.35 (−13.69%), Puritan 5.48 (−9.22%), confession 5.22 (−6.88%) — §5 FAIL; hair better than Phase B C.
- Instance `52830244` destroyed after C; **0 instances**. Standing rule: after C, save adapter locally + destroy pod.

### Do next (operator go)
1. Continue CPT from `0289f1c9` (local continue-from), **new Adam**, mix `a_output_v6` SHA `e050787e…`.
2. Prefer `0289f1c9` as init — **not** Hub `06354dfc`, **not** init LoRA `ddbbee3a` at `fetch/theology_cpt_lora/`.
3. After train: isolation C. Promote Hub only if Puritan+confession hit −15% and Spurgeon stays under ~13.3.
4. After C: save adapter locally + destroy pod (no Hub overwrite without go).

### Do not
- Rent GPU / Cloud Agents without explicit operator go.
- Hub-push / overwrite Phase A `06354dfc`.
- Copy 1.45GB weights into git; marker only.
- Retrain `a_output_v5`. Raise LR. HF-resume. New-authors-only. Redraw holdouts. Fetch Shaw/SSK.

## Pending
Next continue-from CPT is **blocked on operator go**. Marker + memories saved 2026-09-26.