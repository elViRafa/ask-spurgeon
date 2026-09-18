# Vast.ai — CPT S6 continue-B (full corpus v3)

**This session / default:** prepare and dry-search only. **Do not rent** until the operator says go.

Unsloth CPT on Vast works **only** inside Miniforge (`unsloth_cpt`) with **torch 2.11+cu126 pip-installed into that env**. System pip and official Unsloth Docker are known-fail (SIGSEGV / broken SSH).

## What this run is

Resume **S6 continue-B** on the **full packed mix** (`a_output_v3`, 51 417 train docs, ~91.3M verified tokens, 4128 packed steps). Not a 3-step smoke. Not a from-scratch 1e-5 rerun. Not Hub overwrite.

| Item | Value |
|------|--------|
| Mode | `CPT_RUN_MODE=continue` + HF resume `checkpoint-2050` |
| Init adapter | S5 LoRA SHA256 `ef4df3a3…c303` |
| Resume | local complete ckpt **2050/4128** (optimizer present). `checkpoint-2100` is **not** local |
| Image | `nvidia/cuda:12.4.1-devel-ubuntu22.04` + Miniforge |
| GPU | full RTX 4090 (`gpu_frac>=1`, `cuda_max_good>=12.6`) |
| Disk | 120 GB instance disk |
| Fetch / payload | **`continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6`** on **C:** (with corpus + LoRA + ckpt) |
| Hub v2 | keep until finished B **and** winning C |

Do **not** set `S6_FRESH_START=1` over this checkpoint.

## Dry (this session / anytime)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_orchestrate.ps1
.\vast_cpt_orchestrate.ps1 -Pack    # optional: build D:\...\payload.tar for faster scp
```

## Go (next session only)

```powershell
cd continued_pretrain\scripts
.\vast_cpt_orchestrate.ps1 -Go -StartMonitor
```

Walk away only after `/workspace/cpt_train.log` shows:

- `cpt_run_mode=continue` `composite_stop=True`
- `gpu_profile=ampere` `trainer_bf16=True`
- `Resuming from .../checkpoint-2050`
- `packed_epoch_steps=4128` `abort_spurgeon_step=0`
- `INIT_ADAPTER SHA256 OK`
- conda python under `/workspace/miniforge3/envs/unsloth_cpt/`

## After B

C eval vs Ampere base **and** Hub v2. Keep Hub v2 if worse. Merge still requires §5 −15% on puritan+confession.

## Payload (already packed)

`continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/payload.tar` (~4.6 GB) has corpus + S5 LoRA + complete `checkpoint-2050` + train scripts. Sync uploads this single file when present. All train inputs stay on **C:**.

## Cost / credit

Remaining ~2078/4128 steps x ~8-12 s + Miniforge setup ~20-40 min ≈ **8-12 h** wall.

Live marketplace (2026-09-16 dry search, **no rent**):

| GPU | Cheapest on-demand | 10 h ballpark |
|-----|--------------------|---------------|
| RTX 4090 NL | ~$0.54/hr (offer ids rotate) | ~$5-7 |
| RTX 3090 TW | ~$0.24/hr (offer ids rotate) | ~$2.5-3.5 |

`-Go` aborts if credit < **$5** unless `-AllowLowCredit`. A 3090 is Ampere 24 GB (same `GPU_PROFILE=ampere`); slower than 4090 but fits a ~$3 balance. Destroy the instance when done; Vast has no Runpod network volume.

## Related

- Smoke PASS: `kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke_conda.log`
- Runpod S6: `CORPUS_V3_S6_CONTINUE_CHECKLIST.md` (volume `7hb931c5oe` is currently 404 / blocked)
