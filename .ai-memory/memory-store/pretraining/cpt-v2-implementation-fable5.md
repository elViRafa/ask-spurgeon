---
store_path: pretraining/cpt-v2-implementation-fable5
title: "CPT v2 implementation (Fable 5 plan)"
summary: "CPT v2 implementation (Fable 5 plan)"
priority: high
tags: [pretraining, cpt, v2, qwen3.5, mix, notebooks]
schema_version: 1.3
last_updated: "2026-07-13T09:34:46-04:00"
evidence: [continued_pretrain/PLAN_FABLE5_TO_IMPROVE_CPT.md, continued_pretrain/scripts/07_build_theology_mix.py, continued_pretrain/scripts/_gen_sota_notebooks.py]
---

# CPT v2 implementation status (2026-07-13)

Implemented plan `[REDACTED_SECRET].md` in code (Kaggle train/eval still operator-run).

## Code delivered

- **`07_build_theology_mix.py` v2:** `max_chunk_chars=7000` (Spurgeon chunked), G2 multi-bucket guard (`--allow-spurgeon-only`), paragraph dedup + top-20, `--target-spurgeon-share` weight, `--max-bible-share` (default 0.04), optional `--author-tags` (E1).
- **`06_verify_tokens.py`:** `--mix` writes `verified_tokens` into manifest (D3).
- **`08_fetch_pd_sources.py`:** verified Gutenberg IDs only (Bunyan pilgrim/holy_war/badman, KJV). Always spot-check titles.
- **`09_build_catechism_mcq.py`:** WSC + Heidelberg MCQ JSON.
- **`_gen_sota_notebooks.py` = G3 source of truth** for A/B/C sota notebooks. Flagship `unsloth/Qwen3.5-4B-Base`, dual LR emb 1e-5, warmup_ratio 0.03, per-bucket eval, D1/D2/D4 cells, 9B VRAM probe, C_eval with EVAL_BASE + greedy probes + MCQ + merge gate.
- Config/README/SOURCES updated; curated WSC train + Heidelberg holdout.

## Current mix (seed data)

- Sources: Bunyan×3, KJV, WSC; Heidelberg in `holdouts_manual/` only.
- Shares ~ spurgeon 51% / puritan 45% / bible 4% / confession 1%; max_doc 7000.
- MCQ: 50 WSC + 42 Heidelberg items.
- **Still need more Puritans (Owen/Watson/etc.) + confessions + FineWeb replay** before flagship scale.

## Operator next steps (Kaggle)

1. Expand PD corpus under `data/puritans|confessions` (spot-check titles).
2. Rebuild mix + `06_verify_tokens.py --mix`.
3. Upload corpus; A_sota → B_sota (M1/D1–D4) → C_sota.
4. Pin Unsloth commit after first good session (G1).
