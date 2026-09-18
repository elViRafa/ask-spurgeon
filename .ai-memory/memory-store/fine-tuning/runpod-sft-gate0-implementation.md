---
store_path: fine-tuning/runpod-sft-gate0-implementation
title: "RunPod SFT GATE-0 — full implementation"
summary: "**Status:** Implementation complete; GPU execution blocked on US-IL-1 capacity"
priority: high
tags: [sft, runpod, gate0, orchestration]
schema_version: 1.3
last_updated: "2026-09-02T09:21:34-04:00"
---

**Date:** 2026-09-02
**Status:** Implementation complete; GPU execution blocked on US-IL-1 capacity

## Phase

Phase C **GATE-0** SFT on shared CPT volume `7hb931c5oe` (not dry-run). Base = Hub v2 CPT merged HF (`USE_CPT_MERGE=True`).

## Core scripts

| Script | Role |
|--------|------|
| `fine_tuning/scripts/merge_cpt_lora.py` | Hub v2 LoRA → `/workspace/theology_cpt_v2_merged_hf` (bf16 Ampere) |
| `fine_tuning/scripts/train_sft_sota.py` | D tokenize + E train (`--preflight`, `--install`, `--dataprep-only`) |
| `fine_tuning/scripts/eval_sft_sota.py` | F eval; `SFT_EXPORT=0` default |
| `fine_tuning/RUNPOD_RUNBOOK_SFT.md` | Operator runbook |

## Orchestration (`fine_tuning/scripts/sft_*`)

Mirrors CPT S6: `sft_runpod_common.ps1`, `sft_provision_pod.ps1`, `sft_provision_pod_mcp.py`, `sft_wait_ssh.ps1`, `sft_verify_mount.ps1`, `sft_sync_to_pod.ps1`, `sft_launch_train.ps1`, `sft_launch_merge.ps1`, `sft_orchestrate.ps1`, `sft_monitor_until_done.py`, `sft_start_monitor.ps1`, `sft_sync_checkpoints.ps1`, `sft_fetch_results.ps1`, `sft_run_eval.ps1`, `sft_export_if_gates.ps1`, `sft_watch_capacity.py`, `sft_start_capacity_watch.ps1`, `sft_inspect_volume.sh`, `sft_remote_setup.sh`, `sft_remote_train.sh`, `sft_remote_merge.sh`.

Session file: `fine_tuning/kaggle/sft_session.json`
Local fetch dir: `fine_tuning/kaggle/runpod_sft_gate0/`

## Volume layout (do not clobber CPT S6)

```
/workspace/theology_cpt_lora/           # S6 CPT — DO NOT TOUCH
/workspace/checkpoints_sota/            # S6 CPT — DO NOT TOUCH
/workspace/theology_cpt_lora_hub_v2/    # Hub v2 LoRA download target
/workspace/theology_cpt_v2_merged_hf/ # GATE-0 SFT base
/workspace/spurgeon_qa_lora_v2/         # SFT output
```

## Env vars (on pod)

```
SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home USE_CPT_MERGE=1
[REDACTED_SECRET]
[REDACTED_SECRET]
[REDACTED_SECRET]
```

Notebook generator: `GATE0_PATH = os.environ.get("SFT_GATE0_MERGED", kaggle_default)` in `_gen_sota_sft_notebooks.py`.

## Local prep (PASS 2026-09-02)

- `qa_mix_v2`: train=3264, val=153, test=100, refusal 11.3%
- `13_sft_local_readiness.py --gate0` PASS
- `spurgeon-qa-mix-v1.zip` repackaged (12.25 MB)

## GPU blocker

US-IL-1 + volume `7hb931c5oe`: provision failed for 4090, A6000, L40S (all HTTP 500 no instances). `sft_watch_capacity.py` polling every 600s with GPU fallback order 4090→A6000→L40S.

Log: `fine_tuning/kaggle/sft_capacity_watch.log`

## Operator commands

```powershell
cd fine_tuning\scripts
.\sft_start_capacity_watch.ps1 -IntervalSec 600   # auto when capacity returns
.\sft_orchestrate.ps1 -StartMonitor                # manual one-shot
.\sft_run_eval.ps1; .\sft_fetch_results.ps1
.\sft_export_if_gates.ps1                         # after §5 gates
```

## Monitor done markers

`/workspace/sft_train.log`: `SOTA SFT v2 complete`, `Saved adapter to`, `sft_run_config.json`. Require log marker + 2× not-running polls (S6 false-positive lesson).

## Decisions

- Detached Python over Jupyter on billed GPU (CPT lesson)
- Hub v2 LoRA in isolated path; never overwrite S6 `theology_cpt_lora/`
- MCP create-pod may drop volume — always verify with `sft_verify_mount.ps1`
