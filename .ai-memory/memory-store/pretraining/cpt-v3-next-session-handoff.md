---
store_path: pretraining/cpt-v3-next-session-handoff
title: "CPT next session — S6 continue B run (code ready)"
summary: "**Paste into next chat:** Read `pretraining/cpt-s6-continue-b-run-handoff` first"
priority: high
tags: [cpt, corpus-v3, handoff, s6, continue-b]
schema_version: 1.3
last_updated: "2026-08-28T06:58:47-04:00"
evidence: [continued_pretrain/NEXT_CPT_MORE_TOKENS.md, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/scripts/train_cpt_sota.py]
---

# CPT S6 continue B — next session handoff (code ready)

**Paste into next chat:** Read `pretraining/cpt-s6-continue-b-run-handoff` first. Operator says go → provision GPU and run S6 continue B. Do **not** re-implement trainer code.

## Done (do not redo)
- S5 B+C complete. S5 adapter SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303` at `kaggle/runpod_cpt_v3/theology_cpt_lora`.
- Hub stays `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` until new C wins.
- **B eval strategy coded** 2026-08-28: `_gen_sota_notebooks.py` → `train_cpt_sota.py`. `CPT_RUN_MODE=continue`, composite early-stop, 16-doc buckets, adapter load, min_steps floor. Tests pass (`test_cpt_runtime.py`).

## Next session = GPU run only (when operator says go)
1. Follow `[REDACTED_SECRET].md`
2. Copy `a_output_v3` + S5 LoRA + scripts to `/workspace`
3. Volume `7hb931c5oe` via **runpodctl** (MCP drops mount)
4. Env: `CPT_RUN_MODE=continue`, `CPT_INIT_ADAPTER=/workspace/theology_cpt_lora`, `EXPECTED_ADAPTER_SHA256=ef4df3a…`, `PREV_RUN_CHECKPOINT=` empty, `EVAL_DOCS_PER_BUCKET=16`
5. Post-B: scp adapter + checkpoints + optimizer; C with new SHA256

## Do not
- Re-C S5 adapter; merge; overwrite Hub v2; rebuild mix; use `kaggle/a_output` (v2); HF resume (`PREV_RUN_CHECKPOINT`) on continue

Spec: `pretraining/cpt-b-eval-strategy`. Playbook: `pretraining/cpt-next-b-more-tokens-playbook`.
