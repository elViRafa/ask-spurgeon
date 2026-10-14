---
store_path: fine-tuning/sft-s8-weighted-crash-fix-2026-10-14
title: "Weighted SFT S8 crash fix (seq 4608 + SSH + mask harden)"
summary: "Vast instance after operator go: training crashed before step 1 with `AssertionError: S3 FAIL: user turn leaked into labels`"
priority: high
tags: [sft, weighted, crash, mask, ssh, vast]
schema_version: 1.3
last_updated: "2026-10-14T11:36:32-03:00"
evidence: ["commit:5b12b79"]
---

# Weighted SFT S8 crash fix (2026-10-14)

## What failed

Vast instance after operator go: training crashed before step 1 with `AssertionError: S3 FAIL: user turn leaked into labels`. Dataprep showed max length 4330 and `over 2048: 2879 (75.3%)`. TRL truncates to `SFT_MAX_SEQ_LENGTH` before our mask; most RAG rows lost `<|im_start|>assistant`; `_mask_assistant_labels` fell back to training all tokens. Open-theology rows were all under 2048.

Orchestrator also died earlier: `$ErrorActionPreference=Stop` turned ssh first-connect "Permanently added" stderr into a terminating error in `vast_wait_ssh.ps1`.

## What landed in code

1. `SFT_MAX_SEQ_LENGTH=4608` in `sft_remote_train_s8_weighted.sh` and `sft_s8_weighted_plan.py` (batch 1 / accum 16 unchanged). Runbook + plan tests updated.
2. Missing assistant marker → all labels `-100`; drop fully masked rows; S3 checks every row (PEFT + Unsloth). Tests in `test_mask_assistant_labels.py`.
3. SSH: `LogLevel=ERROR` on `Get-VastSshArgs` and wait-ssh; Continue + exit-code around ssh and `Invoke-Vastai`. LF endings kept.

## Verify

- `pytest` mask + weighted plan: passed
- Dry `vast_sft_s8_weighted_orchestrate.ps1`: READY / DRY COMPLETE
- No GPU rent in the fix session; no Hub

## Still before next go

Credit top-up (last report ~$4.89), operator go, Forge dry then `-Go -StartMonitor`. See `fine-tuning/sft-s8-weighted-residual-risks`.

## Follow-up harden (main `5b12b79`)

Cursor TODO + residual burn risks closed without rent:

- `Copy-ToVastWeighted`: LogLevel=ERROR, 3 retries, gzip `qa_mix_train.jsonl`, speed abort
- `vast_verify_gpu.ps1` EAP Continue + exit code
- `SFT_FORCE_DATAPREP=1` + wipe weighted dataprep cache
- Unsloth path drops fully-masked rows; dataprep tokenizer prefers merged base; `fix_mistral_regex=True`
- `GROK_BOT_FORGE.md` / Foundry / NEXT paste / skills point at weighted SFT (not CPT S7)

Proof: pytest mask + weighted plan passed; dry READY; pushed `5b12b79`. Next blocker is credit + operator go.
