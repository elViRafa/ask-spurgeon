---
store_path: pretraining/cpt-eval-unify-vs-buckets
title: "CPT eval: 2-doc Spurgeon stop is too small; do not unify C buckets"
summary: "Operator asked (2026-08-27): is a 2-doc Spurgeon eval too small, and should Spurgeon/Puritan/confession/general become one unified eval so CPT can keep learning Reformed theology?"
priority: high
tags: [cpt, eval, early-stop, review]
schema_version: 1.3
last_updated: "2026-08-28T00:11:29-04:00"
evidence: [continued_pretrain/scripts/18_prep_hf_dataset.py, continued_pretrain/kaggle/b_output/checkpoints_sota/checkpoint-250/trainer_state.json, continued_pretrain/kaggle/b_output_v6/checkpoints_sota/checkpoint-75/trainer_state.json, continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/kaggle/runpod_cpt_v3/cpt_train.log]
---

# Do not collapse C buckets; enlarge B stop sample

Operator asked (2026-08-27): is a 2-doc Spurgeon eval too small, and should Spurgeon/Puritan/confession/general become one unified eval so CPT can keep learning Reformed theology?

## Answer
Yes, 2 docs is too small **as a stop key**. No, do not merge C holdout buckets into one mix score. Knowledge comes from **unread mix tokens**, not from how eval is labeled. Training is already one mix (Spurgeon 40.2%, Puritan 45.7%, confession 5.5%).

## Three evals people conflate
- **Train mix:** already unified. Multiple eval names do not split training.
- **B in-train eval:** `EVAL_DOCS_PER_BUCKET=2`, `EVAL_BUCKETS_DURING_TRAIN=[spurgeon]`, plus 4 mix docs. Metric `eval_spurgeon_loss`. VRAM hatch from T4 OOM (v7 tried 8 docs). This fired S5 at 375/4128.
- **C scorecard:** spurgeon 50 docs / 70k tok, puritan 20 / 37k, confession 10 / 20k, general 10 / 16k. Probe + §5 gate. This is the real eval.

## S5 evidence (cpt_train.log)
`eval_spurgeon`: 2.292@25 → **2.254@325** → 2.259@350 → 2.257@375. Δ after 325 is ±0.005 noise on ~2 sermons. Patience 2 × eval 25 = stop.
`eval_mix`: 2.085@25 → **2.029@375**, still falling. Mix val on disk is 520 docs; B only scores 4 of them.

C then: all four buckets beat Ampere base (−6.8 / −5.2 / −4.4 / −1.2%) but miss §5 −15%. Puritan/confession are 45.7%/5.5% of the mix; 8.2M tokens only gave a thin slice.

## Why not one C number
A single mix PPL hides the tradeoffs the gates need: Spurgeon-ness (product), Puritan/confession −15% (§5), general forgetting. Historical RC3: mix-only B eval overfit while holdout PPL got worse. Mix test is a random split of train, not a held-out author/work set.

## Next B (when approved) — do this instead of unifying
1. Early-stop **floor** (min_steps ~0.4–0.5 epoch or min_tokens ~25–40M) so 2-doc noise cannot halt at 9%.
2. On 24 GB raise `EVAL_DOCS_PER_BUCKET` to 16–32 (or full C spurgeon 50). Keep logging mix.
3. Optional composite: stop only if Spurgeon **and** mix are both flat; or weight 0.4 spurgeon + 0.4 puritan + 0.2 confession.
4. Do not switch `METRIC_FOR_BEST` to `eval_mix_loss` without a larger mix sample and a Spurgeon-not-rising guard.
5. Keep C per-bucket. Keep Hub v2 until a new C wins.

## Fact-check of the B-eval strategy summary (2026-08-28)

The summary is **directionally right**. Nits:

- Mix val **is** `VAL_FRACTION=0.01` (`18_prep_hf_dataset.py`). v3 = 520 test rows. B in-train mix is still only `EVAL_DOCS_PER_BUCKET*2` (4 docs on S5), not those 520.
- Mix-only B (`eval keys=['mix']`, `b_output`): `eval_mix` **rose** 2.316→2.463. C v3 holdouts **+9 / +11.6 / +15.4 / +17.8%**. True. Do not describe that run as “mix improved.”
- **B v6 did not show mix-stable + spurgeon-rising.** Both rose (mix 1.890→1.920; spurgeon 2.568→2.607; puritan/confession/general also rose). Spurgeon as `METRIC_FOR_BEST` is justified because C scores **holdouts**, not because v6 mix and spurgeon diverged.
- S5 is the divergence the other way: spurgeon ±0.005 after 325, mix still falling. Composite+floor is the synthesis of both eras.
- Floor: 25M tokens ≈ 28% of the 90M epoch, not 40–50%. Pick one: `min_steps≈0.4–0.5 epoch` (~36–45M) **or** `min_tokens=25–40M`. Do not treat them as equal.
- Confession C holdout is 10 docs; `EVAL_DOCS_PER_BUCKET=32` will cap. Spurgeon C is 50.
- Composite stop is **not** in `train_cpt_sota.py` today (`QuietEarlyStoppingCallback` is single-metric `eval_spurgeon_loss`). Needs a custom callback, a flat epsilon (else ±0.005 still fires after the floor), and a separate `METRIC_FOR_BEST` for which ckpt to save. `max_steps` (one epoch) still required so mix can crawl forever.
- Keep abort-at-50 **on a fresh-from-base run**; loosen only on the S5-LoRA continue.
