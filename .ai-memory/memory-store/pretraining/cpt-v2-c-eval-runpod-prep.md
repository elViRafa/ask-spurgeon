---
store_path: pretraining/cpt-v2-c-eval-runpod-prep
title: "CPT v2 C eval Runpod prep — copy list, gates, Ampere-only"
summary: "Execute C on the **Runpod B** adapter"
priority: high
tags: [cpt, runpod, c-eval, handoff]
schema_version: 1.3
last_updated: "2026-08-27T08:21:31-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/RUNPOD_RUNBOOK.md, continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_lora/adapter_config.json]
---

# CPT v2 C eval — Runpod session prep (2026-08-27)

Execute C on the **Runpod B** adapter. Do not C Kaggle 4-bit ckpts. Do not merge this session unless holdout PPL beats base (unexpected for a 15.6M-token probe).

## Why C is allowed
B abort-at-50 **passed** (`eval_spurgeon` 2.288 @ 25 → 2.286 @ 50) and kept falling to 2.248 @ 400. Runbook: C only after complete B with stable/falling eval through 50.

## Score this file
`continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_lora`
- `adapter_model.safetensors` ~1445 MB
- SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- `find_adapter` looks for `theology_cpt_lora/adapter_config.json` under `CPT_WORK_ROOT`
- Also copy: `kaggle/a_output/theology_holdouts/` (spurgeon/puritan/confession/general HF dirs), `data/catechism_mcq.json`

## C code
Source of truth: `continued_pretrain/scripts/_gen_sota_notebooks.py` → `notebooks/C_eval_sota.ipynb`. There is **no** `eval_cpt_sota.py` yet — run the notebook or generate a script first. C install still uses pip without `--break-system-packages`; add it on the official PyTorch image.

Config that must stay:
- `ADAPTER_OVERRIDE = None` (not B v6 `checkpoint-25`)
- `EVAL_BASE = True` (§5 needs base PPL)
- `RUN_MERGE = False`
- `SCORE_LAST_CHECKPOINT = False` unless `checkpoints_sota/checkpoint-*` is on the box (not in the local copy)
- Ampere: `load_in_4bit=False` (adapter trained bf16 + embed FT)

## §5 gates (unchanged; probe will likely FAIL the −15%)
Compare **prefix PPL** vs base (C v4 base: spurgeon 14.94, puritan 6.20, confession 7.78, general 14.07):
- spurgeon: better than base
- puritan / confession: ≥15% better
- general: ≤10% worse
MCQ does not override a PPL FAIL.

This C answers: did Ampere + embed LoRA + one_doc_padded **stop hurting** the base (C v4 was uniform ~+2% PPL)?

## Pod recipe
1. Have `RUNPOD_API_KEY` + runpodctl **before** create (MCP cannot attach volume).
2. Attach volume `7hb931c5oe` at `/workspace` **or** copy LoRA+holdouts onto a 75 GB disk and scp results off before delete (B had to do the latter).
3. One 4090, no extra ports, `--terminate-after` backstop, delete GPU when C finishes.
4. `python3 -u` so logs are not fully buffered.
