# Vast.ai runbook — SFT v2 GATE-0 (Qwen3.5-4B + Hub v2 CPT merge)

One on-demand RTX 4090 container: remake GATE-0 merged HF, train SFT LoRA, fetch artifacts, **destroy** the instance (do not stop).

Companion: [`VULTR_RUNBOOK_SFT.md`](VULTR_RUNBOOK_SFT.md) (blocked ~30 days), [`RUNPOD_RUNBOOK_SFT.md`](RUNPOD_RUNBOOK_SFT.md).

## Why this path

- Vultr Cloud GPU entitlement denied (~30 days).
- RunPod GATE-0 hit torch/`ScalingType` issues and capacity gaps.
- Same remote scripts as Vultr: `/workspace` + torch **2.11** smoke + merge + train.

## GPU pick

Search (scripts use this query — `vast_common.ps1` `$SearchQuery`):

```text
num_gpus=1 gpu_name=RTX_4090 reliability>=0.95 disk_space>=100 gpu_frac>=1 cuda_max_good>=12.6
```

- **Full GPU only** (`gpu_frac>=1`). Fractional offers NVML-spoof as 3090 and are a SIGSEGV trap.
- **Driver/CUDA:** `cuda_max_good>=12.6` required for torch 2.11+cu126 (driver 535 / CUDA 12.4 → error 804).
- **On-demand** only (not interruptible) — long SFT must not die mid-run.
- **Image:** `nvidia/cuda:12.4.1-devel-ubuntu22.04` (default in `vast_common.ps1`) + our `sft_remote_setup.sh` (unzip + Python 3.11 if needed, then torch **2.11**). Avoid huge `pytorch/pytorch` tags — they stall on pull.
- Create: `--ssh --direct --disk 100 --label sft-gate0`; onstart best-effort installs `unzip` + `python3.11` (setup.sh fail-closes if still wrong).
- Profile: `SFT_GPU_PROFILE=4090`, **`SFT_BACKEND=peft`**, `SFT_MAX_SEQ_LENGTH=2048`, `SFT_PER_DEVICE_BATCH=1`, `SFT_GRAD_ACCUM=16`.

### Unsloth on Vast → use PEFT

**Unsloth SIGSEGVs on Vast** at the first `SFTTrainer.train()` step — including on a **full** RTX 4090 (4bit and bf16). Do **not** relaunch with the Unsloth backend.

Always inject/train with:

```bash
export SFT_BACKEND=peft
```

That path is transformers `AutoModelForCausalLM` bf16 + PEFT LoRA + TRL `SFTTrainer` (no Unsloth). `vast_inject_hf_token.ps1` writes this by default so relaunches do not regress.

## Spend controls (mandatory)

Credit headroom ~**$6**. At ~$0.22–0.37/hr that is ~17–27h; target wall **≤10h** then destroy.

| Control | Rule |
|--------|------|
| Instance count | One `sft-gate0` only; destroy leftovers before rent |
| Fail path | Setup / inject / launch / no nvidia-smi → destroy immediately |
| Success path | Fetch → `vast_destroy.ps1` (DESTROY, not stop) |
| Wall clock | Monitor ≤ **10h**; then fetch + destroy |
| Budget | Expect ~**$2–5** for a good run; abort if setup burns too long |

Never log `VAST_API_KEY` / `HF_TOKEN`.

## Local prep

```powershell
python fine_tuning/scripts/12_package_kaggle_qa_mix.py
python fine_tuning/scripts/13_sft_local_readiness.py --gate0
```

`vast_orchestrate.ps1` re-packs the zip if train is newer, then runs readiness.

## Dry search (no rent)

```powershell
cd fine_tuning\scripts
.\vast_search.ps1
```

## One-shot (rent + merge + SFT)

**Only when the operator says go / rent:**

```powershell
cd fine_tuning\scripts
.\vast_orchestrate.ps1
```

Attach an already-rented instance:

```powershell
.\vast_orchestrate.ps1 -InstanceId <id>
# or after SSH is known:
.\vast_orchestrate.ps1 -SkipRent
```

Skip long monitor (you must fetch + destroy yourself):

```powershell
.\vast_orchestrate.ps1 -SkipMonitor
python .\vast_monitor_until_done.py
```

## Manual steps

```powershell
.\vast_search.ps1
.\vast_provision.ps1          # rents — only on go
.\vast_wait_ssh.ps1
.\vast_verify_gpu.ps1
.\vast_sync.ps1
.\vast_inject_hf_token.ps1
.\vast_launch.ps1
python .\vast_monitor_until_done.py
```

On-box: `sft_remote_setup.sh` → `sft_remote_merge.sh` → detached `train_sft_sota.py`.

## Env on the container (`/workspace/.sft_env`)

```bash
export SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
export SFT_CPT_ADAPTER=/workspace/theology_cpt_lora_hub_v2
export SFT_EXPORT=0
export SFT_GPU_PROFILE=4090
export SFT_BACKEND=peft
export SFT_MAX_SEQ_LENGTH=2048
export SFT_PER_DEVICE_BATCH=1 SFT_GRAD_ACCUM=16
```

Force CPU merge: `export SFT_MERGE_DEVICE=cpu`.

**Do not** set `SFT_BACKEND=unsloth` on Vast. Seq 4096 + batch 2 OOMs on PEFT bf16; the working GATE-0 recipe is 2048/1/16.

## CLI access to the GPU container

CLI lives at `.venv\Scripts\vastai.exe` (activate `.venv` or use the full path). API key: `.env` `VAST_API_KEY` or `~\.config\vastai\vast_api_key`.

SSH private key: `%USERPROFILE%\.ssh\runpod_cpt` (public key registered on Vast as `runpod-cpt-v2`).

```powershell
cd c:\Users\rafael\Projetos\search-sermons
.\.venv\Scripts\Activate.ps1

# List rented instances
vastai show instances -v --raw

# SSH URL for instance ID → ssh://root@HOST:PORT
vastai ssh-url <INSTANCE_ID>
```

Interactive shell:

```powershell
ssh -i $env:USERPROFILE\.ssh\runpod_cpt -p <PORT> root@<HOST>
```

One-shot remote command / copy:

```powershell
vastai execute <INSTANCE_ID> -- "nvidia-smi"
scp -i $env:USERPROFILE\.ssh\runpod_cpt -P <PORT> -r .\file root@<HOST>:/workspace/
```

Inside the container:

```bash
tail -f /workspace/sft_launch.log /workspace/sft_train.log
```

Destroy when done (stopped instances still bill storage — always destroy):

```powershell
vastai destroy instance <INSTANCE_ID>
# or:
.\vast_destroy.ps1 -Force
```

## Idle / GPU-unused watchdog (15 minutes)

`vast_monitor_until_done.py` polls every **15 minutes** (`VAST_MONITOR_INTERVAL_SEC=900`):

| Condition | Action |
|-----------|--------|
| Train healthy (process + GPU busy / step advancing) | Keep billing |
| Train dead (crash or idle) | **One** corrective relaunch (`SFT_BACKEND=peft`, `SFT_EVAL_STRATEGY=no`) |
| Still unused after **2** idle polls (~30 min) | Fetch artifacts → **destroy** (not stop) |
| SFT finished | Fetch → destroy |
| Wall clock max (default 10h) | Fetch → destroy |

Start / restart:

```powershell
cd fine_tuning\scripts
.\vast_start_idle_watch.ps1 -KillExisting
# log: fine_tuning\kaggle\vast_sft_gate0\vast_monitor.log
```

Env knobs: `VAST_IDLE_STREAK_LIMIT` (default 2), `VAST_IDLE_GPU_UTIL_MAX` (default 5%).

## Done markers

`/workspace/sft_train.log` contains any of:

- `SOTA SFT v2 complete`
- `Saved adapter to`
- `sft_run_config.json`

Monitor requires two consecutive not-running polls **plus** a log marker. Crash detection inspects **`sft_train.log` only** (and requires `Total steps` in that log) so benign Tracebacks during setup/launch must **not** destroy the instance. Setup/smoke failure (`SMOKE FAIL` / no `SETUP_OK` after grace) → fetch logs → **destroy**.

## Fetch / destroy

```powershell
.\vast_fetch.ps1 -PartialOnly   # adapter + logs; merged HF if tokenizer-complete
.\vast_destroy.ps1              # DESTROY, do not stop
```

Local dir: `fine_tuning/kaggle/vast_sft_gate0/`

Session: `fine_tuning/kaggle/vast_sft_session.json`

## Out of scope this pass

- F §5 eval, GGUF, Ollama, Hub upload (`SFT_EXPORT=0`)
- CPT S6 / RunPod volume
- Renting without explicit operator go
