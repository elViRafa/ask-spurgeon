---
store_path: pretraining/cpt-v3-s6-interrupted
title: "S6 continue-B interrupted — resume later"
summary: "S6 B interrupted at 2110/4128; pointer to cpt-v3-s6-handoff for resume and C eval."
priority: high
tags: [cpt, s6, c-eval]
schema_version: 1.3
last_updated: "2026-08-29T11:07:00-04:00"
summary_hash: 15b39e7ce3d55ac42863abbd9fe97e5d
review_status: stale
---

# CPT S6 continue-B — interrupted (pointer)

S6 continue-B stopped at **step 2110/4128** (~51%) after monitor false-positive pod delete. Volume `7hb931c5oe` is source of truth (`checkpoint-2100`; HF best `checkpoint-2050`).

**Canonical handoff (resume + partial C metrics + Hub v2 policy):** `pretraining/cpt-v3-s6-handoff`

Resume rule: HF `PREV_RUN_CHECKPOINT` with `CPT_RUN_MODE=fresh` (or unset) — **not** `continue` mode. Keep Hub v2 until a full S6 B + winning C eval.
