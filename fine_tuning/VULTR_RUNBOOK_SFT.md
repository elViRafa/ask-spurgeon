# Vultr runbook — SFT v2 GATE-0 (Qwen3.5-4B + Hub v2 CPT merge)

One Cloud GPU VM: remake GATE-0 merged HF, train SFT LoRA, fetch artifacts, **delete** the instance.

Companion: [`RUNPOD_RUNBOOK_SFT.md`](RUNPOD_RUNBOOK_SFT.md) (volume + MCP path). Do not clone that watcher stack here.

## Why this path

- RunPod GATE-0 crashed on `ScalingType` (torch 2.8 vs trl/torchao). Credits/capacity may be gone.
- Local `fine_tuning/kaggle/runpod_sft_gate0/theology_cpt_v2_merged_hf/` is **weights-only** (no tokenizer). Unusable.
- Vultr has **no cheap network volume**. Fetch before destroy. Stopped GPU VMs still cost — always **delete**.

## GPU pick

Use `vcg-a16-12c-128g-32vram` in **blr** (~$0.94/hr, 128 GB RAM, 700 GB disk).

This is **2× ~16 GB A16 devices**, not one 32 GB GPU. Unsloth uses GPU 0. Scripts set:

- `SFT_GPU_PROFILE=a16`
- `CUDA_VISIBLE_DEVICES=0`
- `SFT_PER_DEVICE_BATCH=1`
- `SFT_GRAD_ACCUM=16`

Merge tries Unsloth GPU bf16 first; on OOM it falls back to CPU PEFT (`merge_cpt_lora.py`). Prefer A40 24 GB if it returns to stock.

Skip 2/4/8/12 GB VDI slices.

## Operator before first provision

1. Vultr dashboard → API → allowlist the agent public IP (current: check `vultr_probe_api.ps1`) **or** create Ubuntu 24.04 **GPU** on that plan in Bangalore and pass `-SshHost`.
2. SSH pubkey `%USERPROFILE%\.ssh\runpod_cpt.pub` (scripts upload it if missing on the account).
3. Credits headroom ~$10+. Never log `VULTR_API_KEY` / `HF_TOKEN`.
4. If create fails with *open a support request* / Max Instance Cost too low: request limit increase (~**$700–1000/mo** max instance cost for A16 32vram). Limit raise is a ceiling only — not auto-spend.

## Spend risk controls (mandatory)

Raising account limits does **not** increase the bill by itself. You pay only while a GPU instance exists (~$0.94/hr for A16). Stopped GPUs still bill — always **delete**.

| Control | Rule |
|--------|------|
| Instance count | One `sft-gate0` VM only; list/destroy leftovers before provision |
| Fail path | Setup / inject / launch / no nvidia-smi → destroy immediately |
| Success path | Fetch artifacts → `vultr_destroy.ps1` (DELETE, not stop) |
| Wall clock | Monitor ≤ **8h**; then fetch + destroy |
| Budget | Expect ~**$8–12** for a good run; ~$23 if left 24h by mistake |
| Limits request | Ask only for what Cloud GPU needs (~$700–1000/mo); do not overshoot |

Agent memory: `fine-tuning/vultr-spend-risk-controls`.

## Local prep

```powershell
python fine_tuning/scripts/12_package_kaggle_qa_mix.py
python fine_tuning/scripts/13_sft_local_readiness.py --gate0
```

`vultr_orchestrate.ps1` re-packs the zip if train is newer, then runs readiness.

## One-shot

```powershell
cd fine_tuning\scripts
.\vultr_orchestrate.ps1
```

If the API is IP-blocked, wait/allowlist then retry, or attach a console VM:

```powershell
.\vultr_orchestrate.ps1 -SshHost 1.2.3.4
```

Skip the long monitor (you must fetch + destroy yourself):

```powershell
.\vultr_orchestrate.ps1 -SkipMonitor
python .\vultr_monitor_until_done.py
```

## Manual steps (same as orchestrate)

```powershell
.\vultr_probe_api.ps1
.\vultr_provision.ps1
.\vultr_wait_ssh.ps1
.\vultr_verify_gpu.ps1
.\vultr_sync.ps1
.\vultr_inject_hf_token.ps1
.\vultr_launch.ps1
python .\vultr_monitor_until_done.py
```

On-box pipeline: `sft_remote_setup.sh` (torch **2.11.0+cu126**, `ScalingType` / trl / unsloth / CUDA smoke) → `sft_remote_merge.sh` → detached `train_sft_sota.py`.

## Env on the VM (`/workspace/.sft_env`)

```bash
export SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
export SFT_CPT_ADAPTER=/workspace/theology_cpt_lora_hub_v2
export SFT_EXPORT=0
export SFT_GPU_PROFILE=a16 CUDA_VISIBLE_DEVICES=0
export SFT_PER_DEVICE_BATCH=1 SFT_GRAD_ACCUM=16
```

Force CPU merge: `export SFT_MERGE_DEVICE=cpu` (or `python3 merge_cpt_lora.py --cpu`).

## Done markers

`/workspace/sft_train.log` contains any of:

- `SOTA SFT v2 complete`
- `Saved adapter to`
- `sft_run_config.json`

Monitor requires two consecutive not-running polls **plus** a log marker. Setup/smoke failure or traceback → fetch logs → **delete**.

## Fetch / destroy

```powershell
.\vultr_fetch.ps1 -PartialOnly   # adapter + logs; merged HF if tokenizer-complete
.\vultr_destroy.ps1              # DELETE, do not stop
```

Local dir: `fine_tuning/kaggle/vultr_sft_gate0/`

Session: `fine_tuning/kaggle/vultr_sft_session.json`

## Out of scope this pass

- F §5 eval, GGUF, Ollama, Hub upload (`SFT_EXPORT=0`)
- CPT S6 / RunPod volume `7hb931c5oe`
- Do not overwrite RunPod `/workspace/theology_cpt_lora/` or `/workspace/checkpoints_sota/` if that volume returns
