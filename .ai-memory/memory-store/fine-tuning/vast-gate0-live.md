---
store_path: fine-tuning/vast-gate0-live
title: "Vast GATE-0 live run status"
summary: "**Started:** 2026-09-05 ~19:42 ET (operator said go)"
priority: high
tags: [vast, sft, gate0, live]
schema_version: 1.3
last_updated: "2026-09-05T19:55:43-04:00"
review_status: stale
---

# Vast GATE-0 live run

**Started:** 2026-09-05 ~19:42 ET (operator said go)

## Instance
- `instance_id=49992506` (destroyed stuck `49991334` — pytorch image pull hung)
- Image: `nvidia/cuda:12.4.1-devel-ubuntu22.04` (lighter; setup installs torch 2.11)
- SSH direct: `root@137.175.76.24:49025` with `%USERPROFILE%\.ssh\runpod_cpt`
- Profile: 4090 + `CUDA_VISIBLE_DEVICES=0`

## Fixes during run
- `vast_wait_ssh.ps1`: `${target}:port` PowerShell parse fix
- `vast_destroy.ps1`: pass `-y` to skip CLI confirm
- `vast_launch.ps1`: pgrep false-positive on ssh bash -c (use `[b]ash /workspace/sft_remote_train.sh`)

## Status
Setup/train launched (`LAUNCH_PID`); installing torch 2.11+cu126. Monitor: `vast_monitor_until_done.py` (10h wall).
