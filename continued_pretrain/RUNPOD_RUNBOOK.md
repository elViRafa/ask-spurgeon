# Runpod runbook — CPT (Qwen3.5-4B bf16 LoRA)

**S5 B is complete** (2026-08-27/28, best step 325, early-stop 375/4128). Next GPU = **C only with approval**: [`CORPUS_V3_S5_C_CHECKLIST.md`](CORPUS_V3_S5_C_CHECKLIST.md). Adapter: [`kaggle/runpod_cpt_v3/README.md`](kaggle/runpod_cpt_v3/README.md). Do **not** retrain. Do **not** create a GPU until C is the active approved session.

**v2 B and C are complete** (2026-08-27, best step 400). Keepable fallback: [`kaggle/runpod_cpt_v2/README.md`](kaggle/runpod_cpt_v2/README.md). Do **not** merge, do **not** re-C that adapter, no Hub overwrite, no Kaggle push.

Kaggle stays STOP on `rafaelvieira1`. Do **not** resume T4 4-bit checkpoints onto Ampere/Ada bf16. Do **not** git-clone this repo onto the pod (other `theology_cpt_lora` dirs exist).

Source of truth: [`scripts/_gen_sota_notebooks.py`](scripts/_gen_sota_notebooks.py) (regenerates notebooks, [`scripts/train_cpt_sota.py`](scripts/train_cpt_sota.py), and [`scripts/eval_cpt_sota.py`](scripts/eval_cpt_sota.py)).

## S6 — continue B (more mix tokens; operator approval required)

S5 C is complete (probe PASS, §5 FAIL). **Do not re-C S5.** When approved for more tokens, use [`CORPUS_V3_S6_CONTINUE_CHECKLIST.md`](CORPUS_V3_S6_CONTINUE_CHECKLIST.md): `CPT_RUN_MODE=continue`, load S5 LoRA, composite early-stop, no `PREV_RUN_CHECKPOINT` resume.

## S5 — corpus v3 B (already ran; do not repeat)

Do **not** copy [`kaggle/a_output/`](kaggle/a_output/) (v2 probe, ~8162 train docs). B used **v3**:

```text
continued_pretrain/kaggle/a_output_v3/theology_dataset/   →  $CPT_WORK_ROOT/theology_dataset/
continued_pretrain/kaggle/a_output_v3/theology_holdouts/  →  $CPT_WORK_ROOT/theology_holdouts/
continued_pretrain/data/theology_mix_manifest.json        →  $CPT_WORK_ROOT/theology_mix_manifest.json
continued_pretrain/scripts/train_cpt_sota.py
continued_pretrain/scripts/cpt_runtime.py
```

On this machine, `kaggle/a_output_v3` is a junction to `D:\search-sermons-cpt\a_output_v3` (~320 MB; C: was full). Copy from either path. Meta: [`kaggle/a_output_v3/DATASET_META.json`](kaggle/a_output_v3/DATASET_META.json) — 51417 train / 520 val, mix SHA256 `23dd3820baa0b657…090973`, 91.31M verified tokens.

**Volume:** `7hb931c5oe` US-IL-1 **75 GB** STANDARD, name `theology-cpt-v3`. MCP `create-pod` **silently drops** the mount — use **runpodctl**:

```text
--template-id runpod-torch-v280 --gpu-id "NVIDIA GeForce RTX 4090"
--data-center-ids US-IL-1 --network-volume-id 7hb931c5oe --volume-mount-path /workspace
--ssh   (no --ports)
--terminate-after  >= 14h
```

Prefer community 4090 (~$0.34/hr). US-IL-1 community stock is often LOW; fallback **Secure same DC** (~$0.74/hr). Do not create a second volume in EU-RO-1 for this run.

B actually ran: packed 66045 rows, `MAX_STEPS=4128`, abort-at-50 **pass**, early-stop **375**, best **325**, ~8.2M of ~90M tokens. Adapter SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303` in `kaggle/runpod_cpt_v3/`. GPU deleted. Volume unused (MCP dropped the mount). **C next**, with approval — see [`CORPUS_V3_S5_C_CHECKLIST.md`](CORPUS_V3_S5_C_CHECKLIST.md). Keep Hub `…-cpt-lora-v2` if the new C is worse.

## Why a script, not Jupyter

Kaggle died from `DeadKernelError` in the notebook process. On Runpod, train with a detached Python process (`nohup`). Do **not** leave Jupyter or extra ports open on a billed GPU — inspect `cpt_train.log` on the volume after the pod is deleted.

## GPU / cost

| Pick | Why |
|------|-----|
| **RTX 4090** community (~**$0.34/hr**, 24 GB, Ada sm_89) | Preferred. Stock was MEDIUM when this runbook was written. |
| L4 / A100 | Also sm_80+ bf16. L40 (~$0.69/hr) is overkill for 4B LoRA. |
| **Not T4** | No bf16; Unsloth float32 + 4-bit is the unofficial path that already failed. |

**v2 probe (already ran):** one padded epoch was **674** steps (`ceil(10779/16)`), ~1 h at ~7.4 s/step. **S5:** expect **~3200–4300** steps (~6–9 h) plus tokenize-pack of ~51k docs; `--terminate-after` **≥ 14 h**. The trainer still **stops at step 50** if `eval_spurgeon_loss` rose vs step 25. See **Do not burn GPU credits** below — a Running pod bills even when idle.

`GPU_PROFILE` is **auto**: sm_80+ → `ampere` (`load_in_4bit=False`, trainer **bf16 even with embed LoRA**). Override with `GPU_PROFILE=t4` only if you must.

This $15 run is a **probe** (~15.6M mix tokens), not a ~110M-token CPT. Do not expect §5 −15% PPL. Continue / C only if `eval_spurgeon` is flat or falling through step 50.

## Recipe (do not change unless OOM)

- Base: `unsloth/Qwen3.5-4B-Base`
- `PACKING_MODE=one_doc_padded`, `PAD_TO_MAX=False`, `LORA_GDN=True` (`in_proj_qkv` / `in_proj_z` / `out_proj` only)
- LoRA r=32, body LR `1e-5`, emb LR `5e-6`, `TRAIN_EMBEDDINGS=True`, `TRAIN_LM_HEAD=False`
- After pack, `MAX_STEPS` = one padded epoch (v2: ~674; S5: thousands). Eval every 25 on spurgeon holdout
- **Encoded abort:** if `eval_spurgeon_loss` at step 50 is worse than step 25, training stops (`ABORT: eval_spurgeon rose by step 50`)
- OOM hatch: `TRAIN_EMBEDDINGS=False` **before** dropping GDN

**S5 mix** is already rebuilt (`spurgeon_weight` 1.0688, 91.31M tokens). Local A wrote `kaggle/a_output_v3`. Do not rebuild the mix. Do not copy v2 `kaggle/a_output`.

## Data to copy — v2 probe (already ran; do not use for S5)

S5 copy list is in **S5 — corpus v3 B** above. The v2 probe used:

```text
continued_pretrain/kaggle/a_output/theology_dataset/     →  $CPT_WORK_ROOT/theology_dataset/
continued_pretrain/kaggle/a_output/theology_holdouts/    →  $CPT_WORK_ROOT/theology_holdouts/
```

`CPT_DATA_ROOT` may point at the same directory as `CPT_WORK_ROOT`. Volume is now **75 GB** (`7hb931c5oe`) for embed-FT optimizer dumps.

## Provision (S5: see section above; this block is the shared env)

Volume `7hb931c5oe` already exists in US-IL-1 (75 GB). Pod: official **PyTorch** template `runpod-torch-v280`, GPU `NVIDIA GeForce RTX 4090`, **same DC**, SSH, volume at `/workspace`, **no ports**. Set `--terminate-after` ≥ 14 h. Copy the **S5** trees (not v2 `a_output`). Do not git-clone the repo.

Env:

```bash
export CPT_WORK_ROOT=/workspace
export CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home
# First run must be fresh:
export PREV_RUN_CHECKPOINT=
```

Later sessions on the **same Ampere run**: unset `PREV_RUN_CHECKPOINT` so auto-resume picks `$CPT_WORK_ROOT/checkpoints_sota/checkpoint-*`.

## Train

`--install` **exits after pip**. It does not start training in the same process.

```bash
cd /workspace   # or the cloned repo root
python continued_pretrain/scripts/train_cpt_sota.py --install   # first boot only; then exits
nohup python continued_pretrain/scripts/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
tail -f /workspace/cpt_train.log
```

Gates to confirm before walking away:

- Config print: `gpu_profile=ampere load_in_4bit=False`, `packing_mode=one_doc_padded`, `lora_gdn=True`
- Trainer print: `trainer_bf16=True` (even with `train_embed=True`)
- After pack: `MAX_STEPS` equals `packed_epoch_steps` (S5: thousands, not 674)
- D1/D2: `multi_doc_rows=0`
- `save_only_model=False`, `save_total_limit=3` (Runpod volume, not Kaggle 20 GB)
- At step 50: either `ABORT: eval_spurgeon rose` or `abort-at-50: eval_spurgeon did not rise`

## Resume (same Runpod run only)

If the process dies after a checkpoint **and** step-50 abort did not fire:

```bash
unset PREV_RUN_CHECKPOINT    # auto: highest checkpoint-* with trainer_state.json
# or:
export PREV_RUN_CHECKPOINT=/workspace/checkpoints_sota/checkpoint-100
nohup python continued_pretrain/scripts/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
```

Do **not** point this at a Kaggle 4-bit adapter.

## C eval — S5 v3 adapter (next, with approval)

Do **not** re-C the v2 LoRA. S5 C must use **`a_output_v3` holdouts** and `runpod_cpt_v3` LoRA. Full copy/export list: [`CORPUS_V3_S5_C_CHECKLIST.md`](CORPUS_V3_S5_C_CHECKLIST.md).

v2 C already ran (keep as fallback comparison). Do **not** re-C that adapter. Score the **new** LoRA only if C is approved:

- Adapter: `kaggle/runpod_cpt_v3/theology_cpt_lora` SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`
- `export EXPECTED_ADAPTER_SHA256=` that hash (`eval_cpt_sota.py` still defaults to v2 `319d17a3…1478`)
- Holdouts: `kaggle/a_output_v3/theology_holdouts/`
- Ampere bf16 (`load_in_4bit=False`). `REQUIRE_AMPERE=1`. `ADAPTER_OVERRIDE=None`. `EVAL_BASE=True`. `RUN_MERGE=False`.
- Probe bar: any holdout PPL better than **this C’s** base. Keep Hub v2 if worse than v2 Ampere C. Do not expect §5 −15%.
- After C, more-tokens continue (if warranted): [`NEXT_CPT_MORE_TOKENS.md`](NEXT_CPT_MORE_TOKENS.md). Do not start that B in the C session.

### C eval (v2 adapter — already ran; fallback only)

Do **not** re-C the v2 LoRA. Historical copy list if you ever must re-score it:

B abort-at-50 **passed**; early-stop 450; best ckpt-400. Score the **local** v2 LoRA only if you ever re-run that eval:

- Adapter: `kaggle/runpod_cpt_v2/theology_cpt_lora` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Ampere bf16 (`load_in_4bit=False`). `REQUIRE_AMPERE=1` is baked into `eval_cpt_sota.py`.
- `ADAPTER_OVERRIDE=None`. `EVAL_BASE=True`. `RUN_MERGE=False`. `SCORE_LAST_CHECKPOINT=False`.
- Probe bar: any holdout PPL better than base. Do not expect §5 −15%.
- MCP `create-pod` **cannot** attach a network volume. Use **runpodctl** (`--network-volume-id 7hb931c5oe`, US-IL-1) or a 75 GB disk + scp. Need `RUNPOD_API_KEY` for runpodctl.

Do **not** copy `kaggle/b_output*` or the rest of the repo. Tarball only:

```text
kaggle/runpod_cpt_v2/theology_cpt_lora/   →  $CPT_WORK_ROOT/theology_cpt_lora/
kaggle/a_output/theology_holdouts/        →  $CPT_WORK_ROOT/theology_holdouts/
data/catechism_mcq.json                   →  $CPT_WORK_ROOT/catechism_mcq.json
scripts/eval_cpt_sota.py                  →  $CPT_WORK_ROOT/eval_cpt_sota.py
```

Pod `--env` is **not** in the SSH shell (PID 1 only). Export in the SSH/nohup command:

```bash
export CPT_WORK_ROOT=/workspace CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export EXPECTED_ADAPTER_SHA256=319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478
python3 -u /workspace/eval_cpt_sota.py --preflight    # fail → delete GPU now
python3 -u /workspace/eval_cpt_sota.py --install      # PEP 668; exits; fail → delete GPU now
nohup python3 -u /workspace/eval_cpt_sota.py > /workspace/cpt_eval.log 2>&1 &
```

Stay attached until the log shows `gpu_profile=ampere`, `load_in_4bit=False`, SHA256 OK, `ADAPTER_PATH=.../theology_cpt_lora`, holdouts found, `RUN_MERGE=False`. `--terminate-after 2h` is a backstop, not a target. Prefer community 4090; Secure if community is empty. No Jupyter ports.

C writes `/workspace/theology_cpt_eval_metrics.json`. Scp that + `cpt_eval.log` off, then **delete the GPU**. Keep the volume if it was attached.

## Do not burn GPU credits

A **Running GPU pod bills the 4090 rate the whole time it is up** — training, packing, pip install, SSH idle, Jupyter, and “I’ll look at logs later.” Network volume storage is cheap (~$0.07/GB/month; 50 GB is cents per day). **Idle GPU is the waste.** ~$15 ≈ 40 h of 4090; a forgotten overnight pod can spend most of that on nothing.

### GPU off (no 4090 running)

Do **not** create or start a GPU pod for:

- Reading this runbook, editing the generator, running local tests
- Inspecting `a_output` / `a_output_v3`, mix manifest, or Kaggle logs
- Waiting on a human decision
- C eval **before** `--preflight` would pass (adapter SHA256, holdouts, Ampere GPU)
- “Just Jupyter” or extra exposed ports (this runbook: **no ports**)

Keep the **network volume**. It survives pod stop/terminate. Put `theology_dataset`, `hf_home`, checkpoints, and `cpt_train.log` **on the volume** (`CPT_WORK_ROOT=/workspace`), never only on container disk (wiped on stop).

### GPU on (pay) — only while CPT is actually running

1. Volume already exists in the DC you will use.
2. Data + `train_cpt_sota.py` are ready to copy (or already on the volume from a previous pod).
3. Create **one** community **RTX 4090**. Not L40/A100. Not a second pod. Not T4.
4. Set `--terminate-after` **past expected wall time** (backstop if you fall asleep). Prefer `--terminate-after`, **not** `--stop-after` (`--stop-after` leaves a stopped pod that can still charge disk; it is not a GPU-off guarantee).
5. SSH → `--install` (exits) → `nohup` train. Confirm gates (ampere, bf16, D1/D2, packed `MAX_STEPS`). Then you may disconnect; **the process must keep running under nohup**.

### Stop the GPU immediately (do not wait for `--terminate-after`)

Copy or confirm logs/ckpts are on the **volume**, then **stop and delete the pod** (keep the volume) when any of these happen:

| Signal | Action |
|--------|--------|
| Log line `ABORT: eval_spurgeon rose by step 50` | Teardown GPU. Do not resume. Do not C. |
| D1/D2 GATE FAIL, wrong `gpu_profile=t4` on a 4090, or OOM after the embed hatch | Teardown GPU. Fix code locally; do not leave the box up. |
| Training **finished** (epoch done or early-stop) | Teardown GPU. Read logs from the volume later. |
| C eval **finished** (`Done. Metrics at` / `theology_cpt_eval_metrics.json`) | Scp metrics+log, then teardown GPU. Do not merge. |
| `--preflight` or `--install` FAIL | Teardown GPU immediately. Fix locally. |
| You are not going to watch the run and `--terminate-after` was **not** set | Set it or delete the pod. An unattended Running pod is an open tab on the credit balance. |

Do **not** keep a Running pod overnight “to inspect in the morning.” `tail` the log, `cp` it onto the volume if needed, then delete the GPU.

### After teardown

- Volume stays until C/merge is decided (or you are sure you will not resume the **same Ampere** run).
- Resume **only** the same Ampere job (`unset PREV_RUN_CHECKPOINT` or a `checkpoint-*` on that volume). Never spend GPU time loading Kaggle 4-bit adapters.
- Next GPU create: attach the **same** volume so `HF_HOME` is already warm (no re-download on the clock).
- C on a GPU only after `--preflight` passes on the **Runpod B** LoRA. `RUN_MERGE=False` until holdout PPL beats base.
