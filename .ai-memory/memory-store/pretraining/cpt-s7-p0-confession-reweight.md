---
store_path: pretraining/cpt-s7-p0-confession-reweight
title: "S7 P0 confession reweight pack ready"
summary: "﻿# CPT P0 confession reweight ready"
priority: high
tags: [cpt, s7, p0, mix-v6-p0, reweight]
schema_version: 1.3
last_updated: "2026-09-28T08:10:13-03:00"
---

﻿# CPT P0 confession reweight ready

Built 2026-09-28. One knob: `--target-confession-share 0.15` after holdout-sibling 0.25.

- Mix: `continued_pretrain/data/mix_v6_p0`
- HF: `kaggle/a_output_v6_p0` (14037 docs; HF 13896/141; ~21.5M tok)
- mix_sha256: `ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962`
- Shares: confession 15.0% / puritan 50.0% / spurgeon 35.0% (general+bible cut)
- Init: `0289f1c9` @ vast_cpt_s7_replay/fetch/theology_cpt_lora_s5best, new Adam
- Session: `vast_cpt_s7_p0`
- Dry `vast_cpt_s7_orchestrate.ps1` READY; credit ~$5.83; instances=[]
- Frozen: a_output_v6 / mix_v6 / v3–v5 untouched
- Hub stays Phase A `06354dfc` until C win under reframed section-5

No GPU until operator go.
