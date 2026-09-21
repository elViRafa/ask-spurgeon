---
store_path: pretraining/vast-cpt-s6-early-stop-handoff
title: "Vast S6 early-stop — analyse + destroy (from side chat)"
summary: "Operator asked side chat to notify the **waiting principal CPT session**: analyse why continue-B stopped improving, and **destroy the idle Vast pod** if that makes sense (it does)"
priority: low
tags: [cpt, s6, vast, resolved]
schema_version: 1.3
last_updated: "2026-09-18T11:16:07-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_session.json, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/vast_cpt_monitor.log]
---

# Principal session — act now (side-chat handoff 2026-09-18)

Operator asked side chat to notify the **waiting principal CPT session**: analyse why continue-B stopped improving, and **destroy the idle Vast pod** if that makes sense (it does).

## Live facts
- Instance **51416115** (`cpt-s6-continue-b`) still **running / billed** ~$0.59/hr — GPU **idle** (0% / 0 MiB).
- Training **finished** via `COMPOSITE EARLY-STOP @ step 2400/4128` (not a crash, not half-corpus).
- Full corpus was packed: 51417 docs → `packed_epoch_steps=4128`. Resume from **2050**; stop at **2400**.
- Best saved adapter = **checkpoint-2050** (`eval_spurgeon_loss` **2.4987**). Post-2050 steps did **not** beat that.
- Local fetch path: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/` — monitor was mid-scp after stop; **re-fetch LoRA + run_config + log before destroy** (local `theology_cpt_lora` mtime may predate the finish).

## Why it stopped / why not improving (analyse this)
Continue-B composite early-stop (on by design):
- metrics: `eval_spurgeon_loss` + `eval_mix_loss`
- patience=2, epsilon=0.005, min_steps≈0.4×4128≈1652

After HF resume from 2050, Spurgeon holdout **spiked** then only partially recovered:
- 2050: **2.4987** (best overall / what was saved)
- 2075: **2.618** (spike right after resume)
- 2325: 2.5115 (composite window “best”)
- 2350–2400: gains &lt; epsilon → flat streak=2 → halt

So: full-corpus schedule, intentional early-stop; continued steps after 2050 did not improve the kept LoRA.

## Required principal actions (in order)
1. Confirm remote log still shows early-stop + `OK: saved LoRA matches best_model_checkpoint`.
2. `vast_cpt_fetch.ps1` (or finish monitor fetch) — ensure `fetch/theology_cpt_lora`, `cpt_train.log`, `theology_cpt_run_config.json`, complete ckpts.
3. **Destroy instance 51416115** (`fine_tuning/scripts/vast_destroy.ps1`) — stop credit burn. Do not leave idle 4090 up for analysis.
4. Write analysis: resume spike root cause (optimizer/state, LR continue, eval noise, composite vs HF best at 2050); decide C-eval vs keep Hub v2; **no Hub overwrite** yet.
5. Update `pretraining/cpt-current` + session journal.

## Do not
- Re-rent / resume another B until analysis recorded.
- `S6_FRESH_START`.
- Overwrite Hub v2.

## Resolved 2026-09-18 (principal)
1. Re-ran `vast_cpt_fetch.ps1` — complete.
2. Destroyed **51416115**; `instances=[]`.
3. Analysis written: `pretraining/vast-cpt-s6-resume-spike-analysis`. Canonical LoRA nested path SHA `6aab9194…` (=2050). Next = C-eval; Hub v2 kept.

## Closed for next session
Fetch + destroy + analysis done. **Do not** re-open destroy/fetch. Next session follows `pretraining/cpt-next-session-handoff` → **C-eval only**.
