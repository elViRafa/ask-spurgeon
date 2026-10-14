---
store_path: fine-tuning/sft-s8-weighted-residual-risks
title: "Weighted SFT S8 residual risks after harden push"
summary: "Fixed on main `5b12b79`: 2048→4608 S3 truncation leak; mask fail-closed + Unsloth drop; SSH/scp/verify_gpu EAP Continue; `SFT_FORCE_DATAPREP=1`; Forge/Foundry guides aligned to weighted SFT"
priority: medium
tags: [sft, risk, oom, vast, weighted, forge]
schema_version: 1.3
last_updated: "2026-10-14T11:36:29-03:00"
evidence: ["commit:5b12b79", fine_tuning/scripts/vast_sft_s8_weighted_orchestrate.ps1, fine_tuning/scripts/sft_remote_train_s8_weighted.sh, fine_tuning/scripts/vast_verify_gpu.ps1]
---

# Residual risks for next weighted SFT S8

Fixed on main `5b12b79`: 2048→4608 S3 truncation leak; mask fail-closed + Unsloth drop; SSH/scp/verify_gpu EAP Continue; `SFT_FORCE_DATAPREP=1`; Forge/Foundry guides aligned to weighted SFT.

## Before next -Go (can burn money)

| Priority | Risk | Likelihood | Mitigation |
|----------|------|------------|------------|
| 1 | Vast credit low (~$4.69–$4.89 after failed run) | H | Top up before Forge go, or explicit `-AllowLowCredit` |
| 2 | OOM at seq 4608 on 4090 (unproven) | M | Keep `SFT_EVAL_STRATEGY=no`; if OOM → `SFT_LORA_RANK=16` (do not drop seq below ~4330) |
| 3 | Long `sft_remote_setup` → monitor thinks train never started | M | Watch `sft_launch.log`; widen idle polls |
| 4 | `vast_inject_hf_token.ps1` writes GATE-0 `.sft_env` (2048, v2 merge) | M footgun | Weighted script re-exports after source — keep that override |

## Wrong launcher / legacy

- Non-weighted `sft_remote_train_s8.sh` / `sft_s8_plan.py` still `SFT_MAX_SEQ_LENGTH=2048`. Use only `vast_sft_s8_weighted_orchestrate.ps1`.

## Quality (not train crashes)

- F §5 refusal still ~0.54 vs 0.85 expected; weighted mix does not upsample refusal. Expect `SFT_EXPORT=0` after train.
- Open-theology has no F-gate coverage yet.

## Walk-away on next successful rent

- `over 4608` ~0, `S3 masking OK`, drop count ~0
- Base under `.../qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit`
- Output `.../sft_s8_weighted/adapter`; not resuming `spurgeon_qa_lora_v2`
- Fetch before destroy; no Hub until F gates
