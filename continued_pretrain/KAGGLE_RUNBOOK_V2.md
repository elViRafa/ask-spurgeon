# Kaggle runbook — CPT v2 (Fable 5)

Local code/data work is done. This is the **operator path on Kaggle T4**.

## 0. What is ready locally

| Asset | Location |
|-------|----------|
| Mix train | `data/theology_mix_train.txt` (~51.5M chars, max doc 7k) |
| Manifest | `data/theology_mix_manifest.json` (+ `verified_tokens`) |
| Holdouts | `data/holdouts/{spurgeon,puritan,confession,general}_holdout.txt` |
| MCQ | `data/catechism_mcq.json` (WSC 50 + Heidelberg 42) |
| M1 gate notes | `data/M1_BASE_MODEL_GATE.md` |
| Local preflight | `python continued_pretrain/scripts/13_local_preflight.py` → `data/preflight_report.json` |
| Package zip | `python continued_pretrain/scripts/12_package_kaggle_corpus.py` → `data/kaggle_upload/` |
| Notebooks | `notebooks/{A,B,C}_*_sota.ipynb` (from `_gen_sota_notebooks.py`) |

### Recommended `MAX_STEPS` (v7 after C v4 §5 FAIL)

Expanded mix D3 ≈ **15.6M** verified tokens; tokens/step = 1 × 16 × 2048 = **32 768**.

**`MAX_STEPS = 476`**, clamped after pack to `ceil(packed_rows / 16)` (B v6 pack was 7255 rows → **~454**). That is **one packed epoch**.

Do **not** keep the v4/v6 cap of 100. C v4 scored B v6 **step 25** (819k tokens, ~5.5% of an epoch) and still missed §5. Early-stop on `eval_spurgeon_loss` (patience 2) still aborts if eval rises.

If `eval_spurgeon_loss` is **rising** by step 50 **with embed LoRA on**: set `LEARNING_RATE = 1e-5` and re-run — do not only raise steps.

Also: **one-doc padded rows** (`MANUAL_PACK=True`, `PACKING_MODE=one_doc_padded`, `packing=False`, `PAD_TO_MAX=False`). D1 requires pre-tokenized `input_ids`/`labels` and no row > 2048; D2 `multi_doc_rows` must be **0**. **`TRAIN_EMBEDDINGS=True`** at batch 1×16 (v5 OOM was batch 2 + embeds). Optional GDN LoRA on this path. `GPU_PROFILE` is **auto** (T4 → `t4` 4-bit; sm_80+ → `ampere` bf16). Override with env `GPU_PROFILE=t4|ampere`. Runpod: [`RUNPOD_RUNBOOK.md`](RUNPOD_RUNBOOK.md).

### Mix shares (last rebuild with 10% PD replay)

| Bucket | Share | Target |
|--------|-------|--------|
| Spurgeon | ~40–45% | 40–50% |
| Puritan | ~40–45% | 30–40% |
| Confession | ~5–6% | 3–6% |
| Bible | ~3–4% | 2–4% |
| General replay | ~10% | 8–12% |

### Flagship model defaults (M1 + RC4)

- Model: **`unsloth/Qwen3.5-4B-Base`**
- **`tie_word_embeddings: true`** → notebook defaults **`TRAIN_LM_HEAD = False`**
- Architecture is hybrid (`linear_attention` + `full_attention` + vision config) — VL Processor ignores native packing; use document-isolated manual pack
- Unsloth may force float32 train path for this arch
- Fallback: **`unsloth/Mistral-7B-v0.3`** if hybrid Qwen3.5 fails (not Qwen2.5-3B)

---

## 1. Upload corpus

```bash
# local
python continued_pretrain/scripts/12_package_kaggle_corpus.py
```

Kaggle → New Dataset → upload `theology-cpt-corpus.zip` → name **`theology-cpt-corpus`**.

Contents expected by A_sota:

- `theology_mix_train.txt`
- `theology_mix_manifest.json`
- `holdouts/*_holdout.txt`
- `catechism_mcq.json`

---

## 2. Notebook A — dataset prep

1. Mount `theology-cpt-corpus`
2. Open `A_data_prep_sota.ipynb`
3. Confirm paths to corpus root
4. Run all — **G2 must not raise** (≥2 domain buckets)
5. Save output as Kaggle dataset **`theology-cpt-dataset`**  
   (`theology_dataset/` + `theology_holdouts/`)

---

## 3. Notebook B — training (session 1 = diagnostics)

1. Mount **`theology-cpt-dataset`** (must include **`theology_holdouts/spurgeon`** as HF dataset — not corpus `holdouts/*.txt`)
2. GPU: **T4** (not P100). CLI push must set `"machine_shape": "NvidiaTeslaT4"` — `enable_gpu` alone defaults to P100 and crashes with modern PyTorch cu128 (`cudaErrorNoKernelImageForDevice`).
3. Run install cell → note `requirements_lock.txt` (G1); GPU sanity cell must print T4 / sm_75+
4. Config (**v7+**): flagship 4B, `TRAIN_LM_HEAD=False`, **`TRAIN_EMBEDDINGS=True`**, **r=32**, **LR 1e-5**, **MAX_STEPS≈packed epoch**, **document-isolated manual pack @ 2048**, `METRIC_FOR_BEST=eval_spurgeon_loss`, `EVAL_DOCS_PER_BUCKET=2`
5. Run model + PEFT + **D4** cell → record tied-storage; **must** list trainable `embed_tokens` (or warn)
6. Build trainer + **D1 / D2** → packed rows ≪ raw docs; **eval keys must include `spurgeon`**; quiet EarlyStopping patience=2
7. Measure s/step; session budget: `steps_this_session ≈ floor(8h × 3600 / s_per_step)` (cap still `MAX_STEPS`; resume if needed)
8. Train; save adapter + run config; confirm printed SHA256(saved LoRA) == SHA256(best ckpt)
9. **If hybrid model OOMs / fails to load** → drop eval docs/buckets first; only then `TRAIN_EMBEDDINGS=False`; last resort `MODEL_NAME = "unsloth/Mistral-7B-v0.3"`

Push **B v7** from regenerated notebooks. **Do not run C until B v7 completes.** C v4 already scored B v6 checkpoint-25.

### Resume sessions

- Same `MAX_STEPS`, set `PREV_RUN_CHECKPOINT` to last checkpoint path  
- Cosine schedule stays consistent

### Offload dir

Writable: `/kaggle/working/unsloth_offload` (already set in notebook)

---

## 4. Notebook C — eval (**only after B v7**)

1. Mount **B v7** adapter + holdouts + `catechism_mcq.json` (not the B v6 kernel unless you intend to re-score a known FAIL)
2. `EVAL_BASE = True`, `RUN_MERGE = False` until §5 **holdout PPL** passes
3. Leave `ADAPTER_OVERRIDE = None` (loads `theology_cpt_lora` = best-at-end). **Do not** override to B v6 `checkpoint-25` (C v4 already scored it; SHA256 match).
4. `SCORE_LAST_CHECKPOINT=True` runs extra PPL on the highest `checkpoint-*` vs best LoRA (selection check only)
5. Record Δ PPL table, greedy probes, MCQ (WSC + Heidelberg)
6. **Ship on holdout PPL first** (RC5: MCQ alone is not enough)
7. Only then set `RUN_MERGE = True` and export

### Ship criteria (plan §5)

- Puritan/confession PPL ≥15% better than base  
- General ≤10% worse than base  
- Heidelberg MCQ ≥ +10 pts absolute vs base  
- Greedy style preferred over base  

---

## 5. Pin Unsloth (G1) after first good session

1. In Kaggle: `!pip show unsloth` or inspect install log for commit  
2. Set `UNSLOTH_GIT_REF` in `_gen_sota_notebooks.py` and regenerate notebooks  
3. Keep last-known-good sha in this runbook

```
UNSLOTH_GIT_REF = "<commit after first good T4 run>"
```

---

## 6. Stretch (later)

| ID | What |
|----|------|
| E1 | Rebuild mix with `--author-tags` |
| E2 | `MAX_SEQ_LENGTH=4096`, batch 1 |
| E3 | 9B only after VRAM probe cell passes (&lt;~15 GB reserved) |

---

## Local rebuild cheatsheet

```bash
# After adding sources
python continued_pretrain/scripts/07_build_theology_mix.py \
  --target-spurgeon-share 0.45 \
  --replay-frac 0.10 \
  --replay-txt continued_pretrain/data/replay/general_replay.txt

python continued_pretrain/scripts/06_verify_tokens.py --mix
python continued_pretrain/scripts/09_build_catechism_mcq.py
python continued_pretrain/scripts/13_local_preflight.py
python continued_pretrain/scripts/12_package_kaggle_corpus.py
python continued_pretrain/scripts/_gen_sota_notebooks.py
```
