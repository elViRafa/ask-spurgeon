---
store_path: pretraining/cpt-v2-pre-train-analysis-checklist
title: "CPT v2 pre-train analysis checklist (closed)"
summary: "Analysis/check session finished"
priority: high
tags: [cpt, runpod, analysis, checklist, handoff]
schema_version: 1.3
last_updated: "2026-08-26T23:15:31-04:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/RUNPOD_RUNBOOK.md]
---

# CPT v2 — pre-train analysis checklist (CLOSED 2026-08-26)

Analysis/check session finished. **Next session trains on Runpod.** Do not re-run this checklist as a blocker.

## Decisions locked
- **TRAIN_EMBEDDINGS:** True (official CPT). OOM hatch: embeds off before dropping GDN.
- **Mix 0.164:** not rebuilt.
- **MAX_STEPS:** after pack, set to `PACKED_EPOCH_STEPS` (one padded epoch; ~674 on B v13 10779 rows / 16).
- **Abort-at-50:** `AbortIfSpurgeonRisesCallback` stops if `eval_spurgeon_loss` at 50 > 25. Flat/equal continues.
- **§5 −15%:** long-term bar unchanged. This $15 job is a ~15.6M-token **probe**; ship later only if holdout PPL beats base.

## Checks done (this session)
- Tests: `test_manual_pack.py`, `test_cpt_runtime.py`, `test_kaggle_path_resolve.py` PASS (incl. abort helper).
- Local `kaggle/a_output`: theology_dataset (8162/83 from A log) + HF holdouts + `catechism_mcq.json` present. `a_output` ~51 MB. 50 GB volume still enough.
- `GPU_PROFILE` auto (not hardcoded Ampere). C install now picks `kaggle-new` vs `colab-new` from `/kaggle/working`.
- `--install` exits after pip.
- Runpod MCP: 0 pods, 0 volumes (auth OK). No provision this session.

## Recipe unchanged
`one_doc_padded`, `PAD_TO_MAX=False`, `LORA_GDN=True` (`in_proj_qkv`/`in_proj_z`/`out_proj`). Fresh first Runpod job (`PREV_RUN_CHECKPOINT=` empty).
