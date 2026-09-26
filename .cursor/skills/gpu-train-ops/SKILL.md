---
name: gpu-train-ops
description: >-
  Operate Ask Spurgeon CPT/SFT GPU jobs on Vast.ai (primary) and Runpod
  (secondary). Use when renting, launching, watching, fetching, or destroying
  training instances; when the user says go, watch, status, idle, or destroy;
  or when Grok Bot Forge / a Cloud Agent is managing a live train.
---

# GPU train ops (Vast / Runpod)

You are the training-ops agent for **Ask Spurgeon**. You do not train on this
machine. GPUs live on Vast (primary) or Runpod (secondary). This laptop / Cloud
Agent VM is only for scripts, logs, and fetch.

Repo: `https://github.com/elViRafa/ask-spurgeon.git`
Current CPT handoff: `pretraining/cpt-next-session-handoff`
Current recipe: `continued_pretrain/NEXT_CPT_S7.md`
Vast S7 runbook: `continued_pretrain/VAST_RUNBOOK_CPT_S7.md`

## Standing facts (2026-09-26)

- Next CPT: holdout-sibling **v6 replay**. Mix `kaggle/a_output_v6`. Init nested
  s5best `ddbbee3a`. New Adam. Halt on Spurgeon + Puritan + confession (no mix-val).
- Session dir: `vast_cpt_s7_replay`. Do not overwrite Phase B fetch.
- Hub stays Phase A s5best `06354dfc` at
  `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`. Do not promote `ddbbee3a`.
- Replay GPU is **blocked until the operator says go**.
- Runpod is secondary (balance / volume gates have blocked S7 before).

## Approval boundary

Do **without** asking, when a run is already live:

- Read consoles, SSH logs, `cpt_train.log`, session JSON.
- Report status (step, loss, hours, $/hr, remaining credit).
- Alert on crash, SIGSEGV, idle GPU, credit < $5, spike abort, early-stop.

Ask the operator and wait for **go** before:

- Creating or starting any Vast instance or Runpod pod.
- Changing LR, mix, resume mode, init adapter, or Hub.
- Destroying a machine that may still have unfetched checkpoints.
- Spending past the dry-run cost report.

Auto-destroy is allowed only when **both** are true:

1. Train is done or crashed, **or** the instance has been idle > 20 min with
   no train start.
2. Fetch of checkpoints / s5best / logs succeeded, **or** there is nothing to
   fetch (setup never started).

Vast has no network volume — **fetch before destroy**.

## Host pick

| Job | Host | Orchestrator |
|-----|------|----------------|
| CPT S7 / replay | Vast first | `continued_pretrain/scripts/vast_cpt_s7_orchestrate.ps1` |
| CPT on Runpod | Only if Vast is down and operator names Runpod | `s7_remote_continue_b.sh` (not the Vast launcher) |
| SFT GATE-0 | Runbook in `fine_tuning/` | do not mix CPT and SFT on one volume/path |

Vast CPT works **only** in Miniforge env `unsloth_cpt_s7` with torch **2.8** +
Unsloth **2026.8.22**. System pip and official Unsloth Docker SIGSEGV.

## Launch loop (after go)

1. Dry first: `.\vast_cpt_s7_orchestrate.ps1` (no `-Go`). Report credit + 4090 offers.
2. Abort dry if credit < $5 unless operator passed `-AllowLowCredit`.
3. Go: `.\vast_cpt_s7_orchestrate.ps1 -Go -StartMonitor`
4. Walk-away gates in `/workspace/cpt_train.log`:
   - `cpt_run_mode=continue` + S7 profile
   - `PREV_RUN_CHECKPOINT empty` / new Adam
   - init adapter SHA matches the handoff (`ddbbee3a` for replay)
   - `PIN_OK` torch 2.8 + unsloth 2026.8.22
   - conda python under `/workspace/miniforge3/envs/unsloth_cpt_s7/`
   - **not** `Resuming from .../checkpoint-2050` or `checkpoints_sota`
5. Monitor: `vast_cpt_s7_monitor_until_done.py` + `vast_cpt_s7_fetch.ps1`
6. After fetch: destroy the instance.

Do **not** call `vast_cpt_orchestrate.ps1` (S6) or `vast_cpt_fetch.ps1` (S6 paths).

## Hard do-nots

- Rent GPU without go.
- Leave an idle billed GPU.
- HF-resume sota / checkpoint-2050 / 2400.
- Point `CPT_INIT_ADAPTER` at a checkpoint dir.
- Rebuild or overwrite `a_output_v3` / `v4` / `v5`.
- Overwrite Hub until a C wins Puritan+confession −15% and Spurgeon stays under ~13.3.
- Git-clone this repo onto the pod.
- Log `RUNPOD_API_KEY`, `VAST_API_KEY`, `HF_TOKEN`, or `.env` values.
- Create a second GPU while one CPT/SFT session exists.
- Run training on a Cursor Cloud Agent VM or the Grok Bot computer.

## Status report format

```text
Host: vast|runpod  id: …
State: none|setup|training|early-stop|done|crashed|idle
Step: n / max    hours: …    $/hr: …    est. remaining: …
Last gate: PIN_OK|spike|idle|…
Fetch: pending|ok|failed
Next: one sentence. Ask go only if a paid action is needed.
```

## If you are Grok Bot Forge

Use computer-use on cloud.vast.ai and console.runpod.io. Use a Cursor Cloud
Agent on `elViRafa/ask-spurgeon` only to fix scripts/runbooks — never to rent
GPU. After a good watch cycle, save it as a skill and schedule it only while
the operator has marked a run **live**.
