---
store_path: pretraining/cpt-s6-gpu-blocked-volume-balance
title: "S6 GPU blocked: volume 404 and $5 balance"
summary: "Highest **complete** local HF checkpoint (adapter + `optimizer.pt` + `trainer_state.json`): `continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota/checkpoints_sota/checkpoint-2050` (w"
priority: high
tags: [cpt, s6, runpod, blocker, volume]
schema_version: 1.3
last_updated: "2026-09-16T07:21:48-03:00"
evidence: [continued_pretrain/scripts/s6_runpod_common.ps1, continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota/checkpoints_sota/checkpoint-2050]
---

# S6 GPU resume blocked — volume gone + balance (2026-09-16)

Phase 0 code is ready. GPU resume **did not start**.

## Blockers
1. Network volume `7hb931c5oe` → **404** on the authenticated Runpod MCP account (`list-network-volumes` empty).
2. Creating a replacement 75 GB US-IL-1 volume → **400**: account must have **≥ $5** balance.
3. `~/.runpod/config.toml` has empty `apikey = ''`; REST/runpodctl path unusable until a real `RUNPOD_API_KEY` is set. MCP OAuth REST v1 pod create returned Cloudflare **403/1010**.

## Local resume artifact (when volume/funds restored)
Highest **complete** local HF checkpoint (adapter + `optimizer.pt` + `trainer_state.json`): `continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota/checkpoints_sota/checkpoint-2050` (was HF best during interrupted S6; step 2100 not present locally).

## Do not
Train on container disk only. Do not `S6_FRESH_START` over a good ckpt. Keep Hub v2 until finished B + winning C.

## Next operator steps
1. Add ≥ $5 Runpod balance **or** restore/recreate volume in **US-IL-1** with checkpoint data.
2. Set real `RUNPOD_API_KEY` (or `flash login`).
3. `s6_orchestrate.ps1 -StartMonitor` with continue+resume (Phase 0). Upload/use `checkpoint-2050` if volume no longer has `checkpoint-2100`.
