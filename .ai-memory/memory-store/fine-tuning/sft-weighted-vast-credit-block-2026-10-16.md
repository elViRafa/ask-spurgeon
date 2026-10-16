---
store_path: fine-tuning/sft-weighted-vast-credit-block-2026-10-16
title: "Weighted SFT ready on 228b9c0; Vast credit $2.82 blocks -Go"
summary: "Code on main `228b9c010e9878b13ba5bc7eea877c3032f8fb51` is ready to launch"
priority: high
tags: [sft, weighted, vast, credit, readiness]
schema_version: 1.3
last_updated: "2026-10-16T14:47:11-03:00"
evidence: ["commit:228b9c010e9878b13ba5bc7eea877c3032f8fb51"]
---

# Weighted SFT Vast readiness (2026-10-16 14:46 -03)

Code on main `228b9c010e9878b13ba5bc7eea877c3032f8fb51` is ready to launch. A paid `-Go` is blocked by credit.

## Live read (no rent)
- `vastai show instances`: instance_count=0. Session file still says `ssh_ready` for instance `56270845` at `79.112.108.70:44906`; that machine is gone. Orchestrator provisions with `Force`, so the stale session does not reuse it.
- Credit: $2.82.
- Cheapest full RTX 4090: offer `47039615`, New York, $0.526/hr, 10h quote $5.26. Next offers $0.668/hr and $0.681/hr.
- `-Go` aborts when credit is under $5 or the 10h quote exceeds credit. Top up before go. Do not use `-AllowLowCredit` to start a job the balance cannot finish.
- First post-fix launch stays `WATCHDOG_DRY=1` (local monitor is the only destroyer). Seq 4608, peft, `SFT_EXPORT=0`.

## Ops next
Add funds so the balance covers the 10h quote, then operator go. No second GPU while one session is live.
