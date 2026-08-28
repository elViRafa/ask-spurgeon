---
store_path: pretraining/cpt-v2-next-steps-after-v13
title: "CPT v2 next steps after B v13 ERROR"
summary: "**Context:** B v13 `one_doc_padded` D1/D2 PASS (`multi_doc_rows=0`)"
priority: high
tags: [cpt, kaggle, handoff, b-v13, next-steps]
schema_version: 1.3
last_updated: "2026-08-26T19:25:47-04:00"
evidence: [continued_pretrain/CPT_V2_KAGGLE_STATUS.md, continued_pretrain/kaggle/b_logs_v13_raw.txt, pretraining/cpt-v2-qwen35-upstream-recipes]
---

# CPT v2 — next steps after B v13 ERROR (do not act in save-only session)

**Context:** B v13 `one_doc_padded` D1/D2 PASS (`multi_doc_rows=0`). Kernel died ~step 100 (~3.07 h). Ckpts 25/50/75/100 saved. Only eval: step 25 `eval_spurgeon_loss=2.335` (vs v12 2.340). No step-50 eval. Last C still v4 §5 FAIL. Do not C. Do not merge.

## Recommended order

### 1. Confirm v13 artifacts (operator, ~5 min)
- Open B v13 log/output: verify `checkpoints_sota/checkpoint-{25,50,75,100}` and `run_config.json` on the kernel output mount.
- Confirm `packing_mode=one_doc_padded`, `multi_doc_rows=0` in saved run_config.
- **Do not run C** on partial v13.

### 2. Next GPU B — resume, not a new LR-only rerun
**Preferred:** push same notebook with `[REDACTED_SECRET]` (or highest saved) and same `MAX_STEPS=476`. Goal: finish to early-stop or step 476 and get **step 50/75 eval_spurgeon**.

**Abort rule unchanged:** if `eval_spurgeon` **rises by step 50**, stop and do not C.

### 3. If resume dies again (~3 h / OOM)
Pick one (in order):
1. **Multi-session resume** — same config, chain checkpoints until 476 steps or early-stop.
2. **L4/A100:** set `GPU_PROFILE=ampere` (`load_in_4bit=False`, bf16 LoRA ~10 GB) — upstream recommended path; avoids T4 float32-on-4-bit noise.
3. **T4 fallback only if needed:** `TRAIN_EMBEDDINGS=False` (drop full embed `modules_to_save`; v6 proved embed-on T4 is heavy — v13 had 696M trainable / 13.3%). Keep GDN LoRA + one_doc_padded.

**Do not:** another stream/isolated concat B; another LR-only v12-style run; C on v11/v12/v13 partial.

### 4. C eval — only after COMPLETE B with stable eval
Run C only if a **full** B run completes and `eval_spurgeon` is flat or falling through step 50 (ideally 75). §5 holdout PPL is still the ship gate.

### 5. Mix rebuild — separate, optional
`--keep-all-spurgeon` exists locally; mix **not** rebuilt (Kaggle weight still 0.164). Rebuild + upload corpus only if you explicitly want more Spurgeon exposure (~5× chars). Not required to validate one_doc_padded.

## Decision tree (one line)
`Resume v13 ckpt-100 → eval @50/75 → if stable COMPLETE → maybe C → §5 PASS → merge` ; else `ampere bf16` or `TRAIN_EMBEDDINGS=False` + resume.

## v14 resume miss (2026-08-26)
- v14 pushed with `kernel_sources` but config printed **"No prior checkpoint found"** — mount path not hit at config time (fixed `_find_prev_run_checkpoint` to walk `/kaggle/input`).
- v14 therefore restarted **fresh from step 0** (not resume). Poller watching.
- **If v14 ERRORs: STOP this Kaggle user.** Other user should push regen notebook with fixed walker + `kernel_sources`.
