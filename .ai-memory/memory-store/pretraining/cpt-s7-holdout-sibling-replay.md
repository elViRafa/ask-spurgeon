---
store_path: pretraining/cpt-s7-holdout-sibling-replay
title: "S7 holdout-sibling replay pack ready"
summary: "Phase B isolation C on nested s5best `ddbbee3a` missed §5: Spurgeon 12.39 (−13.42%), Puritan 5.50 (−8.88%), confession 5.25 (−6.37%) vs Ampere base"
priority: high
tags: [cpt, s7, mix-v6, replay, vast]
schema_version: 1.3
last_updated: "2026-09-23T18:15:47-03:00"
evidence: [[REDACTED_SECRET].json, continued_pretrain/data/mix_v6/theology_mix_manifest.json, continued_pretrain/scripts/vast_cpt_s7_common.ps1, continued_pretrain/NEXT_CPT_S7.md]
---

## Holdout-sibling replay (v6) — packed 2026-09-23

Phase B isolation C on nested s5best `ddbbee3a` missed §5: Spurgeon 12.39 (−13.42%), Puritan 5.50 (−8.88%), confession 5.25 (−6.37%) vs Ampere base. Slightly better than Hub `06354dfc` (12.45 / 5.52 / 5.27). Hub stays Phase A until a C wins Puritan and confession without Spurgeon past ~13.3.

Do not retrain `a_output_v5`. Next CPT is a new pack:

- Mix: `continued_pretrain/data/mix_v6` SHA `2d5a99c1a0d4d3e4d64013dabe894a52f4de1bf0b576e8997b02af595f691acd`
- HF: `kaggle/a_output_v6` (23,139 docs; HF train 22,907 / val 232; ~42.4M tokens)
- Sibling share 25% (5,661 docs / 35.1M chars of pinned puritan+confession train siblings)
- Spurgeon floor 35%; new-author (Downame/wave 5) cap 5%
- Shares: puritan 49.5% / spurgeon 35.0% / confession 9.2% / general 5.4% / bible 0.9%
- Confession 9.2% is sibling upweight of existing S4 systematics, not Shaw/SSK. Leave S5 out.
- Holdouts: pinned v3 (puritan 20, confession 10, spurgeon 298)
- Init: nested Phase B s5best `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214`, new Adam, LR 2e-6
- Halt composite: spurgeon + puritan + confession only (no `eval_mix_loss`)
- Same early-stop: min 400, patience 4, ε 0.003, max 955
- Stack pin: Unsloth 2026.8.22 + torch 2.8
- Session/results: `vast_cpt_s7_replay` (do not overwrite Phase B fetch)

No GPU until operator go. Do not overwrite v3/v4/v5 or Hub.
