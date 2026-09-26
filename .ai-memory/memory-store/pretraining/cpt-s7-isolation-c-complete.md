---
store_path: pretraining/cpt-s7-isolation-c-complete
title: "S7 isolation C complete: spurgeon 12.45; §5 FAIL"
summary: "S7 Phase A **s5best** SHA `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` (step 1200) on **Unsloth 2026.8.22 + torch 2.8.0+cu126** (Vast Miniforge `unsloth_cpt_s5pin`)"
priority: low
tags: [cpt, s7, c-eval, vast, isolation, scorecard]
schema_version: 1.3
last_updated: "2026-09-22T16:55:19-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/theology_cpt_eval_metrics.json, continued_pretrain/scripts/vast_cpt_s7_c_eval.ps1, pretraining/cpt-s6-stack-isolation-c]
---

# S7 isolation C COMPLETE (2026-09-22)

## Bottom line
S7 Phase A **s5best** SHA `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` (step 1200) on **Unsloth 2026.8.22 + torch 2.8.0+cu126** (Vast Miniforge `unsloth_cpt_s5pin`).

**§5 −15% puritan+confession: FAIL** (−8.6% / −6.0%). Spurgeon **improved** vs S6 isolation C. **No Hub overwrite** this session.

## Host
- Vast instance `52108817` (label `cpt-s7-isolation-c`), RTX 4090, destroyed after fetch.
- Launcher: `continued_pretrain/scripts/vast_cpt_s7_c_eval.ps1`
- Remote: `vast_remote_stack_isolation_c.sh` (NOT torch-2.11 `vast_remote_c_eval.sh`)
- Artifacts: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/`

## Scorecard (a_output_v3 holdouts, Ampere bf16)

| Bucket | Base | S7 s5best | Δ% | S6 isolation C |
|--------|------|-----------|-----|----------------|
| spurgeon | 14.31 | **12.45** | **−13.0%** | 12.85 (−10.2%) |
| puritan | 6.03 | 5.52 | −8.6% | 5.60 (−7.2%) |
| confession | 5.61 | 5.27 | −6.0% | 5.27 (−6.0%) |
| general | 12.04 | 11.95 | −0.8% | 11.83 (−1.8%) |

Train probe spurgeon@16: ppl **11.88** (−10.6% vs base 13.30).

## Gate vs Hub S6
- Hub stays S6 `6aab9194…` until operator approve.
- §5 win bar (≤−15% puritan+confession): **not met**.
- Spurgeon 12.45 is **better** than S6 12.85 and well under 13.3 keep-bar.
- Puritan 5.52 slightly better than S6 5.60; confession ties 5.27.
- Next: Phase B mix `a_output_v4` (Downame) — do not Hub overwrite on §5 alone.

## Stack pin used
Unsloth 2026.8.22, torch 2.8.0+cu126, torchvision 0.23, no xformers, `CPT_EVAL_TRAIN_PROBE_DOCS=16`.
