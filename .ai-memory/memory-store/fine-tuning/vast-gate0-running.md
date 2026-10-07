---
store_path: fine-tuning/vast-gate0-running
title: "Vast GATE-0 SFT running (post eval-OOM relaunch)"
summary: "**Updated:** 2026-09-05 ~22:25 ET"
priority: high
tags: [vast, sft, gate0, live, peft]
schema_version: 1.3
last_updated: "2026-09-06T02:28:24-04:00"
evidence: [fine_tuning/scripts/train_sft_sota.py, fine_tuning/kaggle/vast_sft_session.json, fine_tuning/scripts/vast_monitor_until_done.py]
review_status: stale
---

# Vast GATE-0 SFT — running (post eval-OOM relaunch)

**Updated:** 2026-09-05 ~22:25 ET

## Instance
- **instance_id:** `50011937` (keep; do not destroy)
- **SSH:** `root@75.129.99.99:5250` key `%USERPROFILE%\.ssh\runpod_cpt`
- **Rate:** ~$0.334/hr | Vast `show user` credit ~$8.21 (operator had cited ~$3.26 — API higher)
- **Session:** `fine_tuning/kaggle/vast_sft_session.json`

## Incident
- First PEFT run OOMed at **step 20** during `Trainer.evaluate` (`logits.float()` needed ~15GiB extra on 24GB).
- GPU went idle; empty `spurgeon_qa_lora_v2/checkpoints` (save_steps was 40).
- OOM log archived: `/workspace/sft_train_oom_step20.log`

## Fix + relaunch
- `train_sft_sota.py`: default `SFT_EVAL_STRATEGY=no`; `per_device_eval_batch_size=1`; no `eval_dataset` when off; `load_best_model_at_end` only if eval on; `gradient_checkpointing` + `empty_cache`; optional resume via `SFT_RESUME_FROM_CHECKPOINT` / latest checkpoint-*.
- Env: `SFT_BACKEND=peft`, seq **2048**, batch **1**, accum **16**, `SFT_EVAL_STRATEGY=no`, `SFT_SAVE_STEPS=40`.
- **Restarted:** yes | **Resume-from:** none (fresh) | merge already present.
- Monitor killed during fix (would have seen crash markers), restarted PID in `vast_monitor.pid`; log `vast_monitor.log`.

## Status at relaunch
- Train PID live; `eval_strategy no`; progress bar `0/408`; ~17GB VRAM during train.
- Est. remaining ~408×~82s ≈ 9.3h ≈ **~$3.1** at $0.334/hr vs credit ~$8.2 → headroom OK if no more idle.
