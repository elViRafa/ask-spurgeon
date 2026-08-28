---
store_path: pretraining/kaggle-c-eval-adapter-mount
title: "Kaggle C_eval kernel-source adapter mount"
summary: "C v1 failed `FileNotFoundError: CPT adapter not found` even though B output was mounted"
priority: high
tags: [kaggle, cpt, eval, adapter]
schema_version: 1.3
last_updated: "2026-08-24T09:24:55-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/test_kaggle_path_resolve.py]
---

# Kaggle C_eval adapter path (2026-08-24)

C v1 failed `FileNotFoundError: CPT adapter not found` even though B output was mounted. Kaggle kernel sources land at `/kaggle/input/notebooks/<user>/<slug>/`, not `/kaggle/input/<slug>/`.

C_eval now walks `/kaggle/input` for `adapter_config.json` under `theology_cpt_lora` / `checkpoints_sota` (prefers LoRA, then checkpoint-50). Skip `hf_home` / caches. Holdouts prefer B `theology_holdouts` HF dirs; corpus `*_holdout.txt` is fallback.

Push C with `--accelerator NvidiaTeslaT4` and `kernel_sources: rafaelvieira1/theology-cpt-v2-b-training-sota`.
