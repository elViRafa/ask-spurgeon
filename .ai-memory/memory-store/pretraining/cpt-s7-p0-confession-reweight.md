---
store_path: pretraining/cpt-s7-p0-confession-reweight
title: "S7 P0 confession reweight — run + C complete"
summary: "P0 early-stop 600; C section-5 FAIL Puritan; adapter a70fded8 saved; pod destroyed"
priority: high
tags: [cpt, s7, p0, mix-v6-p0, isolation-c]
schema_version: 1.3
last_updated: "2026-10-02T18:15:00-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best/adapter_model.safetensors]
---

# CPT P0 confession reweight — complete

Built + trained 2026-09-28. One knob was `--target-confession-share 0.15` after holdout-sibling 0.25.

## Pack
- Mix: `continued_pretrain/data/mix_v6_p0`
- HF: `kaggle/a_output_v6_p0` (~13896 train docs)
- mix_sha256: `ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962`
- Shares: confession 15% / puritan 50% / spurgeon 35%
- Init was `0289f1c9` + new Adam; session `vast_cpt_s7_p0`

## Train
- Early-stop ~600/955; train loss ~1.91
- Ops: double-rent cleaned; scp resume once; C before destroy

## Isolation C (step600 best)
- Adapter SHA `a70fded8` @ `vast_cpt_s7_p0/fetch/theology_cpt_lora_s5best`
- Spurgeon ~-13.87%, Puritan ~-9.45%, confession ~-7.4%
- section-5 FAIL (Puritan hard). Nearly identical to prior replay C.
- Pod destroyed after fetch; Hub still Phase A `06354dfc`

## Lesson
Confession reweight alone did not move Puritan hard. Next knob = `metric_for_best=eval_puritan_loss` (P1), same pack, init `a70fded8`.
