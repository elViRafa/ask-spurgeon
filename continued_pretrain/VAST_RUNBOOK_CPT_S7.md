# Vast.ai — CPT S7 Phase A (continue from S6 LoRA)

**Primary GPU path for S7 Phase A.** Recipe: [`NEXT_CPT_S7.md`](NEXT_CPT_S7.md).

Unsloth CPT on Vast works **only** inside Miniforge (`unsloth_cpt_s7`) with **torch 2.8.0+cu126**
and **Unsloth 2026.8.22** pip-installed into that env (same pin as stack-isolation C).
System pip and official Unsloth Docker are known-fail (SIGSEGV / broken SSH).

Do **not** run `s7_remote_continue_b.sh` on Vast (that is the Runpod system-python launcher).

## What this run is

| Item | Value |
|------|--------|
| Mode | `CPT_RUN_MODE=continue` + `CPT_CONTINUE_PROFILE=s7` |
| Init adapter | S6 Hub SHA256 `6aab9194…` (flattened nested fetch LoRA) |
| Optimizer | **new Adam** — `PREV_RUN_CHECKPOINT=` (empty string) |
| Checkpoints | `/workspace/checkpoints_s7` only (never auto-resume `checkpoints_sota`) |
| max_steps | **2064** |
| Image | `nvidia/cuda:12.4.1-devel-ubuntu22.04` + Miniforge |
| GPU | full RTX 4090 (`gpu_frac>=1`, `cuda_max_good>=12.6`) |
| Disk | **120 GB** instance disk |
| Results | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7` |
| Hub v2 | keep until finished B **and** winning C |

## Dry (no rent)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s7_orchestrate.ps1
.\vast_cpt_s7_orchestrate.ps1 -Pack    # optional: build payload.tar
```

Checks: mix `23dd…`, nested LoRA `6aab…`, launcher policy, Vast credit + 4090 offers.

## Go (after dry credit/offer report)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_s7_orchestrate.ps1 -Go -StartMonitor
```

`-Go` aborts if credit &lt; **$5** unless `-AllowLowCredit` (e.g. 3090 + `-OfferId`).

Mid-S7 interrupt on the same instance:

```powershell
.\vast_cpt_s7_launch.ps1 -Resume
# or on-box: S7_RESUME=1 bash /workspace/vast_cpt_s7_remote_continue_b.sh
```

## Walk-away gates (`/workspace/cpt_train.log`)

- `cpt_run_mode=continue` + S7 profile (LR 2e-6, max_steps 2064, `checkpoints_s7`)
- `PREV_RUN_CHECKPOINT empty` / new Adam
- `INIT_ADAPTER SHA256 OK` for `6aab…`
- `PIN_OK` torch 2.8 + unsloth 2026.8.22
- conda python under `/workspace/miniforge3/envs/unsloth_cpt_s7/`
- **Not** `Resuming from .../checkpoint-2050`

## Fetch / destroy

Monitor (`vast_cpt_s7_monitor_until_done.py`) polls, pulls via `vast_cpt_s7_fetch.ps1`
(`checkpoints_s7`, `theology_cpt_lora`, `theology_cpt_lora_s5best`, `s5_best.json`, logs),
then destroys the instance. Vast has no network volume — fetch before destroy.

Do **not** use `vast_cpt_fetch.ps1` (S6 — hardcodes `checkpoints_sota`).

## After B — C eval

Use isolation-C pin (torch 2.8 / Unsloth 2026.8.22). Prefer fetched
`theology_cpt_lora_s5best` when present; pin `EXPECTED_ADAPTER_SHA256` to that artifact.
Keep Hub S6 unless §5 / scorecard win.

## Do not

- Call `vast_cpt_orchestrate.ps1 -Go` (S6) for this job
- Ship or HF-resume `checkpoints_sota` / 2050 / 2400
- Install torch 2.11 or floating `unsloth.git`
- Rebuild mix / overwrite `a_output_v3` or `a_output_v4`
- Overwrite Hub until winning C

## Cost ballpark

Phase B v5: ~955 steps × ~8–12 s + Miniforge ~30–40 min ≈ **3–5 h** wall on 4090.
At ~$0.50–0.55/hr ≈ **$2–3**. Destroy when done.

## Current continue — holdout-sibling replay (v6)

Phase B isolation C on nested s5best `ddbbee3a` was Spurgeon **12.39** (−13.4%),
Puritan **5.50** (−8.9%), confession **5.25** (−6.4%) vs Ampere base. Hub `06354dfc`
stays until a C wins both Puritan and confession without Spurgeon past ~13.3.

Next train (operator go only): copy **`kaggle/a_output_v6`**, init nested
`ddbbee3a`, new Adam, halt on Spurgeon + Puritan + confession (no mix-val).
Session/results: `vast_cpt_s7_replay`. Do not overwrite v3 / v4 / v5 or Hub.
