# CPT corpus v3 — S6 continue B checklist

**More-tokens B only.** S5 B+C are complete. Do **not** re-C the S5 adapter. Do **not** merge. Do **not** overwrite Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` until a new C beats v2 Ampere.

Create a GPU **only when the operator says go.**

Spec: memory `pretraining/cpt-b-eval-strategy`. Playbook: [`NEXT_CPT_MORE_TOKENS.md`](NEXT_CPT_MORE_TOKENS.md). Runbook: [`RUNPOD_RUNBOOK.md`](RUNPOD_RUNBOOK.md).

**Windows automation (REST v1 — MCP `create-pod` 400s):** uses Cursor Runpod MCP OAuth (same as S5 C) or set `RUNPOD_API_KEY`:

```powershell
cd continued_pretrain\scripts
.\s6_orchestrate.ps1 -StartMonitor   # provision + verify volume + sync + launch + monitor
.\s6_sync_checkpoints.ps1            # manual checkpoint backup while training
.\s6_fetch_results.ps1               # after B finishes
.\s6_run_c_eval.ps1                  # C eval after B
```

**Safer re-run (after attempt 1 pod loss):** see [`CORPUS_V3_S6_RERUN_SAFE.md`](CORPUS_V3_S6_RERUN_SAFE.md).

---

## What changed in the trainer

`train_cpt_sota.py` supports `CPT_RUN_MODE=continue`:

- Continue hyperparams: body LR ~4e-6, emb ~1.5e-6, `EVAL_DOCS_PER_BUCKET=16`, buckets spurgeon + puritan + confession + mix
- Early-stop **floor** ~0.4 packed epoch; **composite** halt (Spurgeon **and** mix flat within ε=0.005) after merging split HF eval events
- `abort-at-50` **off** on continue
- Best checkpoint still `eval_spurgeon_loss` (ckpt pick ≠ halt)
- **First launch:** empty `PREV_RUN_CHECKPOINT=` + S5 `CPT_INIT_ADAPTER` (SHA `ef4df3a3…`) — new Adam
- **Mid-S6 resume:** keep `CPT_RUN_MODE=continue` and **honor** `PREV_RUN_CHECKPOINT` / auto highest `checkpoints_sota/checkpoint-*` (HF resume keeps Adam). Do **not** point `CPT_INIT_ADAPTER` at checkpoint-2100.

Fresh-from-base runs (no `CPT_RUN_MODE`) keep the old 2-doc / spurgeon-only / abort-at-50 recipe.

---

## Copy onto the pod (`/workspace`)

```text
kaggle/a_output_v3/theology_dataset/          →  /workspace/theology_dataset/
kaggle/a_output_v3/theology_holdouts/         →  /workspace/theology_holdouts/
data/theology_mix_manifest.json               →  /workspace/theology_mix_manifest.json
kaggle/runpod_cpt_v3/theology_cpt_lora/       →  /workspace/theology_cpt_lora/
scripts/train_cpt_sota.py
scripts/cpt_runtime.py
```

Mix SHA256 `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`.  
S5 adapter SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`.

Do **not** copy `kaggle/a_output/` (v2 probe). Do **not** git-clone the repo.

---

## Provision

Volume `7hb931c5oe` US-IL-1 **75 GB** (`theology-cpt-v3`). **Required** — scripts abort without it (`s6_verify_mount.ps1`).

```text
--template-id runpod-torch-v280 --gpu-id "NVIDIA GeForce RTX 4090"
--data-center-ids US-IL-1 --network-volume-id 7hb931c5oe --volume-mount-path /workspace
--ssh   (no --ports)
```

**terminate-after:** REST v1 / runpodctl 2.12 lack create-time auto-terminate. Use `s6_start_monitor.ps1` (`S6_MAX_WALL_HOURS=16`) as backstop. With the network volume, pod delete does not wipe `/workspace`.

Prefer community 4090 (~$0.34/hr). Fallback Secure **same DC** if community is empty. **Never** provision EU-RO-1 without the volume.

---

## Train (continue B)

Prefer `s6_remote_continue_b.sh` (auto-resumes `checkpoint-*` on the volume). Manual env:

**First continue-B from S5 LoRA (new Adam):**

```bash
export CPT_WORK_ROOT=/workspace CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export CPT_RUN_MODE=continue
export CPT_INIT_ADAPTER=/workspace/theology_cpt_lora
export EXPECTED_ADAPTER_SHA256=ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303
export PREV_RUN_CHECKPOINT=
export EVAL_DOCS_PER_BUCKET=16
```

**Resume interrupted S6 (keep continue hyperparams + HF Adam):**

```bash
export CPT_RUN_MODE=continue
export CPT_INIT_ADAPTER=/workspace/theology_cpt_lora   # S5 SHA check; resume overwrites weights
export EXPECTED_ADAPTER_SHA256=ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303
unset PREV_RUN_CHECKPOINT   # auto highest complete checkpoint-*
# or: export PREV_RUN_CHECKPOINT=/workspace/checkpoints_sota/checkpoint-2100
```

Do **not** set `CPT_INIT_ADAPTER` to checkpoint-2100. Do **not** use `S6_FRESH_START=1` unless volume checkpoints are junk.

```bash
python3 -u /workspace/train_cpt_sota.py --install    # first boot only
nohup python3 -u /workspace/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
tail -f /workspace/cpt_train.log
```

Walk away only after the log shows:

- `cpt_run_mode=continue` `composite_stop=True`
- `gpu_profile=ampere` `trainer_bf16=True`
- `eval_docs=16` `eval_buckets=['spurgeon', 'puritan', 'confession']` (+ mix)
- `early_stop_min_steps` ≈ 1650–2060 (0.4 × packed epoch)
- `abort_spurgeon_step=0`
- `MAX_STEPS` equals `packed_epoch_steps` (thousands)
- Resume: `Resuming from .../checkpoint-2100` (or highest complete ckpt) — **not** a step-0 continue from S5

**Scp optimizer + `checkpoint-*`** (or use the volume) so a mid-run interrupt can true-resume next time.

When B finishes: scp `theology_cpt_lora/`, `checkpoints_sota/`, `cpt_train.log`, `theology_cpt_run_config.json` to a new dir under `kaggle/runpod_cpt_v3/` (or sibling). Delete the GPU.

---

## C (after B, separate approval)

C the **new** adapter vs **its** Ampere base. Export the new `EXPECTED_ADAPTER_SHA256` — `eval_cpt_sota.py` still defaults to v2.

```bash
export EXPECTED_ADAPTER_SHA256=<new adapter sha256 from run_config>
python3 -u /workspace/eval_cpt_sota.py
```

Keep Hub v2 if the new C is worse. Merge still requires §5 −15% on puritan+confession.

---

## Paste into the send-to-run chat

```
S6 continue B. Operator approved. Copy a_output_v3 + S5 LoRA. CPT_RUN_MODE=continue.
Volume 7hb931c5oe via runpodctl. 4090 US-IL-1, terminate-after >= 14h.
If volume has checkpoint-2100: unset PREV_RUN_CHECKPOINT (HF resume, keep continue hyperparams).
First continue-B only: PREV_RUN_CHECKPOINT empty. C only after B with new SHA256.
Hub v2 stays until new C wins.
```
