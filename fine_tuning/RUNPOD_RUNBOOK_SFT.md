# RunPod runbook — SFT v2 GATE-0 (Qwen3.5-4B + Hub v2 CPT merge)

Train **shippable SFT v2** on the CPT-merged base. Do **not** start until local readiness passes.

Companion: [`KAGGLE_RUNBOOK_SFT_V2.md`](KAGGLE_RUNBOOK_SFT_V2.md) (T4 dry-run path).  
CPT volume runbook: [`../continued_pretrain/RUNPOD_RUNBOOK.md`](../continued_pretrain/RUNPOD_RUNBOOK.md).

## Prerequisites

| Item | Value |
|------|-------|
| Base (GATE-0) | `/workspace/theology_cpt_v2_merged_hf` (Hub v2 LoRA merged 16-bit) |
| Hub v2 LoRA SHA256 | `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478` |
| QA mix | `qa_mix_v2` in `spurgeon-qa-mix-v1.zip` |
| Volume | `7hb931c5oe` US-IL-1 at `/workspace` |
| GPU | RTX 4090 community (~$0.34/hr) or Secure fallback |
| SSH key | `%USERPROFILE%\.ssh\runpod_cpt` (+ pub in Runpod account) |

**Do not overwrite** `/workspace/theology_cpt_lora/` or `/workspace/checkpoints_sota/` (CPT S6 resume).

## 0. Local prep

```powershell
python fine_tuning/scripts/12_package_kaggle_qa_mix.py
python fine_tuning/scripts/_gen_sota_sft_notebooks.py
python fine_tuning/scripts/13_sft_local_readiness.py --gate0
python fine_tuning/scripts/audit_qwen35_special_tokens.py
python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 0
python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 1
python fine_tuning/scripts/audit_qa_mix_quality.py
```

Stop-token phased gates: [`STOP_TOKEN_PHASES.md`](STOP_TOKEN_PHASES.md) — phase 2 runs automatically after GATE-0 merge on pod.

## 1. One-time GATE-0 merge (if merged HF missing on volume)

```powershell
cd fine_tuning\scripts
.\sft_orchestrate.ps1 -MergeOnly -StartMonitor:$false
```

If US-IL-1 has no 4090 capacity, start the auto-watcher (polls every 10 min, tries 4090 → L40S; **no pod while waiting**):

```powershell
.\sft_start_capacity_watch.ps1 -IntervalSec 600
```

Billing guardrails (watcher + monitor):
- **No pod** while waiting for US-IL-1 capacity.
- **Idle pod deleted** after ~20 min if train/merge never starts (`SFT_IDLE_DELETE_MIN`).
- **Monitor deletes pod** when training finishes or after 8h wall.
- **Local backup** during training: `sft_fetch_artifacts.ps1` + checkpoint sync each monitor poll.

Tail: `fine_tuning/kaggle/sft_capacity_watch.log`

Or full pipeline (merge runs automatically if `/workspace/theology_cpt_v2_merged_hf/config.json` absent):

```powershell
.\sft_orchestrate.ps1 -StartMonitor
```

**Volume mount gate:** `sft_verify_mount.ps1` aborts if `network_volume_id` is null. MCP `create-pod` silently drops mounts — prefer **runpodctl** with `--network-volume-id 7hb931c5oe`.

## 2. Sync payload (automatic via `sft_sync_to_pod.ps1`)

```text
spurgeon-qa-mix-v1.zip          ->  /workspace/
merge_cpt_lora.py               ->  /workspace/
train_sft_sota.py               ->  /workspace/
eval_sft_sota.py                ->  /workspace/
sft_stop_token_utils.py         ->  /workspace/
verify_sft_stop_tokens.py       ->  /workspace/
sft_remote_*.sh                 ->  /workspace/
config.py                       ->  /workspace/
```

## 3. On-pod env (set by remote scripts)

```bash
export SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export USE_CPT_MERGE=1
export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
export SFT_CPT_ADAPTER=/workspace/theology_cpt_lora_hub_v2
export SFT_EXPORT=0
```

## 4. Training recipe

| Param | Default |
|-------|---------|
| `MAX_SEQ_LENGTH` | 4096 |
| `LORA_RANK` | 32 |
| `PER_DEVICE_BATCH` | 2 |
| `GRAD_ACCUM` | 8 |
| `NUM_EPOCHS` | 2 |
| Masking | `train_on_responses_only` |

OOM ladder: `SFT_PER_DEVICE_BATCH=1`, `SFT_GRAD_ACCUM=16`, then `SFT_MAX_SEQ_LENGTH=3072`, then `SFT_LORA_RANK=16`.

## 5. Monitor completion markers

Log file: `/workspace/sft_train.log`

Done when log contains **any** of:
- `SOTA SFT v2 complete`
- `Saved adapter to`
- `sft_run_config.json`

Monitor requires **two consecutive** not-running polls **plus** a log marker (S6 false-positive lesson).

## 6. Eval (after train)

```powershell
.\sft_run_eval.ps1              # SFT_EXPORT=0
.\sft_fetch_results.ps1
```

Inspect remote:

```powershell
ssh ... "bash /workspace/sft_inspect_volume.sh"
```

## 7. Gates (only then export)

From [`KAGGLE_RUNBOOK_SFT_V2.md`](KAGGLE_RUNBOOK_SFT_V2.md) §5:

| Gate | Target |
|------|--------|
| Faithfulness judge | ≥ 4.0/5 |
| Refusal accuracy | ≥ 85% |
| Structural echo | ≤ 2% |
| Stop-token (phase 3) | im_end ≥85%, corrupt=0, leaked turns ≤2% |
| Ollama smoke (phase 5) | zero corrupt tokens; im_end stop ≥85% at temp 0 |

```powershell
.\sft_run_eval.ps1 -Export      # sets SFT_EXPORT=1 on pod
.\sft_fetch_results.ps1
# then GGUF convert, upload_sft_gguf_to_hf.py, smoke_test_ollama.py
```

## 8. Billing

- Delete pod immediately after fetch (monitor does this automatically).
- Volume persists cheaply; merged HF + tokenized datasets cache on volume for reruns.
- Do **not** leave Jupyter or extra ports open on a billed GPU.

## Session file

`fine_tuning/kaggle/sft_session.json` — pod id, SSH, volume id, gate0 paths.

## Local results

Fetched to `fine_tuning/kaggle/runpod_sft_gate0/`:
- `spurgeon_qa_lora_v2/`
- `sft_run_config.json`
- `sft_eval_metrics.json`
- `sft_train.log`
