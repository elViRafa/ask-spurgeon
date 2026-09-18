---
store_path: pretraining/c-drive-cleanup-2026-09-16
title: "Freed C: by pruning S6 ckpts and moving GATE-0 models to D:"
summary: "Freed **~1.4 GB to ~39 GB** on C: without deleting the S6 resume checkpoint or breaking local paths"
priority: medium
tags: [disk, c-drive, checkpoints, vast]
schema_version: 1.3
last_updated: "2026-09-16T11:23:15-03:00"
---

# C: disk cleanup (2026-09-16)

Freed **~1.4 GB to ~39 GB** on C: without deleting the S6 resume checkpoint or breaking local paths.

## Deleted (stale only)
- Old `s6_continue_b/checkpoints_sota/checkpoint-*` except complete **checkpoint-2050**
- Nested incomplete ckpts (1150/1175/1200/1400/2000/2025)
- `theology_cpt_v2_merged_hf.incomplete.bak`

## Moved to D: (junctions left in repo)
`fine_tuning/kaggle/vast_sft_gate0/{theology_cpt_v2_merged_hf,spurgeon_qa_merged_hf,spurgeon_qa_gguf}` now live under `D:\\search-sermons-cpt\\vast_sft_gate0\\` with directory junctions at the old paths.

## Kept
- `checkpoint-2050` on C: (resume source)
- `D:\\search-sermons-cpt\\vast_cpt_s6\\payload.tar`

## 2026-09-16 later

Moved **`a_output_v3` corpus back onto C:** as a real directory (was junction → `D:\search-sermons-cpt\a_output_v3`). D: copy removed. GATE-0 merged/GGUF folders remain on D: via junctions. `checkpoint-2050` and Vast `payload.tar` unchanged.

## Train assets on C: (2026-09-16)

Operator wants **all CPT train inputs on C:**.

Moved onto C: as real directories (no junctions):
- `kaggle/a_output_v3` corpus
- `kaggle/runpod_cpt_v3/theology_cpt_lora` (S5)
- `vast_cpt_s6/payload.tar` + results dir under `kaggle/runpod_cpt_v3/vast_cpt_s6`

Scripts default `VAST_LOCAL_RESULTS_DIR` to that C: path. Local readiness **PASS**. C: ~31 GB free. GATE-0 SFT merged/GGUF remain on D: (not needed for CPT S6).
