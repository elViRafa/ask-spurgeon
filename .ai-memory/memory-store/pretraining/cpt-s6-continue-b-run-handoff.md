---
store_path: pretraining/cpt-s6-continue-b-run-handoff
title: "CPT S6 continue B — GPU run handoff"
summary: "**Operator approved GPU?** Only then provision"
priority: high
tags: [cpt, s6, runpod, continue-b, handoff]
schema_version: 1.3
last_updated: "2026-08-28T06:58:57-04:00"
---

# CPT S6 continue B — run session paste

**Operator approved GPU?** Only then provision. Else stop.

## Read first
1. `pretraining/cpt-b-eval-strategy` (eval spec)
2. `[REDACTED_SECRET].md` (copy + env + log gates)
3. `continued_pretrain/RUNPOD_RUNBOOK.md` (S6 section)

## Trainer is ready — do not code unless preflight fails
- Source of truth: `_gen_sota_notebooks.py` (regenerates `train_cpt_sota.py`)
- Continue mode: `export CPT_RUN_MODE=continue`
- Load S5 LoRA (not HF checkpoint resume):
  - `CPT_INIT_ADAPTER=/workspace/theology_cpt_lora`
  - `[REDACTED_SECRET]`
  - `PREV_RUN_CHECKPOINT=` (empty)
- Eval: 16 docs/bucket; spurgeon+puritan+confession+mix; composite halt (spurgeon AND mix flat ε=0.005); `early_stop_min_steps` ≈ 0.4×packed epoch; abort-at-50 off
- LR defaults: body 4e-6, emb 1.5e-6 (override via env)

## Copy to `/workspace`
```text
kaggle/a_output_v3/theology_dataset/
kaggle/a_output_v3/theology_holdouts/
data/theology_mix_manifest.json
kaggle/runpod_cpt_v3/theology_cpt_lora/
scripts/train_cpt_sota.py
scripts/cpt_runtime.py
```
Mix SHA256 `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`.

## Pod
- Volume `7hb931c5oe` US-IL-1, runpodctl + network mount at `/workspace`
- RTX 4090, `runpod-torch-v280`, SSH only, `--terminate-after >= 14h`
- `nohup python3 -u train_cpt_sota.py` → `cpt_train.log`

## Log gates before walk away
- `cpt_run_mode=continue` `composite_stop=True`
- `gpu_profile=ampere` `trainer_bf16=True`
- `eval_docs=16` buckets include spurgeon/puritan/confession (+ mix)
- `early_stop_min_steps` ~1650–2060; `abort_spurgeon_step=0`
- `MAX_STEPS` = `packed_epoch_steps` (thousands)

## After B
Scp `theology_cpt_lora/`, `checkpoints_sota/`, `cpt_train.log`, `theology_cpt_run_config.json`. Delete GPU. C later with new `EXPECTED_ADAPTER_SHA256`. Keep Hub v2 if worse.
