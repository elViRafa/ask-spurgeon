---
store_path: pretraining/cpt-s7-new-authors-holdout-pc1-2026-09-26
title: "pc1: new-authors holdout + a_output_v6 pack"
summary: "Repo: `C:\\Users\\rafael\\Projetos\\search-sermons` (origin ask-spurgeon), main @ `c8660ac`"
priority: high
tags: [cpt, s7, v6, new-authors, pc1, foundry]
schema_version: 1.3
last_updated: "2026-09-26T16:15:05-03:00"
---

## pc1 build 2026-09-26

Repo: `C:\Users\rafael\Projetos\search-sermons` (origin ask-spurgeon), main @ `c8660ac`.

- Built `holdouts_new_authors`: **20 docs**, SHA `e490b61d9c24d240dd82623faea382d8ec969399d400f449de1ff67821a846d5`
- Authors: downame 5, ambrose 4, swinnock 3, guthrie 2, venning 2, + binning/durham/preston/vincent
- Updated `a_output_v6` holdouts with `new_authors`; theology_dataset train **22915** / val **232**
- mix_v6 rebuilt excluding new-authors fingerprints → mix SHA `e050787e…` (see `cpt-v6-mix-sha-e050787e`)
- Nested LoRA `ddbbee3a…` confirmed under vast_cpt_s7 fetch
- Untouched: a_output_v3/v4/v5, mix_v3/v4/v5, holdouts_pinned_v3

Forge dry later **PASSED** with pin bump. Still no rent until top-up + go.
