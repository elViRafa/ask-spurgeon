---
store_path: pretraining/cpt-plateau-optimizer-diagnosis
title: "CPT plateau is an optimizer no-op, not a data ceiling"
summary: "The S7 continues at body LR 2e-6 and LoRA r=32 barely moved weights"
priority: high
tags: [cpt, s8, plateau, learning-rate, lora-rank]
schema_version: 1.3
last_updated: "2026-10-05T08:35:22-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_replay/fetch/checkpoints_s7/checkpoint-600/trainer_state.json, continued_pretrain/scripts/cpt_runtime.py]
---

The S7 continues at body LR 2e-6 and LoRA r=32 barely moved weights. Replay puritan in-train loss went 1.7396 to 1.7354 over 600 steps. Phase A went 1.7421 to 1.7399 over 750 steps. Section-5 puritan needs about 0.063 more nats (P0 isolation-C loss 1.6983 to 1.6350). At ~0.004 nats per run that is about 15 more identical runs.

Early-stop epsilon 0.003 per 50-step eval cannot see a ~0.0004 step, so the run looks flat as soon as min_steps passes. Spurgeon train-probe and holdout both improved (about -11.5% and -13.9%), so this is underfit, not overfit.

The Kaggle evidence that 2e-5 and 5e-5 hurt (v11, v12, v3 r=64) was the T4 4-bit path with stream packing that leaked GatedDeltaNet state, frozen embeddings, and a 2-doc probe. It was never retested on Ampere one_doc_padded.

P0 confession reweight moved isolation C by about a quarter of a point. P1 metric_for_best only picks a checkpoint on a flat curve. Do not spend another GPU on those knobs before a higher-LR r=128 sweep.

Pinned puritan docs 7, 10, 11 and confession doc 3 are noisy (French, long-s, OCR). They stay in the gate. Isolation C now also reports a clean sub-score and a bootstrap CI.
