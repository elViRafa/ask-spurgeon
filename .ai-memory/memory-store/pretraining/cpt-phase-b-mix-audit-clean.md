---
store_path: pretraining/cpt-phase-b-mix-audit-clean
title: "Phase B mix audit clean; keep a_output_v4"
summary: "**Status:** Corpus-wide preprocess audit passed"
priority: high
tags: [cpt, phase-b, audit, a-output-v4, preprocess]
schema_version: 1.3
last_updated: "2026-09-23T10:44:32-03:00"
evidence: [continued_pretrain/scripts/audit_cpt_mix_sources.py, [REDACTED_SECRET].json, [REDACTED_SECRET].md]
---

# Phase B mix audit clean (2026-09-23)

**Status:** Corpus-wide preprocess audit passed. **No rebuild.** No GPU until operator go.

## Verdict
`python continued_pretrain/scripts/audit_cpt_mix_sources.py` returned AUDIT_CLEAN / CONTINUE_READY.

- Live mix + a_output_v4 SHA 37a3ba50aa9efb8057d9d36227ac4547f08d35a31ccd71cf3f2d20f928131c81
- Frozen a_output_v3 SHA 23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973
- Puritan/confession holdouts byte-match holdouts_pinned_v3
- Catalog identity 164/164; OCR fail 0; new authors 11/11 present and glyph-clean
- Confession S5 still absent
- Packed mix has 0 mapped glyphs. On-disk book squares are stripped at mix time. Holdout long-s left pinned.

## Continue
Copy a_output_v4 (old corpus plus nine unseen authors). Init Hub / local S7 s5best 06354dfc with a new Adam. Do not train a new-authors-only mix. Do not HF-resume a_output_v3.

S7 pack/sync/readiness now default to v4 + s5best. Do not rent until operator go.
