---
store_path: pretraining/cpt-s8-sweep-complete
title: "S8 plateau sweep complete — MISS"
summary: "m_hi best 1.723 vs break 1.7204; FETCH_OK; pod destroyed; Hub Phase A"
priority: high
tags: [cpt, s8, sweep, isolation-gate, miss]
schema_version: 1.3
last_updated: "2026-10-05T14:24:00-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_sweep/fetch/sweep/m_hi/theology_cpt_lora/adapter_model.safetensors, continued_pretrain/NEXT_CPT_S8_SWEEP.md]
---

# CPT S8 plateau sweep — complete (MISS)

## Ops

- Instance `54312477` RTX 4090; go 2026-10-05
- First `m_lo` attempt ran **defaults** (no Fresh env) and crashed `max_seq_length` — stopped; relaunch with emit-arm OK
- `PIN_OK` Unsloth 2026.8.22 + torch 2.8; merge `a70fded8` → `/workspace/theology_cpt_merged_a70`
- Arms: m_lo → m_hi → f_hi; `VAST_CPT_S8_SWEEP_DONE`
- FETCH_OK ~14:12 America/Sao_Paulo; destroyed; 0 GPUs; credit ~$5.87
- Fetch root: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_sweep/fetch`
  - `s8_launcher.log`, per-arm `cpt_train.log`, `trainer_state.json`, final `theology_cpt_lora/` each arm
  - LoRAs via `s8_fetch_loras.tgz` (~5.4GB); optimizer weights skipped

## Recipe

- Pack `a_output_v6_p0` SHA `ad817213`
- Fresh LoRA r=128 alpha=64, 400 steps, warmup 0.05, cosine min 10%, abort-at-50 off
- `METRIC_FOR_BEST=eval_puritan_loss`
- Buckets during train: spurgeon, puritan, confession, general

## Final bests (puritan / Spurgeon)

| Arm | Base | LR | Best |
|-----|------|-----|------|
| m_lo | merged a70 | 2e-5 | 1.725 / 2.470 |
| m_hi | merged a70 | 5e-5 | **1.723 / 2.469** (state step400 pur **1.7226**) |
| f_hi | stock Qwen3.5-4B-Base | 5e-5 | 1.736 / 2.488 |

Break: puritan ≤**1.7204**, Spurgeon ≤**2.490**. **MISS** → no isolation C, Hub Phase A `06354dfc`.

## m_hi eval trajectory (puritan)

50:1.753 → 100:1.751 → 150:1.744 → 200:1.737 → 250:1.734 → 300:1.729 → 350:1.725 → 400:1.723

Still monotonically improving at step 400.
