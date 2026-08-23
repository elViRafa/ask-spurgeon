---
store_path: pretraining/cpt-sota-assessment-2026-07
title: "CPT SOTA Assessment + Implementation (2026-07)"
summary: "CPT SOTA Assessment + Implementation (2026-07)"
priority: high
tags: [pretraining, cpt, unsloth, qlora, spurgeon, sota]
schema_version: 1.3
last_updated: "2026-07-10T21:34:01-04:00"
evidence: [continued_pretrain/notebooks/B_training.ipynb, continued_pretrain/notebooks/B_training_sota.ipynb, continued_pretrain/scripts/07_build_theology_mix.py]
review_status: stale
---

# CPT SOTA Assessment + Implementation (2026-07-10)

## Verdict on B_training.ipynb
- Solid **Kaggle-practical Phase-1 Spurgeon style CPT** (~style 7/10, engineering 8/10).
- **Not** art-state for Spurgeon/Puritans/theology (**~4.5/10** vs multi-author domain goal).
- Keep as known-good baseline; **never overwrite**.

## Baseline facts
- Model: unsloth/Qwen2.5-3B QLoRA, r=32 alpha=64, targets attn+MLP only
- Seq 2048 packing, LR 2e-4 SFTTrainer, no dual LR / no embed+lm_head
- Corpus Spurgeon-only ~3.5k docs ~32M tokens; 2 epochs done train~2.23 val~2.30

## SOTA path implemented (new files only)
- `scripts/07_build_theology_mix.py` — multi-source mix, Spurgeon weight 2.5×, replay, holdouts, manifest
- `notebooks/A_data_prep_sota.ipynb` — HF dataset + multi-holdouts
- `notebooks/B_training_sota.ipynb` — UnslothTrainer, dual LR 5e-5/5e-6, r=64 rsLoRA, embed+lm_head
- `notebooks/C_eval_sota.ipynb` — multi-bucket PPL + style/doctrine/forgetting + merge
- `configs/train_config_cpt_theology_sota.json`
- `data/SOURCES_SOTA_CPT.md` + empty `data/puritans|confessions|bible/`
- README documents baseline vs SOTA tracks

## Defaults
- Body LR 5e-5, embedding_learning_rate 5e-6
- r=64 use_rslora=True, train embed_tokens+lm_head
- Spurgeon oversample 2.5×, replay target 10% when sources available
- Puritan/confession/Bible: user-supplied under data/

## Next operator steps
1. Add PD Puritan/confession/Bible texts under data/
2. Rebuild mix; upload Kaggle corpus
3. Run A_sota → B_sota → C_sota on T4
