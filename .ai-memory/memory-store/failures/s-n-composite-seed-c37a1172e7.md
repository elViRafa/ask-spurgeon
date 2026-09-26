---
store_path: failures/s-n-composite-seed-c37a1172e7
title: "S7 composite seed used isolation-C full-holdout CE for puritan (1.722) and confe"
summary: "S7 composite seed used isolation-C full-holdout CE for puritan (1.722) and confession (1.662) instead of S6 in-train @ ckpt-2050 (1.751 / 1.668)"
priority: medium
tags: [cpt, early-stop, failure, fix, s7, seed]
schema_version: 1.3
last_updated: "2026-09-21T11:05:20-03:00"
occurrences: 1
error_signature: "s<n> composite seed used isolation-c full-holdout ce for puritan (<n>.<n>) and confession (<n>.<n>) instead of s<n> in-train @ ckpt-<n> (<n>.<n> / <n>.<n>). combined with patience=<n> and seeded bests, first flat cycles would halt at step ~<n> of <n> (~<n>% of budget) because the seed was unreachabl"
---

## Occurrence 1 — 2026-09-21T11:05:20-03:00

**Error:**
S7 composite seed used isolation-C full-holdout CE for puritan (1.722) and confession (1.662) instead of S6 in-train @ ckpt-2050 (1.751 / 1.668). Combined with patience=2 and seeded bests, first flat cycles would halt at step ~525 of 2064 (~25% of budget) because the seed was unreachable on EVAL_DOCS_PER_BUCKET=16.

**Fix:**
Corrected S7_DEFAULT_COMPOSITE_SEED_BESTS to in-train values (puritan 1.751, confession 1.668). Retuned S7 to patience=4, epsilon=0.003, eval/save_steps=50, warmup_ratio=0.04. Documented that isolation-C CE must never replace in-train seeds.
