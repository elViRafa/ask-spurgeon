---
store_path: pretraining/cpt-s6-stack-isolation-c
title: "S6 stack-isolation C: PPL flips on S5 Unsloth/torch pin"
summary: "Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on **Unsloth 2026.8.22 + torch 2.8.0+cu126** scores spurgeon **12.85 (−10.2% vs base 14.31)**"
priority: high
tags: [cpt, s6, c-eval, stack-isolation, early-stop, hub-v2]
schema_version: 1.3
last_updated: "2026-09-20T19:04:21-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/stack_isolation_c/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/cpt_eval.log, pretraining/vast-cpt-s6-resume-spike-analysis]
---

# S6 stack-isolation C COMPLETE (2026-09-20)

## Bottom line
Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on **Unsloth 2026.8.22 + torch 2.8.0+cu126** scores spurgeon **12.85 (−10.2% vs base 14.31)**. Vast C on Unsloth 2026.9.6 / torch 2.11 was a **false FAIL** (+27.9%). Weights are not bad.

## Pins (from S5 `runpod_cpt_v3/cpt_eval.log`)
- Unsloth **2026.8.22** (Hub-v2 C used 2026.8.21)
- torch **2.8.0+cu126** + torchvision **0.23.0**
- `UNSLOTH_SKIP_TORCHVISION_CHECK=1` after dropping xformers (pulls torch≥2.10)

## Host note
Runpod unpaid (402). Ran on **Vast RTX 4090** with the S5/Hub-v2 **software** pin. Residual host confound remains; Unsloth/torch were the controlled variables. Prefer a confirmatory Runpod C when funded.

## Scorecard (a_output_v3 holdouts, Ampere bf16)

| Bucket | Base | Adapter | Δ% |
|--------|------|---------|-----|
| spurgeon | 14.31 | **12.85** | **−10.2%** |
| puritan | 6.03 | 5.60 | −7.2% |
| confession | 5.61 | 5.27 | −6.0% |
| general | 12.05 | 11.83 | −1.8% |

Probe vs base: **PASS**. §5 −15%: still FAIL.

## 16-doc train probe (same C)
- Adapter spurgeon@16: ppl **12.13** loss **2.495** (matches train `eval_spurgeon_loss=2.4987`)
- Base@16: ppl 13.30 → Δ **−8.85%**
- So 16-doc vs 50-doc was **not** the Vast regression cause; both look good on the pinned stack.

## vs Hub v2 / S5 (same holdouts family)
- Hub v2: spurgeon 13.28 (−7.2%)
- S5: spurgeon 13.34 (−6.8%)
- This S6: spurgeon **12.85 (−10.2%)** — **better** on this scorecard

## Interpretation (plan table)
- **Flip** → Vast **C-eval** stack untrustworthy (not proof train stack is buggy).
- Hub overwrite is a **separate approve** — numbers favor overwrite vs Hub v2, but do not auto-overwrite.
- Do **not** start a blind new B to “fix C”.

## Artifacts
Scripts: `vast_remote_stack_isolation_c.sh`, `vast_stack_isolation_c.ps1`, `runpod_stack_isolation_c.ps1`, `runpod_remote_stack_isolation_c.sh`.
Eval: `CPT_EVAL_TRAIN_PROBE_DOCS` + `UNSLOTH_PIP_SPEC` env in `eval_cpt_sota.py`.

## Operator Q&A clarifications (2026-09-20)

### What was broken
- **Proven:** full holdout **C** on Unsloth **2026.9.6** / torch **2.11** inflated adapter PPL (base stayed ~14.31; adapter → 18.31).
- **Not proven as a single package:** Unsloth vs torch alone (both changed in the isolation flip).
- **Rejected:** wrong SHA, 16-vs-50 overfit as the Vast +28% cause, embed→lm_head tying sync.

### Do NOT conflate with B early-stop
- Bug proven = **post-train C** on the new stack.
- S6 B halt = composite early-stop after **resume spike** (train loss also jumped 1.92→2.33) — real train dynamics, not the 50-doc C liar.
- In-train **16-doc** spurgeon loss (~2.4987) **matches** good-stack train probe (2.495) → B’s probe metric was trustworthy.
- Blind new B is **not** required to “undo” the false C.

### Step timeline (C scored best, not last)
| Phase | Steps |
|-------|-------|
| S5 initial v3 | stop ~**375**/4128, best ~**325** |
| S6 continue | HF best **2050** (SHA `6aab…`) |
| S6 last resume session | resume **2050** → stop **2400** (spike; never beat 2050) |
| **C scored** | **2050** only — not 2400 |

### Improvement claim
On good-stack C (v3 holdouts): S6@2050 spurgeon **12.85 (−10.2%)** beats Hub v2 **13.28 (−7.2%)** and S5 **13.34 (−6.8%)**. §5 −15% still FAIL. Hub overwrite still needs **separate operator approve**.
