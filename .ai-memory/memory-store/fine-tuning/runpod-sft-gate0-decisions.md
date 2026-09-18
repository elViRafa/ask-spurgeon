---
store_path: fine-tuning/runpod-sft-gate0-decisions
title: "RunPod billing and local backup"
summary: "**Decision:** Phase C GATE-0 SFT on RunPod (not dry-run)"
priority: high
tags: [sft, runpod, decisions, gate0]
schema_version: 1.3
last_updated: "2026-09-02T10:13:51-04:00"
---

**Decision:** Phase C GATE-0 SFT on RunPod (not dry-run). Shared volume `7hb931c5oe` with CPT S6.

**Chosen:** Hub v2 CPT merged base (`rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`, SHA256 `319d17a3…1478`) merged to `/workspace/theology_cpt_v2_merged_hf` before SFT.

**Rejected for RunPod billing:** Jupyter/nbconvert pipeline (`sft_remote_run_def.sh` kept but not primary).

**Volume safety:** Hub v2 adapter path `theology_cpt_lora_hub_v2/` isolated from S6 `theology_cpt_lora/`.

**Provision:** runpodctl/REST v1 with `networkVolumeId` required; MCP create-pod may drop mount — `sft_verify_mount.ps1` hard gate.

**GPU fallback (US-IL-1):** 4090 → A6000 → L40S in `sft_provision_pod_mcp.py`.

SFT RunPod billing + local backup policy (2026-09-02):
- Capacity watcher polls US-IL-1 only (4090 then L40S); no pod while waiting.
- Idle pod auto-delete after SFT_IDLE_DELETE_MIN (default 20) if merge/train never starts.
- Monitor syncs checkpoints + sft_fetch_artifacts.ps1 each poll; deletes pod when train done or 8h wall.
- HF_TOKEN via /workspace/.sft_env + sft_inject_hf_token.ps1 (non-interactive SSH).
- GATE-0 merge saved locally via sft_fetch_artifacts -PartialOnly when config.json exists.
- Phase 2 stop probe is warn-only in sft_remote_merge.sh (base may fail before SFT).
