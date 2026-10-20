---
store_path: fine-tuning/ot-softstrip-resft-live-2026-10-20
title: "OT soft-strip re-SFT live on Secure 4090"
summary: "- Honesty teacher: 53 accept / 7 reject / not halted (`--honesty --apply --limit 60`)"
priority: high
tags: [sft, open-theology, runpod, live]
schema_version: 1.3
last_updated: "2026-10-20T10:28:56-03:00"
---

# OT soft-strip re-SFT live (2026-10-20)

## Data (before GPU)

- Honesty teacher: 53 accept / 7 reject / not halted (`--honesty --apply --limit 60`)
- Merged into `accepted.jsonl` → 891; soft-strip; export **train 887** / eval 40
- Dirty OT sft vs PINNED_SHA `d0b1464` → `-AllowDirtySync`

## GPU

- Host: RunPod Secure RTX 4090 `r01fu8rxdszh4m` US-IL-1 @ **$0.89/hr**
- SSH direct `203.57.40.146:10223`
- Community 4090: no stock; first Secure `re5vcu9ojlpw4q` bad-host SSH timeout → destroyed
- Stale Oct-17 `sft_smoke.log` false-triggered SMOKE_BEFORE_TRAIN_FAILED → cleared; attach monitor `runpod_sft_s8_weighted_monitor_attach.ps1`
- Patched `sft_remote_train_s8_weighted.sh` to truncate smoke log at supervisor start (not yet on this pod)

## Walk-away gates (confirmed)

- `SFT_OPEN_THEOLOGY=1`, `OPEN_THEOLOGY_ROWS 887`, `MIX_ROWS 4151`
- `RAG_PROMPT_OK` / `THEOLOGY_PROMPT_OK`
- Base S8 merged; `SFT_BACKEND: unsloth`; `SFT_EXPORT=0`
- Smoke OK seq 4608; `FULL_TRAIN`; S3 masking OK; drop 0
- ~12–14 s/it; 520 steps; loss ~1.51 @ step 10; GPU 100% / ~15.8 GiB

## Next

1. Forge long watch (`run is live` on `r01fu8rxdszh4m`)
2. After fetch+destroy: `runpod_sft_s8_weighted_open_theology_eval.ps1 -Go` → Gemini judge on PC
3. Compare to 2026-10-19 `weak_not_useful_yet` (correctness/honesty 2.525)
4. Still out of scope: RAG refusal / Hub / `spurgeon-qa-v2`
