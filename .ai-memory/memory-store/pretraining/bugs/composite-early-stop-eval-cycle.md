---
store_path: pretraining/bugs/composite-early-stop-eval-cycle
title: "Composite CPT early stop merges split HF eval events"
summary: "Hugging Face evaluates a dictionary of CPT eval datasets as separate callback events"
priority: high
tags: [cpt, early-stop, transformers, bug, eval]
schema_version: 1.3
last_updated: "2026-09-15T11:34:36-03:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/scripts/test_cpt_runtime.py, continued_pretrain/scripts/_gen_sota_notebooks.py]
---

# Composite early-stop split-eval fix (Phase 0, 2026-09-15)

Hugging Face evaluates a dictionary of CPT eval datasets as separate callback events. S5 logs show `eval_mix_loss` and `eval_spurgeon_loss` at the same global step.

**Fix implemented (local, no GPU):** `merge_eval_event_for_step` in `cpt_runtime.py` caches metrics by step, scores a cycle only when every configured key has arrived, then pops that step. `CompositeFlatEarlyStoppingCallback` uses the merged dict. Checkpoint pick stays `eval_spurgeon_loss`.

Tests: sequential mix-then-Spurgeon events (S5-like mix still falling → no halt; both flat → halt). Unmerged single-bucket events still never halt.

Generator `_gen_sota_notebooks.py` regenerated `train_cpt_sota.py` / notebooks / `eval_cpt_sota.py`.
