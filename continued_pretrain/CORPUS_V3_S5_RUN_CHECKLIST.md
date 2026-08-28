# CPT corpus v3 — S5 B send-to-run checklist (historical)

**B already ran 2026-08-27/28.** Do not use this file to start another train GPU. Next session: [`CORPUS_V3_S5_C_CHECKLIST.md`](CORPUS_V3_S5_C_CHECKLIST.md).

Preflight (local A + volume grow) already ran 2026-08-27. Do not re-run A, mix, Wave 3, or confession fetch.

Still **no C** until approval, no Kaggle push, no merge, no Hub LoRA overwrite. Packing stays `one_doc_padded`. Fallback LoRA: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`.

Runbook: [`RUNPOD_RUNBOOK.md`](RUNPOD_RUNBOOK.md)

---

## Do not copy

| Path | Why |
|------|-----|
| `kaggle/a_output/` | v2 probe (~8162 train docs / ~15.6M tokens) |
| `kaggle/runpod_cpt_v2/` | fallback LoRA snapshot; keep it |
| `data/kaggle_upload/theology-cpt-corpus.zip` | stale 2026-08-25 package |
| git clone of this repo | other `theology_cpt_lora` dirs exist |

---

## Copy onto the volume (`/workspace`)

`kaggle/a_output_v3` is a **junction** to `D:\search-sermons-cpt\a_output_v3` (~320 MB). If `runpodctl send` fails on the junction, send from `D:\`.

```text
continued_pretrain/kaggle/a_output_v3/theology_dataset/   →  /workspace/theology_dataset/
continued_pretrain/kaggle/a_output_v3/theology_holdouts/  →  /workspace/theology_holdouts/
continued_pretrain/data/theology_mix_manifest.json        →  /workspace/theology_mix_manifest.json
continued_pretrain/scripts/train_cpt_sota.py              →  /workspace/train_cpt_sota.py
continued_pretrain/scripts/cpt_runtime.py                 →  /workspace/cpt_runtime.py
```

Expect HF train **51417** / val **520**. Mix `created_at` 2026-08-27T19:58:31Z, SHA256 `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`. Sidecar: `kaggle/a_output_v3/DATASET_META.json`.

---

## Provision (runpodctl, not MCP create-pod)

MCP `create-pod` **silently ignores** `networkVolumeId`. Need `RUNPOD_API_KEY` + registered SSH key.

- Volume **`7hb931c5oe`** US-IL-1 **75 GB** STANDARD, name `theology-cpt-v3`
- Template `runpod-torch-v280`
- GPU `NVIDIA GeForce RTX 4090`
- `--data-center-ids US-IL-1` (volume is DC-locked)
- `--network-volume-id 7hb931c5oe --volume-mount-path /workspace`
- `--ssh`, **no `--ports`**
- `--terminate-after` **≥ 14h**
- Prefer community (~$0.34/hr). US-IL-1 community is often LOW → **Secure same DC** (~$0.74/hr). Do not create a second volume in EU-RO-1.

Confirm `runpodctl pod get` shows the network mount before copying data. If `mounts` is empty, **delete** the pod and recreate with runpodctl. Do not train on container disk.

---

## Train

Pod `--env` is **not** in the SSH shell. Export in the same shell as `nohup`:

```bash
export CPT_WORK_ROOT=/workspace CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export PREV_RUN_CHECKPOINT=
python3 -u /workspace/train_cpt_sota.py --install    # exits after pip; fail → delete GPU
nohup python3 -u /workspace/train_cpt_sota.py > /workspace/cpt_train.log 2>&1 &
tail -f /workspace/cpt_train.log
```

Walk away only after the log shows:

- `gpu_profile=ampere load_in_4bit=False`
- `packing_mode=one_doc_padded` `lora_gdn=True`
- `trainer_bf16=True`
- `multi_doc_rows=0`
- `MAX_STEPS` equals `packed_epoch_steps` (**thousands**, not 674)
- `save_only_model=False`

`--install` does not start training. Recipe unchanged: r=32, embed FT on, GDN `in_proj_qkv` / `in_proj_z` / `out_proj`, abort if `eval_spurgeon` at 50 > 25.

Cost ballpark **~$3–7** GPU. Idle GPU still bills. When B finishes (or abort/OOM): scp adapter + `cpt_train.log` + `theology_cpt_run_config.json` to **`kaggle/runpod_cpt_v3/`** (new dir). Delete the GPU. Keep the volume.

C only later, on the **new** adapter, with approval. Keep Hub `…-cpt-lora-v2` if the new run is worse.

---

## Paste into the send-to-run chat

```
S5 send-to-run. Preflight done. No C, no Kaggle, no merge, no Hub overwrite. Do not re-run A, mix, Wave 3, or confession fetch.

Copy kaggle/a_output_v3 (NOT a_output). Junction may resolve to D:\search-sermons-cpt\a_output_v3. HF 51417 train / 520 val. Mix SHA256 23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973.

Volume 7hb931c5oe US-IL-1 75GB theology-cpt-v3. runpodctl only (MCP create-pod drops the mount). RTX 4090, template runpod-torch-v280, no ports, terminate-after >= 14h. PREV_RUN_CHECKPOINT empty. Scp results to kaggle/runpod_cpt_v3/. Fallback LoRA stays …-cpt-lora-v2 SHA256 319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478.

Checklist: continued_pretrain/CORPUS_V3_S5_RUN_CHECKLIST.md
```
