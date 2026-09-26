---
store_path: pretraining/cpt-v6-new-authors-diagnostic-holdout
title: "CPT v6 new-authors diagnostic holdout (PR #1)"
summary: "Merged to main as `c8660ac` (2026-09-26)"
priority: high
tags: [cpt, s7, v6, new-authors, foundry, holdout]
schema_version: 1.3
last_updated: "2026-09-26T16:15:03-03:00"
---

## New-authors diagnostic holdout (PR #1)

Merged to main as `c8660ac` (2026-09-26).

- Builder: `continued_pretrain/scripts/19_build_new_authors_holdout.py` → `data/holdouts_new_authors/`
- Monitor-only like `general`: not in COMPOSITE_EARLY_STOP_METRICS, not §5/Hub
- Isolation C reports `new_authors` when present
- Pinned v3 Spurgeon/Puritan/confession untouched

Operator build completed on pc1 — see `pretraining/cpt-s7-new-authors-holdout-pc1-2026-09-26`.
