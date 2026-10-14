---
store_path: fine-tuning/sft-s8-weighted-forge-ready
title: "Weighted SFT S8 ready for Grok Bot Forge"
summary: "- Base: private Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`"
priority: high
tags: [sft, weighted, forge, seq-length]
schema_version: 1.3
last_updated: "2026-10-14T11:27:33-03:00"
evidence: ["commit:5b12b79", fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1, fine_tuning/NEXT_SFT_S8_WEIGHTED.md, continued_pretrain/GROK_BOT_FORGE.md]
---

# Weighted SFT S8 ready for Forge

## Contract (current)

- Base: private Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit`
- Mix: frozen RAG 3264 + open-theology train 558, repeat 1, both system prompts kept
- Seq / batch / accum: **4608 / 1 / 16**
- Backend: `SFT_BACKEND=peft`; `SFT_EXPORT=0`; `SFT_FORCE_DATAPREP=1`; output `/workspace/sft_s8_weighted/adapter`
- Hub LoRA v2 `06354dfc` and `spurgeon-qa-v2` stay

## Landed on main (`5b12b79`)

- Mask fail-closed + drop fully-masked (PEFT + Unsloth)
- scp harden: LogLevel=ERROR, retries, gzip `qa_mix_train.jsonl`, speed abort
- `vast_verify_gpu` EAP Continue; SSH wait already LogLevel=ERROR
- Forge/Foundry profiles + NEXT paste aligned to weighted SFT (not CPT S7)

## Forge path

- Dry: `fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1`
- Go (after credit + operator go): same `-Go -StartMonitor`
- Runbook: `fine_tuning/NEXT_SFT_S8_WEIGHTED.md`
- Do **not** call `vast_orchestrate.ps1`, `vast_sft_s8_orchestrate.ps1`, or CPT launchers

## Still before next go

Credit top-up (last ~$4.69–$4.89) or explicit `-AllowLowCredit`. No Hub until F gates.
