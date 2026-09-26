---
store_path: pretraining/cpt-s7-vast-phase-b
title: "S7 Phase B Vast composite early-stop @ 750"
summary: "**Instance:** `52264974` destroyed after fetch (`destroyed_at` 2026-09-23T19:37:29Z)"
priority: medium
tags: [cpt, s7, vast, phase-b, v5, early-stop]
schema_version: 1.3
last_updated: "2026-09-23T16:49:42-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/cpt_train.log, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_run_config.json]
---

## S7 Phase B on Vast — DONE (2026-09-23)

**Instance:** `52264974` destroyed after fetch (`destroyed_at` 2026-09-23T19:37:29Z).
**Stop:** **COMPOSITE EARLY-STOP @ step 750** / 955 (patience 4, ε 0.003). Not a crash. Train ~1.63 h, train_loss 2.017.

## In-train CE @ 750
- spurgeon **2.482** (seed 2.4987)
- puritan **1.740** (seed 1.751)
- confession **1.666** (seed 1.668)
- mix-val **2.205** (unseeded v5 split; best 2.2048)
- Composite bests never moved enough after ~550–600 → flat streak 4 → halt.

## Artifacts (nested fetch)
- HF best (spurgeon): step **700** SHA `6d0030418b0a6fecd4dbf29c63f467dd746119555818e4ad294c04dfd31a363a` at `fetch/theology_cpt_lora/theology_cpt_lora/`
- §5 s5best: step **600** SHA `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214` at `fetch/theology_cpt_lora_s5best/theology_cpt_lora_s5best/`
- Top-level `fetch/theology_cpt_lora_s5best/adapter_model.safetensors` is still Phase A `06354dfc` — do not confuse.

## Next
Isolation C on Unsloth 2026.8.22 + torch 2.8. Pin SHA (`ddbbee3a` and/or `6d003041`). **Keep Hub S7 `06354dfc` until winning C.**
