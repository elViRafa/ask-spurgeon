---
store_path: pretraining/bugs/b-training-sota-known-issues
title: "CPT B_training_sota known issues (P1 closed — log spam)"
summary: "Source of truth: `continued_pretrain/scripts/_gen_sota_notebooks.py` (regenerate notebooks; do not hand-edit only)"
priority: high
tags: [pretraining, cpt, kaggle, bugs, unsloth, qwen35, p1]
schema_version: 1.3
last_updated: "2026-08-25T10:20:30-04:00"
evidence: [continued_pretrain/kaggle/b_output_v6/checkpoints_sota/checkpoint-75/trainer_state.json, continued_pretrain/kaggle/c_output/theology_cpt_lora_final/adapter_model.safetensors, continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md]
---

# CPT B_training_sota known issues (fix next)

Source of truth: `continued_pretrain/scripts/_gen_sota_notebooks.py` (regenerate notebooks; do not hand-edit only).

## P1 — Early-stop log spam (NOT a missing metric) — closed 2026-08-25

**Symptom (B v6):** stderr spam `early stopping required metric_for_best_model, but did not find eval_spurgeon_loss so early stopping is disabled`.

**What we thought:** metric never logged → EarlyStopping disabled → C scored last step without Spurgeon-best selection.

**What actually happened (evidence):**
- `checkpoints_sota/checkpoint-75/trainer_state.json` has `eval_spurgeon_loss` at steps 25 / 50 / 75.
- `best_global_step=25`, `best_metric=2.5679` (that Spurgeon loss), EarlyStopping patience 0→1→2, stop at 75.
- HuggingFace logs **each eval dataset as its own dict**. The callback looks at the *current* logs; mix/puritan/confession/general do not contain `eval_spurgeon_loss` → warning. The spurgeon sub-eval **does** contain it.
- SHA256 of `adapter_model.safetensors` is **identical** for `checkpoint-25`, `theology_cpt_lora`, and C's `theology_cpt_lora_final`. C v4 already scored the best ckpt.

**Fix in generator (v7):** `QuietEarlyStoppingCallback` — same patience logic, no warning when the current bucket lacks the key. Print eval keys on first Spurgeon eval. After save, SHA256-compare `theology_cpt_lora` vs `best_model_checkpoint`.

**Do not** re-run C with `ADAPTER_OVERRIDE` on B v6 `checkpoint-25` (already scored).

## P2 — Unsloth `formatting_func` required (B v4)

**Symptom:** `RuntimeError: Unsloth: You must specify a formatting_func` when constructing `UnslothTrainer` with `eval_dataset` dict of text HF datasets while train is already packed `input_ids`.

**Fix applied:** tokenize eval the same way as train (`_tokenize_eval_ds`) when `MANUAL_PACK=True`. Keep this whenever train is pre-tokenized.

## P3 — CUDA OOM on T4 (B v5)

**Symptom:** `OutOfMemoryError` (~2.37 GiB alloc) during train/eval with Qwen3.5 float32 + manual pack.

**Failing recipe:** `PER_DEVICE_BATCH=2`, `GRAD_ACCUM=8`, `TRAIN_EMBEDDINGS=True`, eval 8 docs/bucket.

**Working recipe (B v6):** `PER_DEVICE_BATCH=1`, `GRAD_ACCUM=16`, `TRAIN_EMBEDDINGS=False`, `EVAL_DOCS_PER_BUCKET=4`.

**B v7 try:** same 1×16 shape **with** `TRAIN_EMBEDDINGS=True`. If OOM: `EVAL_DOCS_PER_BUCKET=2` and/or `EVAL_BUCKETS_DURING_TRAIN=["spurgeon"]` (keep mix). Do not go back to batch 2 + embeds without a VRAM probe.

## P4 — Manual pack itself (RC1) — works

Do **not** regress: Qwen3.5 Processor ignores native `packing=True`. Keep `build_manual_packed_dataset` + D1 gate (packed rows ≪ raw docs). B v6: 8162 → 7255 packed rows.

## Checklist before next B push (v7)

- [x] Understand P1: metric was logged; C scored ckpt-25
- [ ] `QuietEarlyStoppingCallback` — no spam; Spurgeon key still drives stop
- [ ] SHA256(saved LoRA) == SHA256(best ckpt)
- [ ] D1 packed rows ≪ docs; MAX_STEPS ≈ one packed epoch (~454–476), not 100
- [ ] T4: try embed LoRA at batch 1; peak reserved headroom
- [ ] If eval_spurgeon **rises** by step 50 with embeds: halve body LR (1e-5), do not just push steps
- [ ] C only after B v7; ship only on §5 holdout PPL
