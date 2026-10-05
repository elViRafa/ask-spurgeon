---
store_path: pretraining/cpt-next-session-handoff
title: "CPT next-session handoff"
summary: "S8 MISS; propose m_hi continue MAX_STEPS 800; wait approve+go; 0 GPUs"
priority: high
tags: [cpt, s8, handoff, m_hi, one-knob]
schema_version: 1.3
last_updated: "2026-10-05T14:24:00-03:00"
evidence: [pretraining/cpt-s8-sweep-complete, pretraining/cpt-current]
---

# CPT next-session handoff

## For Cursor / next agent analysis

S8 plateau sweep finished and fetched. Decision: **in-train plateau not broken**. Best arm = `m_hi`.

### Proposed next one-knob (NOT started — needs Rafael approve + go)

1. Init: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_sweep/fetch/sweep/m_hi/theology_cpt_lora`
2. Knob: `MAX_STEPS` **400 → 800** only
3. Keep: LR body **5e-5**, emb **5e-6**, `METRIC_FOR_BEST=eval_puritan_loss`, r=128 alpha=64, pack `a_output_v6_p0` SHA `ad817213`
4. New Adam (optimizer weights were not fetched)
5. Foundry dries orchestrate; Forge rents only after **go**
6. After C-worthy in-train win: isolation C; Hub stays Phase A until C win

### Why this knob

`m_hi` puritan fell every eval 50→400 (1.753→1.723) and stopped ~0.002 short of ≤1.7204. Merged >> stock (`f_hi` worse). Higher LR beat `m_lo`.

### Do not

- Rent without go
- Re-run S7/P1 as its own session
- Hub-push / overwrite Phase A
- HF-resume `checkpoints_sota`
- Change mix in the same change as the step bump
