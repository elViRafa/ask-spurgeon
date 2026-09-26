---
store_path: pretraining/cpt-next-cpt-improvements-prep
title: "S7 Phase A improvements applied; GPU still blocked on go"
summary: "**No GPU B until operator says go.** Production Hub is S6 SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c`"
priority: high
tags: [cpt, s7, continue, adam, prep, ready]
schema_version: 1.3
last_updated: "2026-09-21T11:05:35-03:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/s7_remote_continue_b.sh, continued_pretrain/scripts/s7_remote_c_eval.sh, continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/scripts/test_cpt_runtime.py]
---

# S7 CPT improvements — Phase A prep + post-audit fixes (2026-09-21)

**No GPU B until operator says go.** Production Hub is S6 SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c`.
Canonical C: Unsloth **2026.8.22 + torch 2.8**.

## Code ready
- `CPT_CONTINUE_PROFILE=s7`: body **2e-6**, emb **8e-7**, warmup **0.04**, max_steps **2064**, min_steps **500**
- patience **4**, ε **0.003**, eval/save **50**, `cosine_with_min_lr` min_lr_rate **0.1**
- Seeded bests = S6 **in-train** @ 2050 (spurgeon 2.4987 / mix 2.0208 / puritan **1.751** / confession **1.668**) — not isolation-C CE
- `theology_cpt_lora_s5best` exporter + `AbortOnSeedRegressionCallback` (seed+0.12 × 2 cycles)
- general bucket monitor-only; `CPT_TRAIN_EMBEDDINGS` env ablation
- Launchers: `s7_remote_continue_b.sh`, `s7_remote_c_eval.sh`; monitor `--total-steps` / `CPT_TOTAL_STEPS`
- Playbook: `continued_pretrain/NEXT_CPT_S7.md`

## Goal
§5 −15% on puritan + confession (isolation C: −7.2% / −6.0%).

## Do on GPU go
1. Copy a_output_v3 + nested 6aab LoRA + train/eval + s7 launchers
2. `bash s7_remote_continue_b.sh`; monitor with `-TotalSteps 2064`
3. C via `s7_remote_c_eval.sh` with explicit SHA; keep Hub S6 unless win

## Do not
- HF-resume 2050/2100/2400; unset PREV with leftover sota
- Seed with isolation-C full-holdout CE
- Fresh 1e-5; 4e-6 S6 clone; C on torch 2.11
- Mix rebuild / merge / Hub overwrite without winning C
