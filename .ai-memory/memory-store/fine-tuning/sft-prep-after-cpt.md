---
store_path: fine-tuning/sft-prep-after-cpt
title: "SFT prep plan after CPT (2026-08-28)"
summary: "**Status:** Prep planning (no SFT train started)"
priority: high
tags: [sft, phase-b, dry-run]
schema_version: 1.3
last_updated: "2026-08-28T20:41:44-04:00"
review_status: stale
---

# Fine-tuning (SFT) prep plan — after CPT

**Date:** 2026-08-28
**Status:** Prep planning (no SFT train started)

## Pipeline position

```
Qwen3.5-4B-Base → CPT (Hub v2 LoRA / future S6) → merge 16-bit HF → SFT v2 (grounded Q&A) → GGUF/Ollama → app
```

SFT is **instruction** fine-tune on top of CPT, not a replacement for CPT.

## Current readiness (2026-08-28)

| Asset | Status |
|-------|--------|
| `13_sft_local_readiness.py` | **PASS** (train=2553, val=134, test=100) |
| `qa_mix_v1` + kaggle zip | Present |
| SOTA notebooks D/E/F | Present |
| `KAGGLE_RUNBOOK_SFT_V2.md` | Current operator path |
| CPT **merged** HF folder | **Missing locally** (`theology_cpt_v2_merged_hf` not found) |
| Hub v2 | LoRA only — keep; need merge for GATE-0 final SFT |
| S6 B | Incomplete (2110/4128) — not ready as SFT base |
| Idle C-eval pod `snuapq7oqrd8ww` | Still RUNNING — terminate to stop billing |

## Recommended prep phases

### Phase A — stop bleed / freeze CPT handoff (do now)
1. Terminate idle pod `snuapq7oqrd8ww` (C eval done).
2. Keep volume `7hb931c5oe` (S6 resume later).
3. Do not start SFT on incomplete S6 adapter.

### Phase B — SFT dry-run prep (parallel, no CPT merge needed)
1. Re-confirm mix: `build_qa_mix.py` + `12_package_kaggle_qa_mix.py` if data changes.
2. Regen notebooks if generator changed: `_gen_sota_sft_notebooks.py`.
3. Upload `spurgeon-qa-mix-v1.zip` to Kaggle if not current.
4. Run **D_sota** (token audit).
5. Run **E_sota** with `USE_CPT_MERGE=False`, stock `unsloth/Qwen3.5-4B-Base` — 2 epochs dry-run.
6. Run **F_sota** with `EXPORT=False` — check corrupt_rate, refusal accuracy.

### Phase C — GATE-0 final SFT (blocked until merge)
1. Merge Hub v2 LoRA (or finished S6 if it beats v2) → `theology_cpt_*_merged_hf`.
2. Publish merge as dataset / volume path.
3. Retrain E with `USE_CPT_MERGE=True` on that base.
4. F gates (§5): faithfulness ≥4.0, refusal ≥85%, echo ≤2%, Ollama smoke clean.
5. Only then EXPORT → GGUF → HF → Ollama Modelfile.

## Base-model choice for shippable SFT

| Option | When |
|--------|------|
| **Hub v2 CPT merged** | Default for first shippable SFT (policy: keep Hub v2) |
| **S6 after full B+C win** | Only if C beats Hub v2 scorecard |
| **Stock base dry-run** | Now — plumbing only, not shippable |

## Known SFT risks (from PLAN_FABLE5_TO_IMPROVE_FN)

- One ChatML template across D/E/F/Ollama (no Alpaca mix).
- Completion-only masking (`train_on_responses_only`).
- Align train context shape with app (multi-chunk headers).
- Never resize vocab (GGUF corruption).
- Never EXPORT until F gates pass.

## Next operator decision

Pick one:
1. **Terminate pod + start Phase B dry-run** (Kaggle T4 or Runpod)
2. **Merge Hub v2 first** then GATE-0 SFT
3. **Resume S6 CPT first**, then SFT later

## Phase A done (2026-08-28)
- Terminated idle pod `snuapq7oqrd8ww` (C eval complete).
- Volume `7hb931c5oe` kept for S6 resume.

## Phase B started — stock-base dry-run prep
- Rebuilt QA mix + `spurgeon-qa-mix-v1.zip` (1.64 MB)
- Regenerated D/E/F SOTA notebooks from `_gen_sota_sft_notebooks.py`
- `13_sft_local_readiness.py` PASS (2553/134/100)

### Operator next (Kaggle T4)
1. Upload `fine_tuning/data/kaggle_upload/spurgeon-qa-mix-v1.zip` → dataset `spurgeon-qa-mix-v1`
2. D_qa_data_prep_sota — mount mix, token audit
3. E_qa_training_sota — `USE_CPT_MERGE=False`, `BASE_MODEL=unsloth/Qwen3.5-4B-Base`, 2 epochs
4. F_qa_eval_sota — `EXPORT=False`
5. Do **not** merge/export until GATE-0 (CPT merged HF)

Runbook: `fine_tuning/KAGGLE_RUNBOOK_SFT_V2.md`

## Phase B dry-run pod terminated + QA mix v2 (2026-08-28)

- Deleted pod `47zu29u0yth5a3` (`sft-phase-b-dry`). Volume `7hb931c5oe` kept.
- Replaced `qa_mix_v1` with **qa_mix_v2** (serve-shaped headers, k≈4, train refusal 11.9%). Counts: train=2923 / val=153 / test=100.
- Rebuild: `build_qa_mix_v2.py` + `12_package_kaggle_qa_mix.py`. Readiness PASS.
- D_sota now uses `AutoTokenizer.from_pretrained` (no Unsloth `get_tokenizer`).
- Do **not** start training until operator uploads the new zip and chooses Kaggle vs a new pod.
