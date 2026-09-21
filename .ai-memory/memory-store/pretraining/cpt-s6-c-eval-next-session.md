---
store_path: pretraining/cpt-s6-c-eval-next-session
title: "S6 C-eval session playbook (post-Vast B)"
summary: "Score the finished Vast S6 best LoRA (HF best **checkpoint-2050**) against Ampere bf16 base and Hub v2"
priority: low
tags: [cpt, s6, c-eval]
schema_version: 1.3
last_updated: "2026-09-18T11:59:01-03:00"
evidence: [continued_pretrain/scripts/eval_cpt_sota.py, continued_pretrain/scripts/s6_run_c_eval.ps1, [REDACTED_SECRET].md, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_run_config.json]
---

# S6 C-eval — next-session playbook

## Goal
Score the finished Vast S6 best LoRA (HF best **checkpoint-2050**) against Ampere bf16 base and Hub v2. Decide keep-vs-replace Hub. **No training.**

## Pin
- Adapter dir: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/`
- Adapter digest (full): `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c`
- Set env `EXPECTED_ADAPTER_SHA256` to that digest before `eval_cpt_sota.py` (script default is Hub v2 — wrong for this C).
- Hub v2 reference digest prefix: `319d17a3…1478`
- Verify with `sha256sum` on `adapter_model.safetensors` before load.
- Outer `fetch/theology_cpt_lora/` without nested folder is **stale S5** — do not evaluate that.

## How
1. Provision short-lived Ampere 24 GB (Vast or Runpod). Prefer proven Miniforge/Unsloth stack if on Vast.
2. Sync adapter + holdouts (`a_output_v3/theology_holdouts`) + `eval_cpt_sota.py`.
3. Export `EXPECTED_ADAPTER_SHA256` to the **6aab9194…** digest above.
4. Run C; save metrics under e.g. `kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/`.
5. Destroy GPU immediately after fetch.

Automation hint: `continued_pretrain/scripts/s6_run_c_eval.ps1` (adapt paths/SHA for Vast fetch tree). Checklist pattern: `CORPUS_V3_S5_C_CHECKLIST.md`.

## Success criteria / policy
- Report PPL Δ on spurgeon / puritan / confession / general vs base **and** vs Hub v2 numbers.
- **Keep Hub v2** unless this C clearly wins the scorecard.
- Merge still blocked until §5 −15% on puritan+confession (do not merge in the C session).
- Optional: note Aug-28 partial C of same digest (`s6_c_eval/theology_cpt_eval_metrics.json`) for comparison, but ship a fresh post-Vast run.

## After C
- If worse/tie → Hub v2 stays; optional later B with lower continue LR (see `vast-cpt-s6-resume-spike-analysis`).
- If wins → Hub overwrite is a **separate** approved session.

## Outcome (2026-09-18)
Done on Vast RTX 4090 instance 51446613 (destroyed). Probe **FAIL** — adapter worse than Ampere base on all buckets (spurgeon +27.9%). **Keep Hub v2.** Metrics under `vast_cpt_s6/c_eval/`. Scripts: `vast_cpt_c_eval.ps1` + `vast_remote_c_eval.sh`. Full scorecard: `pretraining/cpt-s6-c-eval-complete`.
