# CPT corpus v3 — S5 C send-to-run checklist

**GPU eval session only.** S5 B already finished (early-stop 375, best 325). Do **not** re-train. Do **not** merge. Do **not** overwrite Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`. Do **not** re-C the v2 LoRA.

Still **no GPU** until the operator approves C. Packing recipe is irrelevant here (eval only).

Runbook: [`RUNPOD_RUNBOOK.md`](RUNPOD_RUNBOOK.md) (C section). B artifacts: [`kaggle/runpod_cpt_v3/README.md`](kaggle/runpod_cpt_v3/README.md).

---

## Score this adapter (not v2)

| Item | Value |
|------|--------|
| LoRA | `kaggle/runpod_cpt_v3/theology_cpt_lora` |
| On disk | junction → `D:\search-sermons-cpt\runpod_cpt_v3\theology_cpt_lora` if C: is full |
| SHA256 `adapter_model.safetensors` | `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303` |
| Best train step | 325 (`eval_spurgeon` 2.254118) |
| Holdouts | `kaggle/a_output_v3/theology_holdouts/` (**not** `kaggle/a_output`) |
| MCQ | `data/catechism_mcq.json` |
| Script | `scripts/eval_cpt_sota.py` |

`eval_cpt_sota.py` defaults `EXPECTED_ADAPTER_SHA256` to the **v2** hash. C **must** export the v3 hash or `--preflight` fails.

---

## Do not copy

| Path | Why |
|------|-----|
| `kaggle/a_output/theology_holdouts/` | v2 probe holdouts |
| `kaggle/runpod_cpt_v2/theology_cpt_lora` | keepable fallback; do not re-C |
| `theology_dataset/` (51k train rows) | C does not need the mix |
| git clone of this repo | other `theology_cpt_lora` dirs exist |

---

## Copy onto the pod (`/workspace`)

```text
kaggle/runpod_cpt_v3/theology_cpt_lora/     →  /workspace/theology_cpt_lora/
kaggle/a_output_v3/theology_holdouts/       →  /workspace/theology_holdouts/
data/catechism_mcq.json                     →  /workspace/catechism_mcq.json
scripts/eval_cpt_sota.py                    →  /workspace/eval_cpt_sota.py
```

If `scp` fails on a junction, send from `D:\search-sermons-cpt\`.

---

## Provision

Prefer **runpodctl** + volume `7hb931c5oe` US-IL-1 if `RUNPOD_API_KEY` exists. MCP `create-pod` still **drops** `networkVolumeId`.

Proven fallback (v2 C and S5 B): MCP create-pod, RTX 4090, **75 GB container disk**, SSH key `~/.ssh/runpod_cpt`, ports `22/tcp` only, **no Jupyter**. `--terminate-after` **2h**. Prefer community; Secure same DC if community is empty.

---

## Eval

Pod `--env` is **not** in the SSH shell. Export in the same shell as `nohup`:

```bash
export CPT_WORK_ROOT=/workspace CPT_DATA_ROOT=/workspace
export HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
export REQUIRE_AMPERE=1
export EXPECTED_ADAPTER_SHA256=ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303
python3 -u /workspace/eval_cpt_sota.py --preflight    # fail → delete GPU now
python3 -u /workspace/eval_cpt_sota.py --install      # PEP 668; exits; fail → delete GPU now
nohup python3 -u /workspace/eval_cpt_sota.py > /workspace/cpt_eval.log 2>&1 &
tail -f /workspace/cpt_eval.log
```

Walk away only after the log shows: `gpu_profile=ampere`, `load_in_4bit=False`, SHA256 OK, `ADAPTER_PATH=.../theology_cpt_lora`, holdouts found, `RUN_MERGE=False`.

Scp `theology_cpt_eval_metrics.json` + `cpt_eval.log` to **`kaggle/runpod_cpt_v3/`**. Delete the GPU. Keep the volume.

---

## How to read the numbers

Do **not** mix these tables:

1. **Probe (this C vs this C’s Ampere bf16 base):** all four holdout PPLs better than that base → probe PASS. That is not a merge.
2. **Keep vs Hub v2 (Ampere C 2026-08-27):** spurgeon 13.28 (−7.25%), puritan 5.68 (−5.05%), confession 6.73 (−6.98%), general 13.20 (−1.73%). If this C is worse, **keep** Hub `…-cpt-lora-v2` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`.
3. **Merge / §5:** −15% on puritan and confession vs **this** C’s base. Probe pass ≠ merge. `RUN_MERGE` stays false until that bar.

Do not mix in Kaggle C v4 T4 4-bit PPLs.

---

## After C (not this checklist)

Decide whether a **lower-LR continue** on this LoRA is worth it using [`NEXT_CPT_MORE_TOKENS.md`](NEXT_CPT_MORE_TOKENS.md). Do not start that B in the C session. Optimizer was never copied; HF resume is not available.

---

## Paste into the send-to-run chat

```
S5 C send-to-run. B is done (best 325, early-stop 375). No retrain, no merge, no Hub overwrite, no Kaggle, no re-C of v2.

Score kaggle/runpod_cpt_v3/theology_cpt_lora SHA256 ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303.
Holdouts from kaggle/a_output_v3 (NOT a_output). MCQ data/catechism_mcq.json.
export EXPECTED_ADAPTER_SHA256 to the v3 hash (script default is still v2).
Ampere bf16, RUN_MERGE=False. Scp metrics to kaggle/runpod_cpt_v3/. Delete GPU.
Keep Hub …-cpt-lora-v2 if this C is worse than v2 Ampere scorecard.

After C only: continued_pretrain/NEXT_CPT_MORE_TOKENS.md
Checklist: continued_pretrain/CORPUS_V3_S5_C_CHECKLIST.md
```
