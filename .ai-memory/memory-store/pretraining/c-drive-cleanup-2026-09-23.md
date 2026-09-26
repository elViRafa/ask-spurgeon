---
store_path: pretraining/c-drive-cleanup-2026-09-23
title: "Freed C: by pruning Projetos caches and archiving stale CPT"
summary: "Freed **C: from 2.0 GB to 82.0 GB** (D: still 480 GB free)"
priority: medium
tags: [disk, c-drive, checkpoints, projetos, cleanup]
schema_version: 1.3
last_updated: "2026-09-23T13:41:02-03:00"
evidence: [continued_pretrain/kaggle/a_output_v5, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_lora_s5best, fine_tuning/kaggle/vast_sft_gate0]
---

# C: / Projetos disk cleanup (2026-09-23)

Freed **C: from 2.0 GB to 82.0 GB** (D: still 480 GB free). Phase B inputs stayed on C: as real directories.

## Deleted (regenerable)
`node_modules` plus `android/app/build`, `android/app/.cxx`, `android/.gradle` in:
- `C:\Users\rafael\Projetos\controle-medico`
- `C:\Users\rafael\Projetos\irglobal-app`
- `C:\Users\rafael\Projetos\app-us`
- `C:\Users\rafael\Projetos\ai-personal`

Android `src` and keystores left in place. Reinstall with `npm install` / Gradle when those apps are opened again.

## Deleted (superseded CPT/SFT)
- `vast_cpt_s7/fetch/checkpoints_s7/` (Phase A intermediates)
- `vast_cpt_s7/payload.tar` (repack on operator go for v5)
- `vast_cpt_s7/fetch/theology_cpt_lora/` (not s5best)
- `kaggle/b_output` and `b_output_v6`
- `runpod_sft_gate0/theology_cpt_v2_merged_hf` (incomplete Runpod copy; complete merge remains on D: via junction)

## Moved to D:\search-sermons-cpt\archive-2026-09-23\
- `vast_cpt_s6/` (15.6 GB)
- `s6_continue_b/` (5.6 GB)
- `runpod_cpt_v3_theology_cpt_lora/` (S5, 1.4 GB)
- `runpod_cpt_v2/` (1.4 GB)
- `models/unsloth.F16.gguf` (5.8 GB)
- `models/spurgeon_phase1_merged_hf.F16.gguf` (5.8 GB)
- `models/spurgeon-qa-v2.Q4_K_M.gguf` (2.5 GB)

File symlink for `continued_pretrain/models/unsloth.F16.gguf` failed (needs admin). Ollama `FROM ./unsloth.F16.gguf` will not resolve until an admin `mklink` is created or the Modelfile is pointed at the D: archive path.

## Kept on C:
- `a_output_v5` (real dir) + frozen `a_output_v3` / `a_output_v4`
- `vast_cpt_s7/fetch/theology_cpt_lora_s5best/` (Hub production)
- `search-sermons/.venv`
- GATE-0 junctions under `fine_tuning/kaggle/vast_sft_gate0/` → `D:\search-sermons-cpt\vast_sft_gate0\`

Left alone: `transcriptor-hosp`, `search-sermons/.git`.
