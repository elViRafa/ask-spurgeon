---
store_path: fine-tuning/sft-weighted-sparse-sync
title: "Weighted SFT GPU sync via pinned sparse-checkout"
summary: "Stop bulk SCP of `qa_mix_train.jsonl` (~36 MB) laptop-to-Vast"
priority: high
tags: [sft, vast, sparse-checkout, sync, upload]
schema_version: 1.3
last_updated: "2026-10-14T12:37:18-03:00"
evidence: [fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1, fine_tuning/NEXT_SFT_S8_WEIGHTED.md, .cursor/skills/gpu-train-ops/SKILL.md]
---

# Weighted SFT sync: pinned sparse-checkout (2026-10-14)

Stop bulk SCP of `qa_mix_train.jsonl` (~36 MB) laptop-to-Vast.

## Contract

- Pin: local `git rev-parse HEAD` printed as `PINNED_SHA` on dry and -Go.
- On -Go: GPU shallow cone sparse-checkout of `fine_tuning/data` + `fine_tuning/scripts` from public `https://github.com/elViRafa/ask-spurgeon.git`, then materialize into `/workspace/spurgeon-qa-mix-v1/`, `/workspace/qa_open_theology/sft/`, and train scripts under `/workspace/`.
- `config.py` via `git show HEAD:config.py` (not in cone).
- SCP only dirty sync-map overrides, and only with `-AllowDirtySync`. Clean tree: no jsonl SCP.
- CPT still must not full-clone (wrong `theology_cpt_lora*` trees).

## Ops notes

- Push `PINNED_SHA` before -Go so `git fetch origin <SHA>` works on the pod.
- Dry prints `SPARSE_CONE`, sync path map, `DIRTY_OVERRIDES`.
- Avoid Unicode em-dashes inside PowerShell double-quoted strings (PS 5.1 ANSI decode can treat UTF-8 em-dash as a smart quote and swallow function braces).
