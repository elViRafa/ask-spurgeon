---
store_path: pretraining/cpt-b-eval-strategy-implementation
title: "CPT B eval strategy — implemented, ready for S6 run"
summary: "B eval strategy implementation is **complete** (2026-08-28)"
priority: high
tags: [cpt, eval, training, continue, implemented]
schema_version: 1.3
last_updated: "2026-08-28T06:59:00-04:00"
---

B eval strategy implementation is **complete** (2026-08-28). Next step is GPU only.

**Files:** `cpt_runtime.py`, `_gen_sota_notebooks.py`, regenerated `train_cpt_sota.py`, `test_cpt_runtime.py`, `CORPUS_V3_S6_CONTINUE_CHECKLIST.md`, `RUNPOD_RUNBOOK.md` S6 link.

**Continue env block:**
```bash
export CPT_RUN_MODE=continue
export CPT_INIT_ADAPTER=/workspace/theology_cpt_lora
export [REDACTED_SECRET]
export PREV_RUN_CHECKPOINT=
export EVAL_DOCS_PER_BUCKET=16
```

**Handoff for next chat:** `pretraining/cpt-s6-continue-b-run-handoff`
