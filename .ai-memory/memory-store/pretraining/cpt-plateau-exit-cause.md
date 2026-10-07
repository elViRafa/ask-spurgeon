---
store_path: pretraining/cpt-plateau-exit-cause
title: "Plateau exit was LR and rank, not the mix"
summary: "The S8 exit from the puritan plateau was the optimizer, not the mix"
priority: high
tags: [cpt, plateau, playbook]
schema_version: 1.3
last_updated: "2026-10-07T09:09:25-03:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_sweep/fetch/sweep/m_hi/theology_cpt_lora/adapter_config.json]
---

The S8 exit from the puritan plateau was the optimizer, not the mix.

Old continues used body LR 2e-6 and LoRA r=32 alpha=32. Replay in-train puritan moved 1.7396 to 1.7354 in 600 steps (~0.00035 nats per 50 steps), under the early-stop epsilon of 0.003. That was underfit. Spurgeon holdout was already improving.

What moved the loss:
1. Fresh r=128 alpha=64 on merged a70 at LR 5e-5 (m_hi sweep, 400 steps) dropped in-train puritan from about 1.753 at step 50 to 1.7226, still falling. m_lo at 2e-5 reached 1.725. f_hi, same rank and 5e-5 but from stock Qwen, only reached 1.736. So the exit is higher LR times wider LoRA on the existing CPT weights.
2. Keeping that adapter at body LR 5e-6. Continue steps 1-400 were wasted (new Adam replayed seed-42 batches; puritan rose to 1.7462 and only returned to 1.7229). Steps 400-800 fell to 1.7082 (~0.015 nats).
3. HF-resume of that Adam to step 2250 added only 1.7082 to 1.701. The slope was flat again. Isolation C 1.6605 vs prior best C 1.6983 is mostly the sweep plus the productive half of the continue.

Not the cause: P0 confession reweight, P1 metric_for_best, or more steps at 2e-6 / r=32.

General rule for other domains and models: `pretraining/cpt-plateau-escape-playbook`.
