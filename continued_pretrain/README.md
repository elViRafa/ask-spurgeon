# Continued Pretraining Setup

Two parallel tracks:

| Track | Goal | Training notebook |
|-------|------|-------------------|
| **Phase 1 baseline** | Spurgeon-only style CPT (known-good Kaggle path) | `notebooks/B_training.ipynb` |
| **SOTA / v2 track** | Spurgeon + Puritans + theology domain CPT (Fable 5 plan) | `notebooks/B_training_sota.ipynb` |

**Policy:** Do **not** overwrite `B_training.ipynb`. SOTA work lives in `*_sota` notebooks + mix scripts.

**Flagship base (v2):** `unsloth/Qwen3.5-4B-Base` (Apache 2.0; **tied embeddings** → train `embed_tokens` only by default).  
**9B:** concession-gated experiment only (VRAM probe required).  
**Plan:** [`PLAN_FABLE5_TO_IMPROVE_CPT.md`](PLAN_FABLE5_TO_IMPROVE_CPT.md)  
**Kaggle steps:** [`KAGGLE_RUNBOOK_V2.md`](KAGGLE_RUNBOOK_V2.md)  
**M1 gate:** [`data/M1_BASE_MODEL_GATE.md`](data/M1_BASE_MODEL_GATE.md)

**Notebook source of truth (G3):** edit `scripts/_gen_sota_notebooks.py`, then regenerate — do not dual-edit notebooks and generator.

---

## Directory Structure

```text
continued_pretrain/
├── PLAN_FABLE5_TO_IMPROVE_CPT.md
├── README.md
├── configs/
│   └── train_config_cpt_theology_sota.json
├── scripts/
│   ├── 05_build_corpus.py          # Spurgeon train/holdout .txt
│   ├── 06_verify_tokens.py         # + --mix → verified_tokens (D3)
│   ├── 07_build_theology_mix.py    # multi-source mix (v2 chunk/dedup/share)
│   ├── 08_fetch_pd_sources.py      # optional PD downloads
│   ├── 09_build_catechism_mcq.py   # WSC / Heidelberg MCQ JSON
│   └── _gen_sota_notebooks.py      # regenerates *_sota notebooks
├── notebooks/
│   ├── B_training.ipynb            # Phase 1 (freeze)
│   ├── A_data_prep_sota.ipynb
│   ├── B_training_sota.ipynb
│   └── C_eval_sota.ipynb
└── data/
    ├── spurgeon_train.txt
    ├── theology_mix_train.txt
    ├── theology_mix_manifest.json
    ├── holdouts/
    └── holdouts_manual/            # Heidelberg + Belgic (never train)
```

External sources: [`data/SOURCES_SOTA_CPT.md`](../data/SOURCES_SOTA_CPT.md).

---

## Phase 1 baseline (Spurgeon-only)

```bash
python continued_pretrain/scripts/01_inventory.py
python continued_pretrain/scripts/04_holdout_split.py
python continued_pretrain/scripts/05_build_corpus.py
python continued_pretrain/scripts/06_verify_tokens.py
```

Kaggle: `A_data_prep` → `B_training` → `C_eval_and_merge`.

---

## SOTA track v2 (Fable 5)

### What changed vs v1

| Area | v1 | v2 |
|------|----|----|
| Base | Qwen2.5-3B | **Qwen3.5-4B-Base flagship** |
| Chunking | Spurgeon unchunked; trees 40k | **≤7000 chars** all buckets (F1) |
| Mix guard | Spurgeon-only OK | **≥2 domain buckets** (G2) |
| Spurgeon weight | 2.5 fixed | **share-targeted** (~0.45) |
| Dedup | file prefix only | + **paragraph dedup** + top-20 report |
| Training | warmup_steps=100, emb_lr=5e-6 | **warmup_ratio=0.03**, emb_lr=**1e-5** |
| Eval during train | mix 1% only | **per-bucket dict** |
| Eval notebook | sampled probes, EVAL_BASE=False | **greedy probes**, EVAL_BASE=True, **MCQ** |
| 9B | “flagship” | **VRAM-probe gated experiment** |

### Local data pipeline

```bash
# Optional: fetch PD Bunyan / KJV / holdout Heidelberg (network)
python continued_pretrain/scripts/08_fetch_pd_sources.py --include-holdouts

# Add more under data/puritans|confessions|bible (see SOURCES_SOTA_CPT.md)
# Hold out Heidelberg + Belgic under continued_pretrain/data/holdouts_manual/

# Spurgeon train/holdout if needed
python continued_pretrain/scripts/05_build_corpus.py

# Multi-source mix (fails if only Spurgeon unless --allow-spurgeon-only)
python continued_pretrain/scripts/07_build_theology_mix.py \
  --target-spurgeon-share 0.45 \
  --replay-frac 0.10
# Optional: --replay-txt path/to/general_replay.txt
# Optional: --replay-hf HuggingFaceFW/fineweb-edu

# Token verification → writes verified_tokens into manifest
python continued_pretrain/scripts/06_verify_tokens.py --mix

# Catechism MCQ for C_sota
python continued_pretrain/scripts/09_build_catechism_mcq.py

# Regenerate notebooks after generator edits
python continued_pretrain/scripts/_gen_sota_notebooks.py
```

Upload to Kaggle: `theology_mix_train.txt`, `theology_mix_manifest.json`, `holdouts/`, `catechism_mcq.json`.

### Kaggle

1. **A_data_prep_sota.ipynb** — G2 multi-bucket guard; build HF dataset  
2. **B_training_sota.ipynb** — D1/D2/D4 diagnostics; dual-LR CPT; per-bucket eval  
3. **C_eval_sota.ipynb** — base Δ table, greedy probes, MCQ; merge only if `RUN_MERGE=True`  

Config mirror: `configs/train_config_cpt_theology_sota.json`

### VRAM fallbacks (T4 16 GB)

1. `TRAIN_LM_HEAD = False` if D4 tied  
2. `TRAIN_EMBEDDINGS = False`  
3. `LORA_RANK = 32`  
4. `PER_DEVICE_BATCH = 1`, raise grad accum  

### 9B (E3)

Do not multi-session until ~20-step probe shows `torch.cuda.max_memory_reserved() < ~15 GB`.  
T4×2 without Unsloth is documented in the plan risk register — generally not worth it vs 4B.

---

## Success criteria (v2)

See plan §5. Headline:

- ≥4 buckets, shares in range, `verified_tokens`, non-empty holdouts  
- Domain PPL ≥15% better than base; general ≤10% worse  
- Heidelberg MCQ ≥ +10 pts vs base  
- Greedy style preferred over base  
