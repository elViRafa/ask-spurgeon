# PLAN — Fable 5 review: improving the Spurgeon/Puritans/Theology CPT

**Date:** 2026-07-12
**Scope:** Continued pre-training (CPT) of `unsloth/Qwen2.5-3B` on Kaggle T4, based on
`notebooks/B_training.ipynb` (Phase-1 baseline, frozen) and `notebooks/B_training_sota.ipynb` (v1 improvement).
**Goal:** a base model that (a) speaks with Spurgeon's voice, (b) has absorbed Puritan/Reformed
theology broadly (Owen, Watson, Bunyan, confessions, KJV register), and (c) has not forgotten
general English/knowledge.

---

## 0. TL;DR — the six things that matter most

1. **Verify the suspected 2048-token truncation bug before anything else (F1).** Step-count math
   from the baseline run strongly suggests every document was clipped to its first ~2048 tokens —
   i.e. ~78% of each sermon (the whole application/appeal section) was never trained on. If
   confirmed, fixing this is worth more than every hyperparameter change combined. Fix = chunk
   documents to ≤ ~7,000 chars at corpus-build time.
2. **The SOTA mix does not exist yet.** `theology_mix_manifest.json` shows 100% Spurgeon, 0%
   replay, empty puritan/confession/general holdouts; `data/puritans|confessions|bible/` contain
   only `.gitkeep`. The v1 *recipe* is good; the v1 *data* is the baseline data. Data acquisition
   is the real blocker and the highest-ROI work.
3. **Check Qwen2.5-3B tied embeddings (F3).** The 3B config ties `embed_tokens` and `lm_head`.
   Targeting `lm_head` in LoRA on a tied model either does nothing, errors, or silently unties —
   verify what Unsloth actually does before trusting the dual-LR recipe.
4. **Make evaluation decision-grade (F5):** per-bucket eval *during* training, deterministic
   generation probes, base-vs-adapter deltas by default, and a catechism multiple-choice
   log-likelihood score so "did it learn doctrine" becomes a number, not a vibe.
5. **Pin the environment and link data→run (F6):** `unsloth @ git+…` HEAD drifts between Kaggle
   sessions; the run config doesn't record which mix it trained on. Pin, and store the manifest
   hash + `pip freeze` in the run config.
6. **Move off Qwen2.5-3B as the base model.** It is research-licensed (**non-commercial**), two
   generations old, and tied-embedded. **Flagship = `Qwen3.5-4B-Base`** (Apache 2.0, full recipe
   or embed-only comfortably on T4 16 GB at seq 2048/batch 2, 1–2 sessions/epoch). **9B is a
   concession-gated experiment only** (mandatory VRAM probe before multi-session commit). Full
   analysis §4.1.

---

## 1. Current state (what actually exists)

### 1.1 Baseline — `B_training.ipynb` (Phase 1, frozen — do not modify)

| Aspect | Value |
|---|---|
| Model | `unsloth/Qwen2.5-3B`, 4-bit QLoRA |
| LoRA | r=32, α=64 (scale 2.0), attn+MLP only, dropout 0 |
| Trainer | `SFTTrainer`, LR 2e-4 cosine, warmup 100, wd 0.01, `adamw_8bit` |
| Batch | 2 × grad-accum 8 = 16 seq/step ≈ 32,768 tok/step; packing @ 2048 |
| Data | Spurgeon only: 3,451 train / 35 val docs, 128 MB chars ≈ ~30M tokens |
| Result | 2 epochs (432 steps), train loss ≈ 2.23, val ≈ 2.30 |
| Resume | fragile "epoch = run number" hack |

Known limitations (already identified in the v1 README): no `embed_tokens`/`lm_head`, single-domain
corpus, no replay, LR high for CPT.

### 1.2 v1 improvement — `B_training_sota.ipynb` + `07_build_theology_mix.py`

What v1 already gets right (keep all of it):

- `UnslothTrainer` + dual LR (`learning_rate=5e-5`, `embedding_learning_rate=5e-6`)
- `embed_tokens` + `lm_head` in `target_modules`; r=64 + rsLoRA
- `max_steps`-based resume instead of the epoch hack
- Multi-source mix script with Spurgeon oversampling (2.5×), replay fraction, per-bucket holdouts,
  provenance manifest
- Multi-bucket PPL eval notebook + style/doctrine/forgetting probes
- VRAM fallback ladder documented for T4

### 1.3 What is actually on disk (the gap)

- `theology_mix_manifest.json`: **buckets = {spurgeon: 100%}**, `replay_frac_target: 0.0`,
  holdouts: puritan 0, confession 0, general 0 (files exist but are 0 bytes).
- `data/puritans/`, `data/confessions/`, `data/bible/`: empty (`.gitkeep` only).
- So a v1 training run today would apply the SOTA recipe to **the same Spurgeon-only data** as the
  baseline — and per F1 below, likely truncated the same way.

---

## 2. Findings (ordered by impact)

### F1 — SUSPECTED CRITICAL: documents truncated at 2048 tokens (baseline, and v1 will inherit it)

**Evidence (from the baseline run logs):**

- Corpus: 128,003,542 chars ≈ 30M tokens across 3,451 train docs → **avg ≈ 9,000 tokens/doc**.
- Trainer banner: `Num examples = 3,451 | Num Epochs = 2 | Total steps = 432` → 216 steps/epoch.
- 216 steps × 16 seq × 2048 tok ≈ **7.1M tokens/epoch**, not ~30M.
- If packing concatenated full documents, the packed dataset would be ~30M/2048 ≈ **14–15k rows**
  → ~950 steps/epoch. Instead, steps/epoch = ceil(3451/16) = 216 **exactly matches one row per
  raw document**, which is what you get when each document is tokenized with
  `truncation=True, max_length=2048` *before* packing (all rows already full → nothing to pack).

**Implication if confirmed:** the model only ever saw the first ~20% of each sermon — the reading
of the text and the opening exposition, never the doctrine development or the closing appeal (which
is where the most distinctive Spurgeon rhetoric lives). Baseline PPL numbers are also not measuring
what we think: `C_eval` truncates holdout docs at 2048 too, so the eval is consistent, but the
"trained on ~60M tokens (2 epochs × 30M)" assumption is off by ~4×.

**Verification (run as a cell in B_sota right after trainer creation — 30 seconds):**

```python
# D1 — where did my tokens go?
import numpy as np
tds = trainer.train_dataset
n = len(tds)
lens = [len(tds[i]["input_ids"]) for i in range(0, n, max(1, n // 200))]
print(f"packed rows: {n}")
print(f"row token len: min={min(lens)}  p50={int(np.median(lens))}  max={max(lens)}")
print(f"tokens/epoch ≈ {int(n * np.mean(lens)):,}")
# Compare with the real corpus token count (06_verify_tokens.py style estimate).
# tokens/epoch << corpus tokens  →  truncation confirmed.
```

**Fix (regardless of which component truncates):** chunk every document to **≤ ~7,000 chars
(≈ 1,700–1,900 Qwen tokens)** at mix-build time, paragraph-bounded. Then no upstream tokenizer
truncation can lose text, and packing recombines chunks efficiently.

`07_build_theology_mix.py` changes:

- `load_tree(...)` already chunks at `max_chunk_chars=40_000` → lower default to **7,000**.
- `load_spurgeon_from_concat(...)` does **not** chunk at all (Spurgeon docs avg ~37k chars) →
  route each doc through `split_long_text(text, max_chars=7_000)`.
- Add `--max-chunk-chars` CLI arg (default 7000) so this is tunable.
- Optional: 200-char paragraph overlap between adjacent chunks is unnecessary if packing preserves
  order — keep it simple, no overlap.

**Expected effect:** effective Spurgeon tokens per epoch go from ~7M to ~30M. This is the single
largest lever in the entire plan.

### F2 — The multi-source corpus must be built (data is the moat)

The recipe is ready; the shelves are empty. See Phase 1 for the concrete acquisition list. Note
`07_build_theology_mix.py` prints a warning when only Spurgeon is found but **exits 0 and writes a
valid-looking mix** — add a guard so this can't silently happen again (Phase 0, G2).

### F3 — Qwen2.5-3B has tied embeddings; `lm_head` as a LoRA target may not do what v1 assumes

Qwen2.5 models at 3B and below set `tie_word_embeddings=true` (`lm_head.weight` *is*
`embed_tokens.weight`). The Unsloth CPT recipe (dual LR, train embed+head) was published on
untied models (Mistral 7B). On a tied model, three outcomes are possible depending on
Unsloth/PEFT version: error, silent no-op for `lm_head`, or automatic untying (which costs
~600 MB fp16 and changes optimizer memory). A LoRA delta on the `Embedding` forward does **not**
propagate to the output projection, so "training embeddings" and "training the head" are genuinely
different updates even when the base weight is shared.

**Verification (cell in B_sota after `get_peft_model`):**

```python
# D4 — tied embeddings check
print("tie_word_embeddings:", model.config.tie_word_embeddings)
emb  = model.get_input_embeddings().weight
head = model.get_output_embeddings().weight
print("same storage:", emb.data_ptr() == head.data_ptr())
for n, p in model.named_parameters():
    if ("embed_tokens" in n or "lm_head" in n) and p.requires_grad:
        print("trainable:", n, tuple(p.shape))
```

**Decision rule:** if Unsloth unties cleanly and VRAM holds → keep both targets. If not, prefer
**`embed_tokens` only** (input-side register adaptation for KJV-era vocabulary) and drop `lm_head`
from `target_modules`; the dual-LR mechanism still applies.

### F4 — Document boundaries in the packed stream (EOS) need proof

`A_data_prep_sota.ipynb` splits on `<|endoftext|>` and **strips** it; the pipeline then relies on
the trainer to re-insert EOS between packed documents. Qwen's tokenizer does not auto-append EOS.
If boundaries are missing, the model learns cross-document bleed and never learns to stop.

```python
# D2 — EOS boundary check (first 5 packed rows)
eos = tokenizer.eos_token_id
for i in range(5):
    row = trainer.train_dataset[i]["input_ids"]
    print(i, "eos count:", list(row).count(eos))
print(tokenizer.decode(trainer.train_dataset[0]["input_ids"][:200]))
```

**Fix if count is 0:** map the dataset before training:
`ds = ds.map(lambda x: {"text": x["text"] + tokenizer.eos_token})`.

### F5 — Evaluation blind spots

1. In-training eval uses the mix's 1% split → dominated by (oversampled) Spurgeon. You cannot see
   forgetting or Puritan progress *during* the run — only after, in C_sota.
2. Generation probes use `do_sample=True, temperature=0.7` with no seed → not comparable across
   checkpoints/models.
3. `EVAL_BASE = False` by default → headline numbers ship without a baseline delta.
4. No doctrine *metric* — only eyeballing generations.

Fixes in Phases 2–3 (per-bucket eval dict, greedy probes, `EVAL_BASE=True`, catechism MCQ).

### F6 — Reproducibility and process

1. `pip install "unsloth[kaggle-new] @ git+…"` floats with upstream HEAD → two sessions of the
   same notebook can run different code. Pin to a tag/commit that you have verified on T4 once
   (e.g. `…unsloth.git@<commit-sha>`), and record `pip freeze` in the run config.
2. The run config JSON doesn't record **which mix** it trained on → store the manifest's
   `created_at` + a SHA256 of `theology_mix_manifest.json`.
3. `*_sota` notebooks are **generated** by `scripts/_gen_sota_notebooks.py`. Decide one source of
   truth: either make all v2 edits in the generator and regenerate, or retire the generator and
   edit notebooks directly (then delete/mark the script). Editing both will end in silent
   overwrites.

### F7 — Forgetting risk profile

- v1 targets 10% general replay — right ballpark (continual-pretraining literature consistently
  shows small replay fractions, even 1–5%, prevent most forgetting; 10% is comfortable).
- The forgetting probe in C_sota includes **Python code**, but the planned replay (FineWeb-Edu) is
  prose-heavy. If preserving code matters, add ~2% code slice to replay; if it doesn't, swap the
  probe for prose-domain probes (history, science) so the metric matches the intent.
- Optional: if the model will ever serve Portuguese users (the Ask Spurgeon app), a ~1–2% PT-BR
  slice in replay is cheap insurance. Not required for v2.

---

## 3. The plan

### Phase 0 — Diagnostics & guards (½ day; one short T4 session + local edits)

| ID | Task | Acceptance |
|---|---|---|
| D1 | Truncation diagnostic (cell above) on the *current* dataset in a throwaway B_sota session | Know real tokens/epoch; truncation confirmed or ruled out |
| D2 | EOS boundary diagnostic | ≥1 EOS per packed row, or fix applied |
| D3 | Real token counts per bucket: extend `06_verify_tokens.py` to read `theology_mix_train.txt` + manifest buckets (sample-ratio method is fine) | Manifest gains `verified_tokens` field |
| D4 | Tied-embeddings check → decide `lm_head` in/out | Decision recorded in config JSON |
| G1 | Pin unsloth install to tested commit; save `pip freeze` to `/kaggle/working/requirements_lock.txt` | Same env across sessions |
| G2 | Add guard in `07_build_theology_mix.py` **and** `A_data_prep_sota.ipynb`: if buckets < 2 (or puritan chars == 0), raise unless `--allow-spurgeon-only` | Impossible to silently train "SOTA" on Spurgeon-only data |
| G3 | Pick single source of truth for notebooks (generator vs. direct edits) | No dual-maintenance |
| M1 | Base-model verification gate (§4.1): `Qwen/Qwen3.5-4B-Base` exists on HF, `tie_word_embeddings` in its config.json, Unsloth 4-bit build available, D4 on the new base | Go/no-go on Qwen3.5-4B-Base as **flagship** |

### Phase 1 — Data v2 (1–2 days of collection; the highest-ROI phase)

**1a. Acquire public-domain texts** (all available on CCEL / Project Gutenberg / monergism /
Internet Archive; log provenance in folder names as `data/puritans/<author>/<work>.txt`):

| Bucket | Priority works | Rough size |
|---|---|---|
| `puritans/owen` | Mortification of Sin, Communion with God, Glory of Christ, Indwelling Sin | 3–6M chars |
| `puritans/watson` | Body of Divinity, All Things for Good, The Godly Man's Picture | 2–4M chars |
| `puritans/bunyan` | Pilgrim's Progress, Grace Abounding, The Holy War, sermons | 3–5M chars |
| `puritans/brooks` | Precious Remedies Against Satan's Devices, Mute Christian | 2–3M chars |
| `puritans/sibbes` | The Bruised Reed, The Soul's Conflict | 1–2M chars |
| `puritans/baxter` | The Saints' Everlasting Rest, The Reformed Pastor | 3–5M chars |
| `puritans/flavel`, `charnock`, `edwards` (stretch) | The Mystery of Providence; Existence & Attributes of God; Religious Affections + sermons | 5–15M chars |
| `puritans/henry` (stretch, big volume) | Matthew Henry commentary (selected books) | 10–30M chars |
| `confessions/westminster` | WCF + Larger & Shorter Catechisms | ~1M chars |
| `confessions/1689` | 1689 LBCF + Baptist catechism | ~0.4M chars |
| `confessions/institutes` | Calvin's Institutes (Beveridge, PD) | 3–5M chars |
| `bible/kjv` | Full KJV | ~4.3M chars |
| **HELD OUT — do not place in training dirs** | **Heidelberg Catechism + Belgic Confession** → save under `continued_pretrain/data/holdouts_manual/` | doctrine-generalization eval (§ Phase 3) |

Realistic first-pass total: **40–80M chars of Puritans (~10–20M tokens)**, more with the stretch
items. OCR quality gate: spot-check each file; reject if garbled (Archive.org OCR varies; prefer
CCEL/Gutenberg transcriptions).

**1b. Replay:** FineWeb-Edu sample via `--replay-hf HuggingFaceFW/fineweb-edu` (or a local
`replay.txt`), target `--replay-frac 0.10`. Optionally splice ~2% code if code preservation is a
goal (see F7).

**1c. Chunking fix (F1):** patch `07_build_theology_mix.py` as described — Spurgeon docs through
`split_long_text`, default `max_chunk_chars=7000` everywhere.

**1d. Dedup upgrade (cheap version):** current dedup is a 300-char-prefix fingerprint per file.
Add: (i) exact-duplicate paragraph removal across the whole mix (hash set of normalized
paragraphs ≥ 200 chars — catches repeated front-matter, boilerplate prayers, duplicated editions);
(ii) report top-20 most-frequent paragraphs in the manifest for manual review. Skip MinHash unless
(ii) reveals a real problem.

**1e. Share targeting:** with chunked Spurgeon at 128M chars, `spurgeon_weight=2.5` gives
320M weighted chars — it would swamp a 50M-char Puritan bucket (~80% share). Pick the weight from
the target share instead:

```
spurgeon_weight = target_share × total_other_chars / (128M × (1 − target_share))
```

Target composition (char share after weighting): **Spurgeon 40–50%, Puritan 30–40%,
confessions 3–6%, Bible 2–4%, general replay 8–12%.** With ~50M chars of Puritans that means
`spurgeon_weight ≈ 0.7–1.0` (i.e. *no* oversampling — possibly subsampling); with ~150M chars of
Puritans, `spurgeon_weight ≈ 1.5–2.0`. Repetition stays well inside the safe zone (data-constrained
scaling results show ≤4 epochs of repeats ≈ fresh data).

**1f. Rebuild + verify:** run the mix script, then D3. Acceptance: manifest shows ≥4 buckets with
shares inside the targets, all holdout files non-empty, verified token total recorded, and no doc
> 8,000 chars.

### Phase 2 — Training v2 (edits to `B_training_sota.ipynb`, or its generator per G3)

Hyperparameter deltas (everything not listed stays as v1):

| Setting | v1 | v2 | Why |
|---|---|---|---|
| `warmup_steps=100` | fixed | `warmup_ratio=0.03` | robust to corpus-size changes |
| `embedding_learning_rate` | 5e-6 | **1e-5** | Unsloth's published CPT pairing with 5e-5 body LR; 5e-6 is the conservative floor — keep as fallback if loss spikes (T4 = fp16) |
| `eval_dataset` | mix 1% split | **dict**: `{"mix": …, "spurgeon": …, "puritan": …, "general": …}`, ≤8 docs each | see forgetting/domain progress *during* training |
| best model | none | `load_best_model_at_end=True`, `metric_for_best_model="eval_mix_loss"` | don't ship the last checkpoint by accident |
| `save_total_limit` | 3 | 2 | Kaggle 20 GB disk headroom with embed offload |
| `report_to` | none | `wandb` (optional, Kaggle secret) | loss curves across resumed sessions |
| run config | params only | + manifest SHA256, unsloth commit, `pip freeze` path, D1–D4 results | data→run traceability |
| `target_modules` | incl. `lm_head` | per D4 decision | F3 |
| epochs | 1.0 | 1.0, then *optionally* resume +1 if mix-val still falling and general PPL flat | Muennighoff-safe repetition budget |

Per-bucket eval wiring (Trainer supports a dict natively — metrics come out as
`eval_spurgeon_loss`, `eval_puritan_loss`, …):

```python
from datasets import load_from_disk
eval_sets = {"mix": split_test}
for name in ["spurgeon", "puritan", "confession", "general"]:
    p = os.path.join(LOCAL_HOLDOUT_PATH, name)
    if os.path.exists(p):
        ds = load_from_disk(p)
        eval_sets[name] = ds.select(range(min(8, len(ds))))
trainer = UnslothTrainer(..., eval_dataset=eval_sets, args=training_args)
```

**Session/step budget (Kaggle 9h/session, 30h/week):**

- tokens/step = 16 × 2048 = 32,768. For a ~110M-token mix → **~3,300–3,600 steps/epoch**.
- Measure s/step over the first 50 steps, then set
  `MAX_STEPS = steps_per_epoch` (fixed!) and plan sessions:
  `steps_this_session ≈ floor(8h × 3600 / s_per_step)`.
- Resume across sessions with the **same `MAX_STEPS`** + `PREV_RUN_CHECKPOINT` (cosine schedule
  stays consistent because it is computed from `max_steps`). Expect 1–2 sessions/epoch on T4 with
  embeddings trained; embed/lm_head training costs extra — if s/step > ~14s, apply the VRAM/speed
  fallback ladder from the README.
- Known Kaggle gotcha (from project memory): Unsloth offloads embeddings to disk when training
  them — ensure the offload dir is **writable** (`/kaggle/working` or `/tmp`), not the read-only
  input mount.

### Phase 3 — Evaluation v2 (edits to `C_eval_sota.ipynb`)

1. **`EVAL_BASE = True` by default** for the headline run; print a Δ-table:
   rows = buckets, cols = base / Phase-1 adapter / v2 adapter, values = PPL and %Δ vs base.
   (Load the Phase-1 adapter as a third scored model — it's the honest comparison the success
   criteria already promise.)
2. **Deterministic probes:** keep the sampled generations for flavor, but add
   `do_sample=False` (greedy) versions of every style/doctrine/forgetting prompt with a fixed
   seed — those are the ones you compare across checkpoints.
3. **Catechism MCQ metric (new):** score doctrine as multiple-choice log-likelihood — for each
   catechism question, the model must rank the true answer above 3 distractor answers sampled from
   *other* questions of the same catechism.
   - **WSC set** (in training data) → measures absorption/memorization.
   - **Heidelberg set** (held out per Phase 1a) → measures doctrine generalization.

```python
import torch

def option_logprob(model, tok, prompt, option):
    full = tok(prompt + " " + option, return_tensors="pt").to("cuda")
    p_len = tok(prompt, return_tensors="pt")["input_ids"].size(1)
    with torch.no_grad():
        logits = model(**full).logits[:, :-1].float()
    ids = full["input_ids"][:, 1:]
    lp = torch.log_softmax(logits, -1).gather(-1, ids.unsqueeze(-1)).squeeze(-1)
    return lp[0, p_len - 1:].mean().item()

def mcq_accuracy(model, tok, items):
    # items: [{"q": str, "a": str, "distractors": [str, str, str]}]
    hits = 0
    for it in items:
        opts = [it["a"], *it["distractors"]]
        scores = [option_logprob(model, tok, f"Q. {it['q']}\nA.", o) for o in opts]
        hits += int(scores.index(max(scores)) == 0)
    return hits / len(items)
```

   Build `items` automatically by parsing the Q/A structure of the catechism files (~107 WSC +
   129 Heidelberg items; cap at 50 each for runtime). Report base vs v2.
4. **Merge gate:** only run `save_pretrained_merged` / GGUF after the success criteria (§5) pass.
   Reuse the known GGUF vocab-shift fix from project memory if exporting to Ollama.

### Phase 4 — Stretch experiments (after v2 ships, one variable at a time)

| ID | Experiment | Hypothesis |
|---|---|---|
| E1 | **Author-tag conditioning:** prepend a light header to every doc at mix build (`[AUTHOR: John Owen] [WORK: The Mortification of Sin]\n\n`) | enables "write like Owen / like Spurgeon" steering at inference; makes multi-author CPT *controllable* instead of a style blend |
| E2 | `MAX_SEQ_LENGTH = 4096` (batch 1 × accum 16) | sermons are ~9k tokens; longer context teaches discourse structure that 2048-chunking cannot |
| E3 | **9B concession experiment (not flagship):** **`Qwen3.5-9B-Base`** — full dual-LR embed+lm_head is over-budget on single-T4 at seq 2048; only proceed after mandatory VRAM probe (§4.1) lands under ~15 GB reserved with headroom. Expect heavy concessions (embed-only / shorter seq / smaller batch) if probe fails. Selection analysis + M1 in §4.1 | optional capacity stretch after 4B flagship ships; default path is stay on 4B |
| E4 | Replay composition sweep (5% vs 10%; +2% code) | quantify the forgetting/absorption trade-off |

**Beyond CPT (out of scope here):** the CPT output is a *completion* model. The instruction phase
(existing `fine_tuning/` pipeline) can bootstrap from this corpus — catechism Q/A pairs are
ready-made seed SFT data. Plan that after v2 evals pass.

---

## 4. Base model & target v2 configuration

### 4.1 Base model selection (reviewed 2026-07-12, web-verified)

The baseline's `Qwen2.5-3B` is **no longer the best available choice**: it ships under the Qwen
*Research* License (non-commercial — a blocker if Ask Spurgeon is ever deployed), it is two model
generations old, and its tied embeddings are the root of F3. Candidates that fit the project
constraints (Kaggle T4 16 GB, Unsloth 4-bit QLoRA, embed-training CPT recipe, GGUF/Ollama export),
with epoch time relative to the current 3B on the same ~110M-token mix (params-scaling estimates —
measure s/step over the first 50 steps before trusting them):

| Model | Params | License | Embeddings (F3) | Vocab | Epoch time | Fit for this project |
|---|---|---|---|---|---|---|
| `Qwen2.5-3B` *(current)* | 3.1B | ⚠️ Qwen Research (non-commercial) | tied | 152k | 1.0× | Known-good in this repo; keep only for Phase-0 diagnostic continuity |
| `Llama-3.2-3B` | 3.2B | Llama Community | tied | 128k | ~1.05× | No edge over Qwen3.5-4B — skip |
| `Qwen3-4B-Base` | 4.0B | Apache 2.0 | tied | 152k | ~1.3× | Superseded by Qwen3.5-4B |
| **`Qwen3.5-4B-Base`** ✅ | ~4B | Apache 2.0 | tied (likely — M1) | ~152k | ~1.3× | **Flagship**: full untied recipe (if 4B is untied) or embed-only comfortably on T4 16 GB @ seq 2048/batch 2; 1–2 sessions/epoch |
| `Gemma-4-E4B` (base) | ~4.5B eff. | Apache 2.0 | exotic arch (MatFormer, multimodal) | ~256k | ~1.4× | CPT-plumbing risk; this project already hit Gemma template/processor bugs; costliest embed training |
| `Mistral-7B-v0.3` | 7.2B | Apache 2.0 | **untied** | **33k** | ~2.1× | Unsloth's CPT reference model; cheapest embed+lm_head training; oldest/weakest base here |
| `Llama-3.1-8B` | 8.0B | Llama Community | untied | 128k | ~2.4× | Best literary-English prior of the older gen; license naming/attribution strings |
| **`Qwen3.5-9B-Base`** ⚠️ | ~9B | Apache 2.0 | untied (expected — M1) | ~152k | ~2.6× | **Concession experiment only**: full dual-LR recipe over-budget on single T4 @ seq 2048; requires VRAM probe + concessions (see below) |

**Excluded:** `Qwen2.5-7B` / `Qwen3-8B` (superseded by Qwen3.5-9B), `Gemma-2-9B` (tied + 256k
vocab + old custom license), `Gemma-4-12B/26B/31B` and `Phi-4-14B` (beyond comfortable T4
QLoRA-CPT), Llama 4 (MoE, far too big).

**Verdict (two-tier — revised 2026-07-13):**

1. **Flagship (v2 main path) → `Qwen3.5-4B-Base`.** Not merely the dev-cycle default: 4B is the
   model we actually ship CPT on. It runs the full untied dual-LR recipe *if* M1 shows untied
   embeddings, or `embed_tokens`-only comfortably if tied — either way within 16 GB at seq
   2048 / batch 2, in **1–2 sessions/epoch**. Iteration speed and recipe fidelity both land
   here; English-register adaptation (not a new script) means the tied/embed-only fallback
   costs little if D4 requires it.
2. **Concession-gated experiment only → `Qwen3.5-9B-Base`.** Do **not** plan a multi-session 9B
   run as the flagship. The full dual-LR embed+lm_head recipe at seq 2048 is over-budget on a
   single T4 16 GB. Estimated embedding matrix cost (~2.5 GB) could swing ±0.5 GB — exact
   hidden size / layer count for Qwen3.5-9B were not web-verified at plan time — but not enough
   to change the verdict that the full recipe does not fit. Treat 9B as "fits only with
   concessions" (e.g. embed-only, shorter seq, batch 1, drop head target) and only after the
   empirical probe below.

Fallback if 4B hits VRAM walls with embedding training: `Mistral-7B-v0.3` (33k vocab makes the
embed/head matrices ~5× cheaper than Qwen's).

**Verification gate (M1) — 10 minutes, run before switching (also listed in Phase 0):**

- [ ] `Qwen/Qwen3.5-4B-Base` exists on HF; read `tie_word_embeddings` in `config.json`
- [ ] Unsloth publishes a 4-bit build (or dynamic quant) of it
- [ ] D4 diagnostic passes after `get_peft_model` on the new base
- Any check fails → stay on `Qwen2.5-3B` for v2 and demote the swap back to a stretch experiment.

**Mandatory VRAM probe before any multi-session 9B commit (E3 gate):**

```python
# Run ~20 optimizer steps under the intended 9B recipe (seq/batch/targets), then:
import torch
torch.cuda.reset_peak_memory_stats()
# ... train ~20 steps ...
peak_gb = torch.cuda.max_memory_reserved() / (1024**3)
print(f"peak reserved: {peak_gb:.2f} GB")
# Gate: only commit multi-session if peak_gb < ~15.0 with headroom for eval/checkpoint spikes.
```

- Pass (< ~15 GB reserved, headroom for eval + adapter save) → optional multi-session 9B with
  the probed config locked.
- Fail → stay on 4B flagship; if still curious, re-probe only after explicit concessions
  (embed-only / seq 1024 / batch 1), not by hoping peak memory drops mid-run.

**Cross-base comparison caveat:** PPL is tokenizer-dependent. After a base swap, compare each
adapter against **its own base** (%Δ), never absolute PPL across bases; the Phase-1-vs-v2
comparison then rests on the probe suite and MCQ metrics (§ Phase 3), not raw PPL.

**Currency caveat:** Qwen3.5 and Gemma 4 post-date this reviewer's training data (Jan 2026);
details above come from July 2026 secondary sources — hence the M1 gate before committing.
Qwen3.5-9B hidden size / layer count were not web-verified; VRAM estimates for 9B embeddings
are approximate (±0.5 GB) and must be replaced by the empirical probe above.

### 4.2 Target v2 configuration (summary)

```
Model:      Qwen3.5-4B-Base FLAGSHIP (pending M1 gate; fallback: unsloth/Qwen2.5-3B), 4-bit,
            seq 2048 (E2: 4096); 9B only as concession-gated E3 after VRAM probe (§4.1)
LoRA:       r=64, alpha=64, rsLoRA, dropout 0, targets attn+MLP+embed_tokens(+lm_head per D4)
Trainer:    UnslothTrainer, lr 5e-5 (body) / 1e-5 (embeddings), cosine, warmup_ratio 0.03,
            adamw_8bit, wd 0.01, fp16 (T4), grad clip 1.0 (default), seed 42
Batch:      2 × 8 accum = 32,768 tok/step, packing on, EOS boundaries verified
Steps:      max_steps = 1 epoch of mix (~3.3–3.6k steps for ~110M tokens), fixed across sessions
Data:       chunked ≤7k chars; Spurgeon 40–50% / Puritan 30–40% / confessions 3–6% /
            Bible 2–4% / replay 8–12%; paragraph-dedup; Heidelberg+Belgic held out
Eval:       per-bucket dict in-training; C_sota with base + Phase-1 deltas, greedy probes,
            WSC + Heidelberg MCQ
```

## 5. Success criteria (quantified) & kill criteria

**Ship v2 when all of:**

1. Manifest: ≥4 buckets, shares in target ranges, verified tokens recorded, holdouts non-empty.
2. Spurgeon holdout PPL ≤ Phase-1 adapter × 1.03 (within 3%), and better than base — valid for
   same-base runs only; after the §4.1 base swap, use %Δ-vs-own-base per bucket and rely on the
   probe suite + MCQ metrics for the Phase-1 comparison (PPL is tokenizer-dependent).
3. Puritan + confession holdout PPL ≥ 15% better than base.
4. General holdout PPL ≤ 10% worse than base (target ≤ 5%).
5. Heidelberg MCQ accuracy > base by ≥ 10 points (absolute); WSC MCQ near-ceiling.
6. Greedy style probes: v2 output blind-preferred over base for "Spurgeon-ness" (self-judged A/B,
   or LLM-as-judge with fixed rubric).

**Mid-run kill/adjust triggers (check at each eval step):**

- `eval_general_loss` rising > 15% over its step-0 value → raise replay share / halve body LR.
- fp16 loss spike (NaN or > 2× moving average) → drop `embedding_learning_rate` to 5e-6; if it
  persists, drop `lm_head` target (see F3/D4).
- s/step makes 1 epoch > 3 sessions → apply VRAM/speed fallback ladder (r=32, embeddings off).

## 6. Risk register

| Risk | Mitigation |
|---|---|
| F1 truncation confirmed → all past numbers optimistic | Re-baseline: re-run Phase-1 eval protocol on chunked data before comparing v2 to it |
| Unsloth HEAD drift breaks Kaggle mid-project | Pin commit (G1); keep last-known-good sha in README |
| Embedding offload → read-only FS crash (seen before) | Writable offload dir; documented fix in project memory (`bugs/unsloth-embedding-offload-readonly`) |
| Tied embeddings surprise (F3) | D4 before any long run; fallback = embed_tokens only |
| OCR garbage in Puritan bucket | Per-file spot check + top-paragraph report (1d); drop bad files |
| Tiny confessions bucket overfits/memorizes | No oversampling of confessions; it's fine — memorizing confessions is nearly the point; Heidelberg holdout measures generalization |
| Kaggle 9h/20GB limits | max_steps sessions, save_total_limit 2, adapter-only saves mid-run |
| SFTConfig pickling (seen in Phase 1) | Pickle guard already carried into v1 — keep |
| GGUF vocab shift on export (seen in Phase 2 SFT) | Reuse documented fix; export only after §5 passes |
| **Qwen2.5-3B ships under the Qwen *Research* License (non-commercial)** — a blocker if Ask Spurgeon is ever deployed commercially | Swap base to **Qwen3.5-4B-Base flagship** (Apache 2.0) per §4.1; decide before the flagship run, not after. 9B is optional E3 only |
| **9B full dual-LR recipe over-budget on single T4 16 GB** at seq 2048 (embed matrix ~2.5 GB ±0.5; not web-verified to exact hidden size) | Default = stay on 4B. If trying 9B: mandatory ~20-step VRAM probe (`torch.cuda.max_memory_reserved()`); commit multi-session only if peak reserved < ~15 GB with headroom. Else concessions only (embed-only / shorter seq / batch 1) |
| **T4×2 (32 GB) escape hatch for 9B + embed + head** | Kaggle dual-T4 can fit 9B full recipe via plain HF Transformers + PEFT + bitsandbytes with `device_map="auto"` (pipeline-parallel across both cards) — **but only by dropping Unsloth**. Cost: lose Unsloth's ~2× speed and memory kernels; all project notebooks are Unsloth-based. **Generally not worth it vs running 4B.** |

## 7. Execution checklist (in order)

- [x] **P0:** D1-lite local preflight *(no doc >8k; packed D1 still Kaggle)* → `scripts/13_local_preflight.py`
- [x] **P0:** D2-lite + `APPEND_EOS=True` in B_sota *(packed EOS count still Kaggle D2)*
- [x] **P0:** D4 decision from M1 config: **`TRAIN_LM_HEAD=False`** (tied); runtime D4 cell still on Kaggle
- [x] **P0:** G1 pin unsloth; G2 bucket guard; G3 notebook SoT *(G1: pin after first good Kaggle run)*
- [x] **P0:** M1 base-model gate (partial) → see `data/M1_BASE_MODEL_GATE.md`; hybrid arch risk documented
- [ ] **P4 only:** before any 9B multi-session run → VRAM probe (~20 steps, peak reserved < ~15 GB)
- [x] **P1:** collect Puritan/confession/KJV + holdouts (Heidelberg + Belgic) + PD general replay
- [x] **P1:** chunking ≤7k + paragraph dedup + share targeting + confession/bible caps
- [x] **P1:** rebuild mix → D3 ~8.2M tok → preflight **PASS** → package zip ready
- [ ] **P1:** **upload** `data/kaggle_upload/theology-cpt-corpus.zip` → run A_sota → **[`KAGGLE_RUNBOOK_V2.md`](KAGGLE_RUNBOOK_V2.md)**
- [x] **P2:** training v2 deltas + **`MAX_STEPS=250`** (1 epoch est.) in B_sota
- [ ] **P2:** train to 1 epoch on Kaggle T4
- [x] **P3:** C_sota v2 notebook ready (base Δ, greedy probes, MCQ)
- [ ] **P3:** §5 gate → merge + GGUF → Ollama smoke test
- [ ] **P4:** stretch (E1 `--author-tags`; E2 seq 4096; E3 9B VRAM-gated)

**Operator entrypoint:** [`KAGGLE_RUNBOOK_V2.md`](KAGGLE_RUNBOOK_V2.md)  
**Local gate:** `python continued_pretrain/scripts/13_local_preflight.py` → must be PASS before upload.

## 8. References

- Unsloth continued-pretraining docs (dual LR / `UnslothTrainer`, embed+lm_head recipe):
  https://docs.unsloth.ai/basics/continued-pretraining
- Qwen3.5 model cards (base variants, Apache 2.0 — checked 2026-07-12):
  https://huggingface.co/Qwen/Qwen3.5-4B · https://huggingface.co/Qwen/Qwen3.5-9B-Base
- Gemma 4 announcement (2026-04, Apache 2.0, E2B/E4B/12B/26B-MoE/31B):
  https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
- Ibrahim et al., 2024 — *Simple and Scalable Strategies to Continually Pre-train Large Language
  Models* (re-warming + replay for CPT).
- Muennighoff et al., 2023 — *Scaling Data-Constrained Language Models* (≤4 epochs of repeated
  data ≈ fresh data).
- Kalajdzievski, 2023 — *rsLoRA* (α/√r scaling; note v1's α=64,r=64 ⇒ scale 8 vs baseline's 2 —
  compensated by the 4× lower LR, but keep in mind if instability appears).
- Project memory: `pretraining/cpt-sota-assessment-2026-07`, `bugs/unsloth-embedding-offload-readonly`,
  `bugs/ollama-tokenizer-corruption-fix`, `pretraining/bugs/sftconfig-pickle`.
