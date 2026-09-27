---
store_path: pretraining/cpt-s6-phase0-prepared
title: "S6 Phase 0 prepared; GPU blocked on operator go"
summary: "- Volume `7hb931c5oe` is source of truth (`checkpoint-2100`; HF best `checkpoint-2050`)"
priority: high
tags: [cpt, s6, handoff, phase0]
schema_version: 1.3
last_updated: "2026-09-15T11:34:39-03:00"
evidence: [[REDACTED_SECRET].md, [REDACTED_SECRET].md, continued_pretrain/scripts/s6_remote_continue_b.sh, continued_pretrain/scripts/s6_monitor_until_done.py]
---

# S6 Phase 0 prepared — blocked on operator GPU go (2026-09-15)

Local code+docs only. **No pod, no train, no monitor, no C eval.**

## Ready on next GPU go

- Volume `7hb931c5oe` is source of truth (`checkpoint-2100`; HF best `checkpoint-2050`).
- Resume: `CPT_RUN_MODE=continue` + unset `PREV_RUN_CHECKPOINT` (or set `.../checkpoint-2100`). Keep continue LR/eval/composite. Load S5 LoRA for SHA check; HF resume restores Adam.
- Do **not** `S6_FRESH_START=1`. Do **not** point `CPT_INIT_ADAPTER` at checkpoint-2100.
- Monitor deletes only on log markers (`Saved run config`, `COMPOSITE EARLY-STOP`, `4128/4128`) when the train process is gone. SSH flakes do not finish.
- Hub v2 stays until a finished B + winning C.

Checklists: `[REDACTED_SECRET].md`, `CORPUS_V3_S6_RERUN_SAFE.md`.
