# Kaggle runbook — CPT v2 (Fable 5)

Local code/data work is done. This is the **operator path on Kaggle T4**.

## 0. What is ready locally

| Asset | Location |
|-------|----------|
| Mix train | `data/theology_mix_train.txt` (~27M chars, max doc 7k) |
| Manifest | `data/theology_mix_manifest.json` (+ `verified_tokens`) |
| Holdouts | `data/holdouts/{spurgeon,puritan,confession,general}_holdout.txt` |
| MCQ | `data/catechism_mcq.json` (WSC 50 + Heidelberg 42) |
| M1 gate notes | `data/M1_BASE_MODEL_GATE.md` |
| Local preflight | `python continued_pretrain/scripts/13_local_preflight.py` → `data/preflight_report.json` |
| Package zip | `python continued_pretrain/scripts/12_package_kaggle_corpus.py` → `data/kaggle_upload/` |
| Notebooks | `notebooks/{A,B,C}_*_sota.ipynb` (from `_gen_sota_notebooks.py`) |

### Recommended `MAX_STEPS`

From D3 (~8.2M tokens) and batch 2 × accum 8 × seq 2048 = **32 768 tok/step**:

**`MAX_STEPS = 250`** for ~1 epoch (already set in `B_training_sota.ipynb`).

Reconfirm with D1 packed `tokens_per_epoch_est / 32768` after the trainer is built.

### Mix shares (last rebuild with 10% PD replay)

| Bucket | Share | Target |
|--------|-------|--------|
| Spurgeon | ~40–45% | 40–50% |
| Puritan | ~40–45% | 30–40% |
| Confession | ~5–6% | 3–6% |
| Bible | ~3–4% | 2–4% |
| General replay | ~10% | 8–12% |

### Flagship model defaults (M1)

- Model: **`unsloth/Qwen3.5-4B-Base`**
- **`tie_word_embeddings: true`** → notebook defaults **`TRAIN_LM_HEAD = False`**
- Architecture is hybrid (`linear_attention` + `full_attention` + vision config) — **first session must prove Unsloth loads + trains**
- Fallback: `unsloth/Qwen2.5-3B` if hybrid fails

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

1. Mount `theology-cpt-dataset` (+ optional corpus for manifest hash)
2. GPU: T4 ×1, Internet on for Unsloth install
3. Run install cell → note `requirements_lock.txt` (G1)
4. Config: flagship 4B, `TRAIN_LM_HEAD=False`, packing 2048
5. Run model + PEFT + **D4** cell → record tied-storage result
6. Build trainer + **D1 / D2** cells → confirm tokens/epoch & EOS counts
7. Measure s/step over ~50 steps; set `MAX_STEPS` to full epoch  
   (~ domain tokens / 32768; expect multi-k steps for ~7M tok epoch)
8. Session budget: `steps_this_session ≈ floor(8h × 3600 / s_per_step)`
9. Train; save adapter + run config
10. **If hybrid model OOMs / fails to load** → set `MODEL_NAME = "unsloth/Qwen2.5-3B"` and restart session

### Resume sessions

- Same `MAX_STEPS`, set `PREV_RUN_CHECKPOINT` to last checkpoint path  
- Cosine schedule stays consistent

### Offload dir

Writable: `/kaggle/working/unsloth_offload` (already set in notebook)

---

## 4. Notebook C — eval (after ≥1 epoch)

1. Mount adapter + holdouts + `catechism_mcq.json`
2. `EVAL_BASE = True`, `RUN_MERGE = False` until §5 gates pass
3. Record Δ PPL table, greedy probes, MCQ (WSC + Heidelberg)
4. Only then set `RUN_MERGE = True` and export

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
