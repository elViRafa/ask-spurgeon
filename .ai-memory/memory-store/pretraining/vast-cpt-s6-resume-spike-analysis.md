---
store_path: pretraining/vast-cpt-s6-resume-spike-analysis
title: "Vast S6 resume spike + flat composite analysis"
summary: "- Instance **51416115** destroyed; `vastai show instances` → `[]`"
priority: high
tags: [cpt, s6, vast, early-stop, resume, analysis]
schema_version: 1.3
last_updated: "2026-09-18T09:30:54-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_run_config.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/checkpoints_sota/checkpoint-2400/trainer_state.json, continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/train_cpt_sota.py]
---

# Vast S6 continue-B — resume spike + flat early-stop (2026-09-18)

## Outcome
- Instance **51416115** destroyed; `vastai show instances` → `[]`.
- Artifacts: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/`
- **Canonical finished LoRA:** `fetch/theology_cpt_lora/theology_cpt_lora/` SHA256 `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` (= best ckpt-2050). Outer `fetch/theology_cpt_lora/adapter_model.safetensors` is **stale S5** (`ef4df3a3…`) from mid-run scp — ignore it.
- HF `best_model_checkpoint` = `checkpoint-2050`, `best_metric` = **2.4987235**. Log: `OK: saved LoRA matches best_model_checkpoint`.
- Hub v2: **keep** (no overwrite). No new B yet.

## What happened
Full pack 51417→4128. Resume 2050 → COMPOSITE EARLY-STOP @ **2400** (patience=2, ε=0.005, min_steps=1652).

| step | eval_spurgeon | eval_mix | notes |
|------|---------------|----------|-------|
| 2050 | **2.4987** | 2.0208 | HF best (pre-resume last save) |
| 2075 | **2.6185** | 2.1157 | first eval after resume — spike |
| 2325 | 2.5115 | 2.0322 | composite local bests seeded post-spike |
| 2350–2400 | ≤ε gains | ≤ε | flat streak=2 → halt |
| 2400 | 2.5084 | 2.0276 | still **worse** than 2050 spurgeon |

All holdouts spiked together (puritan 1.751→1.834, confession 1.668→1.755). Train loss 2050→2060: **1.92→2.33**. Not Spurgeon-only eval noise.

## Why the resume spike (most likely)
1. **Real weight degradation in first ~25 post-resume steps**, not measurement noise — multi-bucket + train-loss jump.
2. LR schedule looked continuous (~2.05e-6 at 2050 → ~2.02e-6 at 2070); not a warmup restart.
3. Continue mode loads S5 init adapter then `trainer.train(resume_from_checkpoint=2050)`. HF best tracking correctly kept 2050; continued Adam steps walked **out** of that basin and never returned below 2.4987.
4. Plausible contributors: late-stage LR still too high for a near-flat Spurgeon probe; dataloader/RNG discontinuity after process restart; Unsloth+PEFT resume friction. **Not** proven as a single root bug without a controlled A/B.

## Why flat composite (working as designed)
`CompositeFlatEarlyStoppingCallback` starts with **empty `bests`** on each process. After resume it is already past `min_steps=1652`, so the **first** complete cycle at 2075 **seeds** composite bests at the spiked values. Recovery 2075→2325 counts as improvement; then spurgeon/mix moves &lt; 0.005 for 2 evals → halt at 2400. Composite never compared against HF best 2.4987 — by design it tracks live flatness, while `load_best_model_at_end` restores 2050 for the saved LoRA.

## Decisions / next
- Do **not** treat 2375/2400 adapters as better than 2050.
- Next GPU work: **C-eval** of `6aab9194…` (2050 LoRA) vs Ampere base **and** Hub v2 — only then decide Hub overwrite.
- Optional later B: lower continue LR and/or seed composite bests from resumed `trainer.state.best_metric`; do not re-rent until C plan is approved.
