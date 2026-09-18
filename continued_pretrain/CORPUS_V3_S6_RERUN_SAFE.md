# S6 continue-B — safer re-run checklist (attempt 2+)

**Goal:** Continue from S5 LoRA with volume-backed `/workspace`, local checkpoint backups, and automatic pod teardown.

**Previous attempt lost** because the pod landed in EU-RO-1 **without** network volume — deleting the pod wiped all checkpoints.

Spec: [`CORPUS_V3_S6_CONTINUE_CHECKLIST.md`](CORPUS_V3_S6_CONTINUE_CHECKLIST.md) · Playbook: [`NEXT_CPT_MORE_TOKENS.md`](NEXT_CPT_MORE_TOKENS.md)

---

## CUDA / image compatibility (important)

US-IL-1 **Secure** hosts often run **driver CUDA 12.4** (e.g. 550.x). The default image
`runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` requires **host CUDA ≥ 12.8** and will
**crash-loop** with:

```text
nvidia-container-cli: unsatisfied condition: cuda>=12.8
```

Symptoms: 0% GPU, 0B RAM in telemetry, SSH fails, container logs repeat the error.

**Fix:** provision scripts now prefer **`runpod/pytorch:0.7.0-cu1241-torch260-ubuntu2204`**
(CUDA 12.4.1) for US-IL-1, with legacy `2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` as
fallback. EU hosts with CUDA 12.8+ can still use the cu128 torch280 image.

---

| Gate | Check |
|------|--------|
| Operator approval | You said go |
| S5 LoRA local | `kaggle/runpod_cpt_v3/theology_cpt_lora/adapter_model.safetensors` SHA256 `ef4df3a3…` |
| Mix local | `kaggle/a_output_v3/` (junction → `D:\search-sermons-cpt\a_output_v3`) |
| SSH key | `~/.ssh/runpod_cpt` + **`runpod_cpt.pub` added in [Runpod → Settings → SSH Keys](https://www.runpod.io/console/user/settings)** (required for Secure proxy SSH) |
| **Volume** | `7hb931c5oe` in **US-IL-1** — pod **must** mount it at `/workspace` |
| No stray pod | Runpod console → terminate any old `s6-continue-b-cpt` pods |

**Hard rule:** If `s6_verify_mount.ps1` fails, **delete the pod** and reprovision. Do not train on container disk only.

---

## Capacity watcher (auto-provision when 4090 opens)

If US-IL-1 is full, run a background poller (every **20 min**):

```powershell
cd continued_pretrain\scripts
.\s6_start_capacity_watch.ps1
Get-Content ..\kaggle\runpod_cpt_v3\s6_capacity_watch.log -Wait -Tail 20
```

When a 4090 + volume slot opens, it will: provision → verify mount → sync → launch → start training monitor.

---

Open **PowerShell** (keep this window open until log gates pass, or use `-StartMonitor`):

```powershell
cd C:\Users\rafael\Projetos\search-sermons\continued_pretrain\scripts
.\s6_orchestrate.ps1 -StartMonitor
```

This runs: provision → wait SSH → **verify volume** → sync artifacts → launch continue-B → start background monitor.

### What the scripts do now (safer than attempt 1)

| Script | Safety |
|--------|--------|
| `s6_provision_pod.ps1` | **US-IL-1 + volume only** (no EU fallback without volume) |
| `s6_verify_mount.ps1` | Aborts if `network_volume_id` missing or `/workspace` too small |
| `s6_sync_checkpoints.ps1` | Copies only **complete** `checkpoint-*` dirs (`trainer_state.json` present) |
| `s6_start_monitor.ps1` | Polls every **10 min**, syncs checkpoints, deletes pod when B finishes |
| Monitor backstop | **`S6_MAX_WALL_HOURS=16`** — fetch + delete pod even if you forget (volume keeps data) |

---

## Step-by-step (if you prefer manual control)

### 1. Provision (US-IL-1 + volume)

```powershell
cd continued_pretrain\scripts
.\s6_provision_pod.ps1
```

Auth order: `runpodctl` + `RUNPOD_API_KEY` → MCP OAuth (`s6_provision_pod_mcp.py`) → REST API key.

If US-IL-1 community 4090 is empty, script retries **Secure same DC** (still with volume).

### 2. Wait for SSH

```powershell
.\s6_wait_ssh.ps1
```

**Secure US-IL-1** pods often use **proxy SSH** (`user@ssh.runpod.io`), not a direct IP. If SSH fails with `Permission denied (publickey)`:

1. Open [Runpod SSH Keys](https://www.runpod.io/console/user/settings)
2. Add the contents of `%USERPROFILE%\.ssh\runpod_cpt.pub`
3. Test: `ssh -i ~/.ssh/runpod_cpt cryeqjtrfanoxz-6441169d@ssh.runpod.io` (user from `s6_session.json`)

Session file stores `ssh_user`, `ssh_host`, `ssh_mode` after a successful wait.

### 3. Verify volume mount (mandatory)

```powershell
.\s6_verify_mount.ps1
```

Expect `network_volume_id: 7hb931c5oe` in `kaggle/runpod_cpt_v3/s6_session.json` and `/workspace` ~75G+.

### 4. Sync artifacts to `/workspace`

```powershell
.\s6_sync_to_pod.ps1
```

Copies: `a_output_v3`, S5 LoRA, manifest, `train_cpt_sota.py`, `cpt_runtime.py`, launcher script.

**Clean restart from S5** (wipes partial checkpoints on volume):

```powershell
# optional — only if volume has junk from a failed run
ssh -i ~/.ssh/runpod_cpt root@<host> -p <port> "S6_FRESH_START=1 bash /workspace/s6_remote_continue_b.sh"
```

Or set `S6_FRESH_START=1` before first launch on a new pod.

### 5. Launch training

```powershell
.\s6_launch_continue_b.ps1
```

### 6. Verify log gates (do not walk away until all pass)

```powershell
ssh -i ~/.ssh/runpod_cpt root@<host> -p <port> "tail -n 60 /workspace/cpt_train.log"
```

Required lines:

- `cpt_run_mode=continue` `composite_stop=True`
- `lr=4e-06` `emb_lr=1.5e-06` `abort_spurgeon_step=0`
- `eval_docs=16` + spurgeon/puritan/confession buckets
- `early_stop_min_steps=1652` `packed_epoch_steps=4128`
- `INIT_ADAPTER SHA256 OK`
- `gpu_profile=ampere` `trainer_bf16=True`
- Resume from interrupted S6: `Resuming from .../checkpoint-2100` (or highest complete ckpt) — **not** a step-0 continue from S5

### 7. Start monitor (background)

```powershell
.\s6_start_monitor.ps1
# tail monitor log:
Get-Content ..\kaggle\runpod_cpt_v3\s6_monitor.log -Wait -Tail 20
```

Monitor behavior:

1. Every **10 min**: SSH status + **sync complete checkpoints** to `kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota/`
2. When B finishes (**log marker** such as `Saved run config` / `COMPOSITE EARLY-STOP` / `4128/4128`, **and** the train process is gone): full fetch + **delete pod**. SSH timeouts never count as done.
3. After **16 h** wall: fetch + delete pod (billing backstop; checkpoints remain on **volume**)

---

## terminate-after note

Runpod REST v1 / current `runpodctl 2.12` do **not** expose `--terminate-after` on create. The **16 h monitor backstop** replaces it. With the network volume, a forced pod delete does **not** lose `/workspace` data — remount the volume on the next pod.

---

## After B completes

```powershell
.\s6_fetch_results.ps1
.\s6_run_c_eval.ps1    # keep Hub v2 if C is worse
```

Confirm pod deleted (monitor or console). **Keep volume** `7hb931c5oe` for future runs.

---

## If something goes wrong

| Situation | Action |
|-----------|--------|
| `verify_mount` fails | Delete pod; reprovision — never train without volume |
| Pod deleted mid-run | Provision new pod **same volume**; checkpoints on `/workspace/checkpoints_sota/` survive |
| Resume mid-S6 from volume ckpt | Keep `CPT_RUN_MODE=continue`. **Unset** `PREV_RUN_CHECKPOINT` (or set `.../checkpoint-2100`). HF resume keeps Adam. Do **not** point `CPT_INIT_ADAPTER` at the ckpt. Do **not** `S6_FRESH_START=1` unless ckpts are junk. |
| Monitor stopped (closed Cursor) | Re-run `.\s6_start_monitor.ps1` — training on pod continues |
| Manual checkpoint backup | `.\s6_sync_checkpoints.ps1` anytime while pod is up |

---

## Cost estimate

- Community 4090 US-IL-1: ~$0.34/hr × ~8–12 h ≈ **$3–5**
- Secure fallback: ~$0.74/hr × ~8–12 h ≈ **$6–9**
- Volume: small idle storage charge; delete pod, not volume

---

## Paste into a new agent chat

```
S6 continue-B resume (attempt 2). Operator approved.
US-IL-1 only, network volume 7hb931c5oe at /workspace — abort if not mounted.
CPT_RUN_MODE=continue, S5 LoRA init SHA ef4df3a3…, HF resume checkpoint-2100 (unset PREV_RUN_CHECKPOINT).
Do not S6_FRESH_START. s6_orchestrate.ps1 -StartMonitor. Monitor deletes only on log markers.
After B: fetch + C eval; keep Hub v2 if worse.
```
