---
store_path: pretraining/c-drive-cleanup-2026-10-05
title: "Freed C: by dropping finished-run optimizer state and caches"
summary: "Freed **C: from 6.7 GB to 58.9 GB**"
priority: medium
tags: [disk, c-drive, checkpoints, cleanup]
schema_version: 1.3
last_updated: "2026-10-05T19:48:58-03:00"
---

# C: disk cleanup (2026-10-05)

Freed **C: from 6.7 GB to 58.9 GB**. D: still has about 480 GB free.

## Deleted (finished runs / regenerable)
- `optimizer.pt` under `vast_cpt_s7`, `vast_cpt_s7_p0`, and `vast_cpt_s7_replay` checkpoints (23.1 GB). Adapter weights kept.
- `payload.tar` in those three session dirs (6.0 GB). Repack from the pack scripts if a parked run is relaunched.
- `.gradle/caches`, npm cache, pnpm store, puccinialin cache, user Temp.

## Moved to D:\search-sermons-cpt\archive-2026-10-05\
- `vast_cpt_s8_sweep/fetch/s8_fetch_loras.tgz` (5.3 GB). Extracted `sweep/` (`f_hi`, `m_hi`, `m_lo`) stayed on C:.

## Kept on C:
- S8 sweep adapters, `vast_cpt_s8_mhi_continue`, S7/replay/P0 LoRAs including `theology_cpt_lora_s5best`.
- Docker WSL disk `AppData\Local\Docker\wsl\disk\docker_data.vhdx` (~46 GB). Docker Desktop was not running.
- Downloads wedding photos (~19 GB).
