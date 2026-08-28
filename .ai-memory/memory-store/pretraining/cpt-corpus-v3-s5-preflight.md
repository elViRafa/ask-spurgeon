---
store_path: pretraining/cpt-corpus-v3-s5-preflight
title: "CPT corpus v3 S5 preflight done — GPU next session"
summary: "S5 preflight (no GPU) finished 2026-08-27"
priority: high
tags: [cpt, corpus-v3, s5, preflight, runpod]
schema_version: 1.3
last_updated: "2026-08-27T17:53:38-04:00"
evidence: [continued_pretrain/CORPUS_V3_S5_RUN_CHECKLIST.md, continued_pretrain/kaggle/a_output_v3/DATASET_META.json, continued_pretrain/scripts/18_prep_hf_dataset.py, continued_pretrain/RUNPOD_RUNBOOK.md]
---

S5 preflight (no GPU) finished 2026-08-27. Do not start B from this memory. Send-to-run: `[REDACTED_SECRET].md`.

Local A: `continued_pretrain/scripts/18_prep_hf_dataset.py` wrote `kaggle/a_output_v3` (junction to `D:\\search-sermons-cpt\\a_output_v3`, ~320 MB). HF train **51417** / val **520**. Mix SHA256 `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`. Do **not** copy `kaggle/a_output` (v2).

Volume `7hb931c5oe` US-IL-1 grown **50→75 GB**, renamed `theology-cpt-v3`. 0 GPU pods. MCP create-pod still drops mounts — next session uses runpodctl.

Tests PASS: test_manual_pack, test_cpt_runtime, test_kaggle_path_resolve.

Fallback LoRA unchanged: rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`.
