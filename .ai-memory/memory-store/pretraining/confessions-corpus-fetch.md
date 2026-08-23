---
store_path: pretraining/confessions-corpus-fetch
title: "Confessions + Institutes corpus (WCF, 1689, Calvin)"
summary: "Confessions + Institutes corpus (WCF, 1689, Calvin)"
priority: high
tags: [pretraining, data, confessions, wcf, 1689, calvin]
schema_version: 1.3
last_updated: "2026-07-13T10:30:48-04:00"
evidence: [data/confessions/PROVENANCE.md, continued_pretrain/scripts/11_fetch_confessions.py]
---

# Confessions / Institutes fetch (2026-07-13)

## On disk under `data/confessions/` (~5.4 MB)

- **WCF:** `westminster/westminster_confession.txt` (IA confessionoffa00west)
- **WCF + Larger/Shorter catechisms:** `westminster/wcf_catechisms_1756.txt` (Scottish 1756 IA)
- **WSC:** already curated `westminster/westminster_shorter_catechism.txt`
- **1689 LBCF:** `1689/second_london_confession.txt` — curated PD core chapters (IA only had modern class recordings)
- **Calvin Institutes (Beveridge):** `institutes/institutes_beveridge_vol1.txt` + `vol2.txt`

## Tooling

`continued_pretrain/scripts/11_fetch_confessions.py` (+ `--rebuild-mix`)

## Mix caps

`07_build_theology_mix.py` now supports `--max-confession-share` default **0.06** so Institutes does not dominate (plan target 3–6%). After rebuild: confession ~5.6%, spurgeon 45%, puritan ~45%, bible 4%.

Heidelberg remains holdout-only under `holdouts_manual/`.
