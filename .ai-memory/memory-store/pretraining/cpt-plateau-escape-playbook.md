---
store_path: pretraining/cpt-plateau-escape-playbook
title: "How to leave a CPT plateau on another domain or model"
summary: "Standing rule from the Ask Spurgeon Qwen3.5-4B theology CPT run (2026-10)"
priority: high
tags: [cpt, plateau, learning-rate, lora-rank, playbook, transfer]
schema_version: 1.3
last_updated: "2026-10-07T09:10:03-03:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_sweep/fetch/sweep/m_hi/theology_cpt_lora/adapter_config.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s8_mhi_resume_c/theology_cpt_eval_metrics.json]
---

# How to leave a CPT plateau

Standing rule from the Ask Spurgeon Qwen3.5-4B theology CPT run (2026-10). Use it on another domain or another base model before buying more data or another long run at the same recipe.

Evidence run: S7 continues looked flat and halted. S8 left that flat region. Isolation C then scored the best theology perplexity so far and still missed the promotion gate. Full numbers live in `pretraining/cpt-plateau-exit-cause` and `pretraining/cpt-s8-mhi-resume-isolation-c-complete`.

## A flat loss is often an optimizer no-op

Call it a plateau only after this check:

- In-train domain loss moves less per eval than the early-stop epsilon, so the job halts.
- The domain holdout is still better than the untrained base, and still slowly improving.

That pair means underfit. The weights are barely stepping. It is not proof the corpus is exhausted.

On this project the old recipe was body learning rate 2e-6 and LoRA r=32 alpha=32. Puritan in-train loss moved 1.7396 to 1.7354 in 600 steps, about 0.0004 nats per 50-step check. Early-stop epsilon was 0.003, so every continue halted. Spurgeon holdout perplexity was already about 14% below the base.

## Do not spend the next GPU on these

- Mix reweight. Raising the confession share moved isolation C by about a quarter of a perplexity point and left the same plateau.
- Changing `metric_for_best`. It only picks a checkpoint on a flat curve.
- More steps at the same tiny learning rate and the same narrow LoRA. At the observed slope, the promotion gap needed on the order of 15 identical runs.
- An old result that a higher learning rate hurt, when that result came from a different stack. Here the scary 2e-5 and 5e-5 runs were T4 4-bit, stream packing that leaked recurrent state, frozen embeddings, and a 2-doc probe. They had never been rerun on Ampere, bf16, one-document padding.

## What moved the loss

1. A fresh wider LoRA on the already-trained weights, at a much higher learning rate, for a short sweep. Rank 128, alpha 64, learning rate 2e-5 and 5e-5, 400 steps, parent = the merged best CPT (not the stock base). The 5e-5 arm dropped in-train Puritan from about 1.753 at step 50 to 1.7226 at step 400 and was still falling. The 2e-5 arm reached 1.725, so leaving 2e-6 mattered more than 2e-5 versus 5e-5. The same rank and 5e-5 from the stock base only reached 1.736. The existing CPT weights were part of the gain.
2. Keep that wide adapter and continue at a moderate body learning rate (here 5e-6: about 2.5× the old floor and 10× below the sweep peak). A new Adam that replays the same seed and the same batches wastes the first stretch: loss rose, then only recovered to where the sweep had ended. The next equal stretch was the real gain, about 0.015 nats.
3. Once the per-eval move is back under the early-stop epsilon, more resume steps add little. Keeping Adam from step 800 to step 2250 moved Puritan only 1.708 to 1.701.

## Rule for the next domain or model

1. Compare nats-per-eval with the early-stop epsilon before changing the corpus.
2. If the step is invisible to early-stop and the domain holdout still beats the base, run a short sweep: fresh LoRA about 4× rank, learning rate about 10–25× the stuck body rate, initialized from the current best merged checkpoint. Include one arm from the stock base so you can see whether the existing CPT weights matter.
3. Keep the arm that is still falling. Continue it at a mid learning rate. Keep Adam and the sampler. Do not start a new optimizer on batches that adapter has already seen.
4. Stop extending when the per-eval move is under epsilon again. A longer resume will not repeat the first break.
5. Score a general-domain holdout in the same run. This exit improved theology (Spurgeon −17%, Puritan −13%, confession −11% vs the untrained base) and made the general holdout 3.8% worse than the base. Do not promote on the domain buckets alone.
