<!-- memory-fabric:local/framework-rules -->
---
section: framework-rules
summary: "Defines coding standards, required libraries (Streamlit, LlamaIndex), environment setup (.env), and database rules for the codebase."
priority: medium
tags: [framework, rules]
schema_version: 1.3
last_updated: "2026-06-03T08:33:33-04:00"
summary_hash: f0dd594251d74f0ce1c3d34410c1767e
review_status: stale
---

# Framework Rules

Coding standards, dependency rules, and conventions for the Ask Spurgeon codebase.

## 1. Runtime Environment

- **Python Version**: Enforce **Python 3.11 to 3.13**. Avoid Python 3.14 due to dependency incompatibilities with LlamaIndex and general RAG packages in mid-2026.
- **Configuration Management**: All credentials, vector store endpoints, and LLM providers must be loaded from a `.env` file via `python-dotenv` and centralized in `config.py`.

## 2. Core Libraries & Packages

- **UI Framework**: **Streamlit**. Application execution starts via `streamlit run app.py`.
- **RAG Orchestrator**: **LlamaIndex** is the designated framework for handling document parsing, node generation, embedding, and vector querying.
- **Testing**:
  - Framework: Use `pytest` for unit testing.
  - RAG Validation: Run evaluations with `eval.py` to compare prompt configurations and judge outputs using an LLM-as-a-judge system.

## 3. Vector Database Rules

- **Local Development**: Default to local **ChromaDB** persisted in `./chroma_db` for quick local iteration.
- **Production Integration**: Connect to **Qdrant Cloud** (free tier). Local Docker Qdrant (`docker compose up -d qdrant`) is required when testing production-parity behaviors (e.g., specific metadata filtering).

## 4. Agent Memory Guidelines

- Use the `memory-fabric` MCP tools (`read_combined_context_tool`, `write_local_memory_tool`) to load and maintain local project memories. Direct writes to `.ai-memory/` are prohibited.

<!-- memory-fabric:local/ubiquitous-language -->
---
section: ubiquitous-language
summary: "Defines consistent domain language used throughout the codebase for clarity and shared understanding."
priority: medium
tags: [domain, language]
schema_version: 1.3
last_updated: "2026-06-01T17:30:48-04:00"
summary_hash: 756e7083c73708b08a81a9e3aa0df910
review_status: stale
---

# Ubiquitous Language

Record project terminology here.

<!-- memory-fabric:local/index -->
---
section: index
summary: "Map of available project memory sections."
priority: high
tags: [index, memory]
schema_version: 1.3
last_updated: "2026-09-27T09:59:31-03:00"
consolidation_hash: acd058fab27bf79aa31f9bd2e3dc7172
contradictions: ["`fine-tuning/hf-spurgeon-qa-v2-gguf` and `fine-tuning/plans/ollama-merge-gguf` cover similar content but state different numbers (2.71 vs 07) - review for conflict [heuristic]", "`pretraining/cpt-b-eval-strategy` and `pretraining/cpt-eval-unify-vs-buckets` cover similar content but state different numbers (0 / 1650 / 17 vs 0.2 / 1.2 / 18) - review for conflict [heuristic]", "`bugs/lora-frozen-embeddings-special-tokens` and `bugs/sft-tokenizer-mismatch-vinfos-spepacer` disagree about `im_start` (pos vs neg) - review for conflict [polarity]", "`fine-tuning/next-session-handoff` and `fine-tuning/vast-gate0-candidate` disagree about `scalingtype` (pos vs neg) - review for conflict [polarity]", "`fine-tuning/post-sft-eval-results` and `fine-tuning/qwen35-sft-special-tokens` disagree about `chatml` (pos vs neg) - review for conflict [polarity]"]
consolidation_warnings: ["Skipped bugs\\gemma4-chat-template-fix.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped bugs\\ollama-tokenizer-corruption-fix.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped decisions\\gemma4-local-ollama.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-07-12.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-07-13.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-07-14.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-08-23.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-08-27.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-08-28.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-09-15.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped episodic\\2026-09-26.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped fine-tuning\\runpod-sft-gate0-implementation.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-b-eval-strategy-implementation.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-best-adapter-leaderboard.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-corpus-v3-expansion-plan.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-corpus-v3-s1-complete.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-corpus-v3-s5-b-complete.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-current.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-next-session-handoff.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-phase-b-mix-a-output-v4.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-phase-b-mix-audit-clean.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-phase-b-v5-reweight-ready.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-s6-c-eval-next-session.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-s6-phase0-prepared.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-s7-holdout-sibling-replay.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-s7-replay-isolation-c-complete.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-v2-implementation-fable5.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-v2-next-steps-after-v13.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-v2-plan-fable5.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-v2-runpod-mcp-volume-gap.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-v3-s6-handoff.md during index regeneration: Missing YAML frontmatter delimiter", "Skipped pretraining\\cpt-v4-continue-reweight.md during index regeneration: Missing YAML frontmatter delimiter"]
summary_hash: c81ed9efe309125e42b693ba950f4f04
contradiction_count: 50
---

# Project Memory Index

Updated by Memory Fabric Dreaming mode `light`.

| Section | Priority | Summary | Key Topics |
| --- | --- | --- | --- |
| `architecture` | high | Generated map of memory-store/architecture/ (1 entries). | • **Ask Spurgeon Rag** (`architecture/ask-spurgeon-rag`, me... |
| `bugs` | medium | Generated map of memory-store/bugs/ (5 entries). | • **Qwen3.5 processor text-as-image in C_eval** (`bugs/qwen...<br>• **Bug Fix: Unsloth Embedding Offload on Read-Only Filesys...<br>• **Bug Fix: Training embed_tokens and lm_head when resizin... |
| `debt` | low | App debt (hybrid search, rate limits) plus 2026-08-29 memory-fabric LLM/host hygiene notes. | • Known Technical Debt & Limits<br>• Roadmap & Pending Features |
| `decisions` | medium | Generated map of memory-store/decisions/ (1 entries). | • **Gemma 4 Fine-Tuning Transition** (`decisions/gemma4-fin... |
| `episodic` | medium | Generated map of memory-store/episodic/ (22 entries). | • **Episodic Journal — 2026-07-11** (`episodic/2026-07-11`,...<br>• **Episodic Journal — 2026-08-12** (`episodic/2026-08-12`,...<br>• **Episodic Journal — 2026-08-24** (`episodic/2026-08-24`,... |
| `failures` | medium | Generated map of memory-store/failures/ (32 entries). | • **Vast official Unsloth image smoke blocked; LD_LIBRARY_P...<br>• **asyncua write_value BadTypeMismatch when writing int to...<br>• **B_training_sota: EarlyStopping disabled — metric_for_be... |
| `fine-tuning` | medium | Generated map of memory-store/fine-tuning/ (38 entries). | • **Fine-tuning next session handoff** (`fine-tuning/next-s...<br>• **SFT QA gold rewrite pilot (20 rows, merged)** (`fine-tu...<br>• **SFT/serve: knowledge assistant, not Spurgeon persona** ... |
| `framework-rules` | medium | Defines coding standards, required libraries (Streamlit, LlamaIndex), environment setup (.env), and database rules for the codebase. | • 1. Runtime Environment<br>• 2. Core Libraries & Packages<br>• 3. Vector Database Rules<br>• 4. Agent Memory Guidelines |
| `grok` | medium | Generated map of memory-store/grok/ (3 entries). | • **Grok Bot Forge for Vast/Runpod training** (`grok/forge-...<br>• **Grok Bot Foundry for train/export code** (`grok/foundry...<br>• **Grok Integration with Memory Fabric (MCP + Docs + Nativ... |
| `pretraining` | medium | Generated map of memory-store/pretraining/ (70 entries). | • **CPT B_training_sota known issues (P1 closed — log spam)...<br>• **Composite CPT early stop merges split HF eval events** ...<br>• **Confessions + Institutes corpus (WCF, 1689, Calvin)** (... |
| `schemas` | high | Defines data contracts, metadata schemas for ingested texts, and environment variable configurations. | • 1. Document & Chunk Metadata Schema<br>• 2. Ingestion Parameters<br>• 3. Environment Variables (Configuration Schema) |
| `ubiquitous-language` | medium | Defines consistent domain language used throughout the codebase for clarity and shared understanding. | None recorded |

## Memory Store

Please see the dedicated [Memory Store Index](memory-store/index.md) for a map of available semantic memory store files.

<!-- memory-fabric:local/architecture -->
---
section: architecture
summary: "Generated map of memory-store/architecture/ (1 entries)."
priority: high
tags: [architecture]
schema_version: 1.3
last_updated: "2026-08-29T11:18:40-04:00"
generated: true
generated_from: memory-store/architecture
store_fingerprint: 65a1dac6b7c9fecf4810aed7c05284b6
body_hash: ba494cebbfdb7569c2b90892c3b298c4
---

# Architecture Map

Generated by Memory Fabric from `memory-store/architecture/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Ask Spurgeon Rag** (`architecture/ask-spurgeon-rag`, medium) — Canonical Ask Spurgeon RAG stack: Streamlit, LlamaIndex, Chroma/Qdrant, Groq + local CPT/SFT models.

<!-- memory-fabric:store/pretraining/bugs/b-training-sota-known-issues -->
---
store_path: pretraining/bugs/b-training-sota-known-issues
title: "CPT B_training_sota known issues (P1 closed — log spam)"
summary: "Source of truth: `continued_pretrain/scripts/_gen_sota_notebooks.py` (regenerate notebooks; do not hand-edit only)"
priority: high
tags: [pretraining, cpt, kaggle, bugs, unsloth, qwen35, p1]
schema_version: 1.3
last_updated: "2026-08-25T10:20:30-04:00"
evidence: [continued_pretrain/kaggle/b_output_v6/checkpoints_sota/checkpoint-75/trainer_state.json, continued_pretrain/kaggle/c_output/theology_cpt_lora_final/adapter_model.safetensors, continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md]
review_status: stale
---

# CPT B_training_sota known issues (fix next)

Source of truth: `continued_pretrain/scripts/_gen_sota_notebooks.py` (regenerate notebooks; do not hand-edit only).

## P1 — Early-stop log spam (NOT a missing metric) — closed 2026-08-25

**Symptom (B v6):** stderr spam `early stopping required metric_for_best_model, but did not find eval_spurgeon_loss so early stopping is disabled`.

**What we thought:** metric never logged → EarlyStopping disabled → C scored last step without Spurgeon-best selection.

**What actually happened (evidence):**
- `checkpoints_sota/checkpoint-75/trainer_state.json` has `eval_spurgeon_loss` at steps 25 / 50 / 75.
- `best_global_step=25`, `best_metric=2.5679` (that Spurgeon loss), EarlyStopping patience 0→1→2, stop at 75.
- HuggingFace logs **each eval dataset as its own dict**. The callback looks at the *current* logs; mix/puritan/confession/general do not contain `eval_spurgeon_loss` → warning. The spurgeon sub-eval **does** contain it.
- SHA256 of `adapter_model.safetensors` is **identical** for `checkpoint-25`, `theology_cpt_lora`, and C's `theology_cpt_lora_final`. C v4 already scored the best ckpt.

**Fix in generator (v7):** `QuietEarlyStoppingCallback` — same patience logic, no warning when the current bucket lacks the key. Print eval keys on first Spurgeon eval. After save, SHA256-compare `theology_cpt_lora` vs `best_model_checkpoint`.

**Do not** re-run C with `ADAPTER_OVERRIDE` on B v6 `checkpoint-25` (already scored).

## P2 — Unsloth `formatting_func` required (B v4)

**Symptom:** `RuntimeError: Unsloth: You must specify a formatting_func` when constructing `UnslothTrainer` with `eval_dataset` dict of text HF datasets while train is already packed `input_ids`.

**Fix applied:** tokenize eval the same way as train (`_tokenize_eval_ds`) when `MANUAL_PACK=True`. Keep this whenever train is pre-tokenized.

## P3 — CUDA OOM on T4 (B v5)

**Symptom:** `OutOfMemoryError` (~2.37 GiB alloc) during train/eval with Qwen3.5 float32 + manual pack.

**Failing recipe:** `PER_DEVICE_BATCH=2`, `GRAD_ACCUM=8`, `TRAIN_EMBEDDINGS=True`, eval 8 docs/bucket.

**Working recipe (B v6):** `PER_DEVICE_BATCH=1`, `GRAD_ACCUM=16`, `TRAIN_EMBEDDINGS=False`, `EVAL_DOCS_PER_BUCKET=4`.

**B v7 try:** same 1×16 shape **with** `TRAIN_EMBEDDINGS=True`. If OOM: `EVAL_DOCS_PER_BUCKET=2` and/or `EVAL_BUCKETS_DURING_TRAIN=["spurgeon"]` (keep mix). Do not go back to batch 2 + embeds without a VRAM probe.

## P4 — Manual pack itself (RC1) — works

Do **not** regress: Qwen3.5 Processor ignores native `packing=True`. Keep `build_manual_packed_dataset` + D1 gate (packed rows ≪ raw docs). B v6: 8162 → 7255 packed rows.

## Checklist before next B push (v7)

- [x] Understand P1: metric was logged; C scored ckpt-25
- [ ] `QuietEarlyStoppingCallback` — no spam; Spurgeon key still drives stop
- [ ] SHA256(saved LoRA) == SHA256(best ckpt)
- [ ] D1 packed rows ≪ docs; MAX_STEPS ≈ one packed epoch (~454–476), not 100
- [ ] T4: try embed LoRA at batch 1; peak reserved headroom
- [ ] If eval_spurgeon **rises** by step 50 with embeds: halve body LR (1e-5), do not just push steps
- [ ] C only after B v7; ship only on §5 holdout PPL

<!-- memory-fabric:store/pretraining/bugs/composite-early-stop-eval-cycle -->
---
store_path: pretraining/bugs/composite-early-stop-eval-cycle
title: "Composite CPT early stop merges split HF eval events"
summary: "Hugging Face evaluates a dictionary of CPT eval datasets as separate callback events"
priority: high
tags: [cpt, early-stop, transformers, bug, eval]
schema_version: 1.3
last_updated: "2026-09-15T11:34:36-03:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/scripts/test_cpt_runtime.py, continued_pretrain/scripts/_gen_sota_notebooks.py]
---

# Composite early-stop split-eval fix (Phase 0, 2026-09-15)

Hugging Face evaluates a dictionary of CPT eval datasets as separate callback events. S5 logs show `eval_mix_loss` and `eval_spurgeon_loss` at the same global step.

**Fix implemented (local, no GPU):** `merge_eval_event_for_step` in `cpt_runtime.py` caches metrics by step, scores a cycle only when every configured key has arrived, then pops that step. `CompositeFlatEarlyStoppingCallback` uses the merged dict. Checkpoint pick stays `eval_spurgeon_loss`.

Tests: sequential mix-then-Spurgeon events (S5-like mix still falling → no halt; both flat → halt). Unmerged single-bucket events still never halt.

Generator `_gen_sota_notebooks.py` regenerated `train_cpt_sota.py` / notebooks / `eval_cpt_sota.py`.

<!-- memory-fabric:store/pretraining/confessions-corpus-fetch -->
---
store_path: pretraining/confessions-corpus-fetch
title: "Confessions + Institutes corpus (WCF, 1689, Calvin)"
summary: "Confessions + Institutes corpus (WCF, 1689, Calvin)"
priority: high
tags: [pretraining, data, confessions, wcf, 1689, calvin]
schema_version: 1.3
last_updated: "2026-07-13T10:30:48-04:00"
evidence: [data/confessions/PROVENANCE.md, continued_pretrain/scripts/11_fetch_confessions.py]
review_status: stale
---

# Confessions / Institutes fetch (2026-07-13)

## On disk under `data/confessions/` (~5.4 MB)

- **WCF:** `westminster/westminster_confession.txt` (IA confessionoffa00west)
- **WCF + Larger/Shorter catechisms:** `westminster/wcf_catechisms_1756.txt` (Scottish 1756 IA)
- **WSC:** already curated `westminster/westminster_shorter_catechism.txt`
- **1689 LBCF:** `1689/second_london_confession.txt` — curated PD core chapters (IA only had modern class recordings)
- **Calvin Institutes (Beveridge):** `institutes/institutes_beveridge_vol1.txt` + `vol2.txt`

## Tooling

`continued_pretrain/scripts/11_fetch_confessions.py` (+ `--rebuild-mix`)

## Mix caps

`07_build_theology_mix.py` now supports `--max-confession-share` default **0.06** so Institutes does not dominate (plan target 3–6%). After rebuild: confession ~5.6%, spurgeon 45%, puritan ~45%, bible 4%.

Heidelberg remains holdout-only under `holdouts_manual/`.

<!-- memory-fabric:store/pretraining/cpt-b-eval-strategy -->
---
store_path: pretraining/cpt-b-eval-strategy
title: "CPT B eval strategy — verified next-B spec"
summary: "Operator approved this as the continue-session spec (nits from fact-check applied)"
priority: high
tags: [cpt, eval, early-stop, handoff, corpus-v3]
schema_version: 1.3
last_updated: "2026-08-28T00:14:06-04:00"
evidence: [continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/scripts/18_prep_hf_dataset.py, continued_pretrain/kaggle/runpod_cpt_v3/cpt_train.log, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/NEXT_CPT_MORE_TOKENS.md, continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md]
---

# CPT B eval strategy (verified 2026-08-28) — next B spec

Operator approved this as the continue-session spec (nits from fact-check applied). Do **not** create a GPU until that chat says go. Implement in `train_cpt_sota.py` / generator **when training is approved** — none of floor, 16–32 docs, extra buckets, or composite stop exist in code today.

One-liner: **Train on one mix; during B log separate holdout buckets with 16–32 docs (not 2); do not halt before ~0.4 packed epoch; stop only when Spurgeon and mix are both flat within epsilon — not mix-only, not 2-doc Spurgeon-only. Keep C per-bucket as the ship gate.**

## Context (S5) — do not redo
- Train is already one mix (~90M: Spurgeon 40.2%, Puritan 45.7%, confession 5.5%).
- B early-stop 375/4128 (~8.2M, ~9%). Stop key: `eval_spurgeon_loss` on **2** Spurgeon docs (`EVAL_DOCS_PER_BUCKET=2`, T4 VRAM hatch).
- Spurgeon 2.292@25 → **2.254@325** then ±0.005. Mix **2.085 → 2.029**, still falling. Mix val on disk is 520 docs (1% split); B only scored 4.
- C: probe PASS vs Ampere base; §5 −15% FAIL. Adapter SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`.

## Do not
1. **Mix-only early-stop.** First B `eval keys=['mix']`. Mix **rose** 2.316→2.463 (did not “look OK”). C v3 holdouts +9 / +11.6 / +15.4 / +17.8%. Mix val = `VAL_FRACTION=0.01` random split of train, not C holdouts.
2. **One collapsed “Reformed mix” PPL** (merge Spurgeon/Puritan/confession/general). Hides product vs §5 vs forgetting.
3. **2-doc Spurgeon-only stop.** Too noisy; halted S5 while mix still improved.
4. Fresh 1e-5 from base; rebuild mix; T4 4-bit; overwrite Hub v2 until a new C wins; re-C this S5 adapter.
5. Treat 25M tokens as equal to 40–50% of the epoch (they are not).

## Historical nits (do not repeat the overstated version)
- B v6: **all** buckets rose together (mix 1.890→1.920, spurgeon 2.568→2.607). Not “mix stable + spurgeon rose.” `METRIC_FOR_BEST=eval_spurgeon_loss` is because C scores **holdouts**, not because v6 diverged.
- S5 is the divergence the other way: spurgeon flat, mix falling. Composite + floor is the synthesis of both eras.

## Do this on the next B (code changes)

| Layer | Spec |
|-------|------|
| Training | Same unified mix (`a_output_v3`, SHA256 `23dd3820baa0b657cb6528e4fdf1b2d4813c3cfa7b7c982805b4a7ff34990973`). No rebuild. `one_doc_padded`, r=32, GDN, embed FT. |
| Continue | Load S5 LoRA on Qwen3.5-4B-Base, **new Adam**, body LR ~3e-6–5e-6, emb ~1e-6–2e-6. Cosine over continue `max_steps`. Not HF resume (no optimizer.pt). |
| B in-train eval | Keep **separate** buckets. Minimum mix + spurgeon. Add puritan/confession on 24 GB (`EVAL_BUCKETS_DURING_TRAIN` today is `[spurgeon]` only). |
| Sample size | `EVAL_DOCS_PER_BUCKET` **16–32**, or full bucket. C sizes: spurgeon 50, puritan 20, confession 10, general 10 — cap at `len(ds)`. |
| Early-stop **floor** | Pick **one**: `min_steps` ≈ **0.4–0.5 packed epoch** (~1650–2060 of 4128, ~36–45M tokens). Patience cannot fire before that. |
| Halt rule | **Composite** custom callback (HF EarlyStopping is single-metric). Stop only if Spurgeon **and** mix are both flat/worsening for N evals **within epsilon** (else ±0.005 still fires). Keep `max_steps` = one packed epoch so mix cannot crawl forever. |
| Best ckpt | Separate from halt: keep `METRIC_FOR_BEST=eval_spurgeon_loss` (or a weighted sum). `QuietEarlyStoppingCallback` stays for per-dict log keys. |
| Abort-at-50 | **Off/loosened on this continue** (loss already low). Keep it on any fresh-from-base run. |
| C | Unchanged per-bucket holdouts. Score the **new** adapter vs **its** Ampere base. Export `EXPECTED_ADAPTER_SHA256` (script default is still v2). Keep Hub `…-cpt-lora-v2` until new C wins. |

## Infra (when GPU approved)
Volume `7hb931c5oe` via REST v1 (MCP `create-pod` drops `objectMounts`). Scp optimizer + checkpoints. Community 4090 was empty; Secure US-IL-1 worked. SSH `~/.ssh/runpod_cpt`.

<!-- memory-fabric:store/pretraining/cpt-corpus-expansion-2026-08 -->
---
store_path: pretraining/cpt-corpus-expansion-2026-08
title: "CPT corpus expansion (Puritans/Edwards)"
summary: "Grew non-Spurgeon domain text so Spurgeon in-mix could rise while keeping ~45% share"
priority: high
tags: [pretraining, cpt, corpus, puritans, edwards]
schema_version: 1.3
last_updated: "2026-08-24T22:54:43-04:00"
evidence: [data/puritans/PROVENANCE.md, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
review_status: stale
---

# CPT corpus expansion (2026-08-24)

Grew non-Spurgeon domain text so Spurgeon in-mix could rise while keeping ~45% share.

## Results

| Metric | Before | After |
|--------|--------|-------|
| Raw Puritans | ~18 MB | ~34.4 MB |
| Mix chars | ~27.4M | ~51.5M |
| Verified tokens | ~8.2M | ~15.6M |
| Docs | 4401 | 8245 |
| Spurgeon weight | 0.087 | 0.164 |

Shares remain on target: Spurgeon ~40.5%, Puritan ~40.9%, confession ~5%, Bible ~3.6%, general ~10%.

## New PD sources (OCR PASS)

Watson All Things for Good (CCEL), Brooks Mute Christian, Sibbes Soul's Conflict, Edwards Freedom of the Will + Justification, Charnock Existence & Attributes, Boston Crook in the Lot, Flavel Fountain of Life, Owen Goold vol.10, Henry exposition vol.5, Hodge ST vol.1.

## Tooling

- Extended 10_fetch_puritans.py CATALOG + OCR quality gate
- 17_build_general_replay.py rebuilds Gutenberg classics replay
- Recipe v4 validated locally; config JSON aligned
- Packaged + uploaded theology-cpt-corpus; A refreshed theology-cpt-dataset (8245 docs)

## Do not

- Force full Spurgeon without more non-Spurgeon mass
- Inflate Bible share via repetition
- Merge CPT until section 5 holdout PPL gate passes on v4+expanded retrain

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s1-wave1 -->
---
store_path: pretraining/cpt-corpus-v3-s1-wave1
title: "CPT corpus v3 S1 Wave 1 fetch + mix"
summary: "**No B, no C, no Runpod GPU, no Kaggle push, no merge, no Hub overwrite.**"
priority: high
tags: [cpt, corpus, wave1, mix, puritans]
schema_version: 1.3
last_updated: "2026-08-27T11:02:21-04:00"
evidence: [continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/scripts/07_build_theology_mix.py, continued_pretrain/data/theology_mix_manifest.json, data/puritans/PROVENANCE.md, data/confessions/PROVENANCE.md]
---

# CPT corpus v3 S1 — Wave 1 fetch + mix (2026-08-27)

**No B, no C, no Runpod GPU, no Kaggle push, no merge, no Hub overwrite.**

## Mix policy shipped
- Denylist in `07_build_theology_mix.py`: default `--exclude-glob` skips `henry/exposition*` (file stays on disk). Manifest `exclude_globs` confirms.
- Hodge ST vol.1 moved `data/puritans/hodge/` → `data/confessions/systematic/`; vols 2–3 fetched there. Confession/ST bucket, not Puritan mass.
- Hymns folded into the Puritan bucket from `data/hymns/`.
- Calvin treatises/sermons under `data/puritans/calvin/` (Institutes stay in confessions).

## Disk after Wave 1
~165.6 MB txt under puritans + hymns + systematic (was ~34.4 MB). **+~131 MB** unique. Henry exposition 5.1 MB still on disk, **not** in mix.

Largest new shelves: Manton 41.7 MB (20/22 vols), Owen Goold remaining 27 MB, Sibbes complete works, Brooks remaining vols, Goodwin 1–4, Edwards extra, Hodge ST 2–3, Calvin tracts, Rutherford Letters + Lex Rex, Herbert, Watts + Olney.

**S2 leftovers (IA 503/403 or bad Gutenberg IDs):** Burroughs Rare Jewel + Gospel Worship; Perkins Golden Chain + cases; Flavel remaining complete-works vols; Watson Godly Man's Picture; Henry Method of Prayer; Manton vols 12+22; Scottish Psalter 1650.

## Mix rebuilt (`--no-keep-all-spurgeon`)
`--target-spurgeon-share 0.45 --replay-frac 0.10 --replay-txt continued_pretrain/data/replay/general_replay.txt`

| Metric | v2 (old) | v3 S1 |
|--------|----------|-------|
| spurgeon_weight | 0.164 | **0.6586** |
| train chars | 51.5M | 203.1M |
| verified tokens (Qwen3.5-4B-Base) | 15.6M | **57.60M** |
| docs | 8245 | 32878 |
| Henry in mix | yes | **no** |

Shares: Spurgeon 41.3%, Puritan 45.7% (above 30–40 band until more Spurgeon is kept), confession 2.7%, Bible 2.1%, general 8.2%. `keep-all` other_weight would be ~1.52 (>1.5) — correctly not used.

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s2-complete -->
---
store_path: pretraining/cpt-corpus-v3-s2-complete
title: "CPT corpus v3 S2 complete (fetch + mix, no training)"
summary: "S2 fetch + mix rebuild finished 2026-08-27"
priority: high
tags: [cpt, corpus-v3, s2, mix, tokens]
schema_version: 1.3
last_updated: "2026-08-27T13:57:33-04:00"
evidence: [continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/CORPUS_V3_S2_HANDOFF.md, continued_pretrain/CORPUS_V3_S3_HANDOFF.md, continued_pretrain/data/corpus_v3_catalog.json]
---

S2 fetch + mix rebuild finished 2026-08-27. No B/C, no Kaggle, no merge, no Hub LoRA overwrite.

Manifest `created_at` 2026-08-27T17:47:00Z:
- spurgeon_weight **0.931006**, spurgeon_keep_all **true**, other_bucket_weight **1.074107** (not capped; ≤ 1.5 so keep-all is allowed)
- train_docs **48841**, train_chars **295,083,379**
- verified tokens **86,182,467** (Qwen3.5-4B-Base, sample ratio 0.29129)
- shares S **43.1** / P **46.1** / C **1.8** / B **1.5** / G **7.4**

Wave 1 retries 7/7 keys. Wave 2 30/30 catalog keys. Shelf puritans+hymns+systematic **217.7 MB** (`data/puritans` at repo root, gitignored). Henry exposition still denylisted (`henry/exposition*`). Packing `one_doc_padded`.

Keep-all ON is a change vs S1 (S1 other-weight ~1.52, keep-all off). Confession 1.8% and Bible 1.5% are below band because Puritan mass grew — S3 must not add more treatises as the growth engine.

Fallback LoRA: rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 SHA256 319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478

Next = S3. Handoff: `continued_pretrain/CORPUS_V3_S3_HANDOFF.md`.

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s2-handoff -->
---
store_path: pretraining/cpt-corpus-v3-s2-handoff
title: "CPT corpus v3 S2 is done — next is S3"
summary: "S2 done; pointer to s2-complete."
priority: high
tags: [cpt, corpus-v3, s2, handoff]
schema_version: 1.3
last_updated: "2026-08-29T11:22:29-04:00"
evidence: [continued_pretrain/CORPUS_V3_S2_HANDOFF.md, continued_pretrain/CORPUS_V3_S3_HANDOFF.md]
summary_hash: aecffde35b628683e984e6499da6baff
---

# Corpus v3 S2 — DONE (pointer)

Do not re-fetch S2. Results: `pretraining/cpt-corpus-v3-s2-complete`. Live CPT: `pretraining/cpt-current`.

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s3-complete -->
---
store_path: pretraining/cpt-corpus-v3-s3-complete
title: "CPT corpus v3 S3 complete (Wave 3 + mix, no training)"
summary: "S3 fetch + mix rebuild finished 2026-08-27"
priority: high
tags: [cpt, corpus-v3, s3, mix, tokens, commentary]
schema_version: 1.3
last_updated: "2026-08-27T15:28:08-04:00"
evidence: [continued_pretrain/CORPUS_V3_S3_HANDOFF.md, continued_pretrain/CORPUS_V3_S4_HANDOFF.md, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/scripts/07_build_theology_mix.py]
---

S3 fetch + mix rebuild finished 2026-08-27. No B/C, no Kaggle, no merge, no Hub LoRA overwrite.

Wave 3 **9/9**. Chaderton and John Rogers **skipped**. Commentary cap **12.0 / 15 MB**: Hodge biblical 5.0 MB (Romans IA commentaryepist00hodg, 1 Cor expositionoffirs00hodg, 2 Cor expositionofseco00hodg, Ephesians CCEL); selected Calvin 7.0 MB (CCEL calcom38 Romans, 39 1 Cor, 40 2 Cor, 41 Gal-Eph, 45 Catholic epistles). Not the full Calvin dump. No Henry exposition added. Fetcher gates COMMENTARY_CAP_BYTES=15e6 and per-file max_chars 3.5M.

Manifest `created_at` 2026-08-27T19:23:59Z:
- spurgeon_weight **0.991563**, spurgeon_keep_all **true**, other_bucket_weight **1.008509** (not capped; ≤ 1.5)
- train_docs **49787**, train_chars **303,679,713**
- verified tokens **86,960,259** (Qwen3.5-4B-Base, sample ratio 0.285606)
- shares S **41.9** / P **47.7** / C **1.8** / B **1.4** / G **7.2**

Henry exposition still denylisted. Packing `one_doc_padded`. Mix rebuilt with `--keep-all-spurgeon --max-other-weight 1.5`. Shelf puritans+hymns+systematic **229.7 MB**.

Windows: mix print used Unicode → and crashed cp1252; prints now ASCII `->`. Fetcher `--rebuild-mix` now passes `--max-other-weight 1.5`.


Next = S4 optional confession lift (mix+verify already ran). Handoff: `continued_pretrain/CORPUS_V3_S4_HANDOFF.md`.

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s3-handoff -->
---
store_path: pretraining/cpt-corpus-v3-s3-handoff
title: "CPT corpus v3 S3 handoff (done this session)"
summary: "S3 done; pointer to s3-complete."
priority: high
tags: [cpt, corpus-v3, s3, handoff]
schema_version: 1.3
last_updated: "2026-08-29T11:22:29-04:00"
evidence: [continued_pretrain/CORPUS_V3_S3_HANDOFF.md, continued_pretrain/CORPUS_V3_S4_HANDOFF.md]
summary_hash: c41d485027e323a805bbfe8daa186568
---

# Corpus v3 S3 — DONE (pointer)

Do not re-run Wave 3. Results: `pretraining/cpt-corpus-v3-s3-complete`. Live CPT: `pretraining/cpt-current`.

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s4-complete -->
---
store_path: pretraining/cpt-corpus-v3-s4-complete
title: "CPT corpus v3 S4 complete (confession/ST lift, no training)"
summary: "S4 fetch + mix rebuild finished 2026-08-27"
priority: high
tags: [cpt, corpus-v3, s4, mix, tokens, confession]
schema_version: 1.3
last_updated: "2026-08-27T17:01:34-04:00"
evidence: [continued_pretrain/CORPUS_V3_S4_HANDOFF.md, continued_pretrain/CORPUS_V3_S5_HANDOFF.md, continued_pretrain/data/theology_mix_manifest.json, continued_pretrain/scripts/11_fetch_confessions.py]
---

S4 fetch + mix rebuild finished 2026-08-27. No B/C, no Kaggle, no merge, no Hub LoRA overwrite. Do not re-fetch Wave 3. Do not add more commentary. Do not grow Puritan treatise mass.

S4 unique PD confession/ST **12/12**: Gill doctrinal (CCEL), Dabney syllabus, Shedd Dogmatic 1-3, A.A. Hodge Outlines 1878, Witsius Covenants 1-2, Boyce Abstract, Second Helvetic (Schaff creeds3.v.ix.html), Scots 1560, Canons of Dort (Schaff Dort page only). Turretin English **skipped** (P&R/Dennison copyright). Heidelberg/Belgic still holdout-only.

Manifest `created_at` 2026-08-27T19:58:31Z:
- spurgeon_weight **1.068846**, spurgeon_keep_all **false** (weight > 1; all sermons used), other_bucket_weight **1.0**
- train_docs **51937**, train_chars **316,512,374**
- verified tokens **91,307,937** (Qwen3.5-4B-Base, sample ratio 0.287726)
- shares S **40.2** / P **45.7** / C **5.5** / B **1.4** / G **7.2**

Confession **5.5%** is in the 3-6% band (S3 was 1.8%). Mix rebuilt with `--keep-all-spurgeon --max-other-weight 1.5`. Henry exposition still denylisted. Packing `one_doc_padded`. Puritans unchanged 221.1 MB / 150 files. `data/confessions/` 30.7 MB / 21 files. Preflight PASS_WITH_WARNINGS (Puritan 45.7% just over 45%; Bible/general still low).


Next = S5 Runpod B with operator approval. Handoff: `continued_pretrain/CORPUS_V3_S5_HANDOFF.md`.

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s4-handoff -->
---
store_path: pretraining/cpt-corpus-v3-s4-handoff
title: "CPT corpus v3 S4 handoff (done this session)"
summary: "S4 done; pointer to s4-complete."
priority: high
tags: [cpt, corpus-v3, s4, handoff]
schema_version: 1.3
last_updated: "2026-08-29T11:22:29-04:00"
evidence: [continued_pretrain/CORPUS_V3_S4_HANDOFF.md, continued_pretrain/CORPUS_V3_S5_HANDOFF.md]
summary_hash: 25aecdc17659b3f023916d658ae915d9
---

# Corpus v3 S4 — DONE (pointer)

Do not re-run S4 confession fetch. Results: `pretraining/cpt-corpus-v3-s4-complete`. Live CPT: `pretraining/cpt-current`.

<!-- memory-fabric:store/pretraining/cpt-corpus-v3-s5-c-complete -->
---
store_path: pretraining/cpt-corpus-v3-s5-c-complete
title: "CPT corpus v3 S5 C complete — probe PASS, keep Hub v2"
summary: "GPU `gynfhzyfjcjjyf` **deleted**"
priority: high
tags: [cpt, corpus-v3, s5, eval, runpod]
schema_version: 1.3
last_updated: "2026-08-27T23:44:42-04:00"
evidence: [continued_pretrain/NEXT_CPT_MORE_TOKENS.md, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_run_config.json]
---

# CPT corpus v3 S5 C COMPLETE (2026-08-28)

GPU `gynfhzyfjcjjyf` **deleted**. Volume `7hb931c5oe` kept (this C **did** attach it at `/workspace` via REST v1; MCP `create-pod` still cannot). Do **not** merge. Do **not** overwrite Hub `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`. Do **not** re-C v2. Do **not** retrain in a leftover GPU.

## Adapter scored
`continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_lora` SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303` (B best 325). Holdouts `kaggle/a_output_v3/theology_holdouts`. MCQ `data/catechism_mcq.json`. `EXPECTED_ADAPTER_SHA256` exported to the v3 hash. Ampere bf16, `REQUIRE_AMPERE=1`, `RUN_MERGE=False`.

## Scorecard vs this C’s Ampere bf16 base
Do not mix with Kaggle C v4 T4 4-bit, or with v2 C raw PPL (v2 used `a_output` holdouts).

| Bucket | Base | v3 adapter | %Δ |
|--------|------|------------|-----|
| spurgeon | 14.31 | 13.34 | −6.79% |
| puritan | 6.03 | 5.72 | −5.17% |
| confession | 5.61 | 5.36 | −4.42% |
| general | 12.05 | 11.90 | −1.21% |

Probe (all four better than this base): **PASS**. Plan §5 −15% on puritan/confession: **FAIL**. MCQ WSC 70%→72%; Heidelberg 40.5%→45.2% (need +10).

## Keep vs Hub v2 Ampere C (2026-08-27)
v2: spurgeon 13.28 (−7.25%), puritan 5.68 (−5.05%), confession 6.73 (−6.98%), general 13.20 (−1.73%). Spurgeon/puritan raw PPL are slightly worse here. Confession/general look better but those holdouts changed in v3 — not a Hub overwrite. **Keep** Hub `…-cpt-lora-v2` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`.

## Infra
- MCP `create-pod` GraphQL now 400s (`objectMounts` not on `PodFindAndDeployOnDemandInput`). `runpodctl` still has no REST API key.
- Workaround that worked: REST v1 `POST https://rest.runpod.io/v1/pods` with the MCP OAuth bearer (REST v2 and GraphQL 403 on that token). Community 4090 empty; Secure US-IL-1 **$0.74/hr** **did** attach `networkVolumeId` `7hb931c5oe`.
- SSH `root@203.57.40.78 -p 10057` (key `~/.ssh/runpod_cpt`). Artifacts: `kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json`, `cpt_eval.log`.

## Next
More-tokens continue only if a later session wants it: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md`. Optimizer was never copied; no HF resume. Do not start that B until the operator says go.

## Why this is not “v3 had more data and lost” (operator asked 2026-08-27)

The mix on disk is larger (~90M / 91.31M verified). Training did **not** use it. Early-stop patience 2 on a **2-doc Spurgeon** eval (`eval_steps=25`) halted at **375/4128** (~**8.2M tokens**, ~9% of one packed epoch). v2’s probe mix was ~**15.6M** and best step **400**. This LoRA saw **less** than v2, not more. `eval_mix` was still falling when the probe flattened.

Spurgeon 13.34 vs v2 13.28 and puritan 5.72 vs 5.68 are noise-level. Confession/general used `a_output_v3` holdouts, not v2 `a_output` — not a like-for-like win. Probe vs **this** C’s Ampere base still **PASS**. Puritan is 45.7% of the mix and confession 5.5%; 8.2M only gave them a thin slice, which is why §5 −15% failed.

This is the playbook’s **preferred continue** case (near v2, far from §5). Repo: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md`. Operator said they will continue in the next question about training and eval. Do not start GPU until that chat says go. Do not fresh 1e-5 from base.

<!-- memory-fabric:store/pretraining/cpt-eval-stack-pin-s5 -->
---
store_path: pretraining/cpt-eval-stack-pin-s5
title: "CPT C-eval must use Unsloth 2026.8.22 + torch 2.8"
summary: "Recovered from S5 `continued_pretrain/kaggle/runpod_cpt_v3/cpt_eval.log`:"
priority: high
tags: [cpt, eval, unsloth, torch, pin, s5, hub-v2]
schema_version: 1.3
last_updated: "2026-09-20T19:01:29-03:00"
---

# CPT C-eval stack pin (S5 / Hub-v2 parity)

## Required for trustworthy CPT C of Qwen3.5-4B embed-FT LoRA
Recovered from S5 `continued_pretrain/kaggle/runpod_cpt_v3/cpt_eval.log`:

| Package | Pin |
|---------|-----|
| Unsloth | **2026.8.22** (`unsloth[colab-new]==2026.8.22`; Hub-v2 C used 2026.8.21) |
| torch | **2.8.0+cu126** (or image `2.8.0+cu128`) |
| torchvision | **0.23.0** (must match torch 2.8; 0.26 expects 2.11) |
| torchaudio | **2.8.0** |
| xformers | **omit** when pinning torch 2.8 (Unsloth 2026.8.22 may pull xformers wanting torch≥2.10) |
| Env | `UNSLOTH_SKIP_TORCHVISION_CHECK=1` if needed; `REQUIRE_AMPERE=1`; `load_in_4bit=False` |

## Do not use for C of S6 SHA `6aab…`
Unsloth **2026.9.6** + torch **2.11** produced false FAIL spurgeon **18.31 (+27.9%)**. Same weights on the pin above: **12.85 (−10.2%)**.

## Automation
- Env override: `UNSLOTH_PIP_SPEC` in `eval_cpt_sota.py`
- Train-probe slice: `CPT_EVAL_TRAIN_PROBE_DOCS=16`
- Scripts: `vast_remote_stack_isolation_c.sh`, `runpod_remote_stack_isolation_c.sh`

Evidence: `pretraining/cpt-s6-stack-isolation-c`.

<!-- memory-fabric:store/pretraining/cpt-eval-unify-vs-buckets -->
---
store_path: pretraining/cpt-eval-unify-vs-buckets
title: "CPT eval: 2-doc Spurgeon stop is too small; do not unify C buckets"
summary: "Operator asked (2026-08-27): is a 2-doc Spurgeon eval too small, and should Spurgeon/Puritan/confession/general become one unified eval so CPT can keep learning Reformed theology?"
priority: high
tags: [cpt, eval, early-stop, review]
schema_version: 1.3
last_updated: "2026-08-28T00:11:29-04:00"
evidence: [continued_pretrain/scripts/18_prep_hf_dataset.py, continued_pretrain/kaggle/b_output/checkpoints_sota/checkpoint-250/trainer_state.json, continued_pretrain/kaggle/b_output_v6/checkpoints_sota/checkpoint-75/trainer_state.json, continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/kaggle/runpod_cpt_v3/cpt_train.log]
---

# Do not collapse C buckets; enlarge B stop sample

Operator asked (2026-08-27): is a 2-doc Spurgeon eval too small, and should Spurgeon/Puritan/confession/general become one unified eval so CPT can keep learning Reformed theology?

## Answer
Yes, 2 docs is too small **as a stop key**. No, do not merge C holdout buckets into one mix score. Knowledge comes from **unread mix tokens**, not from how eval is labeled. Training is already one mix (Spurgeon 40.2%, Puritan 45.7%, confession 5.5%).

## Three evals people conflate
- **Train mix:** already unified. Multiple eval names do not split training.
- **B in-train eval:** `EVAL_DOCS_PER_BUCKET=2`, `EVAL_BUCKETS_DURING_TRAIN=[spurgeon]`, plus 4 mix docs. Metric `eval_spurgeon_loss`. VRAM hatch from T4 OOM (v7 tried 8 docs). This fired S5 at 375/4128.
- **C scorecard:** spurgeon 50 docs / 70k tok, puritan 20 / 37k, confession 10 / 20k, general 10 / 16k. Probe + §5 gate. This is the real eval.

## S5 evidence (cpt_train.log)
`eval_spurgeon`: 2.292@25 → **2.254@325** → 2.259@350 → 2.257@375. Δ after 325 is ±0.005 noise on ~2 sermons. Patience 2 × eval 25 = stop.
`eval_mix`: 2.085@25 → **2.029@375**, still falling. Mix val on disk is 520 docs; B only scores 4 of them.

C then: all four buckets beat Ampere base (−6.8 / −5.2 / −4.4 / −1.2%) but miss §5 −15%. Puritan/confession are 45.7%/5.5% of the mix; 8.2M tokens only gave a thin slice.

## Why not one C number
A single mix PPL hides the tradeoffs the gates need: Spurgeon-ness (product), Puritan/confession −15% (§5), general forgetting. Historical RC3: mix-only B eval overfit while holdout PPL got worse. Mix test is a random split of train, not a held-out author/work set.

## Next B (when approved) — do this instead of unifying
1. Early-stop **floor** (min_steps ~0.4–0.5 epoch or min_tokens ~25–40M) so 2-doc noise cannot halt at 9%.
2. On 24 GB raise `EVAL_DOCS_PER_BUCKET` to 16–32 (or full C spurgeon 50). Keep logging mix.
3. Optional composite: stop only if Spurgeon **and** mix are both flat; or weight 0.4 spurgeon + 0.4 puritan + 0.2 confession.
4. Do not switch `METRIC_FOR_BEST` to `eval_mix_loss` without a larger mix sample and a Spurgeon-not-rising guard.
5. Keep C per-bucket. Keep Hub v2 until a new C wins.

## Fact-check of the B-eval strategy summary (2026-08-28)

The summary is **directionally right**. Nits:

- Mix val **is** `VAL_FRACTION=0.01` (`18_prep_hf_dataset.py`). v3 = 520 test rows. B in-train mix is still only `EVAL_DOCS_PER_BUCKET*2` (4 docs on S5), not those 520.
- Mix-only B (`eval keys=['mix']`, `b_output`): `eval_mix` **rose** 2.316→2.463. C v3 holdouts **+9 / +11.6 / +15.4 / +17.8%**. True. Do not describe that run as “mix improved.”
- **B v6 did not show mix-stable + spurgeon-rising.** Both rose (mix 1.890→1.920; spurgeon 2.568→2.607; puritan/confession/general also rose). Spurgeon as `METRIC_FOR_BEST` is justified because C scores **holdouts**, not because v6 mix and spurgeon diverged.
- S5 is the divergence the other way: spurgeon ±0.005 after 325, mix still falling. Composite+floor is the synthesis of both eras.
- Floor: 25M tokens ≈ 28% of the 90M epoch, not 40–50%. Pick one: `min_steps≈0.4–0.5 epoch` (~36–45M) **or** `min_tokens=25–40M`. Do not treat them as equal.
- Confession C holdout is 10 docs; `EVAL_DOCS_PER_BUCKET=32` will cap. Spurgeon C is 50.
- Composite stop is **not** in `train_cpt_sota.py` today (`QuietEarlyStoppingCallback` is single-metric `eval_spurgeon_loss`). Needs a custom callback, a flat epsilon (else ±0.005 still fires after the floor), and a separate `METRIC_FOR_BEST` for which ckpt to save. `max_steps` (one epoch) still required so mix can crawl forever.
- Keep abort-at-50 **on a fresh-from-base run**; loosen only on the S5-LoRA continue.

<!-- memory-fabric:store/pretraining/cpt-future-b-early-stop-scale -->
---
store_path: pretraining/cpt-future-b-early-stop-scale
title: "Future CPT B: early-stop does not scale with mix size"
summary: "S5 B (corpus v3, 2026-08-27/28) did **not** consume the 91M-token mix"
priority: high
tags: [cpt, early-stop, recipe, corpus-v3]
schema_version: 1.3
last_updated: "2026-08-27T22:06:01-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_run_config.json, continued_pretrain/kaggle/runpod_cpt_v3/cpt_train.log, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/configs/train_config_cpt_theology_sota.json]
---

# Future CPT B — early-stop vs mix size

S5 B (corpus v3, 2026-08-27/28) did **not** consume the 91M-token mix. HuggingFace `QuietEarlyStoppingCallback` (patience **2**, `eval_steps=25`, metric `eval_spurgeon_loss`) halted at **375 / 4128** steps (~9% of one packed epoch, **~8.2M tokens**). Best step **325**, `eval_spurgeon=2.254118`.

This is the same absolute-token neighborhood as the v2 probe (stopped 450/674, **~9.9M** of 14.8M). Larger mix made the **same** stop look early as a percentage. 4128 is a **ceiling** (`ceil(packed_rows/16)`), not a consume-the-dataset target.

## Why the 2-sermon probe flattened

- `EVAL_DOCS_PER_BUCKET=2` (VRAM hatch). Stop key is **two** Spurgeon docs, not the 520-row val set and not unread Puritan/confession mass.
- `eval_spurgeon` 2.292 → 2.254 then ±0.005 noise. Patience 2 = **50 steps** after last best, regardless of remaining rows.
- `eval_mix` was **still falling** at 375 (2.031 → 2.029). Unread data was not proven useless.
- Abort-at-50 is a **separate** credit guard (passed: 2.292 @ 25 → 2.291 @ 50). Do not confuse it with early-stop.

## Do this on a future full-mix B (needs approval; do not stealth-change S5 C)

Before another GPU B that is supposed to **see** ~90M tokens:

1. Add a **min_steps / min_tokens floor** before patience can fire (e.g. not before ~10M tokens, or not before 0.4–0.5 packed epoch), **or**
2. Scale patience with `packed_epoch_steps / eval_steps` (patience 2 was written when max_steps was ~674).
3. Do not treat 2-doc `eval_spurgeon` CE as “dataset consumed.” Either raise `EVAL_DOCS_PER_BUCKET` on 24 GB, add a secondary mix metric, or log that the probe can saturate while mix loss still falls.
4. Keep `QuietEarlyStoppingCallback` (skip patience increment when the current eval dict lacks `eval_spurgeon_loss`). Keep `one_doc_padded`, r=32, GDN LoRA, embed FT, abort-at-50.

## Do not

- Re-run S5 B with a longer patience **instead of C**. Next step for **this** adapter is C (approval required).
- Assume 91% of the mix was redundant. Most of it was never seen.
- Compare B `eval_spurgeon` 2.254 vs v2 2.248 as a merge gate (tiny eval CE, different mixes).

Repo playbook for a later more-tokens B (after C, not instead of C): continued_pretrain/NEXT_CPT_MORE_TOKENS.md and store pretraining/cpt-next-b-more-tokens-playbook. Preferred path is load S5 LoRA + lower LR + early-stop floor; optimizer was not copied so HF resume is impossible. Next session is C, not this B.

<!-- memory-fabric:store/pretraining/cpt-future-checklist -->
---
store_path: pretraining/cpt-future-checklist
title: "CPT future session checklist"
summary: "Short CPT resume checklist pointing at cpt-current / cpt-v3-s6-handoff; SFT is separate."
priority: high
tags: [handoff]
schema_version: 1.3
last_updated: "2026-08-29T11:22:29-04:00"
summary_hash: 12369953e99b588bfe506ced27377723
---

## Future CPT quick start

1. Read `pretraining/cpt-current` then `pretraining/cpt-v3-s6-handoff` (+ `s6_session.json` if present).
2. Resume S6: mount volume `7hb931c5oe`, `PREV_RUN_CHECKPOINT=checkpoint-2100`, `CPT_RUN_MODE=fresh`, fix monitor (log completion markers, not SSH-only).
3. New corpus / more tokens: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md` / `CORPUS_V3_S6_CONTINUE_CHECKLIST.md`.
4. C eval: correct `EXPECTED_ADAPTER_SHA256`; compare to Hub v2; keep v2 if worse.
5. Never train without volume verify (`s6_verify_mount.ps1`).

## Parallel track
SFT rewrite / quote gate: `fine-tuning/next-session-handoff`. Do not mix CPT and SFT pods/volumes.

<!-- memory-fabric:store/pretraining/cpt-hub-keep-phase-a -->
---
store_path: pretraining/cpt-hub-keep-phase-a
title: "Do not Hub-overwrite with Phase B ddbbee3a"
summary: "Do **not** upload Phase B C-winner `ddbbee3a` to Hugging Face and do **not** make it the new Hub version"
priority: high
tags: [cpt, s7, hub, ddbbee3a, decision]
schema_version: 1.3
last_updated: "2026-09-26T08:12:05-03:00"
evidence: [pretraining/cpt-s7-phase-b-isolation-c, pretraining/cpt-hub-s7-overwrite]
---

## Operator decision 2026-09-26

Do **not** upload Phase B C-winner `ddbbee3a` to Hugging Face and do **not** make it the new Hub version.

Hub production stays `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` = Phase A s5best `06354dfc…`.

Why: C deltas vs Hub are a few hundredths of PPL (12.45→12.39 / 5.52→5.50 / 5.27→5.25). §5 is still open (−8.9% / −6.4% vs −15%). Overwriting would drop the Hub baseline the next C must beat.

`ddbbee3a` is the local **init** for the `a_output_v6` holdout-sibling replay only. Promote after a later C wins both Puritan and confession without Spurgeon past ~13.3.

<!-- memory-fabric:store/pretraining/cpt-next-b-more-tokens-playbook -->
---
store_path: pretraining/cpt-next-b-more-tokens-playbook
title: "Next CPT B: more mix tokens + agreed eval strategy"
summary: "S5 B stopped at 375/4128 (~8.2M of ~90M)"
priority: high
tags: [cpt, corpus-v3, recipe, early-stop, lr, eval]
schema_version: 1.3
last_updated: "2026-08-28T00:14:16-04:00"
evidence: [continued_pretrain/NEXT_CPT_MORE_TOKENS.md, continued_pretrain/kaggle/runpod_cpt_v3/theology_cpt_eval_metrics.json, continued_pretrain/scripts/train_cpt_sota.py]
---

# Next CPT B — continue with more mix tokens (eval strategy agreed)

S5 B stopped at 375/4128 (~8.2M of ~90M). **S5 C is complete.** Preferred continue: near v2 Ampere C, far from §5 −15%. **Eval spec (use this, not 2-doc Spurgeon):** `pretraining/cpt-b-eval-strategy`. Repo: `continued_pretrain/NEXT_CPT_MORE_TOKENS.md`. Do **not** create a GPU until the operator says go.

## C verdict (do not re-C this adapter)
- Probe vs own Ampere base: **PASS** (spurgeon 14.31→13.34, puritan 6.03→5.72, confession 5.61→5.36, general 12.05→11.90).
- §5 −15%: **FAIL**.
- Keep Hub `…-cpt-lora-v2`. v3 saw **less** data than v2 (~8.2M vs ~15.6M).

## Preferred continue (not trainer resume)
Adapter-only SHA256 `ef4df3a31c9d17f7ba8741e80df6d764bca19a6d535f0a33c210e547f486c303`. Load LoRA on Qwen3.5-4B-Base, **new Adam**, Ampere bf16. Same mix `a_output_v3`.

Deltas when approved (code is not there yet):
- Body LR ~3e-6–5e-6, emb ~1e-6–2e-6; cosine over continue max_steps.
- **Floor:** `min_steps` ≈ 0.4–0.5 packed epoch (~36–45M). Do not equate this with 25M tokens.
- **Eval:** `EVAL_DOCS_PER_BUCKET` 16–32 (cap at bucket size: confession 10, spurgeon 50). Keep mix + spurgeon; add puritan/confession on 24 GB.
- **Halt:** composite Spurgeon **and** mix flat within epsilon (custom callback). `METRIC_FOR_BEST` stays `eval_spurgeon_loss` (ckpt pick ≠ halt).
- Abort-at-50 **off/loosened on continue only**. Keep one_doc_padded, r=32, GDN, embed FT, QuietEarlyStopping.

New `train()` reshuffles. Volume `7hb931c5oe` via REST v1. Scp optimizer + ckpts.

Do not: mix-only stop; collapsed Reformed PPL; 2-doc Spurgeon stop; fresh 1e-5 from base; rebuild mix; T4 4-bit; overwrite Hub v2 until new C wins.

<!-- memory-fabric:store/pretraining/cpt-next-cpt-improvements-prep -->
---
store_path: pretraining/cpt-next-cpt-improvements-prep
title: "S7 Phase A improvements applied; GPU still blocked on go"
summary: "**No GPU B until operator says go.** Production Hub is S6 SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c`"
priority: high
tags: [cpt, s7, continue, adam, prep, ready]
schema_version: 1.3
last_updated: "2026-09-21T11:05:35-03:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/s7_remote_continue_b.sh, continued_pretrain/scripts/s7_remote_c_eval.sh, continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/scripts/test_cpt_runtime.py]
---

# S7 CPT improvements — Phase A prep + post-audit fixes (2026-09-21)

**No GPU B until operator says go.** Production Hub is S6 SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c`.
Canonical C: Unsloth **2026.8.22 + torch 2.8**.

## Code ready
- `CPT_CONTINUE_PROFILE=s7`: body **2e-6**, emb **8e-7**, warmup **0.04**, max_steps **2064**, min_steps **500**
- patience **4**, ε **0.003**, eval/save **50**, `cosine_with_min_lr` min_lr_rate **0.1**
- Seeded bests = S6 **in-train** @ 2050 (spurgeon 2.4987 / mix 2.0208 / puritan **1.751** / confession **1.668**) — not isolation-C CE
- `theology_cpt_lora_s5best` exporter + `AbortOnSeedRegressionCallback` (seed+0.12 × 2 cycles)
- general bucket monitor-only; `CPT_TRAIN_EMBEDDINGS` env ablation
- Launchers: `s7_remote_continue_b.sh`, `s7_remote_c_eval.sh`; monitor `--total-steps` / `CPT_TOTAL_STEPS`
- Playbook: `continued_pretrain/NEXT_CPT_S7.md`

## Goal
§5 −15% on puritan + confession (isolation C: −7.2% / −6.0%).

## Do on GPU go
1. Copy a_output_v3 + nested 6aab LoRA + train/eval + s7 launchers
2. `bash s7_remote_continue_b.sh`; monitor with `-TotalSteps 2064`
3. C via `s7_remote_c_eval.sh` with explicit SHA; keep Hub S6 unless win

## Do not
- HF-resume 2050/2100/2400; unset PREV with leftover sota
- Seed with isolation-C full-holdout CE
- Fresh 1e-5; 4e-6 S6 clone; C on torch 2.11
- Mix rebuild / merge / Hub overwrite without winning C

<!-- memory-fabric:store/pretraining/cpt-s6-gpu-blocked-volume-balance -->
---
store_path: pretraining/cpt-s6-gpu-blocked-volume-balance
title: "S6 GPU blocked: volume 404 and $5 balance"
summary: "Highest **complete** local HF checkpoint (adapter + `optimizer.pt` + `trainer_state.json`): `continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota/checkpoints_sota/checkpoint-2050` (w"
priority: high
tags: [cpt, s6, runpod, blocker, volume]
schema_version: 1.3
last_updated: "2026-09-16T07:21:48-03:00"
evidence: [continued_pretrain/scripts/s6_runpod_common.ps1, continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota/checkpoints_sota/checkpoint-2050]
---

# S6 GPU resume blocked — volume gone + balance (2026-09-16)

Phase 0 code is ready. GPU resume **did not start**.

## Blockers
1. Network volume `7hb931c5oe` → **404** on the authenticated Runpod MCP account (`list-network-volumes` empty).
2. Creating a replacement 75 GB US-IL-1 volume → **400**: account must have **≥ $5** balance.
3. `~/.runpod/config.toml` has empty `apikey = ''`; REST/runpodctl path unusable until a real `RUNPOD_API_KEY` is set. MCP OAuth REST v1 pod create returned Cloudflare **403/1010**.

## Local resume artifact (when volume/funds restored)
Highest **complete** local HF checkpoint (adapter + `optimizer.pt` + `trainer_state.json`): `continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota/checkpoints_sota/checkpoint-2050` (was HF best during interrupted S6; step 2100 not present locally).

## Do not
Train on container disk only. Do not `S6_FRESH_START` over a good ckpt. Keep Hub v2 until finished B + winning C.

## Next operator steps
1. Add ≥ $5 Runpod balance **or** restore/recreate volume in **US-IL-1** with checkpoint data.
2. Set real `RUNPOD_API_KEY` (or `flash login`).
3. `s6_orchestrate.ps1 -StartMonitor` with continue+resume (Phase 0). Upload/use `checkpoint-2050` if volume no longer has `checkpoint-2100`.

<!-- memory-fabric:store/pretraining/cpt-s6-stack-isolation-c -->
---
store_path: pretraining/cpt-s6-stack-isolation-c
title: "S6 stack-isolation C: PPL flips on S5 Unsloth/torch pin"
summary: "Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on **Unsloth 2026.8.22 + torch 2.8.0+cu126** scores spurgeon **12.85 (−10.2% vs base 14.31)**"
priority: high
tags: [cpt, s6, c-eval, stack-isolation, early-stop, hub-v2]
schema_version: 1.3
last_updated: "2026-09-20T19:04:21-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/stack_isolation_c/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v3/cpt_eval.log, pretraining/vast-cpt-s6-resume-spike-analysis]
---

# S6 stack-isolation C COMPLETE (2026-09-20)

## Bottom line
Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on **Unsloth 2026.8.22 + torch 2.8.0+cu126** scores spurgeon **12.85 (−10.2% vs base 14.31)**. Vast C on Unsloth 2026.9.6 / torch 2.11 was a **false FAIL** (+27.9%). Weights are not bad.

## Pins (from S5 `runpod_cpt_v3/cpt_eval.log`)
- Unsloth **2026.8.22** (Hub-v2 C used 2026.8.21)
- torch **2.8.0+cu126** + torchvision **0.23.0**
- `UNSLOTH_SKIP_TORCHVISION_CHECK=1` after dropping xformers (pulls torch≥2.10)

## Host note
Runpod unpaid (402). Ran on **Vast RTX 4090** with the S5/Hub-v2 **software** pin. Residual host confound remains; Unsloth/torch were the controlled variables. Prefer a confirmatory Runpod C when funded.

## Scorecard (a_output_v3 holdouts, Ampere bf16)

| Bucket | Base | Adapter | Δ% |
|--------|------|---------|-----|
| spurgeon | 14.31 | **12.85** | **−10.2%** |
| puritan | 6.03 | 5.60 | −7.2% |
| confession | 5.61 | 5.27 | −6.0% |
| general | 12.05 | 11.83 | −1.8% |

Probe vs base: **PASS**. §5 −15%: still FAIL.

## 16-doc train probe (same C)
- Adapter spurgeon@16: ppl **12.13** loss **2.495** (matches train `eval_spurgeon_loss=2.4987`)
- Base@16: ppl 13.30 → Δ **−8.85%**
- So 16-doc vs 50-doc was **not** the Vast regression cause; both look good on the pinned stack.

## vs Hub v2 / S5 (same holdouts family)
- Hub v2: spurgeon 13.28 (−7.2%)
- S5: spurgeon 13.34 (−6.8%)
- This S6: spurgeon **12.85 (−10.2%)** — **better** on this scorecard

## Interpretation (plan table)
- **Flip** → Vast **C-eval** stack untrustworthy (not proof train stack is buggy).
- Hub overwrite is a **separate approve** — numbers favor overwrite vs Hub v2, but do not auto-overwrite.
- Do **not** start a blind new B to “fix C”.

## Artifacts
Scripts: `vast_remote_stack_isolation_c.sh`, `vast_stack_isolation_c.ps1`, `runpod_stack_isolation_c.ps1`, `runpod_remote_stack_isolation_c.sh`.
Eval: `CPT_EVAL_TRAIN_PROBE_DOCS` + `UNSLOTH_PIP_SPEC` env in `eval_cpt_sota.py`.

## Operator Q&A clarifications (2026-09-20)

### What was broken
- **Proven:** full holdout **C** on Unsloth **2026.9.6** / torch **2.11** inflated adapter PPL (base stayed ~14.31; adapter → 18.31).
- **Not proven as a single package:** Unsloth vs torch alone (both changed in the isolation flip).
- **Rejected:** wrong SHA, 16-vs-50 overfit as the Vast +28% cause, embed→lm_head tying sync.

### Do NOT conflate with B early-stop
- Bug proven = **post-train C** on the new stack.
- S6 B halt = composite early-stop after **resume spike** (train loss also jumped 1.92→2.33) — real train dynamics, not the 50-doc C liar.
- In-train **16-doc** spurgeon loss (~2.4987) **matches** good-stack train probe (2.495) → B’s probe metric was trustworthy.
- Blind new B is **not** required to “undo” the false C.

### Step timeline (C scored best, not last)
| Phase | Steps |
|-------|-------|
| S5 initial v3 | stop ~**375**/4128, best ~**325** |
| S6 continue | HF best **2050** (SHA `6aab…`) |
| S6 last resume session | resume **2050** → stop **2400** (spike; never beat 2050) |
| **C scored** | **2050** only — not 2400 |

### Improvement claim
On good-stack C (v3 holdouts): S6@2050 spurgeon **12.85 (−10.2%)** beats Hub v2 **13.28 (−7.2%)** and S5 **13.34 (−6.8%)**. §5 −15% still FAIL. Hub overwrite still needs **separate operator approve**.

<!-- memory-fabric:store/pretraining/cpt-s7-gpu-blocked-balance -->
---
store_path: pretraining/cpt-s7-gpu-blocked-balance
title: "S7 Phase A GPU blocked: Runpod balance"
summary: "- `a_output_v3` mix SHA `23dd…`"
priority: high
tags: [cpt, s7, runpod, blocker, balance]
schema_version: 1.3
last_updated: "2026-09-22T09:31:17-03:00"
evidence: [continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/scripts/s7_remote_continue_b.sh]
---

# S7 Phase A GPU go blocked — Runpod balance (2026-09-22)

Operator said go. Prep remains ready. **No pod created** (`list-pods` empty).

## Evidence this session
1. `create-network-volume` EU-RO-1 75GB → **400**: account must have **≥ $5**.
2. Secure RTX 4090 EU-RO-1 → **400** no stock (LOW evaporated).
3. Secure L4 (EU-RO-1 / EUR-IS-1 / US-MO-2) with persistent `/workspace` → **402** balance too low to rent a pod.
4. Network volumes on account: **0**. Prior volume `7hb931c5oe` still gone.
5. `runpodctl user` → `no_credentials` (`RUNPOD_API_KEY` unset; `~/.runpod/config.toml` apikey empty). MCP OAuth works for infra CRUD only.

## Local artifacts ready
- `a_output_v3` mix SHA `23dd…`
- Nested S6 LoRA SHA `6aab…` at `kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/`
- Launch: `scripts/s7_remote_continue_b.sh`; monitor `-TotalSteps 2064`
- SSH key registered: `runpod-cpt-v2` (matches `~/.ssh/runpod_cpt.pub`)

## On next go (after funds)
1. Add Runpod balance (enough for volume gate ≥$5 + ~$0.50–0.74/hr × expected B hours).
2. Prefer: create network volume in GPU DC, then Secure pod (4090 / L4 / A100) with mount `/workspace`.
3. Optionally set `RUNPOD_API_KEY` for runpodctl `send`/`receive`; else scp via registered SSH key.
4. Sync a_output_v3 + nested 6aab LoRA + train/eval + s7 launchers; `bash s7_remote_continue_b.sh`.
5. Do **not** HF-resume sota; keep Hub S6 until winning C.

<!-- memory-fabric:store/pretraining/cpt-s7-new-authors-holdout-pc1-2026-09-26 -->
---
store_path: pretraining/cpt-s7-new-authors-holdout-pc1-2026-09-26
title: "pc1: new-authors holdout + a_output_v6 pack"
summary: "Repo: `C:\\Users\\rafael\\Projetos\\search-sermons` (origin ask-spurgeon), main @ `c8660ac`"
priority: high
tags: [cpt, s7, v6, new-authors, pc1, foundry]
schema_version: 1.3
last_updated: "2026-09-26T16:15:05-03:00"
---

## pc1 build 2026-09-26

Repo: `C:\Users\rafael\Projetos\search-sermons` (origin ask-spurgeon), main @ `c8660ac`.

- Built `holdouts_new_authors`: **20 docs**, SHA `e490b61d9c24d240dd82623faea382d8ec969399d400f449de1ff67821a846d5`
- Authors: downame 5, ambrose 4, swinnock 3, guthrie 2, venning 2, + binning/durham/preston/vincent
- Updated `a_output_v6` holdouts with `new_authors`; theology_dataset train **22915** / val **232**
- mix_v6 rebuilt excluding new-authors fingerprints → mix SHA `e050787e…` (see `cpt-v6-mix-sha-e050787e`)
- Nested LoRA `ddbbee3a…` confirmed under vast_cpt_s7 fetch
- Untouched: a_output_v3/v4/v5, mix_v3/v4/v5, holdouts_pinned_v3

Forge dry later **PASSED** with pin bump. Still no rent until top-up + go.

<!-- memory-fabric:store/pretraining/cpt-s7-phase-a-done -->
---
store_path: pretraining/cpt-s7-phase-a-done
title: "CPT S7 Phase A complete (Vast early-stop)"
summary: "- Host: Vast instance `52063161` (destroyed after fetch)"
priority: high
tags: [cpt, s7, vast, early-stop]
schema_version: 1.3
last_updated: "2026-09-22T16:06:36-03:00"
---

## S7 Phase A result (2026-09-22)

- Host: Vast instance `52063161` (destroyed after fetch).
- Continue from S6 LoRA with new Adam; `CPT_CONTINUE_PROFILE=s7`; stopped by **COMPOSITE EARLY-STOP @ step 1250** (max_steps 2064, patience 4, ε 0.003).
- Final HF LoRA SHA: `1381e5ee4eaf8f838aa6b1b21d1757de29404dbb50aa5e68ec3a4fd3bceae4db` (= checkpoint-1250).
- s5best SHA: `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` @ step 1200 (prefer for C eval).
- Local path: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/`.
- Seed CE: spurgeon 2.4987 / mix 2.0208 / puritan 1.751 / confession 1.668.
- @1250 CE (log): spurgeon 2.4867 / mix 2.009 / puritan 1.742 / confession 1.671.
- Train loss ~1.988; runtime ~10179s.

<!-- memory-fabric:store/pretraining/cpt-s7-phase-b-isolation-c -->
---
store_path: pretraining/cpt-s7-phase-b-isolation-c
title: "Phase B isolation C: 12.39 / 5.50 / 5.25; §5 FAIL"
summary: "Nested §5 export step 600 SHA `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214` on Unsloth **2026.8.22 + torch 2.8**"
priority: high
tags: [cpt, s7, c-eval, phase-b, ddbbee3a, vast]
schema_version: 1.3
last_updated: "2026-09-26T08:12:03-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_b_c/theology_cpt_eval_metrics.json, continued_pretrain/scripts/vast_cpt_s7_c_eval.ps1]
---

## Phase B isolation C COMPLETE (2026-09-23)

Nested §5 export step 600 SHA `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214` on Unsloth **2026.8.22 + torch 2.8**. Vast instance `52296492` destroyed after fetch. Artifacts: `kaggle/runpod_cpt_v3/vast_cpt_s7_b_c/`.

Do **not** eval the top-level `fetch/theology_cpt_lora_s5best/` file — that is still Phase A `06354dfc`.

### Scorecard (pinned v3 holdouts, Ampere bf16)

| Bucket | Base | Phase B C | Δ% | Hub `06354dfc` |
| spurgeon | 14.31 | **12.39** | **−13.42%** | 12.45 (−13.0%) |
| puritan | 6.03 | **5.50** | **−8.88%** | 5.52 (−8.6%) |
| confession | 5.61 | **5.25** | **−6.37%** | 5.27 (−6.0%) |
| general | 12.05 | 11.88 | −1.34% | 11.95 |

Train probe Spurgeon@16: ppl 11.83 (−11.09% vs base 13.30). MCQ: WSC 0.74 / Heidelberg 0.45.

### Gate
§5 −15% Puritan+confession: **FAIL**. Slightly better than Hub on all three; not a promote. Optional C on HF-best `6d003041` was skipped — one adapter is enough for the gate.

<!-- memory-fabric:store/pretraining/cpt-sota-assessment-2026-07 -->
---
store_path: pretraining/cpt-sota-assessment-2026-07
title: "CPT SOTA Assessment + Implementation (2026-07)"
summary: "CPT SOTA Assessment + Implementation (2026-07)"
priority: high
tags: [pretraining, cpt, unsloth, qlora, spurgeon, sota]
schema_version: 1.3
last_updated: "2026-07-10T21:34:01-04:00"
evidence: [continued_pretrain/notebooks/B_training.ipynb, continued_pretrain/notebooks/B_training_sota.ipynb, continued_pretrain/scripts/07_build_theology_mix.py]
review_status: stale
---

# CPT SOTA Assessment + Implementation (2026-07-10)

## Verdict on B_training.ipynb
- Solid **Kaggle-practical Phase-1 Spurgeon style CPT** (~style 7/10, engineering 8/10).
- **Not** art-state for Spurgeon/Puritans/theology (**~4.5/10** vs multi-author domain goal).
- Keep as known-good baseline; **never overwrite**.

## Baseline facts
- Model: unsloth/Qwen2.5-3B QLoRA, r=32 alpha=64, targets attn+MLP only
- Seq 2048 packing, LR 2e-4 SFTTrainer, no dual LR / no embed+lm_head
- Corpus Spurgeon-only ~3.5k docs ~32M tokens; 2 epochs done train~2.23 val~2.30

## SOTA path implemented (new files only)
- `scripts/07_build_theology_mix.py` — multi-source mix, Spurgeon weight 2.5×, replay, holdouts, manifest
- `notebooks/A_data_prep_sota.ipynb` — HF dataset + multi-holdouts
- `notebooks/B_training_sota.ipynb` — UnslothTrainer, dual LR 5e-5/5e-6, r=64 rsLoRA, embed+lm_head
- `notebooks/C_eval_sota.ipynb` — multi-bucket PPL + style/doctrine/forgetting + merge
- `configs/train_config_cpt_theology_sota.json`
- `data/SOURCES_SOTA_CPT.md` + empty `data/puritans|confessions|bible/`
- README documents baseline vs SOTA tracks

## Defaults
- Body LR 5e-5, embedding_learning_rate 5e-6
- r=64 use_rslora=True, train embed_tokens+lm_head
- Spurgeon oversample 2.5×, replay target 10% when sources available
- Puritan/confession/Bible: user-supplied under data/

## Next operator steps
1. Add PD Puritan/confession/Bible texts under data/
2. Rebuild mix; upload Kaggle corpus
3. Run A_sota → B_sota → C_sota on T4

<!-- memory-fabric:store/pretraining/cpt-v2-additional-failure-modes -->
---
store_path: pretraining/cpt-v2-additional-failure-modes
title: "CPT v2 other causes of poor results besides token budget"
summary: "C v4 uniform ~+2% PPL on all domain buckets is not only “too few tokens + no embed LoRA.” Other mechanisms that match the evidence:"
priority: high
tags: [cpt, kaggle, ppl, packing, qwen35, holdout]
schema_version: 1.3
last_updated: "2026-08-26T13:51:42-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/07_build_theology_mix.py, continued_pretrain/scripts/test_manual_pack.py, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
review_status: stale
---

# Additional CPT failure modes (beyond token budget / frozen embeds)

C v4 uniform ~+2% PPL on all domain buckets is not only “too few tokens + no embed LoRA.” Other mechanisms that match the evidence:

## High — harmful early LoRA (not just undertraining)

B `eval_spurgeon_loss` rose 2.568→2.602→2.607 at 25/50/75. Best ckpt is still worse than base on C. Greedy probes loop (repetition 0.29–0.82). Trainable 42.5M attn/MLP LoRA (0.93%) at LR ~2e-5 on a base that already has puritan PPL 6.2. The adapter **perturbed** the LM; it did not specialize.

## High — packed train ≠ C eval task

**B v6–v12 (Kaggle):** `build_manual_packed_dataset` concatenated then hard-cut 2048. Attention mask was all-ones (no packing isolation). Train CE included mid-doc cold starts and cross-EOS context. C `eval_ppl` scores independent docs, first 2048 only, `add_special_tokens=False`. D2 `[0,2,1,2,1]`: a 0-EOS row is a mid-document window. Confession C tokens 20480/10 = 2048 exactly — every confession holdout doc truncated.

Δ% vs base is still fair (same protocol). Absolute PPL is not “full-doc LM PPL.”

**Local (2026-08-26, unpushed):** `pack_document_isolated` in `_gen_sota_notebooks.py`. Greedy EOS-aligned pack (no leftover-A + start-of-B splices). Multi-doc rows only when both fit; first token of later docs `labels=-100`. Long docs split at 2048 with continuation prefix ignored. `packing=False` (GatedDeltaNet cannot use 2D segment masks / native varlen). D1 no longer FAILs when packed rows ≈ raw docs. D2 gates post-EOS ignore_index. Test: `continued_pretrain/scripts/test_manual_pack.py`. **Not on Kaggle until the next B push.**

## Medium — Qwen3.5 hybrid + float32 on 4-bit

B log: “Using float32” / “cannot work with float16.” `load_in_4bit=True` train and C. Hybrid linear_attention + VL Processor. Tied embeds, vocab ~248k. Noisy CPT path; small LoRA can look like uniform noise.

## Medium — Spurgeon weight 0.164 = undersample

`oversample()` with weight&lt;1 **subsamples by chars**. ~84% of Spurgeon chunks never enter the mix. Share 40.5% is after dropping most Spurgeon, not “we trained on all sermons.”

**Local (2026-08-26, mix not rebuilt):** `07_build_theology_mix.py --keep-all-spurgeon` (default True) keeps every Spurgeon train chunk and oversamples other domain buckets (`--max-other-weight` default 5) to hold the share target. Expect ~5× mix chars if rebuilt. `--no-keep-all-spurgeon` restores the old drop. **Do not upload a new Kaggle corpus until size/shares are reviewed.**

## Medium — tiny holdouts (measurement)

Puritan 20 docs / 135 KB; confession 10 / 71 KB; general 10. B early-stop used 4 docs/bucket. Gate can FAIL on noise; general +3.8% especially fragile.

## Low / wrong sign

OCR PASS; F1 chunking PASS; mix not Spurgeon-only. Chunk holdouts (`take_holdout` samples chunks) can **leak** siblings into train — that would **help** holdout PPL, not explain +2% worse. Greedy probe loops ≠ PPL (no repetition penalty at eval).

## Confirmed on B v11 (2026-08-26) — drift with embed LoRA at 2e-5

`eval_spurgeon_loss` still rose **2.349 → 2.363 → 2.383** at steps 25/50/75 with `TRAIN_EMBEDDINGS=True`. Early-stop 75; best=ckpt-25. Embed LoRA did **not** stop early drift at body LR 2e-5.

## Confirmed on B v12 (2026-08-26) — drift at 1e-5 too

Same early-stop shape as v6/v11. `eval_spurgeon_loss` **2.340 → 2.345 → 2.361** at steps 25/50/75; wall 2.81 h; best=ckpt-25; SHA256 `ffe193feb33b7fd3a7af745b50e4745998cafcee96c42678c85ef943614b886a`. Body LR **1e-5** did **not** stop the rise by step 50. Do not C; do not push another B on the **stream-pack** recipe. Next B must be isolated pack (local, unpushed).

## Local (2026-08-26) — one_doc_padded is now the generator default

Isolated pack (`manual_isolated`) is **not** the next B: it still concatenates two complete short docs. `_gen_sota_notebooks.py` default is `PACKING_MODE=one_doc_padded` (`pack_one_doc_padded`): one doc or 2048 window per row, `PAD_TO_MAX=False`, GDN LoRA on the padded path, `GPU_PROFILE=t4`. Notebooks regenerated. **Not pushed.** See `pretraining/cpt-v2-one-doc-padded`.

<!-- memory-fabric:store/pretraining/cpt-v2-c-eval-gate-verdict -->
---
store_path: pretraining/cpt-v2-c-eval-gate-verdict
title: "CPT v2 C_eval gate FAIL (C v4 scored ckpt-25)"
summary: "**FAIL — do not merge.** C v4 COMPLETE on B v6 **best** LoRA (checkpoint-25), not a last-step accident"
priority: high
tags: [kaggle, cpt, handoff, gate]
schema_version: 1.3
last_updated: "2026-08-25T10:20:50-04:00"
evidence: [continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md, continued_pretrain/kaggle/c_output/theology_cpt_eval_metrics.json, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
review_status: stale
---

# CPT v2 C_eval gate verdict (2026-08-25, analysis addendum)

**FAIL — do not merge.** C v4 COMPLETE on B v6 **best** LoRA (checkpoint-25), not a last-step accident.

## Adapter identity
SHA256 of `adapter_model.safetensors` is identical for:
- B `checkpoints_sota/checkpoint-25`
- B `theology_cpt_lora`
- C `theology_cpt_lora_final`

`checkpoint-50` / `checkpoint-75` differ and are worse on B `eval_spurgeon_loss`. **Do not** spend a C session on `ADAPTER_OVERRIDE=checkpoint-25`.

## Δ PPL vs base (%)
spurgeon +2.0 | puritan +2.2 | confession +1.9 | general +3.8

- Spurgeon/puritan/confession: worse than base → FAIL
- General within +10% → PASS alone
- Uniform ~+0.02 nats = LoRA noise, not domain learning

## Why (not P1)
Scored ckpt is step 25 ≈ **0.82M tokens** (~5.5% of a 14.9M packed epoch). Recipe was VRAM fallback: r=32, **TRAIN_EMBEDDINGS=False**, MAX_STEPS cap 100. §5 −15% puritan/confession was written for embed CPT × ~1 epoch.

## MCQ
WSC 70%→76% (+6) | Heidelberg 38.1%→42.9% (+4.8, need +10). MCQ alone does not ship.

## Next
B v7: batch 1×16, TRAIN_EMBEDDINGS=True, MAX_STEPS ≈ one packed epoch, quieter early-stop. C **only after** B v7. Do not merge until §5 PPL PASS.

<!-- memory-fabric:store/pretraining/cpt-v2-c-eval-root-causes -->
---
store_path: pretraining/cpt-v2-c-eval-root-causes
title: "CPT v2 C_eval root causes"
summary: "Full report: `continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md`"
priority: high
tags: [kaggle, cpt, rc2, rc3, rc4]
schema_version: 1.3
last_updated: "2026-08-24T22:09:47-04:00"
evidence: [continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md, continued_pretrain/kaggle/b_output/b_logs.txt, continued_pretrain/kaggle/c_output/theology_cpt_eval_metrics.json]
review_status: stale
---

# CPT v2 C_eval — root cause analysis (2026-08-24)

Full report: `continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md`
Handoff: `continued_pretrain/CPT_V2_KAGGLE_STATUS.md`
Metrics: `continued_pretrain/kaggle/c_output/theology_cpt_eval_metrics.json`

## Gate: FAIL (do not merge)

All holdout PPL worse than base: spurgeon +9%, puritan +11.6%, confession +15.4%, general +17.8%.
Heidelberg MCQ +9.5 pts (gate ≥+10). WSC +2 pts.

## Root causes (priority order)

1. **Packing disabled:** B log `Unsloth: packing=True ignored (processor-based model)`. Qwen3.5 Processor path → 4356 rows, max 2048 tok/doc, ~7.4M tok/epoch — not packed CPT.
2. **Overfitting after step 50:** eval_mix_loss 2.32→2.46; grad_norm rose. Best ckpt still fails holdout PPL in C.
3. **Early-stop mismatch:** B eval only `eval keys=['mix']` (45-doc val), not holdout buckets used in §5.
4. **Qwen3.5 constraints:** tied embeddings (TRAIN_LM_HEAD=False), float32 train, processor breaks packing; C needed ids_for_text for VL processor.
5. **MCQ vs PPL:** short MCQ gains without long-form LM improvement.
6. **Probes:** repetition loops, doctrinal confabulation — adapter drift not Spurgeon quality.

## B reference diagnostics

- train rows 4356, D1 max row 2048, tokens_per_epoch_est 7376550
- tie_word_embeddings true, trainable_embed_or_head []
- LoRA r=64 LR 5e-5, 250 steps T4

## Next session

Fix B for processor/no-packing OR pre-chunk; holdout eval in B; do not merge; optional SFT stock dry-run.

## RC1 fix (local, 2026-08-24)

Implemented in `_gen_sota_notebooks.py` B_training generator (not pushed to Kaggle yet):
- `text_tokenizer` / `ids_for_text` helpers (same as C_eval)
- `build_manual_packed_dataset()` — EOS-separated stream split at 2048
- `MANUAL_PACK=True`, `packing=False`, pass inner `train_tok` to UnslothTrainer
- D1 gate raises if packed rows ≈ raw doc count
- run_config records `manual_pack`, `packing_mode`, `raw_doc_count`

Regenerate: `python continued_pretrain/scripts/_gen_sota_notebooks.py`

## RC2–RC4 local fixes (2026-08-24, not pushed)

- **RC2:** r=32, LR 2e-5, emb LR 5e-6, MAX_STEPS=100, EVAL/SAVE=25, SAVE_TOTAL_LIMIT=4
- **RC3:** `_find_hf_holdout_root()` (never corpus .txt); require spurgeon HF; `METRIC_FOR_BEST=eval_spurgeon_loss`; `EarlyStoppingCallback(patience=2)`
- **RC4:** Qwen3.5 constraint docs; D4 warn if TRAIN_EMBEDDINGS but no trainable embed params
- **C:** `ADAPTER_OVERRIDE`; probe trigram repetition warnings (RC6 signal)
- Regenerate notebooks only — no Kaggle push

## Next session (replace older Next session blurb)

Local RC1–RC4 done; notebooks regenerated; **not pushed**. See `pretraining/cpt-v2-next-session-handoff`.
When asked: push B → train with HF theology_holdouts → C eval → ship only on §5 PPL. Do not merge until gate passes.

<!-- memory-fabric:store/pretraining/cpt-v2-c-eval-runpod-complete -->
---
store_path: pretraining/cpt-v2-c-eval-runpod-complete
title: "CPT v2 Runpod C complete — probe PPL beats bf16 base"
summary: "Community RTX 4090 Ampere bf16"
priority: high
tags: [cpt, runpod, c-eval]
schema_version: 1.3
last_updated: "2026-08-27T09:01:07-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json, continued_pretrain/kaggle/runpod_cpt_v2/cpt_eval.log, continued_pretrain/scripts/eval_cpt_sota.py]
---

# CPT v2 Runpod C eval — COMPLETE 2026-08-27

Community RTX 4090 Ampere bf16. Pod `rf2dayesihddon` **deleted**. `RUN_MERGE=False`. No network volume (MCP cannot attach `7hb931c5oe`).

## Adapter scored
`continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_lora` SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478` (B best ckpt-400, embed-FT + GDN).

## Scorecard vs this run’s bf16 base
Do not mix with C v4 T4 4-bit PPL.

| Bucket | Base | v2 | %Δ |
|--------|------|-----|-----|
| spurgeon | 14.31 | 13.28 | −7.2% |
| puritan | 5.99 | 5.68 | −5.0% |
| confession | 7.24 | 6.73 | −7.0% |
| general | 13.43 | 13.20 | −1.7% |

Probe (beat base): **PASS** all four. §5 −15% on puritan/confession: **FAIL**. MCQ WSC 70→74; Heidelberg 40.5→45.2 (need +10).

Artifacts: `kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json`, `kaggle/runpod_cpt_v2/cpt_eval.log`.

Code: `eval_cpt_sota.py` (`--preflight`, `--install --break-system-packages`, HF_HOME, SHA256 pin, two model loads).

<!-- memory-fabric:store/pretraining/cpt-v2-c-eval-runpod-prep -->
---
store_path: pretraining/cpt-v2-c-eval-runpod-prep
title: "CPT v2 C eval Runpod prep — copy list, gates, Ampere-only"
summary: "Execute C on the **Runpod B** adapter"
priority: high
tags: [cpt, runpod, c-eval, handoff]
schema_version: 1.3
last_updated: "2026-08-27T08:21:31-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/RUNPOD_RUNBOOK.md, continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_lora/adapter_config.json]
review_status: stale
---

# CPT v2 C eval — Runpod session prep (2026-08-27)

Execute C on the **Runpod B** adapter. Do not C Kaggle 4-bit ckpts. Do not merge this session unless holdout PPL beats base (unexpected for a 15.6M-token probe).

## Why C is allowed
B abort-at-50 **passed** (`eval_spurgeon` 2.288 @ 25 → 2.286 @ 50) and kept falling to 2.248 @ 400. Runbook: C only after complete B with stable/falling eval through 50.

## Score this file
- `adapter_model.safetensors` ~1445 MB
- SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- `find_adapter` looks for `theology_cpt_lora/adapter_config.json` under `CPT_WORK_ROOT`
- Also copy: `kaggle/a_output/theology_holdouts/` (spurgeon/puritan/confession/general HF dirs), `data/catechism_mcq.json`

## C code
Source of truth: `continued_pretrain/scripts/_gen_sota_notebooks.py` → `notebooks/C_eval_sota.ipynb`. There is **no** `eval_cpt_sota.py` yet — run the notebook or generate a script first. C install still uses pip without `--break-system-packages`; add it on the official PyTorch image.

Config that must stay:
- `ADAPTER_OVERRIDE = None` (not B v6 `checkpoint-25`)
- `EVAL_BASE = True` (§5 needs base PPL)
- `RUN_MERGE = False`
- `SCORE_LAST_CHECKPOINT = False` unless `checkpoints_sota/checkpoint-*` is on the box (not in the local copy)
- Ampere: `load_in_4bit=False` (adapter trained bf16 + embed FT)

## §5 gates (unchanged; probe will likely FAIL the −15%)
Compare **prefix PPL** vs base (C v4 base: spurgeon 14.94, puritan 6.20, confession 7.78, general 14.07):
- spurgeon: better than base
- puritan / confession: ≥15% better
- general: ≤10% worse
MCQ does not override a PPL FAIL.

This C answers: did Ampere + embed LoRA + one_doc_padded **stop hurting** the base (C v4 was uniform ~+2% PPL)?

## Pod recipe
1. Have `RUNPOD_API_KEY` + runpodctl **before** create (MCP cannot attach volume).
2. Attach volume `7hb931c5oe` at `/workspace` **or** copy LoRA+holdouts onto a 75 GB disk and scp results off before delete (B had to do the latter).
3. One 4090, no extra ports, `--terminate-after` backstop, delete GPU when C finishes.
4. `python3 -u` so logs are not fully buffered.

<!-- memory-fabric:store/pretraining/cpt-v2-isolated-pack-review -->
---
store_path: pretraining/cpt-v2-isolated-pack-review
title: "Isolated-pack review: leftover splice fixed"
summary: "Did **not** push Kaggle, run C, or merge"
priority: high
tags: [cpt, packing, kaggle, review]
schema_version: 1.3
last_updated: "2026-08-26T08:47:40-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/test_manual_pack.py, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
review_status: stale
---

# Isolated-pack defect review (2026-08-26)

Did **not** push Kaggle, run C, or merge. Mix was **not** rebuilt (Kaggle corpus still Spurgeon weight 0.164).

## Fixed (high confidence)

- **Leftover-A + start-of-B splice:** `pack_document_isolated` left the last window of a doc longer than 2048 in `cur_ids`, then packed the next *short* doc onto that tail. That is the old stream-pack failure mode. Fix: each split-doc window is flushed as its own row; only *complete* docs that both fit share a row. First token of later docs still `labels=-100`.
- **Collator:** UnslothTrainer now gets `DataCollatorForSeq2Seq` (`label_pad_token_id=-100`) so labels are not cloned from `input_ids`. Transformers LM collator would undo isolation and, with Qwen `pad==eos`, zero EOS CE.
- **D2:** scans **all** packed rows (not first 100); NOTE if no post-EOS token (gate did not fire); FAIL if collator wipes post-EOS `-100`.
- **Tests:** leftover-of-long-A vs next doc; no dropped tokens; HF-shift target at B0 is `-100`; collator-clone footgun documented.
- **MAX_STEPS:** clamp **down** only. Status's “~511” was wrong while `MAX_STEPS=476`. Isolated pack can have *more* rows than stream pack, so 476 may be &lt; one epoch.

Notebooks regenerated from `_gen_sota_notebooks.py`.

## Still true (must not regress)

`TRAIN_EMBEDDINGS=True`, `LR=1e-5`, `EVAL_DOCS=2`, spurgeon-only eval, dtype hook, `save_only_model`, `SAVE_TOTAL_LIMIT=1`, `packing=False`, `PACKING_MODE=manual_isolated`.

## Left / not bugs

- D1 packed-rows ≈ raw-docs is NOTE not FAIL (intent).
- All-ones attention across packed *complete* short docs (GatedDeltaNet cannot isolate).
- Mix `--keep-all-spurgeon` exists in `07_build_theology_mix.py`; **corpus on Kaggle still subsampled**.
- D1 max-length check samples ~200 rows (packer cannot emit &gt;2048).
- Eval rise / C v4 FAIL is unchanged; isolated pack does not by itself make C safe.

## B push

Packing path is defect-clean enough to push **after a human reads D1/D2 on the live kernel**. Do not C. Do not merge.

<!-- memory-fabric:store/pretraining/cpt-v2-lora-snapshot -->
---
store_path: pretraining/cpt-v2-lora-snapshot
title: "CPT v2 keepable LoRA snapshot (best-400, private Hub)"
summary: "Runpod B best **step 400** adapter is documented so a later mix/token run can fail without losing this training"
priority: high
tags: [cpt, lora, runpod, handoff]
schema_version: 1.3
last_updated: "2026-08-27T09:50:01-04:00"
evidence: [continued_pretrain/scripts/upload_cpt_lora_to_hf.py]
---

# CPT v2 keepable LoRA snapshot

Runpod B best **step 400** adapter is documented so a later mix/token run can fail without losing this training.

## Where
- Session scorecard: SESSION RESULTS markdown in `continued_pretrain/kaggle/runpod_cpt_v2/`
- Snapshot index and identity JSON live in that same folder
- Model card / Unsloth load snippet: the README inside `theology_cpt_lora/`
- SHA256 of `adapter_model.safetensors`: `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`

Weights (~1.45 GB) stay on local disk (gitignored safetensors under continued_pretrain). Not merged, not GGUF.

## Load
Unsloth FastLanguageModel.from_pretrained with load_in_4bit=False on Ampere/Ada. Qwen3.5 VL processor: tokenize with text= only. Do not C/infer this adapter on T4 4-bit. Do not use Kaggle B v6 checkpoint-25.

## Hugging Face (2026-08-27)
Private repo `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` uploaded after SHA256 check. Still not merged, not public. Re-upload: `python continued_pretrain/scripts/upload_cpt_lora_to_hf.py`

<!-- memory-fabric:store/pretraining/cpt-v2-next-session-handoff -->
---
store_path: pretraining/cpt-v2-next-session-handoff
title: "CPT v2 handoff: C done, LoRA on private Hub, do not merge"
summary: "Historical v2 pointer; live work is cpt-current / s6-handoff."
priority: high
tags: [cpt, runpod, handoff, c-eval]
schema_version: 1.3
last_updated: "2026-08-29T11:22:29-04:00"
evidence: [continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
summary_hash: ff0e4a961bf41dca633cd820b50305e4
---

# CPT v2 next-session — HISTORICAL (pointer)

v2 Runpod B+C finished 2026-08-27. Hub LoRA `…-theology-cpt-lora-v2` is the production reference.

**Canonical:** `pretraining/cpt-v2-session-2026-08-27-results` and `pretraining/cpt-v2-c-eval-runpod-complete`.

**Current CPT work:** `pretraining/cpt-current` → `pretraining/cpt-v3-s6-handoff` (do not restart v2 C/merge from this file).

<!-- memory-fabric:store/pretraining/cpt-v2-one-doc-padded -->
---
store_path: pretraining/cpt-v2-one-doc-padded
title: "CPT v2 one-doc padded — Kaggle dead; Runpod next"
summary: "**2026-08-26:** B **v13 ERROR** (`DeadKernelError` after ckpt-100)"
priority: high
tags: [cpt, packing, gdn, qwen35, kaggle, runpod]
schema_version: 1.3
last_updated: "2026-08-26T23:15:36-04:00"
evidence: [continued_pretrain/CPT_V2_KAGGLE_STATUS.md, continued_pretrain/scripts/_gen_sota_notebooks.py]
review_status: stale
---

# One-doc padded rows — Kaggle v13/v14 ERROR; Runpod uses the same pack

**2026-08-26:** B **v13 ERROR** (`DeadKernelError` after ckpt-100). B **v14 ERROR** (resume missed, same death window). **STOP Kaggle.** Next GPU path is Runpod, not another T4 notebook.

## Config (generator + `train_cpt_sota.py`)
- `PACKING_MODE=one_doc_padded` — one doc or 2048 window per row; never concat two docs
- `PAD_TO_MAX=False`
- `LORA_GDN=True` → `in_proj_qkv`, `in_proj_z`, `out_proj` (never `in_proj_a`/`in_proj_b`)
- `GPU_PROFILE` **auto** (t4 4-bit / ampere bf16 on sm_80+)
- After pack: `MAX_STEPS = PACKED_EPOCH_STEPS` (v13: 10779 rows → **674** steps)
- Abort if `eval_spurgeon_loss` at 50 > 25 (encoded callback)
- D2 FAIL if `multi_doc_rows > 0`

## v13 evidence
D1/D2 PASS (`multi_doc_rows=0`, 10779 rows, tokens_per_epoch_est ≈14.8M). Only eval @25 ≈2.335 before kernel death. No step-50 eval on T4.

<!-- memory-fabric:store/pretraining/cpt-v2-pre-train-analysis-checklist -->
---
store_path: pretraining/cpt-v2-pre-train-analysis-checklist
title: "CPT v2 pre-train analysis checklist (closed)"
summary: "Analysis/check session finished"
priority: high
tags: [cpt, runpod, analysis, checklist, handoff]
schema_version: 1.3
last_updated: "2026-08-26T23:15:31-04:00"
evidence: [continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/RUNPOD_RUNBOOK.md]
review_status: stale
---

# CPT v2 — pre-train analysis checklist (CLOSED 2026-08-26)

Analysis/check session finished. **Next session trains on Runpod.** Do not re-run this checklist as a blocker.

## Decisions locked
- **TRAIN_EMBEDDINGS:** True (official CPT). OOM hatch: embeds off before dropping GDN.
- **Mix 0.164:** not rebuilt.
- **MAX_STEPS:** after pack, set to `PACKED_EPOCH_STEPS` (one padded epoch; ~674 on B v13 10779 rows / 16).
- **Abort-at-50:** `AbortIfSpurgeonRisesCallback` stops if `eval_spurgeon_loss` at 50 > 25. Flat/equal continues.
- **§5 −15%:** long-term bar unchanged. This $15 job is a ~15.6M-token **probe**; ship later only if holdout PPL beats base.

## Checks done (this session)
- Tests: `test_manual_pack.py`, `test_cpt_runtime.py`, `test_kaggle_path_resolve.py` PASS (incl. abort helper).
- Local `kaggle/a_output`: theology_dataset (8162/83 from A log) + HF holdouts + `catechism_mcq.json` present. `a_output` ~51 MB. 50 GB volume still enough.
- `GPU_PROFILE` auto (not hardcoded Ampere). C install now picks `kaggle-new` vs `colab-new` from `/kaggle/working`.
- `--install` exits after pip.
- Runpod MCP: 0 pods, 0 volumes (auth OK). No provision this session.

## Recipe unchanged
`one_doc_padded`, `PAD_TO_MAX=False`, `LORA_GDN=True` (`in_proj_qkv`/`in_proj_z`/`out_proj`). Fresh first Runpod job (`PREV_RUN_CHECKPOINT=` empty).

<!-- memory-fabric:store/pretraining/cpt-v2-qwen35-upstream-recipes -->
---
store_path: pretraining/cpt-v2-qwen35-upstream-recipes
title: "Qwen3.5 CPT upstream recipes vs T4 pipeline"
summary: "Checked against Unsloth docs, Unsloth issues/PRs, HF transformers packing, and a working Qwen3.5 Unsloth CPT cookbook"
priority: high
tags: [qwen35, unsloth, cpt, packing, qlora, t4]
schema_version: 1.3
last_updated: "2026-08-26T13:37:34-04:00"
evidence: ["continued_pretrain/scripts/_gen_sota_notebooks.py:407", continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
review_status: stale
---

# Qwen3.5 CPT — upstream recipes that already work (2026-08)

Checked against Unsloth docs, Unsloth issues/PRs, HF transformers packing, and a working Qwen3.5 Unsloth CPT cookbook. Map to Ask Spurgeon B on Kaggle T4.

## Already in our pipeline
Dual LR (body 1e-5, emb 5e-6); train embed_tokens; RSLoRA/dropout 0; `packing=False`; seq 2048 batch 1; light eval (`prediction_loss_only`, EVAL_DOCS=2). Tied `lm_head` off is correct.

## Do not copy blindly onto T4
- **No QLoRA:** Unsloth Qwen3.5 fine-tune guide — 4-bit not recommended (quant error). Working 4B path is **bf16 LoRA ~10 GB** (`load_in_4bit=False`, `load_in_16bit=True`). T4 is sm_75 (no bf16); Unsloth forces **float32** for this arch, so we used 4-bit to fit. Official recipe needs **L4/A100**.
- **No Unsloth packing on GDN:** issue 4160 / PR 7211 — packing **silently leaks** across samples. Experimental varlen (PR 7249) needs `cu_seqlens`/`seq_idx`; transformers 5.2–5.8 can **drop** `cu_seq_lens_q` (ms-swift 9618). Need transformers ≥5.9 + collator keys.
- Isolated pack that still **concatenates two complete short docs** in one 2048 row still leaks GDN state. Working fail-closed path: **one doc (or one 2048 window) per row, pad**.
- Cookbook GDN LoRA names: `in_proj_qkv`, `in_proj_z`, `out_proj` plus q/k/v/o + MLP. Too-narrow q/k/v/o-only misses linear-attention layers. **Do not** LoRA `in_proj_a`/`in_proj_b` if packing (NaNs).
- Successful CPT cookbooks use **≥100M–1B tokens** with **falling** loss. Our B early-stops at ~0.8M tokens.

## Links
- https://www.unsloth.ai/docs/models/qwen3.5/fine-tune.md
- https://unsloth.ai/docs/basics/continued-pretraining
- https://github.com/unslothai/unsloth/issues/4160
- https://github.com/unslothai/unsloth/pull/7211
- https://github.com/vessl-ai/vessl-cloud-cookbook/blob/main/aqr-finance/train.py

<!-- memory-fabric:store/pretraining/cpt-v2-runpod-b-complete -->
---
store_path: pretraining/cpt-v2-runpod-b-complete
title: "CPT v2 Runpod B complete — best step 400, adapter local"
summary: "Fresh Ampere bf16 LoRA (not a Kaggle 4-bit resume)"
priority: high
tags: [cpt, runpod, training]
schema_version: 1.3
last_updated: "2026-08-27T08:21:39-04:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_run_config.json, continued_pretrain/kaggle/runpod_cpt_v2/cpt_train.log, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
review_status: stale
---

# CPT v2 Runpod B — COMPLETE 2026-08-27

Fresh Ampere bf16 LoRA (not a Kaggle 4-bit resume). GPU pod `3aift60lb2tr68` **deleted**. Adapter lives only in the repo copy below (volume was never mounted).

## Locked result
- Base: `unsloth/Qwen3.5-4B-Base`; r=32; GDN `in_proj_qkv` / `in_proj_z` / `out_proj`; `TRAIN_EMBEDDINGS=True`; `TRAIN_LM_HEAD=False`
- Pack: `one_doc_padded`, `PAD_TO_MAX=False`, 8162 docs → 10779 rows, `MAX_STEPS=674`, `multi_doc_rows=0`
- Abort-at-50: **pass** — eval_spurgeon 2.28797 @ 25 → 2.28556 @ 50
- Early-stop patience 2 at **450**. Best **400**, metric 2.248331
- Train loss 1.989; ~0.98 h; ~7.4 s/step on 4090; ~20 GB VRAM
- Local: `continued_pretrain/kaggle/runpod_cpt_v2/` (lora, `cpt_train.log`, `theology_cpt_run_config.json`, `checkpoint-400-trainer_state.json` only — **no optimizer ckpts**)

## eval_spurgeon by step
25: 2.288, 50: 2.286, 75: 2.278, 100: 2.272, 125: 2.265, 150: 2.260, 175: 2.259, 200: 2.259, 225: 2.255, 250: 2.255, 275: 2.252, 300: 2.251, 325: 2.250, 350: 2.249, 375: 2.249, **400: 2.248**, 425: 2.249, 450: 2.249.

mix eval also fell ~2.091 → 2.043.

## Infra leftovers
- Volume `7hb931c5oe` US-IL-1 50 GB STANDARD — empty (MCP ignored `networkVolumeId`)
- Secure 4090 because community stock was gone
- Generator typo fixed: `is_hf_holdout_root` (not `_is_hf_holdout_root`)

<!-- memory-fabric:store/pretraining/cpt-v2-runpod-two-session-plan -->
---
store_path: pretraining/cpt-v2-runpod-two-session-plan
title: "CPT v2 plan: B and C done — no merge"
summary: "v2 session plan completed 2026-08-27; pointer only."
priority: high
tags: [cpt, runpod, handoff, plan]
schema_version: 1.3
last_updated: "2026-08-29T11:22:29-04:00"
evidence: [pretraining/cpt-v2-c-eval-runpod-complete, continued_pretrain/CPT_V2_KAGGLE_STATUS.md]
summary_hash: cf6902169c6e2730b444909aefbc57a3
---

# CPT v2 session plan — DONE (pointer)

Prep → analyze → Runpod B → C eval → Hub snapshot all **done** (2026-08-26/27). No merge.

See `pretraining/cpt-v2-session-2026-08-27-results`. Live CPT: `pretraining/cpt-current`.

<!-- memory-fabric:store/pretraining/cpt-v2-session-2026-08-27-results -->
---
store_path: pretraining/cpt-v2-session-2026-08-27-results
title: "CPT v2 2026-08-27 session results (C + LoRA + private Hub)"
summary: "Canonical write-up is SESSION RESULTS markdown inside `continued_pretrain/kaggle/runpod_cpt_v2/` (same folder as the LoRA and eval JSON)"
priority: high
tags: [cpt, runpod, c-eval, lora, handoff]
schema_version: 1.3
last_updated: "2026-08-27T09:49:53-04:00"
evidence: [continued_pretrain/CPT_V2_KAGGLE_STATUS.md, continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_eval_metrics.json]
---

# CPT v2 session results 2026-08-27

Canonical write-up is SESSION RESULTS markdown inside `continued_pretrain/kaggle/runpod_cpt_v2/` (same folder as the LoRA and eval JSON).

## Verdict
- Probe bar **PASS**: all four holdout PPLs better than this C's Ampere bf16 base.
- Plan section 5 (-15% puritan/confession) **FAIL**.
- **Do not merge. Do not re-C this adapter. Do not push Kaggle.** Mix still 0.164.

## C PPL (base to adapter, % better)
- spurgeon 14.31 to 13.28 (-7.25%)
- puritan 5.99 to 5.68 (-5.05%)
- confession 7.24 to 6.73 (-6.98%)
- general 13.43 to 13.20 (-1.73%)
MCQ: WSC 70% to 74%; Heidelberg 40.5% to 45.2% (need +10).

## Adapter
- Best step 400; SHA256 `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478`
- Local `theology_cpt_lora` under kaggle/runpod_cpt_v2; Ampere bf16 only; embed_tokens saved.
- Private Hub: `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` (uploaded this day after SHA256 check). Weights also on disk, gitignored.
- GPU pod deleted. Volume 7hb931c5oe unused.

## Next
Decide mix rebuild / more tokens vs ship this LoRA as-is. Need runpodctl plus API key to attach the volume on a future GPU.

<!-- memory-fabric:store/pretraining/cpt-v3-s6-interrupted -->
---
store_path: pretraining/cpt-v3-s6-interrupted
title: "S6 continue-B interrupted — resume later"
summary: "S6 B interrupted at 2110/4128; pointer to cpt-v3-s6-handoff for resume and C eval."
priority: high
tags: [cpt, s6, c-eval]
schema_version: 1.3
last_updated: "2026-08-29T11:07:00-04:00"
summary_hash: 15b39e7ce3d55ac42863abbd9fe97e5d
---

# CPT S6 continue-B — interrupted (pointer)

S6 continue-B stopped at **step 2110/4128** (~51%) after monitor false-positive pod delete. Volume `7hb931c5oe` is source of truth (`checkpoint-2100`; HF best `checkpoint-2050`).

**Canonical handoff (resume + partial C metrics + Hub v2 policy):** `pretraining/cpt-v3-s6-handoff`

Resume rule: HF `PREV_RUN_CHECKPOINT` with `CPT_RUN_MODE=fresh` (or unset) — **not** `continue` mode. Keep Hub v2 until a full S6 B + winning C eval.

<!-- memory-fabric:store/pretraining/cpt-v6-mix-sha-e050787e -->
---
store_path: pretraining/cpt-v6-mix-sha-e050787e
title: "v6 mix SHA pin e050787e after new_authors"
summary: "After rebuilding mix_v6 on pc1 to exclude `new_authors` diagnostic holdout fingerprints, `mix_sha256` moved:"
priority: high
tags: [cpt, s7, v6, mix-sha, foundry]
schema_version: 1.3
last_updated: "2026-09-26T16:08:03-03:00"
---

## Mix SHA pin bump (2026-09-26)

After rebuilding mix_v6 on pc1 to exclude `new_authors` diagnostic holdout fingerprints, `mix_sha256` moved:

- **was:** `2d5a99c1a0d4d3e4d64013dabe894a52f4de1bf0b576e8997b02af595f691acd`
- **now:** `e050787e138e3d082937e35d1a87aa139f8e980403c3e5fefcc55aa90a2465fc`

Applied on pc1 working tree / branch: `$MixSha` in `vast_cpt_s7_common.ps1`, `EXPECT_MIX` in `vast_cpt_s7_local_readiness.py`, `NEXT_CPT_S7.md`.

Box commit ready on `chore/cpt-v6-mix-sha-e050787e` (`e3ac437`); GitHub push blocked from group-chat Auto-review — push/PR from DM or pc1 when possible.

Forge may re-dry once pc1 pin is live. No rent until go.

<!-- memory-fabric:store/pretraining/cpt-v6-new-authors-diagnostic-holdout -->
---
store_path: pretraining/cpt-v6-new-authors-diagnostic-holdout
title: "CPT v6 new-authors diagnostic holdout (PR #1)"
summary: "Merged to main as `c8660ac` (2026-09-26)"
priority: high
tags: [cpt, s7, v6, new-authors, foundry, holdout]
schema_version: 1.3
last_updated: "2026-09-26T16:15:03-03:00"
---

## New-authors diagnostic holdout (PR #1)

Merged to main as `c8660ac` (2026-09-26).

- Builder: `continued_pretrain/scripts/19_build_new_authors_holdout.py` → `data/holdouts_new_authors/`
- Monitor-only like `general`: not in COMPOSITE_EARLY_STOP_METRICS, not §5/Hub
- Isolation C reports `new_authors` when present
- Pinned v3 Spurgeon/Puritan/confession untouched

Operator build completed on pc1 — see `pretraining/cpt-s7-new-authors-holdout-pc1-2026-09-26`.

<!-- memory-fabric:store/pretraining/forge-gpu-ops-posture-2026-09-26 -->
---
store_path: pretraining/forge-gpu-ops-posture-2026-09-26
title: "Forge Gpu Ops Posture 2026 09 26"
summary: "`vast_cpt_s7_orchestrate.ps1` dry on pc1 passed after mix pin `e050787e…`"
priority: high
tags: []
schema_version: 1.3
last_updated: "2026-09-26T16:09:17-03:00"
---

## Dry PASS 2026-09-26 ~16:09 BRT

`vast_cpt_s7_orchestrate.ps1` dry on pc1 passed after mix pin `e050787e…`. Init `ddbbee3a…`. Credit ~$2.58 still blocks practical -Go until top-up + operator go. No rent.

<!-- memory-fabric:store/grok/forge-training-ops -->
---
store_path: grok/forge-training-ops
title: "Grok Bot Forge for Vast/Runpod training"
summary: "- **Title:** Vast / Runpod training watch"
priority: high
tags: [grok, grok-bot, vast, runpod, cpt, training-ops]
schema_version: 1.3
last_updated: "2026-09-26T14:27:32-03:00"
evidence: [continued_pretrain/GROK_BOT_FORGE.md, .cursor/skills/gpu-train-ops/SKILL.md, continued_pretrain/NEXT_CPT_S7.md, pretraining/cpt-next-session-handoff]
---

# Grok Bot Forge (training ops)

Created 2026-09-26. There is no API to create a Grok Bot from Cursor. The teammate is created in the Grok Bot app from `continued_pretrain/GROK_BOT_FORGE.md`.

## Profile
- **Name:** Forge
- **Title:** Vast / Runpod training watch
- **Job:** Watch/launch CPT+SFT on Vast (primary) and Runpod (secondary). Never train on the Bot computer.

## Alignment
- Cursor / Cloud Agent skill: `.cursor/skills/gpu-train-ops/SKILL.md`
- Current CPT: v6 replay from nested `ddbbee3a`, session `vast_cpt_s7_replay`, Hub stays Phase A `06354dfc`
- No GPU rent until operator says **go**
- Auto-destroy only after fetch, or idle >20 min with no train

## Operator create steps
1. Grok Bot → New → Create new Bot
2. Paste profile from `GROK_BOT_FORGE.md`
3. Sign into cloud.vast.ai and console.runpod.io (no keys in chat)
4. Paste the first-message block (audit only)

<!-- memory-fabric:store/grok/foundry-train-export -->
---
store_path: grok/foundry-train-export
title: "Grok Bot Foundry for train/export code"
summary: "- **Foundry** — write/refine CPT+SFT+export code via Cursor Cloud Agents"
priority: high
tags: [grok, grok-bot, sft, cpt, export, gguf, ollama]
schema_version: 1.3
last_updated: "2026-09-26T15:05:03-03:00"
evidence: [continued_pretrain/GROK_BOT_FOUNDRY.md, .cursor/skills/llm-train-export/SKILL.md, fine_tuning/scripts/sft_export_if_gates.ps1]
---

# Grok Bot Foundry (train + export code)

Created 2026-09-26. Create the Bot in the Grok Bot app from `continued_pretrain/GROK_BOT_FOUNDRY.md`. No create API from Cursor.

## Split
- **Foundry** — write/refine CPT+SFT+export code via Cursor Cloud Agents. Skill: `.cursor/skills/llm-train-export/SKILL.md`.
- **Forge** — Vast/Runpod GPU ops. Skill: `.cursor/skills/gpu-train-ops/SKILL.md`.

## Rules Foundry must keep
- One knob per PR. Dry orchestrator before go.
- No GPU rent, no Hub overwrite, no GGUF upload without operator go.
- SFT export only after `sft_export_if_gates.ps1` (refusal ≥0.85, echo ≤0.02, corrupt 0, im_end stop ≥0.85, leak ≤0.02, groundedness ≥4.0).
- Knowledge Q&A speaker, not Spurgeon persona. No qa_mix_v2 rebuild.

<!-- memory-fabric:store/grok/integration -->
---
store_path: grok/integration
title: "Grok Integration with Memory Fabric (MCP + Docs + Native Layer)"
summary: "Grok Integration with Memory Fabric (MCP + Docs + Native Layer)"
priority: high
tags: [grok, mcp, memory-fabric, integration, docs, agents]
schema_version: 1.3
last_updated: "2026-06-05T09:41:35-04:00"
review_status: stale
---

# Grok + Memory Fabric Integration

Grok (the TUI/agent harness) has full support for Memory Fabric in this project.

## Key Integration Points (as of 2026-06-04/05)

- **MCP Server**: Configured in `~/.grok/config.toml` under `[mcp_servers.memory-fabric]` (uses full path to project's .venv\Scripts\memory-fabric-mcp.exe from the editable install of C:\Users\rafael\Projetos\agentic-memory).
  - Also available via project `.mcp.json` for compatibility with other clients.
  - Timeouts tuned: startup=20s, tool=120s.
- **Agent Instructions**: The project root `AGENTS.md` (and CLAUDE.md, .agents/rules/dreaming.md + memory-store.md) are kept in sync via `python -m memory_fabric.cli sync-agents`. Grok primarily loads `AGENTS.md` (and deeper ones) as project rules. They instruct to **always use the memory-fabric MCP tools** for any .ai-memory/ operations.
- **Grok Native Memory (complementary)**: Separate layer at `~/.grok/memory/search-sermons/MEMORY.md` (and global). Provides auto first-turn injection, /memory modal, /flush, hybrid search via built-in memory_search/memory_get. Documented in Grok's own `~/.grok/docs/user-guide/13-memory.md`.
- **Full Memory Fabric Docs in Grok**: The complete canonical README from agentic-memory source is installed at `~/.grok/docs/user-guide/13-memory-fabric.md`. The help skill lists it, and cross-references were added in 07-mcp-servers.md and 13-memory.md. This makes the full feature set (MCP tools list, CLI, Dreaming, agentic arch, LLM sampling, split-tool protocol, write safety, etc.) available to Grok agents and users asking for help.
- **Discovery in Grok**: Use the built-in `search_tool` (query e.g. "memory-fabric" or "read_combined") to discover tools. Then `use_tool` with qualified names like "memory-fabric__read_combined_context_tool", "memory-fabric__write_memory_store_tool", etc.
- **Project .mcp.json**: Minimal { "mcpServers": { "memory-fabric": { "command": "memory-fabric-mcp" } } } for portable/IDE use.

## Usage in Grok Sessions for this Project

- At session start (or when context needed): call `read_combined_context_tool(cwd="C:\\Users\\rafael\\Projetos\\search-sermons")` (or via the higher-level combined that the system does).
- For semantic store (new standalone topics): `write_memory_store_tool` with store_path like "grok/integration", "decisions/xxx", "fine-tuning/yyy".
- Maintenance: `dream_tool` (mode light|deep, apply=true for real changes; or prepare+apply split for client-driven).
- Eval: `evaluate_memory_fabric_tool` or `evaluate_dream_quality_tool`.
- Never bypass with raw file reads/writes on .ai-memory/ paths.

## Windows / This Env Specifics
- Use `python -m memory_fabric.cli ...` (not bare `ai-memory`) in hooks/scripts to avoid PATH issues with user scripts.
- Editable dev flow: changes in agentic-memory source immediately affect the MCP (after restart of Grok or /mcps refresh).
- Global Grok config takes precedence for the MCP; avoid project-local .grok/config.toml unless intentionally shadowing.

## Benefits for this Project
- Structured, secret-safe, token-budgeted, versioned (via git + snapshots) memory for agentic work on the RAG/fine-tuning codebase.
- Complements Grok's native memory for richer, dual-layer context.
- Agentic architecture ensures even non-MCP-aware instructions still route through the tools.

Last updated via MCP after installing full README into Grok help system.

<!-- memory-fabric:store/pretraining/kaggle-c-eval-adapter-mount -->
---
store_path: pretraining/kaggle-c-eval-adapter-mount
title: "Kaggle C_eval kernel-source adapter mount"
summary: "C v1 failed `FileNotFoundError: CPT adapter not found` even though B output was mounted"
priority: high
tags: [kaggle, cpt, eval, adapter]
schema_version: 1.3
last_updated: "2026-08-24T09:24:55-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/test_kaggle_path_resolve.py]
review_status: stale
---

# Kaggle C_eval adapter path (2026-08-24)

C v1 failed `FileNotFoundError: CPT adapter not found` even though B output was mounted. Kaggle kernel sources land at `/kaggle/input/notebooks/<user>/<slug>/`, not `/kaggle/input/<slug>/`.

C_eval now walks `/kaggle/input` for `adapter_config.json` under `theology_cpt_lora` / `checkpoints_sota` (prefers LoRA, then checkpoint-50). Skip `hf_home` / caches. Holdouts prefer B `theology_holdouts` HF dirs; corpus `*_holdout.txt` is fallback.

Push C with `--accelerator NvidiaTeslaT4` and `kernel_sources: rafaelvieira1/theology-cpt-v2-b-training-sota`.

<!-- memory-fabric:store/pretraining/merge-and-export -->
---
store_path: pretraining/merge-and-export
title: "Pretraining Step 10 (Merge & Export to Hugging Face)"
summary: "Pretraining Step 10 (Merge & Export to Hugging Face)"
priority: high
tags: [pretraining, merge, export, gguf, huggingface, upload]
schema_version: 1.3
last_updated: "2026-06-08T10:18:26-04:00"
review_status: stale
---

# Pretraining Step 10 (Merge & Export to Hugging Face)

Step 10 of the continued pretraining plan has been successfully completed:
1. **Model Weights Merged:** The trained Phase 1 LoRA adapter weights (from checkpoint-432) were merged back into the base Qwen2.5-3B model.
2. **GGUF Conversion (F16 Precision):** The merged model was converted to GGUF format with original 16-bit (`f16`) precision on Kaggle, preserving 100% of the pretraining model quality.
3. **Hugging Face Hub Upload:** The GGUF file (`qwen2.5-3b.F16.gguf` under `/kaggle/working/spurgeon_f16_gguf_gguf/`) was successfully uploaded to the Hugging Face model repository `rafaelvieirar1r/qwen2.5-3b-spurgeon-gguf-phase1` using the user's secure write token (`HF_TOKEN`) from Kaggle Secrets.
4. **Robustness Improvement:** Updated the local template notebook `continued_pretrain/notebooks/C_eval_and_merge.ipynb` to use dynamic glob-based GGUF file detection (`glob.glob("/kaggle/working/**/*.gguf", recursive=True)`) to gracefully handle folder and filename variations.

<!-- memory-fabric:store/fine-tuning/next-session-handoff -->
---
store_path: fine-tuning/next-session-handoff
title: "Fine-tuning next session handoff"
summary: "**Updated:** 2026-09-04 ~01:20 ET"
priority: high
tags: [fine-tuning, handoff, sft, vultr]
schema_version: 1.3
last_updated: "2026-09-04T01:20:10-04:00"
evidence: [fine_tuning/VULTR_RUNBOOK_SFT.md, fine_tuning/scripts/vultr_orchestrate.ps1]
summary_hash: 245ae3c499ffc4aa9aef564463fa3aeb
---

**Updated:** 2026-09-04 ~01:20 ET

## Primary next: allowlist Vultr API IP, then run GATE-0

```powershell
cd fine_tuning\scripts
.\vultr_orchestrate.ps1
# or after console VM:
.\vultr_orchestrate.ps1 -SshHost <ip>
```

Allowlist agent IP **159.26.98.242** on the Vultr API key (or "any IP" temporarily). Two waits (45m + 90m) still got `401 Unauthorized IP`. No instance created. No GPU billing.

## Scripts ready (do not re-implement)
- `vultr_*.ps1` + `vultr_monitor_until_done.py`
- torch 2.11 + ScalingType smoke in `sft_remote_setup.sh`
- CPU PEFT merge fallback in `merge_cpt_lora.py`
- A16: BATCH=1 GRAD_ACCUM=16 CUDA_VISIBLE_DEVICES=0
- Local `13_sft_local_readiness.py --gate0` PASS (3264/153/100)

## Hard rules
- Destroy Vultr GPU when train/fetch done
- EXPORT only after F §5 gates
- Never log VULTR_API_KEY / HF_TOKEN

<!-- memory-fabric:store/pretraining/puritan-corpus-fetch -->
---
store_path: pretraining/puritan-corpus-fetch
title: "Puritan PD corpus fetch (Archive.org)"
summary: "Puritan PD corpus fetch (Archive.org)"
priority: high
tags: [pretraining, data, puritans, archive-org]
schema_version: 1.3
last_updated: "2026-07-13T10:19:03-04:00"
evidence: [data/puritans/PROVENANCE.md, continued_pretrain/scripts/10_fetch_puritans.py]
review_status: stale
---

# Puritan PD corpus (2026-07-13)

Fetched public-domain OCR into `data/puritans/` (~18 MB) from Internet Archive DjVuTXT + a few Gutenberg Bunyan files. Title-verified where possible; early-modern OCR can be noisy (esp. Sibbes Bruised Reed).

## Authors on disk

Owen (4 works), Watson (Body of Divinity), Sibbes (Bruised Reed), Brooks (Precious Remedies + Complete Works vol 3), Baxter (Saints Rest + Reformed Pastor), Bunyan (4), Flavel (2), Gurnall (Complete Armour), Edwards (Religious Affections).

## Tooling

- `scripts/10_fetch_puritans.py` — re-fetch with verified IA `/download/` URLs + SSL workaround.
- Provenance table: `data/puritans/PROVENANCE.md`.

## Mix after rebuild

~22M chars / ~5.5M tokens: spurgeon 45% / puritan 51% / bible 4% / confession ~0%. Still need more confessions + FineWeb replay for targets.

<!-- memory-fabric:store/fine-tuning/qa-gold-rewrite-pilot -->
---
store_path: fine-tuning/qa-gold-rewrite-pilot
title: "SFT QA gold rewrite pilot (20 rows, merged)"
summary: "**Status:** Complete and **merged** into `qa_mix_train.jsonl`"
priority: high
tags: [sft, qa-mix, gold, rewrite]
schema_version: 1.3
last_updated: "2026-08-28T22:16:08-04:00"
evidence: [fine_tuning/scripts/merge_qa_gold_rewrite.py, fine_tuning/data/qa_mix_manifest.json, fine_tuning/data/qa_rewrite_pilot/pilot_manifest.json]
---

# SFT QA gold rewrite pilot (20 rows, 2026-08-29)

**Status:** Complete and **merged** into `qa_mix_train.jsonl`. Mechanical review PASS. Val and frozen test untouched.

## Overlay
- 16 answerable + 4 refusal (seed 3407, short originals preferred).
- Teacher: cursor-session. Inline quotes + `[Sermon N]` only when the header is in CONTEXT.
- Pilot-11: original Lord's Table claim dropped — not in the v2 chunk.

## Files
- `fine_tuning/data/qa_rewrite_pilot/` — sample.json, `qa_gold_rewrite_pilot.jsonl`, `pilot_manifest.json`

## Mix
- `qa_mix_manifest.json` `gold_overlay.rows=20`
- Zip rebuilt: `spurgeon-qa-mix-v1.zip` (~11.75 MB). Re-upload before D/E/F.
- `13_sft_local_readiness.py` PASS.

<!-- memory-fabric:store/fine-tuning/qa-knowledge-not-persona -->
---
store_path: fine-tuning/qa-knowledge-not-persona
title: "SFT/serve: knowledge assistant, not Spurgeon persona"
summary: "SFT/chat must be knowledge assistant about texts, never Spurgeon persona; catechism CONTEXT landed."
priority: high
tags: [sft, qa-mix, persona, spurgeon, puritans, decision]
schema_version: 1.3
last_updated: "2026-08-29T11:07:00-04:00"
evidence: ["config.py:115", "utils/prompts.py:16", fine_tuning/scripts/rewrite_qa_answers_teacher.py, fine_tuning/scripts/qa_rewrite_checks.py, fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2]
summary_hash: 3111e39f906f87e45fdd826d3619f88b
---

# Decision: knowledge assistant, not Spurgeon persona (2026-08-29)

**Decided 2026-08-29.** Live chat is Q&A over texts, not a character. Supersedes the *speaker/persona* half of `fine-tuning/qa-mix-spurgeon-only-decision`.

## Contract
- Speak **about** Spurgeon and the Puritans (knowledge, distinctions, citations). Never speak **as** them.
- Depth first. Light register welcome (scriptural cadence, metaphor, distinction) without costume.
- No vocatives: `Beloved,`, `My beloved`, `Dear friends`, `My brethren`, PT `amados` / `meus queridos irmãos`.
- Ground every claim in CONTEXT. If CONTEXT is silent, refuse plainly.
- Do **not** fill Puritan (or any) answers from parametric memory when CONTEXT has no such headings. Naming Puritans in the prompt is a source class, not a license to invent.

## Canonical prompt
Keep the name `SPURGEON_SFT_SYSTEM_PROMPT`. `SYSTEM_PROMPT_NEUTRAL` is an alias. App uses `build_user_prompt()` / `USER_PROMPT_TEMPLATE` (no third hardcoded copy). Notebooks import the config string at generate time.

## Data
- Do **not** run `build_qa_mix_v2.py` (wipes overlays).
- Remap jsonl system messages; rewrite assistants via teacher before GPU.
- Optional leading-vocative strip on remaining train assistants.
- SFT examples stay Spurgeon-sermon-heavy until RAG returns Puritan chunks. Never train Calvin/Owen as the answering speaker.
- Catechism CONTEXT slice + Chroma ingest landed 2026-08-29 (see `fine-tuning/next-session-handoff`).

## Out of scope until quote gate + operator go
No GPU, no D→E→F run, no EXPORT/GGUF, no full rewrite of all ~2859 originals via teacher.

<!-- memory-fabric:store/fine-tuning/qa-mix-spurgeon-only-decision -->
---
store_path: fine-tuning/qa-mix-spurgeon-only-decision
title: "SFT QA stays Spurgeon-only (decision)"
summary: "**Decided 2026-08-29** after operator question on mixing writers in QA SFT data"
priority: high
tags: [sft, qa-mix, decision, spurgeon]
schema_version: 1.3
last_updated: "2026-08-29T09:53:15-04:00"
---

# Decision: SFT QA mix stays Spurgeon-only (main slice)

**Decided 2026-08-29** after operator question on mixing writers in QA SFT data.

## Decision
Keep **SFT QA data Spurgeon-only** for the primary mix. Do **not** train the assistant as Calvin/Edwards/etc.

Optional later (F5 gap, not required for dry-run): **~8% catechism/confession as CONTEXT** with Spurgeon still as speaker — teaches grounded reading of a second doc type, not multi-author persona.

## Why
- Serve contract is Spurgeon-from-sermons: `SPURGEON_SFT_SYSTEM_PROMPT`, `[Sermon N]` headers, RAG index = `chspurgeon-sermons` only.
- Mixing other writers as speakers causes persona bleed, train/serve mismatch, citation confusion.
- **CPT** already mixes Spurgeon + Puritans + confessions (domain language). **SFT** should match the live app answer format.

## Do not
- Equal-weight Edwards / Lloyd-Jones / Henry as answering authors
- Put Puritan/confession chunks in user CONTEXT unless retrieval will return them
- Alpaca-style generic-assistant replay (dilutes persona)

## Current data
qa_mix_v2 is Spurgeon-only; F5 gap "No catechism/confession slice (~8%)" remains intentional until RAG indexes those texts or operator asks for the 8% CONTEXT slice.

## Supersession (2026-08-29) — speaker/persona

The *speaker/persona* half of this decision is **superseded** by `fine-tuning/qa-knowledge-not-persona`.

Still valid:
- Keep SFT *examples* Spurgeon-sermon-heavy until RAG returns Puritan/confession chunks.
- Do **not** train Calvin/Edwards/Owen as the answering speaker.
- Do **not** put Puritan chunks in user CONTEXT unless retrieval will return them.
- CPT remains the place other writers' *language* is absorbed.

Changed:
- The assistant is a knowledge Q&A speaker, not Spurgeon-as-character.
- `SPURGEON_SFT_SYSTEM_PROMPT` is no longer "You are Charles Haddon Spurgeon".
- Alpaca-style generic replay is still unwanted; the replacement is a grounded knowledge voice, not a sterile modern-assistant ban on all register.

<!-- memory-fabric:store/fine-tuning/qa-overlay-safe-slice-builders -->
---
store_path: fine-tuning/qa-overlay-safe-slice-builders
title: "Overlay-safe catechism + multi-turn builders"
summary: "| `build_catechism_qa_slice.py` | `--variants`, `--target-new`, `--output` for phrasing variants |"
priority: high
tags: [sft, qa-mix, catechism, multi-turn, builder]
schema_version: 1.3
last_updated: "2026-08-30T22:07:08-04:00"
evidence: [fine_tuning/scripts/build_catechism_qa_slice.py, fine_tuning/scripts/merge_catechism_qa_slice.py, fine_tuning/scripts/build_multiturn_qa_slice.py, fine_tuning/scripts/merge_multiturn_qa_slice.py, fine_tuning/data/qa_mix_manifest.json]
---

# Overlay-safe slice builders — implemented (2026-08-30)

**Status:** Landed. Never used `build_qa_mix_v2.py`.

## What shipped

| Script | Role |
|--------|------|
| `build_catechism_qa_slice.py` | `--variants`, `--target-new`, `--output` for phrasing variants |
| `merge_catechism_qa_slice.py` | `--slice` append-only merge; updates gaps + `catechism_overlays` |
| `build_multiturn_qa_slice.py` | 2-turn rows: bare Q history + CONTEXT follow-up |
| `merge_multiturn_qa_slice.py` | append-only; `multiturn_overlay` in manifest |
| `audit_qa_mix_quality.py` | scores last turn for multiturn; prints multiturn/catechism % |

## Live train after merge

- train **3264** (was 3013)
- catechism **241 (7.4%)** — near F5 ~8%
- multiturn **100 (3.1%)** — inside 2–5%
- refusal ~11.3–11.6%; quote **27.9%**; teacherish 553; caricature 0
- `13_sft_local_readiness` **PASS**; zip repackaged 12.20 MB
- one canonical system prompt on all rows

## Operator notes

- Catechism variants: `qa_catechism_variants.jsonl` (151 added)
- Multiturn: `qa_multiturn_slice.jsonl` (100)
- No GPU / no `build_qa_mix_v2` without operator go
- App `generate_response` is still single-turn today; multiturn trains the `build_chat_messages` shape for when history is wired

<!-- memory-fabric:store/fine-tuning/qa-prompt-strategy-verify -->
---
store_path: fine-tuning/qa-prompt-strategy-verify
title: "QA verify + F5 slice gap report"
summary: "After overlay-safe catechism variants + multiturn merge:"
priority: high
tags: [sft, qa-mix, f5, verification]
schema_version: 1.3
last_updated: "2026-08-30T22:07:13-04:00"
evidence: [fine_tuning/scripts/audit_qa_mix_quality.py, fine_tuning/data/qa_mix_manifest.json]
---

# QA verify — post slice expansion (2026-08-30)

After overlay-safe catechism variants + multiturn merge:

| Metric | Value |
|--------|------:|
| train | 3264 |
| catechism | 241 (7.4%) |
| multiturn | 100 (3.1%) |
| refusal | ~11.6% live / 11.3% manifest |
| quote | 27.9% |
| teacherish | 553 |
| caricature | 0 |
| readiness | PASS |
| system uniqueness | 1 / canonical |

F5 gaps closed enough for slice diversity: catechism near 8%, multiturn in band. Still deferred: full 5–6k teacher bank, GPU.

<!-- memory-fabric:store/fine-tuning/qa-prompt-type-decision -->
---
store_path: fine-tuning/qa-prompt-type-decision
title: "One prompt; diversify task slices"
summary: "**Locked after live verify.** Improves SFT via example-type diversity, not multiple prompts"
priority: high
tags: [sft, qa-mix, decision, prompts]
schema_version: 1.3
last_updated: "2026-08-30T21:26:18-04:00"
evidence: ["config.py:115", "utils/prompts.py:16", fine-tuning/qa-knowledge-not-persona, fine-tuning/qa-prompt-strategy-verify]
---

# Decision: one QA prompt; diversify task slices (2026-08-30)

**Locked after live verify.** Improves SFT via example-type diversity, not multiple prompts.

## Do

1. Keep a single canonical system string: `SPURGEON_SFT_SYSTEM_PROMPT` (= `SYSTEM_PROMPT_NEUTRAL`) across train / val / test / app / Modelfile.
2. Keep a single user wrapper: `USER_PROMPT_TEMPLATE` (`CONTEXT` + headed chunks + `QUESTION:`).
3. Expand **task slices** under that contract, in order:
   - **Catechism CONTEXT → ~8%** (~241 of current train; need ~+151). Prefer more confession/catechism doc types with headers matching `format_context` catechism branch — not a second system prompt.
   - **Multi-turn 2–5%** (60–151 rows): 2-turn grounded follow-ups matching `build_chat_messages` history behavior.
   - Optional: more question phrasings (compare / distinguish / "what does Spurgeon teach") inside the same template.
4. Teacher rewrite remains optional further lift; soft gates already MET (quote 21.5%, teacherish 553).

## Do not

- Multiple system prompts in the SFT mix (persona + neutral + specialist + strict + concise).
- Alpaca or alternate user wrappers.
- Bake `get_system_prompt(variant=strict|concise)` into train jsonl unless serve always sends that variant.
- Train Calvin/Owen as answering speakers.
- Run `build_qa_mix_v2.py` (wipes overlays) without an overlay-safe rebuild path + operator go.
- Start GPU D→E→F without operator go.

## Why

Train/serve prompt mismatch was a primary F5 failure mode. The live app always sends one system + one user shape; slice diversity teaches refusal, second doc-type grounding, and follow-ups without forking that contract.

<!-- memory-fabric:store/fine-tuning/qa-sources-rewrite-progress -->
---
store_path: fine-tuning/qa-sources-rewrite-progress
title: "QA Sources Rewrite Progress"
summary: "Cross-session log of QA answer rewrite pipeline for SFT teacherish/quote fidelity"
priority: high
tags: [fine-tuning, qa-rewrite, stop-point]
schema_version: 1.3
last_updated: "2026-09-02T08:58:42-04:00"
---

# QA Sources Rewrite Progress

Cross-session log of QA answer rewrite pipeline for SFT teacherish/quote fidelity.

## Pipeline overview

1. `rewrite_qa_answers_teacher.py --apply` → writes candidates to `bulk_pending.jsonl`
2. `review_qa_rewrite_bulk.py` → human/auto review
3. `merge_qa_bulk_rewrite.py` → merges approved into QA mix overlay
4. `12_package_kaggle_qa_mix.py` → repackage for Kaggle
5. `audit_qa_mix_quality.py` → gate checks (quote %, teacherish count, caricature)
6. `13_sft_local_readiness.py` → final SFT readiness check

## Milestone history

### 2026-08-29 session — Quote gate MET, teacherish ~76 short

**Metrics snapshot:**
- Quote coverage: **15.8%** (419/2655 answerable with CONTEXT quote) — **15% gate MET**
- Teacherish: **324** total (gold 20 + bulk 304 unique) — target ≥400, ~76 short
- Caricature: **0**
- Bulk merged: **304 unique** in overlay
- `13_sft_local_readiness`: **PASS**
- Train: **3013 rows** (90 catechism)

**Resume point:** next unprocessed row = line **649** in `qa_mix_train.jsonl` (last processed: 648).

**Provider learnings this session:**
- Groq 120b best quality but TPD ~197k/200k exhausted; resets ~3 AM ET
- Groq 20b available, ~30% pass rate
- Cerebras daily quota exhausted
- Gemini/OpenRouter: API OK, poor quote fidelity (backup only)
- Ollama not running locally

**Operational rules established:**
- Single provider on `--apply` only (no parallel writes to `bulk_pending.jsonl`)
- Do not run `build_qa_mix_v2.py` or GPU D→E→F without explicit operator go
- Dedupe backup: `bulk_pending.jsonl.bak.20260830T004257Z`
- Fixed null Cerebras content via `_extract_chat_content()` (dataset row 307)
- TEACHER_SYSTEM rule 5 strengthened for verbatim quotes

**Gate status:**
| Gate | Status |
|------|--------|
| Quote ≥10% | MET (15.8%) |
| Teacherish ≥400 | NOT MET (~76 remaining) |
| Caricature = 0 | MET |

**Next action:** continue rewrite from line 649; ~2–3 batches of 50 to clear teacherish gate.

## 2026-08-30 morning — Teacherish gate MET (401)

**Metrics:** quote 18.0% (478/2655); teacherish **401** (gold 20 + bulk 381); caricature 0; `13_sft_local_readiness` PASS; train 3013.

**This session batches:**
- Groq 120b from line 649: 9 OK then TPD ~198k/200k (killed retries)
- Groq 20b: 12 OK then TPD exhausted
- Cerebras: 31/50 then 24/50 (best remaining provider)
- Merged unique bulk 304 → 381

**Resume if continuing:** next unprocessed line **803**. Gates already met; further rewrite is optional lift. Do not run `build_qa_mix_v2.py` or GPU without operator go.

## 2026-08-30 afternoon — continue with available providers

Lifted teacherish **401 → 489**, quote **18.0% → 20.2%** (536/2655). Bulk unique 381 → 469.

Batches: Cerebras 30/50 + 26/50 then token_quota; Groq 120b brief recover then TPD; Groq 20b TPD; OpenRouter 6/50; Gemini smoke 3/5.

Resume line **1008**. Prefer Gemini for more today; Cerebras/Groq after daily reset.

## 2026-08-30 mid-afternoon — Gemini + OpenRouter continue

Gemini from 1008: 6 OK then quota. OpenRouter two batches: 12/50 + 17/50. Teacherish **489→524**, quote **20.2%→20.7%** (550/2651), bulk unique 469→504. Resume **1125**. Only OpenRouter still usable today among cloud teachers.

## 2026-09-02 — Pass 1 complete; retry-drops paused

**Stop state:**
- Pass 1: **3244/3244** non-gold lines attempted (`bulk_pending` has every line).
- Pass 2 `--retry-drops`: **1778** lines still without `ok=true`; **1466** unique ok.
- Merged into train: **1465** bulk + 20 gold → **1485** teacherish; quote **49.1%**.
- ~**1438** rows still "originalish" in train (mixed legacy + teacher answers).

**Tooling added:** `rewrite_qa_rotate_providers.py` (--retry-drops, --providers filter); `rewrite_qa_answers_teacher.py --retry-drops`; merge retry on Windows PermissionError.

**Resume:** `rewrite_qa_rotate_providers.py --retry-drops`; prefer cerebras after daily reset else `--providers groq,openrouter,gemini`.

**SFT:** dry-run ready (readiness PASS); zip needs repack; operator go for GPU; CPT S6 still incomplete for final merge.

## 2026-09-02 morning — Pass 2 retry-drops continue

**Stop state (live ~09:00 ET):**
- Pass 1 complete: 3244/3244 attempted.
- Pass 2: **1734** drop rows remain; **1510** unique ok in `bulk_pending.jsonl`.
- Merged: **1539** bulk + 20 gold → **1559** teacherish.
- Quote **51.5%** (1471/2855); caricature 0; originalish ~1364.
- `13_sft_local_readiness` PASS.

**Session delta from handoff start:** teacherish +67 (1492→1559), quote +2.2pp, bulk merged +67.

**Batches:** OpenRouter 3/15 ok; background `rewrite_qa_rotate_providers.py --retry-drops --providers openrouter,gemini,cerebras,groq --max-rounds 3` still running (Cerebras Round 1). Log: `rotate_session_log.txt`.

**Providers:** OpenRouter best pass rate; Cerebras steady; Groq 429-heavy.

**Resume:** same rotate command; prefer OpenRouter when limits allow.

**SFT:** dry-run ready; repack zip before upload; optional rewrite lift only.

<!-- memory-fabric:store/fine-tuning/qa-teacher-quote-fidelity-prompt -->
---
store_path: fine-tuning/qa-teacher-quote-fidelity-prompt
title: "QA teacher prompt — quote fidelity fix"
summary: "`fine_tuning/scripts/rewrite_qa_answers_teacher.py` TEACHER_SYSTEM rule 5 strengthened:"
priority: high
tags: [sft, qa-mix, rewrite, prompt]
schema_version: 1.3
last_updated: "2026-08-29T17:17:58-04:00"
---

# QA teacher quote-fidelity prompt fix (2026-08-29)

## Change
`fine_tuning/scripts/rewrite_qa_answers_teacher.py` TEACHER_SYSTEM rule 5 strengthened:
- Quotes must be verbatim copy-paste contiguous CONTEXT substrings (character-for-character: punctuation, hyphens, commas)
- Explicit BAD/GOOD examples added (paraphrase "most thorough", truncated "the profit that he makes by it,", exact "battle-field of sin.")
- Validation in `qa_rewrite_checks.py` unchanged (`norm_ws(q) in ctx_n`)

## Smoke after fix
- **Gemini 2.5 Flash**: 0/3 ok (lines 225–227) — still paraphrases/truncates
- **Cerebras gpt-oss-120b**: 2/3 ok (lines 225–227) — meets ≥2/3 bar

## Batch (Cerebras, limit 50)
- 22 ok / 28 dropped (~44% pass); frequent 429 rate limits
- Merged 24 **new** unique answers (103 total bulk ok in pending; 103 merged cumulative)

## Post-merge audit
- quote **261/2657 (9.8%)** — still GATE <10% but rising from 9.1%
- teacherish **123** (gold 20 + bulk 103)
- caricature **0**
- 13_sft_local_readiness **PASS**

## Recommendation
- Use **Cerebras** for bulk batches; avoid Gemini for quote-heavy rewrites until prompt or model improves
- Continue ~50-row batches; target quote ≥10–15% before GPU
- Optional: `--rerun-ok` on near-miss dropped rows with Cerebras

<!-- memory-fabric:store/bugs/qwen35-processor-text-as-image -->
---
store_path: bugs/qwen35-processor-text-as-image
title: "Qwen3.5 processor text-as-image in C_eval"
summary: "C v2 found the adapter then crashed in PPL on the first Spurgeon holdout:"
priority: high
tags: [kaggle, qwen3.5, processor, cpt, eval]
schema_version: 1.3
last_updated: "2026-08-24T10:19:14-04:00"
evidence: [continued_pretrain/scripts/_gen_sota_notebooks.py, continued_pretrain/scripts/test_kaggle_path_resolve.py]
review_status: stale
---

# Qwen3.5 VL processor treats sermon text as image (C_eval)

C v2 found the adapter then crashed in PPL on the first Spurgeon holdout:
`ValueError: Incorrect image source ... Got Sermon 32 | The Necessity of Increased Faith`

Cause: Unsloth returns a multimodal Processor whose `__call__(images, text, ...)` first positional arg is **images**. `tokenizer(text)` feeds the sermon into `load_image`.

Fix in C_eval: unwrap `.tokenizer`, `ids_for_text` / `tokenize_text` (input_ids + attention_mask only). Smoke-test with that sermon title after load.

<!-- memory-fabric:store/fine-tuning/qwen35-sft-special-tokens -->
---
store_path: fine-tuning/qwen35-sft-special-tokens
title: "Qwen3.5-4B SFT special-token contract"
summary: "**Model:** `unsloth/Qwen3.5-4B-Base` (GATE-0 uses the same tokenizer on the CPT merge)"
priority: high
tags: [sft, qwen35, eos, chatml, tokenizer]
schema_version: 1.3
last_updated: "2026-08-28T22:36:58-04:00"
evidence: [fine_tuning/scripts/audit_qwen35_special_tokens.py, fine_tuning/data/qwen35_special_token_audit.json, fine_tuning/scripts/_gen_sota_sft_notebooks.py, fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2]
---

# Qwen3.5-4B SFT special-token contract (2026-08-29)

**Model:** `unsloth/Qwen3.5-4B-Base` (GATE-0 uses the same tokenizer on the CPT merge). Not Qwen2.5. **Do not hardcode 151644/151645.**

## Live ids (tokenizer-only audit PASS)

| Token | Id | Role |
|---|---|---|
| `<\|endoftext\|>` | **248044** | Native `eos_token` (CPT / document EOT). Safety generate stop. |
| `<\|im_start\|>` | **248045** | ChatML turn open; Ollama stop |
| `<\|im_end\|>` | **248046** | ChatML **turn stop** (SFT generate + Ollama stop) |
| `<\|vision_pad\|>` | **248055** | Native **pad** on this Base (existing special; not im_end) |

- `vocab_size=248044`, `len(tokenizer)=248077`. Specials live in added_tokens. **Do not assert `len == vocab_size`** — that aborts a stock Qwen3.5 tokenizer. Never-resize = `len` unchanged after pad/template setup.
- Base has **no `chat_template`**. Inject plain ChatML (no Instruct thinking/vision/tool jinja). Demo: system/user/assistant each end with `<\|im_end\|>`.
- Do **not** set `tokenizer.eos_token = im_end` (would risk pad=stop). Generate with `eos_token_id=[im_end_id, eot_id]`.
- Pad: keep native `vision_pad` if present; if pad is None or equals im_end, set pad to `endoftext`.
- Unwrap VL Processor before tokenizing text (`bugs/qwen35-processor-text-as-image`).
- Collator: `DataCollatorForSeq2Seq(label_pad_token_id=-100)` so pad!=im_end still does not clone labels.
- Never `add_special_tokens` / resize / LoRA embed+lm_head unless S5 shows ChatML tokens are not emitted.

## Files
- `fine_tuning/scripts/audit_qwen35_special_tokens.py` + `fine_tuning/data/qwen35_special_token_audit.json`
- D/E/F regenerated from `_gen_sota_sft_notebooks.py`
- `fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2` — im_end after system/user; `repeat_penalty 1.05`

Special-token contract implemented 2026-08-29: D/E/F regenerated, Modelfile fixed, audit JSON at `fine_tuning/data/qwen35_special_token_audit.json`. Operator next: Track A bulk rewrite (`--apply --limit 50`) then stock-base D→E→F; do not mix with CPT volume `7hb931c5oe`. See `fine-tuning/next-session-handoff`.

<!-- memory-fabric:store/fine-tuning/runpod-sft-gate0-decisions -->
---
store_path: fine-tuning/runpod-sft-gate0-decisions
title: "RunPod billing and local backup"
summary: "**Decision:** Phase C GATE-0 SFT on RunPod (not dry-run)"
priority: high
tags: [sft, runpod, decisions, gate0]
schema_version: 1.3
last_updated: "2026-09-02T10:13:51-04:00"
---

**Decision:** Phase C GATE-0 SFT on RunPod (not dry-run). Shared volume `7hb931c5oe` with CPT S6.

**Chosen:** Hub v2 CPT merged base (`rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2`, SHA256 `319d17a3…1478`) merged to `/workspace/theology_cpt_v2_merged_hf` before SFT.

**Rejected for RunPod billing:** Jupyter/nbconvert pipeline (`sft_remote_run_def.sh` kept but not primary).

**Volume safety:** Hub v2 adapter path `theology_cpt_lora_hub_v2/` isolated from S6 `theology_cpt_lora/`.

**Provision:** runpodctl/REST v1 with `networkVolumeId` required; MCP create-pod may drop mount — `sft_verify_mount.ps1` hard gate.

**GPU fallback (US-IL-1):** 4090 → A6000 → L40S in `sft_provision_pod_mcp.py`.

SFT RunPod billing + local backup policy (2026-09-02):
- Capacity watcher polls US-IL-1 only (4090 then L40S); no pod while waiting.
- Idle pod auto-delete after SFT_IDLE_DELETE_MIN (default 20) if merge/train never starts.
- Monitor syncs checkpoints + sft_fetch_artifacts.ps1 each poll; deletes pod when train done or 8h wall.
- HF_TOKEN via /workspace/.sft_env + sft_inject_hf_token.ps1 (non-interactive SSH).
- GATE-0 merge saved locally via sft_fetch_artifacts -PartialOnly when config.json exists.
- Phase 2 stop probe is warn-only in sft_remote_merge.sh (base may fail before SFT).

<!-- memory-fabric:local/schemas -->
---
section: schemas
summary: "Defines data contracts, metadata schemas for ingested texts, and environment variable configurations."
priority: high
tags: [schemas, contracts]
schema_version: 1.3
last_updated: "2026-06-03T08:33:40-04:00"
summary_hash: e0fe7d0aa73fa2f3f2226b9a4b4b16f9
review_status: stale
---

# Schemas

Data contracts, metadata schemas, and configuration interfaces used in Ask Spurgeon.

## 1. Document & Chunk Metadata Schema

Every ingested sermon text node is indexed with standard metadata fields copied across all generated chunks to facilitate precise filtering:

```yaml
author: string              # Author name (e.g., "Charles Spurgeon")
sermon_num: integer         # Sermon identifier number (e.g., 1045)
volume: integer|string      # Volume number (1 to 63)
year: integer               # Year of the preaching (e.g., 1872)
bible_refs: array[string]   # List of normalized Bible verses referenced in the text (e.g. ["Romans 8:28"])
primary_scripture: string   # (Optional) The primary scripture text preached on in the sermon
```

## 2. Ingestion Parameters

- **Chunk Size**: `768` tokens.
- **Chunk Overlap**: `128` tokens.
- **Embeddings Dimension**: Compatible with `BAAI/bge-small-en-v1.5` dimension output (384).

## 3. Environment Variables (Configuration Schema)

Defined in `.env` and validated through `config.py`:

```properties
LLM_PROVIDER=groq|openai|ollama
GROQ_API_KEY=gsk_...
VECTOR_STORE=chroma|qdrant

# Chroma Configurations (Local Dev)
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=spurgeon_sermons_v1

# Qdrant Configurations (Production / Local Parity)
QDRANT_URL=https://...
QDRANT_API_KEY=...
QDRANT_COLLECTION=spurgeon_sermons_v1

# Custom LLM API Settings (Local/Remote custom models)
CUSTOM_LLM_BASE_URL=http://localhost:11434/v1
CUSTOM_LLM_API_KEY=ollama
CUSTOM_LLM_MODEL=spurgeon-8b
```

<!-- memory-fabric:store/fine-tuning/sft-gate0-readiness-2026-09-02 -->
---
store_path: fine-tuning/sft-gate0-readiness-2026-09-02
title: "SFT GATE-0 readiness revision (2026-09-02)"
summary: "**Date:** 2026-09-02 ~09:30 ET"
priority: high
tags: [sft, runpod, gate0, readiness]
schema_version: 1.3
last_updated: "2026-09-02T09:28:26-04:00"
evidence: [fine_tuning/scripts/merge_cpt_lora.py, fine_tuning/scripts/sft_provision_pod_mcp.py, fine_tuning/scripts/sft_provision_pod.ps1, fine_tuning/scripts/sft_runpod_common.ps1, fine_tuning/scripts/13_sft_local_readiness.py, fine_tuning/RUNPOD_RUNBOOK_SFT.md]
---

**Date:** 2026-09-02 ~09:30 ET
**Verdict:** Data + orchestration are GATE-0 ready locally. GPU launch is **waiting on US-IL-1 capacity** (volume `7hb931c5oe`). Two launch bugs were found and fixed this session.

## Live checks (this session)

| Check | Result |
|-------|--------|
| `13_sft_local_readiness.py --gate0` | PASS after zip repack |
| `audit_qa_mix_quality.py` | quote **52.2%**, teacherish **1579**, caricature **0**, refusal 12.5% live |
| Special tokens | PASS (ChatML atomic; pad is `<\|vision_pad\|>` 248055 — expected, train script remaps pad off `<\|im_end\|>`) |
| Mix zip vs train | Was **stale** (train 09:21, zip 09:08); **repacked** 12.26 MB |
| Pods | 0 (no billing bleed) |
| Volume | `7hb931c5oe` US-IL-1 75 GB |
| Global 4090 stock | High — **not usable**; volume pins US-IL-1 (no instances) |
| SSH key | `~/.ssh/runpod_cpt` present |

## Bugs fixed before GPU

1. **Hub v2 LoRA is private** (HF 401 unauthenticated). Pod env previously had only `PUBLIC_KEY` — merge download would fail on first boot. Now inject `HF_TOKEN` + `HF_HOME` into pod env (runpodctl, REST, MCP paths). Do not log the token.
2. **`merge_cpt_lora.py --preflight` required adapter files before download**, so first-run merge never reached `snapshot_download`. Preflight now downloads (with token) then SHA-checks.
3. **Two capacity watchers** (120s Python 3.14 + 600s) racing the same log. Killed both; restarted **one** 600s watcher on `.venv` Python 3.13 (PID from `sft_start_capacity_watch.ps1`).
4. Readiness now **fails** if zip is older than `qa_mix_train.jsonl`.

## Still not frozen

QA rewrite rotator from 2026-09-01 is **still running** (`rewrite_qa_rotate_providers.py --retry-drops`). Gates already met — further rewrite is optional. If it merges again, **repack the zip** before the watcher syncs. One `--apply` writer remains (parent/child of that rotator).

## Do not

- Touch `/workspace/theology_cpt_lora/` or `/workspace/checkpoints_sota/`
- EXPORT until F §5 gates
- Start a second watcher

<!-- memory-fabric:store/fine-tuning/sft-hf-inject-fix -->
---
store_path: fine-tuning/sft-hf-inject-fix
title: "SFT HF inject fix — urllib verify, no BOM"
summary: "**Date:** 2026-09-02 ~18:45 ET"
priority: high
tags: [sft, runpod, hf-token, fix]
schema_version: 1.3
last_updated: "2026-09-02T18:43:31-04:00"
---

**Date:** 2026-09-02 ~18:45 ET

## Root cause
`sft_inject_hf_token.ps1` failed because:
1. First design verified with `huggingface_hub` before `sft_remote_setup.sh` installs it.
2. Rewrite with curl/bash failed because PowerShell expanded `$HF_TOKEN` to empty in the SSH command.

## Fix
- Write token via remote Python (base64 decode + repr for safe `.sft_env`).
- Verify with `urllib.request` to HF whoami-v2 (stdlib only).
- Session JSON: read with `utf-8-sig`; PowerShell `Save-SftSession` writes UTF-8 no BOM.
- Watcher already force-deletes pod on orchestrate failure.

## Live result
Pod `gt5ureujk6c8dh` provisioned; inject PASS; `train_sft_sota.py` PID 1509; monitor PID 24820; capacity watcher exited `state=training`.

<!-- memory-fabric:store/fine-tuning/sft-idle-pod-force-delete -->
---
store_path: fine-tuning/sft-idle-pod-force-delete
title: "SFT watcher: force-delete on orchestrate failure"
summary: "**Date:** 2026-09-02 ~17:00 ET"
priority: high
tags: [sft, runpod, billing, idle]
schema_version: 1.3
last_updated: "2026-09-02T17:00:52-04:00"
---

**Date:** 2026-09-02 ~17:00 ET

## Incident
Capacity watcher provisioned `sft-gate0` (`ph9wzckj6nttpa`, 4090 US-IL-1) then failed `sft_inject_hf_token.ps1` 3×. GPU util stayed 0 while pod kept billing. Default `SFT_IDLE_DELETE_MIN=20` left the pod up for retries (`watch_status=orchestrate_failed_retry`).

## Immediate action
- Deleted pod via RunPod MCP (HTTP 204).
- Killed `sft_watch_capacity` + `sft_monitor_until_done` processes.
- Session cleared: `pod_id=null`, `watch_status=idle_pod_deleted`.

## Code fix
`sft_watch_capacity.py` `handle_live_pod`: on orchestrate failure, call `cleanup_idle_pod(..., force=True)` immediately instead of waiting the idle timer.

## Follow-up
Fix root of `sft_inject_hf_token.ps1` failure (likely `huggingface_hub` / whoami before setup) before restarting capacity watch.

<!-- memory-fabric:store/fine-tuning/sft-phase-b-dry-terminated -->
---
store_path: fine-tuning/sft-phase-b-dry-terminated
title: "SFT Phase B dry-run pod terminated"
summary: "- Pod `47zu29u0yth5a3` (name `sft-phase-b-dry`) deleted via Runpod MCP `delete-pod` (HTTP 204)"
priority: high
tags: [sft, runpod, billing]
schema_version: 1.3
last_updated: "2026-08-28T20:41:31-04:00"
---

# SFT Phase B dry-run pod terminated (2026-08-28)

- Pod `47zu29u0yth5a3` (name `sft-phase-b-dry`) deleted via Runpod MCP `delete-pod` (HTTP 204).
- `list-pods` afterwards: **0 pods**.
- Network volume `7hb931c5oe` was **not** mounted on this pod (`network_volume_id: null`) and was **not** deleted — keep for CPT S6 resume.
- No leftover local SSH to `38.65.239.56:22046`.
- Session file: `fine_tuning/kaggle/sft_phase_b_session.json` status=`terminated`.
- Dry-run training was not started on that pod before delete.

<!-- memory-fabric:store/fine-tuning/sft-prep-after-cpt -->
---
store_path: fine-tuning/sft-prep-after-cpt
title: "SFT prep plan after CPT (2026-08-28)"
summary: "**Status:** Prep planning (no SFT train started)"
priority: high
tags: [sft, phase-b, dry-run]
schema_version: 1.3
last_updated: "2026-08-28T20:41:44-04:00"
---

# Fine-tuning (SFT) prep plan — after CPT

**Date:** 2026-08-28
**Status:** Prep planning (no SFT train started)

## Pipeline position

```
Qwen3.5-4B-Base → CPT (Hub v2 LoRA / future S6) → merge 16-bit HF → SFT v2 (grounded Q&A) → GGUF/Ollama → app
```

SFT is **instruction** fine-tune on top of CPT, not a replacement for CPT.

## Current readiness (2026-08-28)

| Asset | Status |
|-------|--------|
| `13_sft_local_readiness.py` | **PASS** (train=2553, val=134, test=100) |
| `qa_mix_v1` + kaggle zip | Present |
| SOTA notebooks D/E/F | Present |
| `KAGGLE_RUNBOOK_SFT_V2.md` | Current operator path |
| CPT **merged** HF folder | **Missing locally** (`theology_cpt_v2_merged_hf` not found) |
| Hub v2 | LoRA only — keep; need merge for GATE-0 final SFT |
| S6 B | Incomplete (2110/4128) — not ready as SFT base |
| Idle C-eval pod `snuapq7oqrd8ww` | Still RUNNING — terminate to stop billing |

## Recommended prep phases

### Phase A — stop bleed / freeze CPT handoff (do now)
1. Terminate idle pod `snuapq7oqrd8ww` (C eval done).
2. Keep volume `7hb931c5oe` (S6 resume later).
3. Do not start SFT on incomplete S6 adapter.

### Phase B — SFT dry-run prep (parallel, no CPT merge needed)
1. Re-confirm mix: `build_qa_mix.py` + `12_package_kaggle_qa_mix.py` if data changes.
2. Regen notebooks if generator changed: `_gen_sota_sft_notebooks.py`.
3. Upload `spurgeon-qa-mix-v1.zip` to Kaggle if not current.
4. Run **D_sota** (token audit).
5. Run **E_sota** with `USE_CPT_MERGE=False`, stock `unsloth/Qwen3.5-4B-Base` — 2 epochs dry-run.
6. Run **F_sota** with `EXPORT=False` — check corrupt_rate, refusal accuracy.

### Phase C — GATE-0 final SFT (blocked until merge)
1. Merge Hub v2 LoRA (or finished S6 if it beats v2) → `theology_cpt_*_merged_hf`.
2. Publish merge as dataset / volume path.
3. Retrain E with `USE_CPT_MERGE=True` on that base.
4. F gates (§5): faithfulness ≥4.0, refusal ≥85%, echo ≤2%, Ollama smoke clean.
5. Only then EXPORT → GGUF → HF → Ollama Modelfile.

## Base-model choice for shippable SFT

| Option | When |
|--------|------|
| **Hub v2 CPT merged** | Default for first shippable SFT (policy: keep Hub v2) |
| **S6 after full B+C win** | Only if C beats Hub v2 scorecard |
| **Stock base dry-run** | Now — plumbing only, not shippable |

## Known SFT risks (from PLAN_FABLE5_TO_IMPROVE_FN)

- One ChatML template across D/E/F/Ollama (no Alpaca mix).
- Completion-only masking (`train_on_responses_only`).
- Align train context shape with app (multi-chunk headers).
- Never resize vocab (GGUF corruption).
- Never EXPORT until F gates pass.

## Next operator decision

Pick one:
1. **Terminate pod + start Phase B dry-run** (Kaggle T4 or Runpod)
2. **Merge Hub v2 first** then GATE-0 SFT
3. **Resume S6 CPT first**, then SFT later

## Phase A done (2026-08-28)
- Terminated idle pod `snuapq7oqrd8ww` (C eval complete).
- Volume `7hb931c5oe` kept for S6 resume.

## Phase B started — stock-base dry-run prep
- Rebuilt QA mix + `spurgeon-qa-mix-v1.zip` (1.64 MB)
- Regenerated D/E/F SOTA notebooks from `_gen_sota_sft_notebooks.py`
- `13_sft_local_readiness.py` PASS (2553/134/100)

### Operator next (Kaggle T4)
1. Upload `fine_tuning/data/kaggle_upload/spurgeon-qa-mix-v1.zip` → dataset `spurgeon-qa-mix-v1`
2. D_qa_data_prep_sota — mount mix, token audit
3. E_qa_training_sota — `USE_CPT_MERGE=False`, `BASE_MODEL=unsloth/Qwen3.5-4B-Base`, 2 epochs
4. F_qa_eval_sota — `EXPORT=False`
5. Do **not** merge/export until GATE-0 (CPT merged HF)

Runbook: `fine_tuning/KAGGLE_RUNBOOK_SFT_V2.md`

## Phase B dry-run pod terminated + QA mix v2 (2026-08-28)

- Deleted pod `47zu29u0yth5a3` (`sft-phase-b-dry`). Volume `7hb931c5oe` kept.
- Replaced `qa_mix_v1` with **qa_mix_v2** (serve-shaped headers, k≈4, train refusal 11.9%). Counts: train=2923 / val=153 / test=100.
- Rebuild: `build_qa_mix_v2.py` + `12_package_kaggle_qa_mix.py`. Readiness PASS.
- D_sota now uses `AutoTokenizer.from_pretrained` (no Unsloth `get_tokenizer`).
- Do **not** start training until operator uploads the new zip and chooses Kaggle vs a new pod.

<!-- memory-fabric:store/fine-tuning/sft-qa-mix-v2 -->
---
store_path: fine-tuning/sft-qa-mix-v2
title: "SFT QA mix v2 (serve-shaped)"
summary: "**Status:** Built locally, no GPU"
priority: high
tags: [sft, qa-mix, f3, f5]
schema_version: 1.3
last_updated: "2026-08-28T20:41:31-04:00"
evidence: [fine_tuning/scripts/build_qa_mix_v2.py, fine_tuning/data/qa_mix_manifest.json, "config.py:57", "utils/prompts.py:60"]
---

# SFT QA mix v2 — serve-shaped (2026-08-28)

**Status:** Built locally, no GPU. `13_sft_local_readiness.py` PASS. Do not start Runpod/Kaggle training until operator decides.

## Counts

| Split | Rows |
|-------|------|
| train | 2923 |
| val | 153 |
| test frozen | 100 (50 answerable / 50 refusal) |

- Train refusal: **347 (11.9%)** — inside 10–15% F5 target (v1 was 14 / 0.5%).
- Sermon match rate: **99.9%** (2755/2757) against `data/chspurgeon-sermons` (3536 files).
- k histogram (weighted toward serve k=4): 1=136, 3=408, 4=1968, 5=275.

## Serve contract encoded in examples

- System: `config.SPURGEON_SFT_SYSTEM_PROMPT`
- Headers: `[Sermon N — "Title", Volume V | Text: ref]` (`utils.prompts.format_context`)
- User wrapper: `CONTEXT (excerpts...)` + headed chunks + `QUESTION:`
- Default k=4 (`FINE_TUNED_SIMILARITY_TOP_K`); chunking ~2800 chars / 450 overlap as a 768/128 token proxy
- Fidelity: original answers kept; light trailing `[Sermon N]` citation when matched
- Refusals: original ~30 + 389 synthesized (real questions + unrelated chunks, plus anachronism prompts)

## Builder / package

- `fine_tuning/scripts/build_qa_mix_v2.py` → jsonl + `qa_mix_manifest.json` version `qa_mix_v2`
- `12_package_kaggle_qa_mix.py` → `fine_tuning/data/kaggle_upload/spurgeon-qa-mix-v1.zip` (11.75 MB; Kaggle dataset name unchanged)
- D_sota tokenizer: `AutoTokenizer.from_pretrained` (not `FastLanguageModel.get_tokenizer`)

## Remaining F5 gaps

- No new 5–6k teacher-generated set (rewrapped existing 2787)
- No catechism/confession slice (~8%)
- No multi-turn examples
- Chunking is char-approx, not LlamaIndex `SentenceSplitter`
- Citations are trailing `[Sermon N]`, not teacher-written inline quotes

<!-- memory-fabric:store/fine-tuning/sft-stop-token-phases -->
---
store_path: fine-tuning/sft-stop-token-phases
title: "SFT stop-token phased verification"
summary: "Phased stop-token contract for Qwen3.5 SFT v2:"
priority: high
tags: [sft, stop-tokens, qwen35]
schema_version: 1.3
last_updated: "2026-09-02T09:47:29-04:00"
---

Phased stop-token contract for Qwen3.5 SFT v2:
- Turn stop: `<|im_end|>` (248046); native eos `<|endoftext|>` (248044); pad must not equal im_end.
- Runbook: `fine_tuning/STOP_TOKEN_PHASES.md`
- Script: `fine_tuning/scripts/verify_sft_stop_tokens.py` (phases 0–5)
- Shared utils: `fine_tuning/scripts/sft_stop_token_utils.py`

Phase gates:
- 0–1: local pre-GPU (tokenizer + training template); wired into `13_sft_local_readiness.py`
- 2: CPT merged base greedy probe on pod after merge (`sft_remote_merge.sh`)
- 3: post-eval stop metrics in `eval_sft_sota.py` → `metrics.stop_token`
- 4: exported HF tokenizer audit
- 5: Ollama smoke via `smoke_test_ollama.py` + verify phase 5

Modelfile adds stop for `<|endoftext|>` as fallback. Pod sync includes utils + verify scripts.

<!-- memory-fabric:store/fine-tuning/sft-vs-rewrite-decision -->
---
store_path: fine-tuning/sft-vs-rewrite-decision
title: "SFT vs QA rewrite decision (2026-09-02)"
summary: "- **Pass 1 complete:** all 3244 non-gold train rows attempted once"
priority: high
tags: [fine-tuning, sft, qa-rewrite, decision]
schema_version: 1.3
last_updated: "2026-09-02T08:01:47-04:00"
---

# SFT vs QA rewrite — decision context (2026-09-02)

## QA rewrite stop point

- **Pass 1 complete:** all 3244 non-gold train rows attempted once.
- **Pass 2 retry-drops optional:** 1778 rows still failing validation (no ok=true).
- Metrics at stop: quote **49.1%**, teacherish **1485**, caricature **0**, ~1438 originalish remaining.

## Implications

| Start dry-run SFT now | Continue rewrite |
|----------------------|------------------|
| Validates D→E→F pipeline on stock base | Marginal quote/faithfulness lift |
| ~45% train still legacy-style answers | Time + provider quota cost |
| Kaggle zip must be repackaged first | Multiturn/catechism tail often fails quote gate |
| Not final CPT-merged model | Delays first eval signal |

## Recommendation recorded

Gates met → **dry-run SFT is low-regret**; rewrite is optimization not blocking. Final production SFT waits CPT S6 + operator go.

## Before GPU

1. `12_package_kaggle_qa_mix.py`
2. Operator explicit go
3. `KAGGLE_RUNBOOK_SFT_V2.md` §2–3 (`USE_CPT_MERGE=False` for dry-run)

<!-- memory-fabric:store/bugs/unsloth-embedding-offload-readonly -->
---
store_path: bugs/unsloth-embedding-offload-readonly
title: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
summary: "Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem"
priority: high
tags: [bugs, unsloth, embeddings, lora, kaggle, offloading]
schema_version: 1.3
last_updated: "2026-06-11T14:26:32-04:00"
review_status: stale
---

# Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem

## Context
When training a custom LoRA adapter where `embed_tokens` and `lm_head` are targeted in `FastLanguageModel.get_peft_model()`, Unsloth automatically offloads the base model's input embeddings to disk to save VRAM.
By default, the offload directory is named `_unsloth_temporary_saved_buffers` and is created in the current working directory.

## Problem
When running the training notebook on Kaggle via Papermill or automated run scripts, the current working directory may reside in a read-only area (e.g. `/kaggle/input/...` or the home folder).
Additionally, on certain Kaggle container executions, the system `/tmp` directory is sandbox-restricted or mounted read-only.
This causes `torch.save` inside `offload_to_disk` to crash with:
`RuntimeError: [enforce fail at inline_container.cc:743] . open file failed with strerror: Read-only file system`

Furthermore, even when passing a writeable `TEMP_LOCATION` (like `/kaggle/working/unsloth_temp`), Unsloth's `offload_to_disk` constructs the target file location using:
`file_location = os.path.join(temporary_location, model.config._name_or_path)`

Because the base model is loaded from an absolute local path on Kaggle (`MODEL_NAME = "/kaggle/input/datasets/..."`), the `model.config._name_or_path` attribute holds this absolute path. In Python/Unix, when joining paths where the second path is absolute, `os.path.join` discards the first path entirely. As a result, the target path resolved directly back to the read-only `/kaggle/input/` directory, causing the same `Read-only file system` crash.

## Fix
In `fine_tuning/notebooks/E_qa_training.ipynb`:
1. Configured robust environment checks for Kaggle and Colab:
```python
IS_KAGGLE = "KAGGLE_KERNEL_RUN_TYPE" in os.environ or os.path.exists("/kaggle")
IS_COLAB = "COLAB_GPU" in os.environ or os.path.exists("/content")
```
2. Assigned default temp locations pointing to verified writeable workspaces: `/kaggle/working/unsloth_temp` on Kaggle, and `/content/unsloth_temp` on Colab.
3. Implemented an active writeability check fallback block that attempts to write a dummy file to several directory candidates and dynamically binds `TEMP_LOCATION` to the first path that successfully accepts file writes:
```python
# Robust fallback mechanism to guarantee write permission
writeable_found = False
for path_option in [TEMP_LOCATION, "/kaggle/working/unsloth_temp", "/content/unsloth_temp", "_unsloth_temporary_saved_buffers"]:
    try:
        os.makedirs(path_option, exist_ok=True)
        # Test writing a dummy file
        test_file = os.path.join(path_option, "test_write.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        TEMP_LOCATION = path_option
        writeable_found = True
        break
    except Exception:
        continue

if not writeable_found:
    raise RuntimeError("Could not find any writeable directory for temporary offloading!")
```
4. Added a critical patch in Cell 7 before calling `FastLanguageModel.get_peft_model()` to unconditionally set `model.config._name_or_path = "model"`:
```python
if getattr(model, "config", None) is not None:
    model.config._name_or_path = "model"
    print("Patched model.config._name_or_path to relative path: 'model'")
```
5. Passed `temporary_location=TEMP_LOCATION` explicitly to `FastLanguageModel.get_peft_model()`.

This guarantees that Unsloth offloaded buffers are saved under a directory where the Python process has active write permissions on all execution targets (Kaggle VMs, Colab VMs, and local Windows/Linux development environments), bypassing the absolute path join bug.

<!-- memory-fabric:store/pretraining/vast-cpt-s6-resume-spike-analysis -->
---
store_path: pretraining/vast-cpt-s6-resume-spike-analysis
title: "Vast S6 resume spike + flat composite analysis"
summary: "- Instance **51416115** destroyed; `vastai show instances` → `[]`"
priority: high
tags: [cpt, s6, vast, early-stop, resume, analysis]
schema_version: 1.3
last_updated: "2026-09-18T09:30:54-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_run_config.json, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/checkpoints_sota/checkpoint-2400/trainer_state.json, continued_pretrain/scripts/cpt_runtime.py, continued_pretrain/scripts/train_cpt_sota.py]
---

# Vast S6 continue-B — resume spike + flat early-stop (2026-09-18)

## Outcome
- Instance **51416115** destroyed; `vastai show instances` → `[]`.
- Artifacts: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/`
- **Canonical finished LoRA:** `fetch/theology_cpt_lora/theology_cpt_lora/` SHA256 `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` (= best ckpt-2050). Outer `fetch/theology_cpt_lora/adapter_model.safetensors` is **stale S5** (`ef4df3a3…`) from mid-run scp — ignore it.
- HF `best_model_checkpoint` = `checkpoint-2050`, `best_metric` = **2.4987235**. Log: `OK: saved LoRA matches best_model_checkpoint`.
- Hub v2: **keep** (no overwrite). No new B yet.

## What happened
Full pack 51417→4128. Resume 2050 → COMPOSITE EARLY-STOP @ **2400** (patience=2, ε=0.005, min_steps=1652).

| step | eval_spurgeon | eval_mix | notes |
|------|---------------|----------|-------|
| 2050 | **2.4987** | 2.0208 | HF best (pre-resume last save) |
| 2075 | **2.6185** | 2.1157 | first eval after resume — spike |
| 2325 | 2.5115 | 2.0322 | composite local bests seeded post-spike |
| 2350–2400 | ≤ε gains | ≤ε | flat streak=2 → halt |
| 2400 | 2.5084 | 2.0276 | still **worse** than 2050 spurgeon |

All holdouts spiked together (puritan 1.751→1.834, confession 1.668→1.755). Train loss 2050→2060: **1.92→2.33**. Not Spurgeon-only eval noise.

## Why the resume spike (most likely)
1. **Real weight degradation in first ~25 post-resume steps**, not measurement noise — multi-bucket + train-loss jump.
2. LR schedule looked continuous (~2.05e-6 at 2050 → ~2.02e-6 at 2070); not a warmup restart.
3. Continue mode loads S5 init adapter then `trainer.train(resume_from_checkpoint=2050)`. HF best tracking correctly kept 2050; continued Adam steps walked **out** of that basin and never returned below 2.4987.
4. Plausible contributors: late-stage LR still too high for a near-flat Spurgeon probe; dataloader/RNG discontinuity after process restart; Unsloth+PEFT resume friction. **Not** proven as a single root bug without a controlled A/B.

## Why flat composite (working as designed)
`CompositeFlatEarlyStoppingCallback` starts with **empty `bests`** on each process. After resume it is already past `min_steps=1652`, so the **first** complete cycle at 2075 **seeds** composite bests at the spiked values. Recovery 2075→2325 counts as improvement; then spurgeon/mix moves &lt; 0.005 for 2 evals → halt at 2400. Composite never compared against HF best 2.4987 — by design it tracks live flatness, while `load_best_model_at_end` restores 2050 for the saved LoRA.

## Decisions / next
- Do **not** treat 2375/2400 adapters as better than 2050.
- Next GPU work: **C-eval** of `6aab9194…` (2050 LoRA) vs Ampere base **and** Hub v2 — only then decide Hub overwrite.
- Optional later B: lower continue LR and/or seed composite bests from resumed `trainer.state.best_metric`; do not re-rent until C plan is approved.

<!-- memory-fabric:store/fine-tuning/vast-gate0-live -->
---
store_path: fine-tuning/vast-gate0-live
title: "Vast GATE-0 live run status"
summary: "**Started:** 2026-09-05 ~19:42 ET (operator said go)"
priority: high
tags: [vast, sft, gate0, live]
schema_version: 1.3
last_updated: "2026-09-05T19:55:43-04:00"
---

# Vast GATE-0 live run

**Started:** 2026-09-05 ~19:42 ET (operator said go)

## Instance
- `instance_id=49992506` (destroyed stuck `49991334` — pytorch image pull hung)
- Image: `nvidia/cuda:12.4.1-devel-ubuntu22.04` (lighter; setup installs torch 2.11)
- SSH direct: `root@137.175.76.24:49025` with `%USERPROFILE%\.ssh\runpod_cpt`
- Profile: 4090 + `CUDA_VISIBLE_DEVICES=0`

## Fixes during run
- `vast_wait_ssh.ps1`: `${target}:port` PowerShell parse fix
- `vast_destroy.ps1`: pass `-y` to skip CLI confirm
- `vast_launch.ps1`: pgrep false-positive on ssh bash -c (use `[b]ash /workspace/sft_remote_train.sh`)

## Status
Setup/train launched (`LAUNCH_PID`); installing torch 2.11+cu126. Monitor: `vast_monitor_until_done.py` (10h wall).

<!-- memory-fabric:store/fine-tuning/vast-gate0-plan -->
---
store_path: fine-tuning/vast-gate0-plan
title: "Vast GATE-0 plan (scripts ready)"
summary: "**Verified 2026-09-05:** Runbook + thin `vast_*.ps1` landed"
priority: high
tags: [vast, sft, gate0]
schema_version: 1.3
last_updated: "2026-09-05T19:18:30-04:00"
evidence: [fine_tuning/VAST_RUNBOOK_SFT.md, fine_tuning/scripts/vast_orchestrate.ps1]
---

# Vast.ai GATE-0 — scripts ready (no rent yet)

**Verified 2026-09-05:** Runbook + thin `vast_*.ps1` landed. Dry search + local readiness PASS. Credit **$6**. Still **do not rent** until operator says go.

## Ops defaults
- RTX 4090 on-demand, reliability >=0.95, disk 100GB
- Image: `pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel` + torch 2.11 setup smoke
- Profile: `SFT_GPU_PROFILE=4090` BATCH=2 GRAD_ACCUM=8
- Wall <=10h then destroy

## One-shot (on go)
`cd fine_tuning\\scripts; .\\vast_orchestrate.ps1`

## Docs

<!-- memory-fabric:store/fine-tuning/vast-gate0-running -->
---
store_path: fine-tuning/vast-gate0-running
title: "Vast GATE-0 SFT running (post eval-OOM relaunch)"
summary: "**Updated:** 2026-09-05 ~22:25 ET"
priority: high
tags: [vast, sft, gate0, live, peft]
schema_version: 1.3
last_updated: "2026-09-06T02:28:24-04:00"
evidence: [fine_tuning/scripts/train_sft_sota.py, fine_tuning/kaggle/vast_sft_session.json, fine_tuning/scripts/vast_monitor_until_done.py]
---

# Vast GATE-0 SFT — running (post eval-OOM relaunch)

**Updated:** 2026-09-05 ~22:25 ET

## Instance
- **instance_id:** `50011937` (keep; do not destroy)
- **SSH:** `root@75.129.99.99:5250` key `%USERPROFILE%\.ssh\runpod_cpt`
- **Rate:** ~$0.334/hr | Vast `show user` credit ~$8.21 (operator had cited ~$3.26 — API higher)
- **Session:** `fine_tuning/kaggle/vast_sft_session.json`

## Incident
- First PEFT run OOMed at **step 20** during `Trainer.evaluate` (`logits.float()` needed ~15GiB extra on 24GB).
- GPU went idle; empty `spurgeon_qa_lora_v2/checkpoints` (save_steps was 40).
- OOM log archived: `/workspace/sft_train_oom_step20.log`

## Fix + relaunch
- `train_sft_sota.py`: default `SFT_EVAL_STRATEGY=no`; `per_device_eval_batch_size=1`; no `eval_dataset` when off; `load_best_model_at_end` only if eval on; `gradient_checkpointing` + `empty_cache`; optional resume via `SFT_RESUME_FROM_CHECKPOINT` / latest checkpoint-*.
- Env: `SFT_BACKEND=peft`, seq **2048**, batch **1**, accum **16**, `SFT_EVAL_STRATEGY=no`, `SFT_SAVE_STEPS=40`.
- **Restarted:** yes | **Resume-from:** none (fresh) | merge already present.
- Monitor killed during fix (would have seen crash markers), restarted PID in `vast_monitor.pid`; log `vast_monitor.log`.

## Status at relaunch
- Train PID live; `eval_strategy no`; progress bar `0/408`; ~17GB VRAM during train.
- Est. remaining ~408×~82s ≈ 9.3h ≈ **~$3.1** at $0.334/hr vs credit ~$8.2 → headroom OK if no more idle.

<!-- memory-fabric:store/failures/vast-unsloth-official-image-smoke -->
---
store_path: failures/vast-unsloth-official-image-smoke
title: "Vast official Unsloth image smoke blocked; LD_LIBRARY_PATH still SIGSEGV"
summary: "- Still **SIGSEGV exit 139** at first `trainer.train()` step"
priority: high
tags: [vast, unsloth, smoke, docker, sigsegv]
schema_version: 1.3
last_updated: "2026-09-16T09:47:06-03:00"
---

# Vast Unsloth official-image smoke attempt (2026-09-16)

## Attempted
1. `unsloth/unsloth:core` — SSH never ready (container exits / Vast sshd conflict; #4682 class)
2. `vastai/unsloth-studio:2026.9.2-cuda-12.9-py312` — same SSH failure; orphan `51209859` ran ~2.5h before force-destroy (block GPU for sibling)
3. Fallback cheap mitigation: `nvidia/cuda:12.4.1-devel` + **`unset LD_LIBRARY_PATH`** (PR #6905) on NL 4090 offer `40113383`

## Result of LD_LIBRARY_PATH mitigation
- Still **SIGSEGV exit 139** at first `trainer.train()` step
- Same stack: Unsloth 2026.9.4, torch 2.11.0+cu126, Qwen3.5-4B LoRA, FA/xformers None
- Log: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke.log`

## Conclusion
- Official Unsloth Docker on Vast is **not SSH-operable** with our current `vast_provision`/`--ssh` path
- `unset LD_LIBRARY_PATH` alone does **not** fix Vast Unsloth CPT segfault
- Next untested research fix would be **conda env** (#668) — higher setup cost; or PEFT / Runpod

<!-- memory-fabric:store/fine-tuning/vultr-gate0-blockers -->
---
store_path: fine-tuning/vultr-gate0-blockers
title: "Vultr GATE-0 blockers"
summary: "- Vultr Cloud GPU is **not viable for GATE-0 for ~30 days** from denial date"
priority: high
tags: [vultr, sft, gate0, blocked, billing]
schema_version: 1.3
last_updated: "2026-09-05T18:03:37-04:00"
---

# Vultr GATE-0 blockers (do not retry GPU until review window)

## What failed
1. **API IP ACL** — agent public IP must be allowlisted (IP changes; last OK: `38.43.106.44`).
2. **Cloud GPU product access** — `POST /instances` for *all* VCG plans (incl. 2GB A16) returned HTTP 400: `Please open a support request for access to this product.`
3. **Max Instance Cost $100/mo** — target `vcg-a16-12c-128g-32vram` ≈ $0.94/hr ≈ $690/mo list; ceiling too low.
4. **Support 2026-09-05** — refused limit increase due to **account age**; review extended **+30 days**. Asked continued usage + positive history before substantial increases.

## Implications
- Vultr Cloud GPU is **not viable for GATE-0 for ~30 days** from denial date.
- Exhaustive probe: 112 plan@region creates → **0 OK** (28 access-denied, 84 not-in-region).
- Scripts/runbook remain ready (`VULTR_RUNBOOK_SFT.md`, `vultr_orchestrate.ps1`); spend-risk rules still apply when GPU unlocks.
- Do **not** burn credit on tiny GPUs or multi-day CPU SFT for this job.

## After 30 days
Re-check Limits + create-probe A16; if OK, re-run orchestrate with destroy-on-done.

<!-- memory-fabric:store/fine-tuning/vultr-sft-planning -->
---
store_path: fine-tuning/vultr-sft-planning
title: "Vultr SFT GATE-0 planning"
summary: "**Updated:** 2026-09-03 ~23:00 ET"
priority: high
tags: [vast, sft, gate0]
schema_version: 1.3
last_updated: "2026-09-05T18:04:00-04:00"
evidence: [fine_tuning/VULTR_RUNBOOK_SFT.md, fine_tuning/scripts/vultr_orchestrate.ps1, fine_tuning/scripts/merge_cpt_lora.py, fine_tuning/scripts/sft_remote_setup.sh]
---

**Updated:** 2026-09-03 ~23:00 ET
**Status:** Scripts implemented. Live GPU run blocked on Vultr API IP allowlist (`159.26.98.242`).

## What landed
- Runbook: `fine_tuning/VULTR_RUNBOOK_SFT.md`
- Orchestration: `vultr_probe_api.ps1`, `vultr_provision.ps1`, `vultr_wait_ssh.ps1`, `vultr_verify_gpu.ps1`, `vultr_sync.ps1`, `vultr_inject_hf_token.ps1`, `vultr_launch.ps1`, `vultr_fetch.ps1`, `vultr_destroy.ps1`, `vultr_orchestrate.ps1`, `vultr_monitor_until_done.py`
- Session/results: `fine_tuning/kaggle/vultr_sft_session.json`, `fine_tuning/kaggle/vultr_sft_gate0/`
- One-shot: `cd fine_tuning\scripts; .\vultr_orchestrate.ps1`
- Attach console VM: `.\vultr_orchestrate.ps1 -SshHost <ip>`

## Train/merge hardening
- `sft_remote_setup.sh`: always install torch 2.11.0+cu126 if missing/old; smoke `ScalingType` + trl + unsloth + CUDA sm_80+; fail closed.
- A16 env: `SFT_GPU_PROFILE=a16`, `CUDA_VISIBLE_DEVICES=0`, `SFT_PER_DEVICE_BATCH=1`, `SFT_GRAD_ACCUM=16` in `.sft_env` + remote train/setup/merge.
- `merge_cpt_lora.py`: GPU Unsloth merge then CPU PEFT `merge_and_unload` on OOM; `--cpu` / `SFT_MERGE_DEVICE=cpu`; tokenizer completeness check.
- Tokenizer: `load_qwen35_tokenizer` handles Unsloth `TokenizersBackend`.
- QA zip: atomic temp write in `12_package_kaggle_qa_mix.py`. Local `13_sft_local_readiness.py --gate0` PASS (3264/153/100).

## GPU pick (unchanged)
`vcg-a16-12c-128g-32vram` blr ~$0.94/hr — **2x16GB** not one 32GB GPU. Destroy after fetch; do not stop.

## Blocker
`GET /v2/account` → 401 Unauthorized IP `159.26.98.242`. Allowlist that IP (or console-create Ubuntu 24.04 GPU and `-SshHost`). Never log `VULTR_API_KEY` / `HF_TOKEN`.

## 2026-09-04 API wait timeout

- `vultr_orchestrate.ps1 -ApiWaitMinutes 45` exited **1** after ~46 min (`ended_at` 2026-09-04T03:48:35Z).
- Cause unchanged: Vultr API **401** `Unauthorized IP address: 159.26.98.242`.
- No instance provisioned; no session file; GATE-0 merge/SFT not started.
- Unblock: allowlist `159.26.98.242` at https://my.vultr.com/settings/#settingsapi , then re-run `.\vultr_orchestrate.ps1` — or console-create Ubuntu 24.04 GPU A16 32vram in blr and `.\vultr_orchestrate.ps1 -SshHost <ip>`.

## 2026-09-04 provision blocked (product access)

- After API allowlist OK (`38.43.106.44`), `POST /instances` for `vcg-a16-12c-128g-32vram` in `blr` returned **HTTP 400**: `Server add failed: Please open a support request for access to this product.`
- Catalog lists the plan in `atl,blr`; smaller A16 VDI slices also listed in blr but are out of scope for GATE-0 (need ~16GB+ usable VRAM).
- Unblock: operator opens Vultr support ticket for Cloud GPU / that product, then re-run `vultr_orchestrate.ps1`.

## 2026-09-04 exhaustive VCG probe

Tried **112** `plan@region` creates across all catalog `type=vcg` plans. **OK=0**.
- 28× `Please open a support request for access to this product` (includes tiniest A16 2GB / A40 2GB)
- 84× `plan is not available in the selected region`

Account has **no Cloud GPU entitlement** yet; switching SKU/region cannot unblock GATE-0 on Vultr until support enables the product.

## Spend risk (operator)

Limit increase ≠ higher bill. Ceiling only. See `fine-tuning/vultr-spend-risk-controls`.
Hard rules: one VM, destroy on fail/done, 8h wall, no idle stop-only, expected ~$8–12 for GATE-0.

## 2026-09-05 Vultr support denial

Support refused Max Instance Cost increase due to **account age**; review extended **+30 days**. Ask continued non-GPU usage + positive history before GPU-eligible limits.

**Implication:** GATE-0 on Vultr Cloud GPU is **not viable for ~30 days**. Prior create probes already failed with product-access 400 even on 2GB A16 (under $100/mo), so staying under current $100 ceiling does not unlock training GPUs.

**Do not** burn credit on tiny useless GPUs or multi-day CPU SFT for GATE-0. Prefer RunPod/other GPU host; optional light Vultr **CPU** usage only if building account history for a later limit ask.

## Alternate host: Vast.ai (candidate for GATE-0 while Vultr blocked)

**Can do the job:** Yes — rent SSH/Docker GPU, run same pipeline (CPT LoRA merge + SFT LoRA). Vast markets Unsloth Studio templates; CLI/SSH custom images also work.

**Hardware:** Prefer **≥16 GB** usable VRAM (RTX 4090 24GB ideal; avoid tiny VDI). Qwen3.5-4B LoRA + merge fits; use CPU PEFT merge fallback if OOM.

**Caveats vs Vultr/RunPod:** Marketplace hosts (pick high reliability); interruptible offers cheaper but can die mid-run; SSH/image quirks (some Unsloth tags break sshd — prefer stable pytorch/cuda image + install our stack); no existing `vultr_*.ps1` — need thin Vast rent/sync/destroy or manual SSH with `sft_remote_*.sh`.

**Stack rule unchanged:** torch **2.11+cu126**, ScalingType smoke, destroy when done, HF_TOKEN for private Hub CPT adapter.

<!-- memory-fabric:store/fine-tuning/vultr-spend-risk-controls -->
---
store_path: fine-tuning/vultr-spend-risk-controls
title: "Vultr GATE-0 spend risk controls"
summary: "**Operator intent (2026-09-04):** After Vultr raises Max Instance Cost for Cloud GPU, keep billing risk minimal"
priority: high
tags: [vultr, billing, sft, gate0, risk]
schema_version: 1.3
last_updated: "2026-09-04T08:43:49-04:00"
---

# Vultr GATE-0 spend risk controls

**Operator intent (2026-09-04):** After Vultr raises Max Instance Cost for Cloud GPU, keep billing risk minimal. Limit increase is a *ceiling*, not auto-spend.

## Facts
- Account had Max Instance Cost **$100/mo**, credit ~$255, max instances 5.
- Target SKU `vcg-a16-12c-128g-32vram` ≈ **$0.94/hr** ≈ **$690/mo** list rate → needs limit ~$700–1000/mo.
- Stopped GPU still bills; only **DELETE** stops charges.
- Forgotten 24h GPU ≈ ~$23.

## Mandatory agent/run rules
1. Prefer **one** short-lived GPU VM; never leave idle.
2. On setup/inject/launch fail → **destroy immediately** (`vultr_destroy.ps1 -Force`).
3. Monitor with `vultr_monitor_until_done.py` (wall clock ≤ **8h**); on done/crash → fetch then **DELETE**.
4. Do **not** create a second GPU while one `sft-gate0` session exists.
5. Do **not** request huge limits beyond ~$700–1000/mo max instance cost unless Vultr requires it.
6. Never log `VULTR_API_KEY` / `HF_TOKEN`.
7. Before provision: confirm no leftover `sft-gate0` / probe instances via API list.
8. Expected successful run budget: ~**$8–12** (8–12h); abort/destroy if stuck past wall clock.

## Operator checklist
- Request limit increase only as needed for Cloud GPU.
- Watch Billing / Remaining Credit during the run.
- If unsure a VM is still needed → destroy.

<!-- memory-fabric:store/architecture/ask-spurgeon-rag -->
---
store_path: architecture/ask-spurgeon-rag
title: "Ask Spurgeon Rag"
summary: "Canonical Ask Spurgeon RAG stack: Streamlit, LlamaIndex, Chroma/Qdrant, Groq + local CPT/SFT models."
priority: medium
tags: []
schema_version: 1.3
last_updated: "2026-08-29T11:07:00-04:00"
summary_hash: eda9ebfbc623db8fd9795aea72099fac
---

# Ask Spurgeon — RAG architecture

Ask Spurgeon is a RAG system for search and conversation over Charles Haddon Spurgeon's sermon catalog (~3,500 sermons).

## Core layers

- **UI**: Streamlit (`app.py`) — conversational + search UI, metadata filters, citation highlights.
- **Orchestration**: LlamaIndex — retrieval pipeline, query compilation, grounded prompts.
- **Embeddings**: FastEmbed `BAAI/bge-small-en-v1.5` (local CPU-friendly).
- **Vector DB**:
  - **ChromaDB** for local dev (`./chroma_db`).
  - **Qdrant** for production (Qdrant Cloud free tier) and Docker parity testing.
- **LLM**:
  - **Groq** production default (`llama-3.3-70b-versatile`, fallback `llama-3.1-8b-instant`).
  - **Custom CPT/SFT models** served via Ollama / llama.cpp (e.g. `spurgeon-cpt`, historical `spurgeon-8b` GGUF).

## Key subsystems

- **Bible refs** (`utils/bible_refs.py`): normalize verse references at sermon and chunk level for filtering.
- **Author-aware metadata**: `author` on chunks/docs for future multi-author queries.
- **Catechism CONTEXT** (2026-08-29): Puritan Catechism ingest into Chroma; SFT slice merged into QA mix (see `fine-tuning/next-session-handoff`).

## Related memories

- SFT track: `fine-tuning/next-session-handoff`, `fine-tuning/qa-knowledge-not-persona`
- CPT track: `pretraining/cpt-v3-s6-handoff` (volume `7hb931c5oe` — never mount on SFT pods)

<!-- memory-fabric:store/failures/asyncua-write-value-badtypemismatch-188c68c9d2 -->
---
store_path: failures/asyncua-write-value-badtypemismatch-188c68c9d2
title: "asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi"
summary: "asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-08-12T08:59:14-04:00"
occurrences: 1
error_signature: "asyncua write_value badtypemismatch when writing int to uint<n> or double node without explicit variant wrapper"
review_status: stale
---

## Occurrence 1 — 2026-08-12T08:59:14-04:00

**Error:**
asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node without explicit Variant wrapper

**Fix:**
Wrap variables explicitly using ua.Variant(value, ua.VariantType.UInt16) or ua.VariantType.Double before calling node.write_value()

<!-- memory-fabric:store/failures/b-training-sota-earlystopping-4edd127cc9 -->
---
store_path: failures/b-training-sota-earlystopping-4edd127cc9
title: "B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_lo"
summary: "B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_loss not found in logs (B v6 after tokenized eval)"
priority: medium
tags: [cpt, early-stopping, failure, fix, kaggle, transformers]
schema_version: 1.3
last_updated: "2026-08-25T10:20:39-04:00"
occurrences: 2
error_signature: "b_training_sota: earlystopping disabled — metric_for_best_model eval_spurgeon_loss not found in logs (b v<n> after tokenized eval)"
review_status: stale
---

## Occurrence 1 — 2026-08-25T09:03:00-04:00

**Error:**
B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_loss not found in logs (B v6 after tokenized eval)

**Fix:**
Not fixed yet. Next: print actual eval metric keys from Trainer; align METRIC_FOR_BEST / EarlyStopping; verify load_best_model_at_end picks Spurgeon holdout loss. See pretraining/bugs/b-training-sota-known-issues.

## Occurrence 2 — 2026-08-25T10:20:39-04:00


Not a missing metric. HuggingFace logs each eval dataset as a separate dict, so EarlyStoppingCallback warns on mix/puritan/confession/general. trainer_state had eval_spurgeon_loss at 25/50/75; best_global_step=25; SHA256(theology_cpt_lora)==checkpoint-25==C scored adapter. Fix: QuietEarlyStoppingCallback (skip warn when key absent); do not re-C B v6 ckpt-25.

<!-- memory-fabric:local/bugs -->
---
section: bugs
summary: "Generated map of memory-store/bugs/ (5 entries)."
priority: medium
tags: [bugs]
schema_version: 1.3
last_updated: "2026-09-27T09:59:27-03:00"
generated: true
generated_from: memory-store/bugs
store_fingerprint: 1b8b6e12294455f6e3db4ecbf2390c59
body_hash: d7c16ab24817aae979d6ffd6e0819684
---

# Bugs Map

Generated by Memory Fabric from `memory-store/bugs/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Qwen3.5 processor text-as-image in C_eval** (`bugs/qwen35-processor-text-as-image`, high) — C v2 found the adapter then crashed in PPL on the first Spurgeon holdout:
- **Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem** (`bugs/unsloth-embedding-offload-readonly`, high) — Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem
- **Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA** (`bugs/lora-frozen-embeddings-special-tokens`, medium) — Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA
- **Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)** (`bugs/sft-tokenizer-mismatch-vinfos-spepacer`, medium) — -----
- **Unsloth Training Warnings & Fast Patching Resolution** (`bugs/unsloth-fast-patching-warnings`, medium) — Unsloth Training Warnings & Fast Patching Resolution

<!-- memory-fabric:store/pretraining/c-drive-cleanup-2026-09-16 -->
---
store_path: pretraining/c-drive-cleanup-2026-09-16
title: "Freed C: by pruning S6 ckpts and moving GATE-0 models to D:"
summary: "Freed **~1.4 GB to ~39 GB** on C: without deleting the S6 resume checkpoint or breaking local paths"
priority: medium
tags: [disk, c-drive, checkpoints, vast]
schema_version: 1.3
last_updated: "2026-09-16T11:23:15-03:00"
---

# C: disk cleanup (2026-09-16)

Freed **~1.4 GB to ~39 GB** on C: without deleting the S6 resume checkpoint or breaking local paths.

## Deleted (stale only)
- Old `s6_continue_b/checkpoints_sota/checkpoint-*` except complete **checkpoint-2050**
- Nested incomplete ckpts (1150/1175/1200/1400/2000/2025)
- `theology_cpt_v2_merged_hf.incomplete.bak`

## Moved to D: (junctions left in repo)
`fine_tuning/kaggle/vast_sft_gate0/{theology_cpt_v2_merged_hf,spurgeon_qa_merged_hf,spurgeon_qa_gguf}` now live under `D:\\search-sermons-cpt\\vast_sft_gate0\\` with directory junctions at the old paths.

## Kept
- `checkpoint-2050` on C: (resume source)
- `D:\\search-sermons-cpt\\vast_cpt_s6\\payload.tar`

## 2026-09-16 later

Moved **`a_output_v3` corpus back onto C:** as a real directory (was junction → `D:\search-sermons-cpt\a_output_v3`). D: copy removed. GATE-0 merged/GGUF folders remain on D: via junctions. `checkpoint-2050` and Vast `payload.tar` unchanged.

## Train assets on C: (2026-09-16)

Operator wants **all CPT train inputs on C:**.

Moved onto C: as real directories (no junctions):
- `kaggle/a_output_v3` corpus
- `kaggle/runpod_cpt_v3/theology_cpt_lora` (S5)
- `vast_cpt_s6/payload.tar` + results dir under `kaggle/runpod_cpt_v3/vast_cpt_s6`

Scripts default `VAST_LOCAL_RESULTS_DIR` to that C: path. Local readiness **PASS**. C: ~31 GB free. GATE-0 SFT merged/GGUF remain on D: (not needed for CPT S6).

<!-- memory-fabric:store/pretraining/c-drive-cleanup-2026-09-23 -->
---
store_path: pretraining/c-drive-cleanup-2026-09-23
title: "Freed C: by pruning Projetos caches and archiving stale CPT"
summary: "Freed **C: from 2.0 GB to 82.0 GB** (D: still 480 GB free)"
priority: medium
tags: [disk, c-drive, checkpoints, projetos, cleanup]
schema_version: 1.3
last_updated: "2026-09-23T13:41:02-03:00"
evidence: [continued_pretrain/kaggle/a_output_v5, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_lora_s5best, fine_tuning/kaggle/vast_sft_gate0]
---

# C: / Projetos disk cleanup (2026-09-23)

Freed **C: from 2.0 GB to 82.0 GB** (D: still 480 GB free). Phase B inputs stayed on C: as real directories.

## Deleted (regenerable)
`node_modules` plus `android/app/build`, `android/app/.cxx`, `android/.gradle` in:
- `C:\Users\rafael\Projetos\controle-medico`
- `C:\Users\rafael\Projetos\irglobal-app`
- `C:\Users\rafael\Projetos\app-us`
- `C:\Users\rafael\Projetos\ai-personal`

Android `src` and keystores left in place. Reinstall with `npm install` / Gradle when those apps are opened again.

## Deleted (superseded CPT/SFT)
- `vast_cpt_s7/fetch/checkpoints_s7/` (Phase A intermediates)
- `vast_cpt_s7/payload.tar` (repack on operator go for v5)
- `vast_cpt_s7/fetch/theology_cpt_lora/` (not s5best)
- `kaggle/b_output` and `b_output_v6`
- `runpod_sft_gate0/theology_cpt_v2_merged_hf` (incomplete Runpod copy; complete merge remains on D: via junction)

## Moved to D:\search-sermons-cpt\archive-2026-09-23\
- `vast_cpt_s6/` (15.6 GB)
- `s6_continue_b/` (5.6 GB)
- `runpod_cpt_v3_theology_cpt_lora/` (S5, 1.4 GB)
- `runpod_cpt_v2/` (1.4 GB)
- `models/unsloth.F16.gguf` (5.8 GB)
- `models/spurgeon_phase1_merged_hf.F16.gguf` (5.8 GB)
- `models/spurgeon-qa-v2.Q4_K_M.gguf` (2.5 GB)

File symlink for `continued_pretrain/models/unsloth.F16.gguf` failed (needs admin). Ollama `FROM ./unsloth.F16.gguf` will not resolve until an admin `mklink` is created or the Modelfile is pointed at the D: archive path.

## Kept on C:
- `a_output_v5` (real dir) + frozen `a_output_v3` / `a_output_v4`
- `vast_cpt_s7/fetch/theology_cpt_lora_s5best/` (Hub production)
- `search-sermons/.venv`
- GATE-0 junctions under `fine_tuning/kaggle/vast_sft_gate0/` → `D:\search-sermons-cpt\vast_sft_gate0\`

Left alone: `transcriptor-hosp`, `search-sermons/.git`.

<!-- memory-fabric:store/failures/cpt-b-early-stop-561e9ec07f -->
---
store_path: failures/cpt-b-early-stop-561e9ec07f
title: "CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halt"
summary: "CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halted corpus v3 at step 375 of 4128 (~8.2M of 90M tokens)"
priority: medium
tags: [cpt, early-stop, failure, fix, runpod]
schema_version: 1.3
last_updated: "2026-08-27T21:36:49-04:00"
occurrences: 1
error_signature: "cpt b early-stop patience=<n> with eval_steps=<n> and <n>-doc eval_spurgeon_loss halted corpus v<n> at step <n> of <n> (~<n>.<n>m of <n>m tokens). mix eval still falling. same absolute tokens as the small v<n> probe."
---

## Occurrence 1 — 2026-08-27T21:36:49-04:00

**Error:**
CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halted corpus v3 at step 375 of 4128 (~8.2M of 90M tokens). Mix eval still falling. Same absolute tokens as the small v2 probe.

**Fix:**
Not a crash. For a future B that must consume the large mix: add min_steps/min_tokens before patience, or scale patience with packed_epoch_steps. Do not treat 2-doc Spurgeon CE plateau as dataset exhausted. Next step for the existing S5 adapter is C (approval), not a stealth re-train.

<!-- memory-fabric:store/pretraining/cpt-hub-s6-overwrite -->
---
store_path: pretraining/cpt-hub-s6-overwrite
title: "Hub …-cpt-lora-v2 now S6 SHA 6aab (operator approved)"
summary: "Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S6 ckpt-2050 LoRA"
priority: medium
tags: [cpt, hub, s6, lora, overwrite]
schema_version: 1.3
last_updated: "2026-09-21T10:13:38-03:00"
---

# Hub CPT LoRA overwritten with S6 best (2026-09-21)

## Operator approve
Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S6 ckpt-2050 LoRA.

## Identity
| Field | Value |
|-------|--------|
| Repo | https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2 (private) |
| SHA256 | `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` |
| Local source | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/` |
| Train best | HF checkpoint-2050, `eval_spurgeon_loss=2.4987` |
| C (stack pin) | spurgeon **12.85 (−10.2%)** vs base 14.31 — `pretraining/cpt-s6-stack-isolation-c` |

## Replaced
Previous Hub contents were CPT v2 best-400 SHA `319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478` (spurgeon 13.28). Still on local disk under `kaggle/runpod_cpt_v2/theology_cpt_lora/`.

## Upload
`python continued_pretrain/scripts/upload_cpt_lora_to_hf.py --adapter-dir …/theology_cpt_lora/theology_cpt_lora --expected-sha256 6aab… --metrics-dir …/stack_isolation_c`
Also wrote `ADAPTER_SHA256.txt` on Hub. `eval_cpt_sota.py` / `_gen_sota_notebooks.py` default `EXPECTED_ADAPTER_SHA256` now **6aab…**.

## Not done
- No merge / GGUF
- No public flip
- No new B
- §5 −15% still FAIL on isolation C

<!-- memory-fabric:store/pretraining/cpt-hub-s7-overwrite -->
---
store_path: pretraining/cpt-hub-s7-overwrite
title: "Hub …-cpt-lora-v2 now S7 s5best SHA 06354dfc"
summary: "Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S7 Phase A **s5best** (step 1200)"
priority: medium
tags: [cpt, hub, s7, lora]
schema_version: 1.3
last_updated: "2026-09-22T17:55:58-03:00"
evidence: [continued_pretrain/scripts/eval_cpt_sota.py, continued_pretrain/scripts/upload_cpt_lora_to_hf.py, continued_pretrain/NEXT_CPT_S7.md]
---

# Hub CPT LoRA overwritten with S7 s5best (2026-09-22)

## Operator approve
Explicit Hub overwrite of private `rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2` with S7 Phase A **s5best** (step 1200).

## Identity
| Field | Value |
|-------|--------|
| SHA256 | `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` |
| Local source | `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_lora_s5best/` |
| Train | S7 continue from S6; composite early-stop; s5best @ 1200 |
| C (stack pin) | spurgeon **12.45 (−13.0%)**, puritan 5.52 (−8.6%), confession 5.27 (−6.0%), general 11.95 (−0.8%) |

## Replaced
Previous Hub contents were S6 SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` (spurgeon 12.85). Still on local disk under `vast_cpt_s6/fetch/`.

## Upload
```
python continued_pretrain/scripts/upload_cpt_lora_to_hf.py \
  --adapter-dir …/theology_cpt_lora_s5best \
  --expected-sha256 06354dfc… \
  --metrics-dir …/vast_cpt_s7_c \
  --commit-message "CPT S7 s5best step-1200 isolation-C…"
```
Also wrote `ADAPTER_SHA256.txt`, metrics, `STACK_PIN.txt` on Hub.

## Not done
- No merge / GGUF
- No public flip
- §5 −15% still FAIL (puritan/confession)

## Code defaults after Hub overwrite
- `eval_cpt_sota.py` / `_gen_sota_notebooks.py` `EXPECTED_ADAPTER_SHA256` default → `06354dfc…`
- `upload_cpt_lora_to_hf.py` adds `EXPECTED_SHA256_S7`; default expected SHA is S7
- `NEXT_CPT_S7.md` Hub line updated to S7

<!-- memory-fabric:store/pretraining/cpt-phase-b-downame-next-cycle -->
---
store_path: pretraining/cpt-phase-b-downame-next-cycle
title: "Phase B mix a_output_v4 packed"
summary: "**Status:** Fetch + catalog + holdout-pin code done"
priority: medium
tags: [cpt, phase-b, downame, ocr]
schema_version: 1.3
last_updated: "2026-09-23T09:26:50-03:00"
evidence: [continued_pretrain/NEXT_CPT_S7.md, continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/scripts/11_fetch_confessions.py, continued_pretrain/scripts/07_build_theology_mix.py, data/puritans/downame/christian_warfare.txt, data/puritans/downame/guide_to_godliness.txt, continued_pretrain/data/holdouts_pinned_v3]
---

# Phase B corpus prep — Downame landed (mix still deferred)

**Status:** Fetch + catalog + holdout-pin code done. **No** `07` mix / `a_output_v4` until Phase A finishes.

## Done (2026-09-22)

### Downame (wave 4)
- `data/puritans/downame/christian_warfare.txt` — EEBO-TCP `A20752` (~1.65M chars)
- `data/puritans/downame/guide_to_godliness.txt` — EEBO-TCP `A20762` (~4.06M chars)
- Catalog: `10_fetch_puritans.py` `_wave4_catalog()`; PROVENANCE Wave 4 section

### Confession S5 (catalog only — not on disk)
- Wired in `11_fetch_confessions.py` as `S5_CATALOG` + `--s5`:
  - `shaw_exposition_wcf` (IA `expositionofconf00shaw`)
  - `sum_of_saving_knowledge` (Reformed Standards / Wikisource)
- **Skipped fetch:** after Downame, confession disk ~30.7 MB still exceeds max ≈27.3 MB at `--max-confession-share 0.06` (headroom **−3.39 MB**). Adding S5 would worsen random S4 systematic eviction under `_cap_bucket_to_final_share`.

### Holdout pin
- Snapshot: `continued_pretrain/data/holdouts_pinned_v3/`
- `07_build_theology_mix.py` pins `puritan_holdout.txt` / `confession_holdout.txt` when present (fingerprint = first 200 chars), same pattern as Spurgeon. Downame stays train-only.

### Rejected near-dupes (do not reopen)
Savoy, Vincent WSC exposition, Fisher catechism — WCF/WSC near-duplicates under paragraph dedup.

## After Phase A

```text
python continued_pretrain/scripts/07_build_theology_mix.py --target-spurgeon-share 0.45 --keep-all-spurgeon --max-other-weight 1.5 --max-confession-share 0.06 --replay-frac 0.10 --replay-txt continued_pretrain/data/replay/general_replay.txt
python continued_pretrain/scripts/06_verify_tokens.py --mix
python continued_pretrain/scripts/18_prep_hf_dataset.py --out-dir continued_pretrain/kaggle/a_output_v4
```

Playbook: `continued_pretrain/NEXT_CPT_S7.md` (Later — Phase B).

## Do not
- Rebuild mix / overwrite `a_output_v3` during Phase A
- Fetch S5 while headroom is negative
- Redraw puritan/confession holdouts
- Raise confession cap to force Shaw in

## Long-s normalization (2026-09-22)

EEBO-TCP long-s (`ſ`→`s`) applied on disk for Downame **and** 21 other Puritan files + `wcf_catechisms_1756.txt` (23 shelf files had ~2–3% long-s; Ames/modern IA reprints were already clean). Cleaners updated in `10_fetch_puritans`, `11_fetch_confessions`, and `07` mix. Helper: `continued_pretrain/scripts/normalize_early_modern_orthography.py`.

## Wave 5 landed 2026-09-23 (mix still deferred)

Nine new-author practical-divinity texts on disk (~8.47M chars). Catalog `_wave5_catalog()` in `10_fetch_puritans.py`. Confession S5 still skipped (headroom). Next is mix → `a_output_v4` when operator starts Phase B mix — do not rebuild yet.

## Phase B mix landed (2026-09-23)

`a_output_v4` SHA `37a3ba50…` packed. Holdouts still pinned. Mix rebuild no longer deferred.

<!-- memory-fabric:store/pretraining/cpt-s6-c-eval-regression-diagnosis -->
---
store_path: pretraining/cpt-s6-c-eval-regression-diagnosis
title: "S6 Vast C +27.9% was false FAIL (stack); tying not cause"
summary: "**False FAIL.** Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on Unsloth **2026.8.22 / torch 2.8.0** scores spurgeon **12.85 (−10.2%)**"
priority: medium
tags: [cpt, s6, c-eval, regression, stack-isolation, hub-v2]
schema_version: 1.3
last_updated: "2026-09-20T19:01:23-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/cpt_eval.log, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/theology_cpt_eval_metrics.json, continued_pretrain/scripts/eval_cpt_sota.py]
---

# S6 C-eval regression diagnosis — SUPERSEDED by stack isolation (2026-09-20)

## Resolution
**False FAIL.** Same SHA `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` on Unsloth **2026.8.22 / torch 2.8.0** scores spurgeon **12.85 (−10.2%)**. Canonical write-up: `pretraining/cpt-s6-stack-isolation-c`.

Vast C **18.31 (+27.9%)** under Unsloth 2026.9.6 / torch 2.11 is **not** trustworthy for these weights. Tying sync remains rejected as the cause of that inflated PPL (still useful negative result).

## Original diagnosis (2026-09-19) — historical
Vast C of ckpt-2050 LoRA scored spurgeon **18.31 (+27.9% vs Ampere base ~14.31)**. Embed→lm_head sync did **not** change PPL.

### Controlled tying test (still valid)
- Patch: `maybe_sync_tied_lm_head` in `eval_cpt_sota.py` (`CPT_EVAL_SYNC_TIED_HEAD`).
- Re-C: Vast RTX 4090 Kentucky, instance **51500745** (destroyed).
- Before sync: `same_storage=0`, `max_abs_delta≈0.00195`.
- After sync: `embed_to_lm_head_synced=1`, spurgeon still **18.31 (+27.9%)**.

### Ranked causes — updated
1. **Confirmed** — Vast C-eval stack (Unsloth 2026.9.6 / torch 2.11) mis-scores this embed-FT LoRA. Fixed by re-C on S5 pin.
2. **Meta** — Aug-28 “6aab → 13.34” still unproven as that SHA; stack-isolation now gives **12.85** for `6aab…`.
3. **Rejected as regression cause** — 16-doc vs 50-doc (train probe loss 2.495 matches train 2.4987 on good stack).
4. **Rejected** — Wrong SHA / 4-bit / outer stale S5 LoRA / simple tying copy.

## Policy (post-isolation)
- Do **not** treat Vast +27.9% as ground truth.
- Hub `…-theology-cpt-lora-v2` stays until **explicit** overwrite approve (S6 12.85 beats Hub v2 13.28 on this scorecard).
- No blind new B to “fix C”. Eval CPT only on Unsloth ~2026.8.22 + torch 2.8 for parity with Hub-v2/S5.

<!-- memory-fabric:store/pretraining/cpt-s7-vast-phase-a -->
---
store_path: pretraining/cpt-s7-vast-phase-a
title: "S7 Phase A Vast running on 4090"
summary: "**Instance:** `52063161` (label `cpt-s7-phase-a`), SSH `root@149.40.242.200:40205`, RTX 4090 ~$0.40/hr"
priority: medium
tags: [cpt, s7, vast, running]
schema_version: 1.3
last_updated: "2026-09-22T10:44:29-03:00"
evidence: [continued_pretrain/VAST_RUNBOOK_CPT_S7.md, continued_pretrain/scripts/vast_cpt_s7_orchestrate.ps1]
---

# S7 Phase A on Vast — RUNNING (2026-09-22)

**Instance:** `52063161` (label `cpt-s7-phase-a`), SSH `root@149.40.242.200:40205`, RTX 4090 ~$0.40/hr.
**Credit after top-up:** ~$7.55.
**Session/results:** `kaggle/runpod_cpt_v3/vast_cpt_s7` + `vast_cpt_s7_session.json`.

## Confirmed walk-away gates
- `PREV_RUN_CHECKPOINT` empty / new Adam
- `INIT_ADAPTER SHA256 OK` `6aab…`
- `PIN_OK` torch **2.8.0+cu126** + Unsloth **2026.8.22**
- conda `unsloth_cpt_s7`
- `Continue profile max_steps 4128 -> 2064`, `output_dir=/workspace/checkpoints_s7`
- `trainer_bf16=True`, training at step ≥2/2064, GPU ~100%

## Fixes landed this session
- Parallel Vast S7 lane (`vast_cpt_s7_*` scripts + runbook)
- Launch via **nohup** (foreground SSH died mid-Miniforge)
- `max_seq_length` → `max_length` remap for TRL 0.24; pin `trl>=0.18,<0.24` on fresh installs

## Monitor
`vast_cpt_s7_monitor_until_done.py` with `CPT_TOTAL_STEPS=2064` → fetch `checkpoints_s7` + s5best, then destroy.

## Do not
- Call S6 orchestrate; Hub overwrite; mix rebuild; destroy until B done + fetch OK

<!-- memory-fabric:store/pretraining/cpt-s7-vast-phase-b -->
---
store_path: pretraining/cpt-s7-vast-phase-b
title: "S7 Phase B Vast composite early-stop @ 750"
summary: "**Instance:** `52264974` destroyed after fetch (`destroyed_at` 2026-09-23T19:37:29Z)"
priority: medium
tags: [cpt, s7, vast, phase-b, v5, early-stop]
schema_version: 1.3
last_updated: "2026-09-23T16:49:42-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/cpt_train.log, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_run_config.json]
---

## S7 Phase B on Vast — DONE (2026-09-23)

**Instance:** `52264974` destroyed after fetch (`destroyed_at` 2026-09-23T19:37:29Z).
**Stop:** **COMPOSITE EARLY-STOP @ step 750** / 955 (patience 4, ε 0.003). Not a crash. Train ~1.63 h, train_loss 2.017.

## In-train CE @ 750
- spurgeon **2.482** (seed 2.4987)
- puritan **1.740** (seed 1.751)
- confession **1.666** (seed 1.668)
- mix-val **2.205** (unseeded v5 split; best 2.2048)
- Composite bests never moved enough after ~550–600 → flat streak 4 → halt.

## Artifacts (nested fetch)
- HF best (spurgeon): step **700** SHA `6d0030418b0a6fecd4dbf29c63f467dd746119555818e4ad294c04dfd31a363a` at `fetch/theology_cpt_lora/theology_cpt_lora/`
- §5 s5best: step **600** SHA `ddbbee3ac9ef7baf6cca21dcdb844d027d39f5f6a4b88ba10fcf8a43fa7c8214` at `fetch/theology_cpt_lora_s5best/theology_cpt_lora_s5best/`
- Top-level `fetch/theology_cpt_lora_s5best/adapter_model.safetensors` is still Phase A `06354dfc` — do not confuse.

## Next
Isolation C on Unsloth 2026.8.22 + torch 2.8. Pin SHA (`ddbbee3a` and/or `6d003041`). **Keep Hub S7 `06354dfc` until winning C.**

<!-- memory-fabric:store/pretraining/cpt-wave5-puritan-fetch -->
---
store_path: pretraining/cpt-wave5-puritan-fetch
title: "Wave 5 Puritan fetch complete; mix still deferred"
summary: "**Status:** Catalog + fetch + long-s normalize done"
priority: medium
tags: [cpt, wave5, puritans, corpus, phase-b]
schema_version: 1.3
last_updated: "2026-09-23T09:19:24-03:00"
evidence: [continued_pretrain/scripts/10_fetch_puritans.py, continued_pretrain/data/corpus_v3_catalog.json, continued_pretrain/NEXT_CPT_S7.md, data/puritans/PROVENANCE.md]
---

# Wave 5 Puritan fetch (2026-09-23)

**Status:** Catalog + fetch + long-s normalize done. **No** mix rebuild / `a_output_v4` / CPT train.

## Landed (9/9, 0 fail)

| Key | Path | Source | Chars |
|-----|------|--------|-------|
| ambrose_looking_unto_jesus | data/puritans/ambrose/looking_unto_jesus.txt | EEBO-TCP A25241 | 2,821,289 |
| swinnock_works | data/puritans/swinnock/works_1665.txt | EEBO-TCP A62040 | 1,645,784 |
| swinnock_incomparableness | data/puritans/swinnock/incomparableness_of_god.txt | EEBO-TCP A62054 | 359,563 |
| venning_plague_of_plagues | data/puritans/venning/plague_of_plagues.txt | EEBO-TCP A64834 | 601,046 |
| binning_sinners_sanctuary | data/puritans/binning/sinners_sanctuary.txt | EEBO-TCP A28173 | 740,940 |
| preston_breastplate | data/puritans/preston/breastplate_of_faith_and_love.txt | EEBO-TCP A09950 | 934,050 |
| durham_unsearchable_riches | data/puritans/durham/unsearchable_riches_of_christ.txt | EEBO-TCP B02840 | 686,701 |
| vincent_unseen_christ | data/puritans/vincent/true_christians_love_of_the_unseen_christ.txt | EEBO-TCP A64995 | 271,893 |
| guthrie_great_interest | data/puritans/guthrie/christians_great_interest.txt | CCEL guthrie/interest2 | 412,795 |

Total **8,474,061 chars** (~8.5 MB). Long-s already 0 after fetch; `normalize_early_modern_orthography.py` rewrote 0 files.

## Skipped (plan)
- Gillespie Aaron's Rod (polity)
- Extra titles by authors already on disk
- Confession S5 (Shaw / Sum of Saving Knowledge): 6% of added mix is only ~0.5 MB; confession disk still over cap
- Vincent WSC / Fisher / Savoy near-dupes

## Do not
- Rebuild mix / pack `a_output_v4` until operator starts Phase B mix
- Redraw puritan/confession holdouts (keep `holdouts_pinned_v3`)
- Fetch S5, scrape Banner/Heritage/Puritan Publications

<!-- memory-fabric:store/failures/cuda-oom-during-mid-ffcb775074 -->
---
store_path: failures/cuda-oom-during-mid-ffcb775074
title: "torch.OutOfMemoryError: CUDA out of memory during SFTTrainer.evaluate at step 20"
summary: "CUDA OOM during mid-train eval at step ~20 with PEFT bf16 seq 2048 on RTX 4090 24GB"
priority: medium
tags: [eval, failure, fix, gate0, oom, peft, sft, vast]
schema_version: 1.3
last_updated: "2026-09-06T02:28:22-04:00"
occurrences: 2
error_signature: "cuda oom during mid-train eval at step ~<n> with peft bf<n> seq <n> on rtx <n> <n>gb"
failure_key: "cuda|oom"
---

## Occurrence 1 — 2026-09-06T02:25:26-04:00

**Error:**
CUDA OOM during mid-train eval at step ~20 with PEFT bf16 seq 2048 on RTX 4090 24GB

**Fix:**
Default and inject SFT_EVAL_STRATEGY=no (skip mid-train eval on 24GB). Restart train_sft_sota.py with SFT_BACKEND=peft; no checkpoint so fresh 408 steps.

## Occurrence 2 — 2026-09-06T02:28:22-04:00

torch.OutOfMemoryError: CUDA out of memory during SFTTrainer.evaluate at step 20 (PEFT bf16 Qwen3.5-4B seq 2048 on 24GB). Tried to allocate 15.16 GiB while 16.69 GiB already in use; OOM in ForCausalLMLoss logits.float().

Disable mid-train eval: SFT_EVAL_STRATEGY=no (default), per_device_eval_batch_size=1, load_best_model_at_end=False when eval off, gradient_checkpointing + empty_cache, prediction_loss_only=True. Keep peft/2048/batch1/accum16. Synced train_sft_sota.py to Vast and relaunched (no checkpoint — died before save_steps=40).

<!-- memory-fabric:store/failures/cuda-oom-on-kaggle-e64e9b60ce -->
---
store_path: failures/cuda-oom-on-kaggle-e64e9b60ce
title: "CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch "
summary: "CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch 2, TRAIN_EMBEDDINGS=True)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-08-25T02:32:47-04:00"
occurrences: 1
error_signature: "cuda oom on kaggle t<n> during cpt b v<n> after manual pack (float<n> qwen<n>.<n>, batch <n>, train_embeddings=true)"
review_status: stale
---

## Occurrence 1 — 2026-08-25T02:32:47-04:00

**Error:**
CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch 2, TRAIN_EMBEDDINGS=True)

**Fix:**
Set PER_DEVICE_BATCH=1 GRAD_ACCUM=16 TRAIN_EMBEDDINGS=False EVAL_DOCS_PER_BUCKET=4 in _gen_sota_notebooks.py for T4 headroom

<!-- memory-fabric:store/failures/cuda-out-of-memory-849d59401d -->
---
store_path: failures/cuda-out-of-memory-849d59401d
title: "CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocat"
summary: "CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocate 6.81 GiB on T4 while evaluating mix+4 holdout buckets at EVAL_DOCS_PER_BUCKET=8 (logits for 248k vocab)"
priority: medium
tags: [cpt, eval, failure, fix, kaggle, oom, qwen35]
schema_version: 1.3
last_updated: "2026-08-26T01:22:24-04:00"
occurrences: 1
error_signature: "cuda out of memory during first eval of qwen<n>.<n> embed lora cpt: tried to allocate <n>.<n> gib on t<n> while evaluating mix+<n> holdout buckets at eval_docs_per_bucket=<n> (logits for <n>k vocab). train steps at batch <n>x<n> with train_embeddings=true succeeded."
review_status: stale
---

## Occurrence 1 — 2026-08-26T01:22:24-04:00

**Error:**
CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocate 6.81 GiB on T4 while evaluating mix+4 holdout buckets at EVAL_DOCS_PER_BUCKET=8 (logits for 248k vocab). Train steps at batch 1x16 with TRAIN_EMBEDDINGS=True succeeded.

**Fix:**
Keep TRAIN_EMBEDDINGS=True. Set EVAL_DOCS_PER_BUCKET=2, EVAL_BUCKETS_DURING_TRAIN=[spurgeon] (mix still kept), per_device_eval_batch_size=1, and prediction_loss_only=True so eval does not materialize full vocab logits.

<!-- memory-fabric:store/pretraining/data-collection -->
---
store_path: pretraining/data-collection
title: "Pretraining Step 1 — Data Collection Complete"
summary: "Pretraining Step 1 — Data Collection Complete"
priority: medium
tags: [pretraining, dataset, sermons]
schema_version: 1.3
last_updated: "2026-06-06T18:50:44-04:00"
review_status: stale
---

Domain audit complete: 3,536 sermons (129.60 MB, 129.6M chars) across 63 volumes. Created 50-sermon holdout split in data/chspurgeon-holdout. Flagged two oversized multi-sermon files in volumes 5 and 7.

<!-- memory-fabric:store/fine-tuning/data-generation-gemma4 -->
---
store_path: fine-tuning/data-generation-gemma4
title: "Gemma 4 Local Dataset Generation Analysis"
summary: "Gemma 4 Local Dataset Generation Analysis"
priority: medium
tags: [fine-tuning, gemma4, dataset, ollama]
schema_version: 1.3
last_updated: "2026-06-08T12:46:23-04:00"
review_status: stale
---

# Gemma 4 Local Dataset Generation Analysis

We evaluated the feasibility of using Google's Gemma 4 (12B) model locally via Ollama to generate the synthetic Q&A instruction fine-tuning dataset for the Charles Spurgeon Q&A assistant.

## Evaluation Results
- **groundedness & Fidelity:** The model successfully followed strict instructions to ground its answers 100% in the provided context chunk, avoiding external extrapolations or hallucinations.
- **Stylistic Persona:** The model successfully adopted Charles Spurgeon's theological style, register, and vocabulary (e.g., using markers like "My brethren," and "doth").
- **Question Quality:** Rather than using generic templates, Gemma 4 generated specific, detail-oriented questions directly derived from the passage text.
- **Speed & Feasibility:** Once loaded into local memory in Ollama, generation takes approximately 3.5 seconds per request. Running locally avoids rate limit errors (such as Groq's 30 RPM limit on free tiers) and has zero API costs.

## Implementation
- Created `generate_qa_pairs_ollama.py` to target local Ollama instances (with JSON mode enabled).
- Created `generate_qa_pairs_openrouter.py` to support OpenRouter free model endpoints.
- Launched a parallel background run of 1,000 examples using the local `gemma4:latest` model, writing to `spurgeon_train_ollama.jsonl`.
- Created `merge_datasets.py` to consolidate, deduplicate, shuffle, and split all generated outputs.

<!-- memory-fabric:store/pretraining/dataset-preparation -->
---
store_path: pretraining/dataset-preparation
title: "Pretraining Step 6 — Dataset Preparation (Notebook A) Plan"
summary: "Pretraining Step 6 — Dataset Preparation (Notebook A) Plan"
priority: medium
tags: [pretraining, dataset, kaggle, huggingface]
schema_version: 1.3
last_updated: "2026-06-06T19:38:20-04:00"
review_status: stale
---

Documents the environment settings, directory layout, code cells, and verification diagnostics for Step 6: Dataset Preparation of Phase 1 of the Charles Spurgeon continued pretraining pipeline.

### Details:
- **Notebook A (`data_prep.ipynb`)** runs on CPU-only (accelerator: None) with Internet ON to preserve GPU quota.
- Ingests the cleaned training set `spurgeon_train.txt` and holdout set `spurgeon_holdout.txt` from `/kaggle/input/`.
- Splits text documents on the `<|endoftext|>` marker, filtering out short segments (< 200 chars).
- Partitions the training corpus into a 99% train and 1% validation split (`train_test_split`).
- Saves the resulting binary datasets (`spurgeon_dataset` and `spurgeon_holdout_dataset`) to `/kaggle/working/` using `save_to_disk`.
- The output datasets are versioned as a private Kaggle dataset named `spurgeon-cpt-dataset` to be mounted as input for Notebook B (`training.ipynb`).

<!-- memory-fabric:local/decisions -->
---
section: decisions
summary: "Generated map of memory-store/decisions/ (1 entries)."
priority: medium
tags: [decisions, adr]
schema_version: 1.3
last_updated: "2026-09-27T09:59:27-03:00"
generated: true
generated_from: memory-store/decisions
store_fingerprint: 0d7c862d98938a18678f2a3eb1e6a52e
body_hash: 9a0fa19fa5b069108ede047307149804
---

# Decisions Map

Generated by Memory Fabric from `memory-store/decisions/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Gemma 4 Fine-Tuning Transition** (`decisions/gemma4-finetuning`, medium) — Guides the upgrade of fine-tuning pipelines from Gemma 2 to the efficient, newer Gemma 4 12B model.

<!-- memory-fabric:store/pretraining/environment-setup -->
---
store_path: pretraining/environment-setup
title: "Pretraining Step 5 — Environment Setup & Configurations"
summary: "Pretraining Step 5 — Environment Setup & Configurations"
priority: medium
tags: [pretraining, environment, kaggle, config, secrets]
schema_version: 1.3
last_updated: "2026-06-06T19:35:50-04:00"
review_status: stale
---

Execution configurations and dependency management rules for continued pretraining on Kaggle Free Tier. Guidelines specify toggling Internet ON, choosing None accelerator for Notebook A (Data Prep) to conserve quota, and selecting 1x T4 GPU for Notebook B/C. Installation relies solely on `unsloth[kaggle-new]` package pulling from GitHub, with a strict warning against manual upgrades of transformers/trl/peft to avoid breaking CUDA Triton kernels. Detailed setup includes programmatic Hugging Face token authentication via Kaggle Secrets (HF_TOKEN) and optional Weights & Biases training logs tracking (WANDB_API_KEY).

<!-- memory-fabric:local/episodic -->
---
section: episodic
summary: "Generated map of memory-store/episodic/ (22 entries)."
priority: medium
tags: [episodic]
schema_version: 1.3
last_updated: "2026-09-27T09:59:27-03:00"
generated: true
generated_from: memory-store/episodic
store_fingerprint: e8535d4b3a6a52994843d0bbbf03f221
body_hash: fd5485ee98e08d3e7f8fb181125adce4
---

# Episodic Map

Generated by Memory Fabric from `memory-store/episodic/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Episodic Journal — 2026-07-11** (`episodic/2026-07-11`, low) — Episodic Journal — 2026-07-11
- **Episodic Journal — 2026-08-12** (`episodic/2026-08-12`, low) — Episodic Journal — 2026-08-12
- **Episodic Journal — 2026-08-24** (`episodic/2026-08-24`, low) — CPT B completed 250 steps on T4 (train 4356 rows)
- **Episodic Journal — 2026-08-25** (`episodic/2026-08-25`, low) — Implemented RC2–RC4 in B/C notebook generator: lighter hparams and early stop on spurgeon holdout loss, HF theology_holdouts path finder (fixes mix-only eval), D4 embed warning, C ADAPTER_OVERRIDE and
- **Episodic Journal — 2026-08-26** (`episodic/2026-08-26`, low) — Pushed CPT B through Kaggle kernel v11
- **Episodic Journal — 2026-08-29** (`episodic/2026-08-29`, low) — Terminated SFT Phase B dry-run pod 47zu29u0yth5a3 (sft-phase-b-dry); list-pods is empty and CPT S6 volume 7hb931c5oe was left untouched
- **Episodic Journal — 2026-08-30** (`episodic/2026-08-30`, low) — Resolved parallel Groq+Cerebras rewrite conflict: stopped Cerebras, let Groq finish, deduped bulk_pending.jsonl (648→637, 11 dupes removed), re-ran full pipeline
- **Episodic Journal — 2026-08-31** (`episodic/2026-08-31`, low) — Verified live QA mix against serve contract and F5 targets
- **Episodic Journal — 2026-09-01** (`episodic/2026-09-01`, low) — Verified QA teacher rewrite resume point (line 1786 per handoff, confirmed live)
- **Episodic Journal — 2026-09-02** (`episodic/2026-09-02`, low) — Saved QA rewrite stop point to memory: pass 1 complete (3244/3244 attempted), 1466 ok / 1778 drops remaining for --retry-drops, 1465 bulk merged, quote 49.1%, teacherish 1485
- **Episodic Journal — 2026-09-04** (`episodic/2026-09-04`, low) — Saved Vultr SFT planning for next session: API key present but IP-allowlisted (401 on 159.26.98.242); cheapest usable GPU with stock is A16 32GB blr (~$0.94/hr); SFT resume still needs torch/trl fix;
- **Episodic Journal — 2026-09-05** (`episodic/2026-09-05`, low) — Operator completed Vast.ai setup: $6 credit, VAST_API_KEY + HF_TOKEN in .env, runpod_cpt SSH on account, vastai CLI in .venv
- …and 10 more entries — see `memory-store/index.md`.

<!-- memory-fabric:store/pretraining/eval-and-export -->
---
store_path: pretraining/eval-and-export
title: "Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)"
summary: "Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)"
priority: medium
tags: [pretraining, schedule, evaluation, export, notebook-c, perplexity]
schema_version: 1.3
last_updated: "2026-06-08T07:34:40-04:00"
review_status: stale
---

# Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)

Following the successful execution of Notebook B (Epoch 1 & 2) up to step 432:
1. **Pretraining Schedule Updated:** Timeline has been updated to bypass Epoch 3 and proceed directly to evaluation and merge. v2 of the private Kaggle dataset `spurgeon-training-run-1` carries the `checkpoint-432` weights and files forward.
2. **Notebook C Plan created:** Step 9 details the evaluation requirements (1x T4 GPU, Internet ON), input dataset mounts, loading the adapter via Unsloth's native `FastLanguageModel.from_pretrained()`, computing length-weighted perplexity on the 50-sermon holdout dataset, executing qualitative prompts, and exporting the final Phase 1 LoRA adapter weights.
3. **Jupyter Notebook Template created:** The evaluation template has been created at `continued_pretrain/notebooks/C_eval_and_merge.ipynb`.

<!-- memory-fabric:local/failures -->
---
section: failures
summary: "Generated map of memory-store/failures/ (32 entries)."
priority: medium
tags: [failures]
schema_version: 1.3
last_updated: "2026-09-23T14:22:40-03:00"
generated: true
generated_from: memory-store/failures
store_fingerprint: 6a90f60ca4a53e70b932c78f88a4ad87
body_hash: 26f4d8f650c53855dbe819c48f9a0778
---

# Failures Map

Generated by Memory Fabric from `memory-store/failures/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Vast official Unsloth image smoke blocked; LD_LIBRARY_PATH still SIGSEGV** (`failures/vast-unsloth-official-image-smoke`, high) — - Still **SIGSEGV exit 139** at first `trainer.train()` step
- **asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi** (`failures/asyncua-write-value-badtypemismatch-188c68c9d2`, medium) — asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi
- **B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_lo** (`failures/b-training-sota-earlystopping-4edd127cc9`, medium) — B_training_sota: EarlyStopping disabled — metric_for_best_model eval_spurgeon_loss not found in logs (B v6 after tokenized eval)
- **CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halt** (`failures/cpt-b-early-stop-561e9ec07f`, medium) — CPT B early-stop patience=2 with eval_steps=25 and 2-doc eval_spurgeon_loss halted corpus v3 at step 375 of 4128 (~8.2M of 90M tokens)
- **torch.OutOfMemoryError: CUDA out of memory during SFTTrainer.evaluate at step 20** (`failures/cuda-oom-during-mid-ffcb775074`, medium) — CUDA OOM during mid-train eval at step ~20 with PEFT bf16 seq 2048 on RTX 4090 24GB
- **CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch ** (`failures/cuda-oom-on-kaggle-e64e9b60ce`, medium) — CUDA OOM on Kaggle T4 during CPT B v5 after manual pack (float32 Qwen3.5, batch 2, TRAIN_EMBEDDINGS=True)
- **CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocat** (`failures/cuda-out-of-memory-849d59401d`, medium) — CUDA out of memory during first eval of Qwen3.5 embed LoRA CPT: tried to allocate 6.81 GiB on T4 while evaluating mix+4 holdout buckets at EVAL_DOCS_PER_BUCKET=8 (logits for 248k vocab)
- **Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter dail** (`failures/full-semantic-judge-run-2188a7bf04`, medium) — Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter daily quota 429, and transient Gemini 503 responses
- …and 24 more entries — see `memory-store/index.md`.

<!-- memory-fabric:local/fine-tuning -->
---
section: fine-tuning
summary: "Generated map of memory-store/fine-tuning/ (38 entries)."
priority: medium
tags: [fine-tuning]
schema_version: 1.3
last_updated: "2026-09-27T09:59:27-03:00"
generated: true
generated_from: memory-store/fine-tuning
store_fingerprint: 8f1ed296e32a11ee471036764b819e26
body_hash: a873c67a3a8400fa7141169c06f2881a
---

# Fine Tuning Map

Generated by Memory Fabric from `memory-store/fine-tuning/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Fine-tuning next session handoff** (`fine-tuning/next-session-handoff`, high) — **Updated:** 2026-09-04 ~01:20 ET
- **SFT QA gold rewrite pilot (20 rows, merged)** (`fine-tuning/qa-gold-rewrite-pilot`, high) — **Status:** Complete and **merged** into `qa_mix_train.jsonl`
- **SFT/serve: knowledge assistant, not Spurgeon persona** (`fine-tuning/qa-knowledge-not-persona`, high) — SFT/chat must be knowledge assistant about texts, never Spurgeon persona; catechism CONTEXT landed.
- **SFT QA stays Spurgeon-only (decision)** (`fine-tuning/qa-mix-spurgeon-only-decision`, high) — **Decided 2026-08-29** after operator question on mixing writers in QA SFT data
- **Overlay-safe catechism + multi-turn builders** (`fine-tuning/qa-overlay-safe-slice-builders`, high) — | `build_catechism_qa_slice.py` | `--variants`, `--target-new`, `--output` for phrasing variants |
- **QA verify + F5 slice gap report** (`fine-tuning/qa-prompt-strategy-verify`, high) — After overlay-safe catechism variants + multiturn merge:
- **One prompt; diversify task slices** (`fine-tuning/qa-prompt-type-decision`, high) — **Locked after live verify.** Improves SFT via example-type diversity, not multiple prompts
- **QA Sources Rewrite Progress** (`fine-tuning/qa-sources-rewrite-progress`, high) — Cross-session log of QA answer rewrite pipeline for SFT teacherish/quote fidelity
- **QA teacher prompt — quote fidelity fix** (`fine-tuning/qa-teacher-quote-fidelity-prompt`, high) — `fine_tuning/scripts/rewrite_qa_answers_teacher.py` TEACHER_SYSTEM rule 5 strengthened:
- **Qwen3.5-4B SFT special-token contract** (`fine-tuning/qwen35-sft-special-tokens`, high) — **Model:** `unsloth/Qwen3.5-4B-Base` (GATE-0 uses the same tokenizer on the CPT merge)
- **RunPod billing and local backup** (`fine-tuning/runpod-sft-gate0-decisions`, high) — **Decision:** Phase C GATE-0 SFT on RunPod (not dry-run)
- **SFT GATE-0 readiness revision (2026-09-02)** (`fine-tuning/sft-gate0-readiness-2026-09-02`, high) — **Date:** 2026-09-02 ~09:30 ET
- **SFT HF inject fix — urllib verify, no BOM** (`fine-tuning/sft-hf-inject-fix`, high) — **Date:** 2026-09-02 ~18:45 ET
- …and 25 more entries — see `memory-store/index.md`.

<!-- memory-fabric:store/failures/full-semantic-judge-run-2188a7bf04 -->
---
store_path: failures/full-semantic-judge-run-2188a7bf04
title: "Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter dail"
summary: "Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter daily quota 429, and transient Gemini 503 responses"
priority: medium
tags: [evaluation, failure, fix, llm-judge, rate-limit, resume, sft]
schema_version: 1.3
last_updated: "2026-09-07T22:16:20-04:00"
occurrences: 1
error_signature: "full semantic judge run stalled or failed due groq<path> <n>, openrouter daily quota <n>, and transient gemini <n> responses."
---

## Occurrence 1 — 2026-09-07T22:16:20-04:00

**Error:**
Full semantic judge run stalled or failed due Groq/Cerebras 403, OpenRouter daily quota 429, and transient Gemini 503 responses.

**Fix:**
Persist generation and judge progress, support judge-existing-report resume, batch order-swapped judgments, pin and verify one served judge model, and resume with Gemini 3.5 Flash Lite after transient failures without regenerating model outputs.

<!-- memory-fabric:store/fine-tuning/gemma-support -->
---
store_path: fine-tuning/gemma-support
title: "Gemma 2 Fine-Tuning Support"
summary: "Gemma 2 fine-tuning support scripts and configs."
priority: medium
tags: [gemma2, fine-tuning, ollama]
schema_version: 1.3
last_updated: "2026-06-03T17:19:45-04:00"
summary_hash: c6e3f7de5ff6c7d4b7d2b0101970513d
review_status: stale
---

# Gemma 2 Fine-Tuning Support

Parameterized scripts and config files to support fine-tuning Gemma 2 models (like unsloth/gemma-2-9b-it-bnb-4bit) matching local gemma4 configurations.

- Updated train_spurgeon_qlora.py to read base model and chat template (gemma2) via CLI args.
- Configured launch_training.py to pass parameters dynamically from configuration files.
- Added train_config_gemma.json configuration file.
- Created Spurgeon_Gemma2_Training_Colab.ipynb for Colab training and Modelfile.gemma for Ollama import.

<!-- memory-fabric:store/decisions/gemma4-finetuning -->
---
store_path: decisions/gemma4-finetuning
title: "Gemma 4 Fine-Tuning Transition"
summary: "Guides the upgrade of fine-tuning pipelines from Gemma 2 to the efficient, newer Gemma 4 12B model."
priority: medium
tags: [gemma4, finetuning, decisions]
schema_version: 1.3
last_updated: "2026-06-04T10:24:33-04:00"
summary_hash: 58d9e4c42d7f3c068e76867ebfc3458f
review_status: stale
---

# Decision: Upgrade Fine-Tuning Pipeline to Gemma 4 12B

We have transitioned the Spurgeon fine-tuning configurations, Google Colab notebooks, and Ollama templates from Gemma 2 9B to Google DeepMind's newly released Gemma 4 12B model (`unsloth/gemma-4-12b-it-bnb-4bit`).

## Rationale
- Gemma 4 is Google's newest open frontier-tier model family.
- The 12B variant utilizes a highly efficient "encoder-free" architecture that improves latency and multimodal processing capability.
- Unsloth provides optimized 4-bit configurations for fast, memory-efficient LoRA tuning, fitting well within free Google Colab T4 hardware limits.

## Configuration Details
- **Base model**: `unsloth/gemma-4-12b-it-bnb-4bit`
- **Chat Template**: `gemma-4`
- **Turn boundary sequences**: `<start_of_turn>` and `<end_of_turn>`

<!-- memory-fabric:store/failures/get-runpodapikey-treated-empty-ae395f84fc -->
---
store_path: failures/get-runpodapikey-treated-empty-ae395f84fc
title: "Get-RunpodApiKey treated empty config.toml apikey = '' as a valid key; MCP REST "
summary: "Get-RunpodApiKey treated empty config.toml apikey = '' as a valid key; MCP REST v1 pod create then failed Cloudflare 403/1010 without a usable RUNPOD_API_KEY"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-16T07:22:04-03:00"
occurrences: 1
error_signature: "get-runpodapikey treated empty config.toml apikey = <val> as a valid key; mcp rest v<n> pod create then failed cloudflare <n><path> without a usable runpod_api_key"
---

## Occurrence 1 — 2026-09-16T07:22:04-03:00

**Error:**
Get-RunpodApiKey treated empty config.toml apikey = '' as a valid key; MCP REST v1 pod create then failed Cloudflare 403/1010 without a usable RUNPOD_API_KEY

**Fix:**
Reject empty/quoted-empty apikey values in s6_runpod_common.ps1 Get-RunpodApiKey; require a real key or funded account + volume before S6 orchestrate

<!-- memory-fabric:local/grok -->
---
section: grok
summary: "Generated map of memory-store/grok/ (3 entries)."
priority: medium
tags: [grok]
schema_version: 1.3
last_updated: "2026-09-26T15:05:03-03:00"
generated: true
generated_from: memory-store/grok
store_fingerprint: a2e68d17210508bb8771a5d08cf4cd01
body_hash: 689e7a40f943dd001e1fcfd84a7b0440
---

# Grok Map

Generated by Memory Fabric from `memory-store/grok/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Grok Bot Forge for Vast/Runpod training** (`grok/forge-training-ops`, high) — - **Title:** Vast / Runpod training watch
- **Grok Bot Foundry for train/export code** (`grok/foundry-train-export`, high) — - **Foundry** — write/refine CPT+SFT+export code via Cursor Cloud Agents
- **Grok Integration with Memory Fabric (MCP + Docs + Native Layer)** (`grok/integration`, high) — Grok Integration with Memory Fabric (MCP + Docs + Native Layer)

<!-- memory-fabric:store/fine-tuning/hf-spurgeon-qa-v2-gguf -->
---
store_path: fine-tuning/hf-spurgeon-qa-v2-gguf
title: "HF: spurgeon-qa-v2 GGUF + merged BF16"
summary: "Private Hub repo: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-v2"
priority: medium
tags: [huggingface, gguf, sft, merged, bf16]
schema_version: 1.3
last_updated: "2026-09-06T20:45:41-04:00"
evidence: [fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf, fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf, fine_tuning/scripts/merge_sft_lora_local.py]
---

# HF: Spurgeon QA v2 (GGUF + merged BF16)

**Date:** 2026-09-06

Private Hub repo: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-v2

Contains:
- `spurgeon-qa-v2.Q4_K_M.gguf` (~2.71 GB) — Ollama / quantized
- Full merged BF16 HF weights (rebuilt locally after Vast fetch miss)

## Local
- Merged HF: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf/` (~7.85 GB, 5 shards)
- GGUF: `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf`
- Ollama model: `spurgeon-qa-v2` (smoke passed)
- Ingredients: CPT `theology_cpt_v2_merged_hf/` + LoRA `spurgeon_qa_lora_v2/lora/`

## Related
- LoRA-only: `rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2`
- Rebuild script: `fine_tuning/scripts/merge_sft_lora_local.py`

<!-- memory-fabric:store/failures/hypothesis-vast-s-n-e324f2c659 -->
---
store_path: failures/hypothesis-vast-s-n-e324f2c659
title: "Hypothesis: Vast S6 C +27.9% spurgeon PPL caused by untied embed/lm_head (ensure"
summary: "Hypothesis: Vast S6 C +27.9% spurgeon PPL caused by untied embed/lm_head (ensure_weight_tying=false)"
priority: medium
tags: [c-eval, cpt, failure, fix, peft, s6, tying]
schema_version: 1.3
last_updated: "2026-09-18T20:31:31-03:00"
occurrences: 1
error_signature: "hypothesis: vast s<n> c +<n>.<n>% spurgeon ppl caused by untied embed<path> (ensure_weight_tying=false)."
---

## Occurrence 1 — 2026-09-18T20:31:31-03:00

**Error:**
Hypothesis: Vast S6 C +27.9% spurgeon PPL caused by untied embed/lm_head (ensure_weight_tying=false).

**Fix:**
Added maybe_sync_tied_lm_head to eval_cpt_sota.py; re-C showed same_storage=0 but max_abs_delta≈0.002; after embed→lm_head copy PPL still 18.31 (+27.9%). Tying is NOT the regression cause. Keep Hub v2; treat Aug-28 13.34-for-6aab as unproven.

<!-- memory-fabric:store/bugs/lora-frozen-embeddings-special-tokens -->
---
store_path: bugs/lora-frozen-embeddings-special-tokens
title: "Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA"
summary: "Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA"
priority: medium
tags: [bugs, lora, embeddings, lm_head, special-tokens, unsloth]
schema_version: 1.3
last_updated: "2026-06-15T08:56:50-04:00"
review_status: stale
---

# Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA

## Context
During instruction fine-tuning (Phase 2), we added special tokens `<|im_start|>` and `<|im_end|>` to the vocabulary and called `model.resize_token_embeddings(len(tokenizer))` to adapt the embedding layers.
By default, standard LoRA only targets attention projection weights and MLP weights, leaving `embed_tokens` and `lm_head` frozen.
When new tokens are added to the vocabulary, `model.resize_token_embeddings()` initializes the new rows in the embedding matrix and LM head to random noise or zero.

## Problem
Because `embed_tokens` and `lm_head` were frozen, SFT training could not learn the representations or output projections for the new special tokens. The weights for `<|im_end|>` remained random noise/zero.
Consequently, at inference time, the model could not generate the stop token `<|im_end|>` because its output projection was random noise. Instead, it generated other tokens (which decoded to `"vinfos"` or other junk text) or failed to stop, causing runaway generations.

## Fix
In Notebook E (`fine_tuning/notebooks/E_qa_training.ipynb`), configured `FastLanguageModel.get_peft_model()` to target `embed_tokens` and `lm_head` in LoRA:
```python
model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                    "embed_tokens", "lm_head"], # Train embeddings and language modeling head to learn special tokens
    lora_alpha=32,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)
```
This enables the SFT training to optimize the embeddings and LM head projections for `<|im_start|>` and `<|im_end|>`, allowing the model to learn a clean stop token.

## Update: PEFT Wrapper Attribute Lookup Error during Inference Copying (2026-06-15)
### Problem
Although we successfully copied the pre-trained special token embedding weights during training (Notebook E), the base model weights at inference time (Notebook F) remained untrained because the LoRA adapter does not save frozen embedding weights.
To resolve this, we added a copying step at inference time in Notebook F. However, because `FastLanguageModel.from_pretrained` returns a `PeftModelForCausalLM` when loading an adapter (unlike a base model which returns `Qwen2ForCausalLM` directly), the attribute lookup `model.model.embed_tokens` raised an `AttributeError` during evaluation:
`AttributeError: 'Qwen2ForCausalLM' object has no attribute 'embed_tokens'`

This crashed the copy cell in Notebook F at line 251, leaving the weights of `<|im_end|>` completely untrained. Since the copy crashed, the model fell back to generating the next most probable tokens (`_Pods of grace, indeed!`) at turn boundaries instead of the stop token `<|im_end|>`.

### Fix
Patched both Notebook E and Notebook F to use Hugging Face's standard and robust methods:
- `model.get_input_embeddings().weight` instead of `model.model.embed_tokens.weight`
- `model.get_output_embeddings().weight` instead of `model.lm_head.weight`

These methods correctly delegate attribute lookup through the `PeftModel` wrappers, ensuring the special token weights are successfully copied at both training and inference time.

<!-- memory-fabric:store/pretraining/model-choice -->
---
store_path: pretraining/model-choice
title: "Pretraining Step 4 — Model Choice & Technical Rationale"
summary: "Pretraining Step 4 — Model Choice & Technical Rationale"
priority: medium
tags: [pretraining, model, qwen, vram]
schema_version: 1.3
last_updated: "2026-06-06T19:33:37-04:00"
review_status: stale
---

Technical rationale for choosing unsloth/Qwen2.5-3B (base model) for continued pretraining on Spurgeon's sermons. The model's 151,643 BPE vocabulary natively represents 19th-century English registers (thee, thou, hast) without excessive subword fragmentation. Detailed VRAM budgeting allocates ~7.55 GB out of 16 GB on a single T4 GPU, leaving massive headroom for packed training. Rationale covers choosing not to train input embeddings or lm_head to save VRAM and maintain gradient stability, while setting lora_dropout=0 enables Unsloth's fused Triton kernels.

<!-- memory-fabric:store/failures/nameerror-name-val-is-1276dd9806 -->
---
store_path: failures/nameerror-name-val-is-1276dd9806
title: "NameError: name '_is_hf_holdout_root' is not defined. Did you mean: 'is_hf_holdo"
summary: "NameError: name '_is_hf_holdout_root' is not defined"
priority: medium
tags: [cpt, failure, fix, nameerror, qwen35, runpod]
schema_version: 1.3
last_updated: "2026-08-26T23:34:20-04:00"
occurrences: 1
error_signature: "nameerror: name <val> is not defined. did you mean: <val>? in train_cpt_sota.py after pack (max_steps <n> -> <n>). crashed before d<n><path> load."
failure_key: nameerror
review_status: stale
---

## Occurrence 1 — 2026-08-26T23:34:20-04:00

**Error:**
NameError: name '_is_hf_holdout_root' is not defined. Did you mean: 'is_hf_holdout_root'? in train_cpt_sota.py after pack (MAX_STEPS 476 -> 674). Crashed before D2/holdout load.

**Fix:**
Typo in _gen_sota_notebooks.py B cell: called _is_hf_holdout_root instead of is_hf_holdout_root (cpt_runtime helper). Fixed generator + train_cpt_sota.py. Relaunch on Runpod.

<!-- memory-fabric:store/pretraining/notebook-structure -->
---
store_path: pretraining/notebook-structure
title: "Pretraining Step 3 — Kaggle Notebook Structure"
summary: "Pretraining Step 3 — Kaggle Notebook Structure"
priority: medium
tags: [pretraining, kaggle, notebook, setup]
schema_version: 1.3
last_updated: "2026-06-06T19:30:22-04:00"
review_status: stale
---

Overview of Kaggle Notebooks layout for Spurgeon's Qwen2.5-3B continued pretraining. Work is split across three notebooks (A: data prep, B: training, C: evaluation/export) to circumvent Kaggle's 9-hour execution limits. Notebook B details PEFT QLoRA configuration, memory-saving parameters (lora_dropout=0, batch size 2, gradient accumulation 8, packing=True), and includes strict rules for trainer epoch incrementing when resuming checkpoints from input datasets. Notebook C handles holdout perplexity and qualitative style evaluation.

<!-- memory-fabric:store/fine-tuning/ollama-local-test-next-session -->
---
store_path: fine-tuning/ollama-local-test-next-session
title: "DONE: Ollama local test complete (spurgeon-qa-v2)"
summary: "**Status:** COMPLETE (2026-09-06 / 2026-09-07)"
priority: medium
tags: [ollama, complete, done, sft, gguf]
schema_version: 1.3
last_updated: "2026-09-06T20:06:17-04:00"
evidence: [fine_tuning/scripts/smoke_test_ollama.py, fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf, fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf]
---

# DONE — Ollama local test (spurgeon-qa-v2)

**Status:** COMPLETE (2026-09-06 / 2026-09-07)
**No pending next-session work for merge/GGUF/Ollama smoke.**

## Done
- SFT LoRA merged on Vast `50091768` → `/workspace/spurgeon_qa_merged_hf` (CausalLM PEFT, 256/256 keys)
- Q4_K_M GGUF: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf` (~2.6GB) + copy at `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf`
- Ollama model `spurgeon-qa-v2` created; `smoke_test_ollama.py` **exit 0**
- Vast instance destroyed after fetch
- Full HF merge folder fetch incomplete; GGUF sufficient

## Chat
```
ollama run spurgeon-qa-v2
```

Plan (DONE): `fine-tuning/plans/ollama-merge-gguf`

<!-- memory-fabric:store/fine-tuning/plans/ollama-merge-gguf -->
---
store_path: fine-tuning/plans/ollama-merge-gguf
title: "DONE: merged HF local + Hub upload"
summary: "**Initially no** — Vast fetch of `/workspace/spurgeon_qa_merged_hf` failed; instance destroyed"
priority: medium
tags: [ollama, gguf, huggingface, sft, merged, done]
schema_version: 1.3
last_updated: "2026-09-06T20:45:20-04:00"
evidence: [fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf, fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf, fine_tuning/scripts/merge_sft_lora_local.py]
---

# Local + Hub: merged Spurgeon QA v2 (DONE)

**Date:** 2026-09-06/07

## Answer: was full HF merge saved after Vast?
**Initially no** — Vast fetch of `/workspace/spurgeon_qa_merged_hf` failed; instance destroyed. Only **Q4_K_M GGUF** was kept locally for Ollama.

## Now on disk
- **Full bf16 HF merge (rebuilt locally):** `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf/` (~7.85 GB, 5 shards)
- **GGUF:** `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf` (+ copy under `…/spurgeon_qa_gguf/`)
- **Ingredients still present:** `theology_cpt_v2_merged_hf/` + `spurgeon_qa_lora_v2/lora/`
- **Ollama:** `spurgeon-qa-v2` (smoke passed earlier)

## Hub
Private: https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-v2
- GGUF uploaded
- Merged bf16 HF folder uploaded

LoRA-only (earlier): https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2

<!-- memory-fabric:store/failures/oserror-errno-n-no-5a8bfd0fe3 -->
---
store_path: failures/oserror-errno-n-no-5a8bfd0fe3
title: "OSError: [Errno 28] No space left on device on Kaggle /kaggle/working while pape"
summary: "OSError: [Errno 28] No space left on device on Kaggle /kaggle/working while papermill saved the notebook after checkpoint-75"
priority: medium
tags: [checkpoints, cpt, disk, failure, fix, kaggle]
schema_version: 1.3
last_updated: "2026-08-26T01:22:27-04:00"
occurrences: 1
error_signature: "oserror: [errno <n>] no space left on device on kaggle <path> while papermill saved the notebook after checkpoint-<n>. embed lora modules_to_save plus optimizer.pt x save_total_limit=<n> filled the ~<n>gb working disk."
failure_key: oserror
review_status: stale
---

## Occurrence 1 — 2026-08-26T01:22:27-04:00

**Error:**
OSError: [Errno 28] No space left on device on Kaggle /kaggle/working while papermill saved the notebook after checkpoint-75. Embed LoRA modules_to_save plus optimizer.pt x SAVE_TOTAL_LIMIT=4 filled the ~20GB working disk.

**Fix:**
SAVE_TOTAL_LIMIT=1 and save_only_model=True so checkpoints skip optimizer.pt. Print disk free at train start.

<!-- memory-fabric:store/failures/pack-document-isolated-spliced-ead647ad1d -->
---
store_path: failures/pack-document-isolated-spliced-ead647ad1d
title: "pack_document_isolated spliced leftover tokens of a document longer than max_seq"
summary: "pack_document_isolated spliced leftover tokens of a document longer than max_seq_len onto the start of the next short document (same row), recreating stream-pack leftover-A + start-of-B"
priority: medium
tags: [cpt, failure, fix, packing, unsloth]
schema_version: 1.3
last_updated: "2026-08-26T08:47:44-04:00"
occurrences: 1
error_signature: "pack_document_isolated spliced leftover tokens of a document longer than max_seq_len onto the start of the next short document (same row), recreating stream-pack leftover-a + start-of-b"
review_status: stale
---

## Occurrence 1 — 2026-08-26T08:47:44-04:00

**Error:**
pack_document_isolated spliced leftover tokens of a document longer than max_seq_len onto the start of the next short document (same row), recreating stream-pack leftover-A + start-of-B

**Fix:**
Flush every split-doc window as its own row so only complete documents that both fit share a row. Added test_long_doc_leftover_not_spliced_onto_next. DataCollatorForSeq2Seq preserves post-EOS labels=-100.

<!-- memory-fabric:store/failures/peft-sft-lora-merge-5b98bf291d -->
---
store_path: failures/peft-sft-lora-merge-5b98bf291d
title: "PEFT SFT LoRA merge onto Qwen3.5 CPT-merged HF silently no-ops when loaded as Qw"
summary: "PEFT SFT LoRA merge onto Qwen3.5 CPT-merged HF silently no-ops when loaded as Qwen3_5ForConditionalGeneration (config architectures) because adapter keys use model.layers.* (CausalLM training) but Con"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-06T20:04:46-04:00"
occurrences: 1
error_signature: "peft sft lora merge onto qwen<n>.<n> cpt-merged hf silently no-ops when loaded as qwen<n>_<n>forconditionalgeneration (config architectures) because adapter keys use model.layers.* (causallm training) but condgen expects model.language_model.layers.*; peft warns missing adapter keys and merge_and_un"
---

## Occurrence 1 — 2026-09-06T20:04:46-04:00

**Error:**
PEFT SFT LoRA merge onto Qwen3.5 CPT-merged HF silently no-ops when loaded as Qwen3_5ForConditionalGeneration (config architectures) because adapter keys use model.layers.* (CausalLM training) but CondGen expects model.language_model.layers.*; PEFT warns missing adapter keys and merge_and_unload saves base unchanged.

**Fix:**
Always merge SFT with AutoModelForCausalLM (Qwen3_5ForCausalLM paths). Fail closed if peft state key count << adapter tensors. See merge_sft_lora.py.

<!-- memory-fabric:store/fine-tuning/post-sft-eval-2026-09-07 -->
---
store_path: fine-tuning/post-sft-eval-2026-09-07
title: "Post-SFT frozen evaluation complete"
summary: "Full post-SFT evaluation completed on all 100 frozen fixed-context examples (50 answerable, 50 refusal), comparing Ollama `spurgeon-qa-v2` against `spurgeon-cpt` with identical raw ChatML and temperat"
priority: medium
tags: [sft, evaluation, ollama, gemini, gates]
schema_version: 1.3
last_updated: "2026-09-07T22:16:20-04:00"
evidence: [fine_tuning/eval_results/post_sft_eval.json, fine_tuning/eval_results/post_sft_eval_human_review.md, fine_tuning/data/qa_test_frozen.sha256]
---

Full post-SFT evaluation completed on all 100 frozen fixed-context examples (50 answerable, 50 refusal), comparing Ollama `spurgeon-qa-v2` against `spurgeon-cpt` with identical raw ChatML and temperature 0. Gemini 3.5 Flash Lite judged 200 order-swapped pairs: candidate groundedness 4.51, correctness 4.455, citation quality 4.19, honesty 4.49, style 4.615; candidate won 171/200 judgments vs 21 losses and 8 ties. Deterministic SFT results: format 100%, echo 0%, corruption 0%, valid citations 100%, stop 100%, leaked turns 0%, false-refusal 2%, but refusal recall only 54% (27/50), precision 96.43%, F1 69.23%, and 2% persona violations. Release verdict: FAIL only the refusal-recall >=85% hard gate; export remains blocked. Baseline was much worse: groundedness 2.485, corruption 24%, echo 9%, refusal recall 18%, stop 78%.

<!-- memory-fabric:store/fine-tuning/post-sft-eval-results -->
---
store_path: fine-tuning/post-sft-eval-results
title: "Post-SFT evaluation results"
summary: "Compared local Ollama `spurgeon-qa-v2` against `spurgeon-cpt` on all 100 frozen fixed-context examples, using deterministic raw ChatML generation and 200 order-swapped judgments from a pinned independ"
priority: medium
tags: [sft, evaluation, ollama, cpt, release-gate]
schema_version: 1.3
last_updated: "2026-09-07T22:16:54-04:00"
evidence: [fine_tuning/eval_results/post_sft_eval.json, fine_tuning/eval_results/post_sft_eval_human_review.md, fine_tuning/scripts/evaluate.py]
---

# Post-SFT evaluation complete (2026-09-07)

Compared local Ollama `spurgeon-qa-v2` against `spurgeon-cpt` on all 100 frozen fixed-context examples, using deterministic raw ChatML generation and 200 order-swapped judgments from a pinned independent judge.

## Results
- Candidate groundedness: **4.51/5** vs CPT **2.485/5**.
- Candidate judge wins: **171/200**.
- Refusal recall: **54%** (27/50), below required **85%**.
- Corruption: **0%**; context echo: **0%**; leaked turns: **0%**; stop compliance: **100%**.
- Verdict: **release gates FAIL solely on refusal recall**. Do not change app defaults or treat the model as release-ready.

## Evidence
- Full report: `fine_tuning/eval_results/post_sft_eval.json`
- Human review: `fine_tuning/eval_results/post_sft_eval_human_review.md`
- Focused tests: 16 passed.
- Full pytest collection is blocked by unrelated vendored llama.cpp dependency imports.

<!-- memory-fabric:store/failures/post-sft-stop-token-e8b2fdaa15 -->
---
store_path: failures/post-sft-stop-token-e8b2fdaa15
title: "Post-SFT stop-token phases falsely failed raw-ID generations, while Ollama API s"
summary: "Post-SFT stop-token phases falsely failed raw-ID generations, while Ollama API stops could falsely pass after stripping leaked im_start turns"
priority: medium
tags: [evaluation, failure, fix, ollama, sft, stop-tokens]
schema_version: 1.3
last_updated: "2026-09-07T22:16:20-04:00"
occurrences: 1
error_signature: "post-sft stop-token phases falsely failed raw-id generations, while ollama api stops could falsely pass after stripping leaked im_start turns."
---

## Occurrence 1 — 2026-09-07T22:16:20-04:00

**Error:**
Post-SFT stop-token phases falsely failed raw-ID generations, while Ollama API stops could falsely pass after stripping leaked im_start turns.

**Fix:**
Treat raw im_end token IDs as authoritative; for Ollama compliance use raw ChatML and configure only im_end as the stop so im_start leaks remain visible; phase 3 recomputes from raw stop probes and phase 5 fails whenever the complete summary fails.

<!-- memory-fabric:store/failures/powershell-n-n-parsererror-b9e9a8ea15 -->
---
store_path: failures/powershell-n-n-parsererror-b9e9a8ea15
title: "PowerShell 5.1 ParserError: string has no terminator when a UTF-8 em-dash sits i"
summary: "PowerShell 5.1 ParserError: string has no terminator when a UTF-8 em-dash sits inside double quotes in a .ps1 without BOM"
priority: medium
tags: [encoding, failure, fix, powershell, scripts, vast]
schema_version: 1.3
last_updated: "2026-09-16T11:02:02-03:00"
occurrences: 1
error_signature: "powershell <n>.<n> parsererror: string has no terminator when a utf-<n> em-dash sits inside double quotes in a .ps<n> without bom"
failure_key: "parsererror|utf-8"
---

## Occurrence 1 — 2026-09-16T11:02:02-03:00

**Error:**
PowerShell 5.1 ParserError: string has no terminator when a UTF-8 em-dash sits inside double quotes in a .ps1 without BOM

**Fix:**
Use ASCII -- in PowerShell scripts instead of Unicode em-dashes. Windows PowerShell 5.1 reads UTF-8 without BOM as ANSI and byte 0x94 inside the em-dash closes the string.

<!-- memory-fabric:local/pretraining -->
---
section: pretraining
summary: "Generated map of memory-store/pretraining/ (70 entries)."
priority: medium
tags: [pretraining]
schema_version: 1.3
last_updated: "2026-09-27T09:59:27-03:00"
generated: true
generated_from: memory-store/pretraining
store_fingerprint: a0f079667a0aff7625b9b392ac326eeb
body_hash: d3ccfcb4078cb9d0b2ff7295bb82eb08
---

# Pretraining Map

Generated by Memory Fabric from `memory-store/pretraining/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **CPT B_training_sota known issues (P1 closed — log spam)** (`pretraining/bugs/b-training-sota-known-issues`, high) — Source of truth: `continued_pretrain/scripts/_gen_sota_notebooks.py` (regenerate notebooks; do not hand-edit only)
- **Composite CPT early stop merges split HF eval events** (`pretraining/bugs/composite-early-stop-eval-cycle`, high) — Hugging Face evaluates a dictionary of CPT eval datasets as separate callback events
- **Confessions + Institutes corpus (WCF, 1689, Calvin)** (`pretraining/confessions-corpus-fetch`, high) — Confessions + Institutes corpus (WCF, 1689, Calvin)
- **CPT B eval strategy — verified next-B spec** (`pretraining/cpt-b-eval-strategy`, high) — Operator approved this as the continue-session spec (nits from fact-check applied)
- **CPT corpus expansion (Puritans/Edwards)** (`pretraining/cpt-corpus-expansion-2026-08`, high) — Grew non-Spurgeon domain text so Spurgeon in-mix could rise while keeping ~45% share
- **CPT corpus v3 S1 Wave 1 fetch + mix** (`pretraining/cpt-corpus-v3-s1-wave1`, high) — **No B, no C, no Runpod GPU, no Kaggle push, no merge, no Hub overwrite.**
- **CPT corpus v3 S2 complete (fetch + mix, no training)** (`pretraining/cpt-corpus-v3-s2-complete`, high) — S2 fetch + mix rebuild finished 2026-08-27
- **CPT corpus v3 S2 is done — next is S3** (`pretraining/cpt-corpus-v3-s2-handoff`, high) — S2 done; pointer to s2-complete.
- **CPT corpus v3 S3 complete (Wave 3 + mix, no training)** (`pretraining/cpt-corpus-v3-s3-complete`, high) — S3 fetch + mix rebuild finished 2026-08-27
- **CPT corpus v3 S3 handoff (done this session)** (`pretraining/cpt-corpus-v3-s3-handoff`, high) — S3 done; pointer to s3-complete.
- **CPT corpus v3 S4 complete (confession/ST lift, no training)** (`pretraining/cpt-corpus-v3-s4-complete`, high) — S4 fetch + mix rebuild finished 2026-08-27
- **CPT corpus v3 S4 handoff (done this session)** (`pretraining/cpt-corpus-v3-s4-handoff`, high) — S4 done; pointer to s4-complete.
- **CPT corpus v3 S5 C complete — probe PASS, keep Hub v2** (`pretraining/cpt-corpus-v3-s5-c-complete`, high) — GPU `gynfhzyfjcjjyf` **deleted**
- …and 57 more entries — see `memory-store/index.md`.

<!-- memory-fabric:store/fine-tuning/qwen-sft-alpaca-reversion -->
---
store_path: fine-tuning/qwen-sft-alpaca-reversion
title: "Reverting Custom Model, Weight Copying, and ChatML in Qwen 2.5 SFT"
summary: "Reverting Custom Model, Weight Copying, and ChatML in Qwen 2.5 SFT"
priority: medium
tags: [finetuning, qwen2.5, unsloth, alpaca, reversion]
schema_version: 1.3
last_updated: "2026-06-15T09:29:56-04:00"
review_status: stale
---

# Reverting Custom Base Model, Weight Copying, and ChatML Alignment in SFT Notebook

## Context
Initially, the SFT notebook (`Qwen_2_5_+_Unsloth_2x_faster_finetuning.ipynb`) was adapted to load a custom pre-trained GGUF-shifted base model (`spurgeon_phase1_merged_hf`) and align ChatML formatting with the Qwen-2.5 Instruct model by copying embedding weights.

## Reversion Decision
The user requested to revert these changes. The notebook was re-configured to:
1. Load the standard `"unsloth/Qwen2.5-7B"` base model instead of the custom phase 1 merged model.
2. Remove the Instruct model loading and special token weights copying logic entirely.
3. Revert ChatML formatting to the standard Alpaca prompt template format.

## Implementation Details
- **Dataset Preprocessing:** The dataset (`spurgeon_qa_train_final.jsonl`'s `messages` key) is parsed:
  - System messages are combined with `QUESTION:` as the **Instruction**.
  - `CONTEXT:` is extracted as the **Input**.
  - Assistant responses are mapped to the **Response**.
- **SFT Trainer Delimiters:** The `train_on_responses_only` function masks the labels up to `"### Response:\n"` to focus training only on response generations.

<!-- memory-fabric:store/failures/runtimeerror-adapter-sha-n-b83673b4f0 -->
---
store_path: failures/runtimeerror-adapter-sha-n-b83673b4f0
title: "RuntimeError: adapter SHA256 mismatch: got ef4df3a3… (S5 LoRA) want 319d17a3… (H"
summary: "RuntimeError: adapter SHA256 mismatch: got ef4df3a3… (S5 LoRA) want 319d17a3… (Hub v2)"
priority: medium
tags: [cpt, failure, fix, s6, sft_env, sha256, vast]
schema_version: 1.3
last_updated: "2026-09-18T07:38:55-03:00"
occurrences: 1
error_signature: "runtimeerror: adapter sha<n> mismatch: got <hex>… (s<n> lora) want <hex>… (hub v<n>). vast cpt continue-b crashed immediately because vast_inject_hf_token.ps<n> writes expected_adapter_sha<n>=hub-v<n> into <path>, and vast_cpt_remote_continue_b.sh sourced .sft_env after exporting the s<n> sha, overw"
failure_key: runtimeerror
---

## Occurrence 1 — 2026-09-18T07:38:55-03:00

**Error:**
RuntimeError: adapter SHA256 mismatch: got ef4df3a3… (S5 LoRA) want 319d17a3… (Hub v2). Vast CPT continue-B crashed immediately because vast_inject_hf_token.ps1 writes EXPECTED_ADAPTER_SHA256=Hub-v2 into /workspace/.sft_env, and vast_cpt_remote_continue_b.sh sourced .sft_env after exporting the S5 SHA, overwriting it.

**Fix:**
Re-export EXPECTED_ADAPTER_SHA256=S5 (ef4df3a3…) AFTER sourcing .sft_env in vast_cpt_remote_continue_b.sh. On the live pod also sed-fixed .sft_env, moved the failed log aside, and relaunched. Training then passed INIT_ADAPTER SHA256 OK and resumed checkpoint-2050.

<!-- memory-fabric:store/failures/runtimeerror-expected-mat-n-e21431291d -->
---
store_path: failures/runtimeerror-expected-mat-n-e21431291d
title: "RuntimeError: expected mat1 and mat2 to have the same dtype, but got: float != c"
summary: "RuntimeError: expected mat1 and mat2 to have the same dtype, but got: float != c10::Half during trainer.evaluate after Unsloth upcasts embed_tokens to fp32 (D4 same_storage=0)"
priority: medium
tags: [cpt, dtype, failure, fix, kaggle, lm-head, qwen35]
schema_version: 1.3
last_updated: "2026-08-26T01:22:26-04:00"
occurrences: 1
error_signature: "runtimeerror: expected mat<n> and mat<n> to have the same dtype, but got: float != c<n>::half during trainer.evaluate after unsloth upcasts embed_tokens to fp<n> (d<n> same_storage=<n>). eval calls self.lm_head(hidden_fp<n>) vs fp<n> lm_head weight. disabling trainer fp<n><path> alone did not fix it"
failure_key: runtimeerror
review_status: stale
---

## Occurrence 1 — 2026-08-26T01:22:26-04:00

**Error:**
RuntimeError: expected mat1 and mat2 to have the same dtype, but got: float != c10::Half during trainer.evaluate after Unsloth upcasts embed_tokens to fp32 (D4 same_storage=0). Eval calls self.lm_head(hidden_fp32) vs fp16 lm_head weight. Disabling Trainer fp16/bf16 alone did not fix it.

**Fix:**
Register a forward pre-hook on get_output_embeddings() that casts lm_head inputs to weight.dtype. Keep trainer fp16/bf16 off when TRAIN_EMBEDDINGS=True. Do not upcast the full lm_head table (VRAM).

<!-- memory-fabric:store/failures/s-n-composite-seed-c37a1172e7 -->
---
store_path: failures/s-n-composite-seed-c37a1172e7
title: "S7 composite seed used isolation-C full-holdout CE for puritan (1.722) and confe"
summary: "S7 composite seed used isolation-C full-holdout CE for puritan (1.722) and confession (1.662) instead of S6 in-train @ ckpt-2050 (1.751 / 1.668)"
priority: medium
tags: [cpt, early-stop, failure, fix, s7, seed]
schema_version: 1.3
last_updated: "2026-09-21T11:05:20-03:00"
occurrences: 1
error_signature: "s<n> composite seed used isolation-c full-holdout ce for puritan (<n>.<n>) and confession (<n>.<n>) instead of s<n> in-train @ ckpt-<n> (<n>.<n> / <n>.<n>). combined with patience=<n> and seeded bests, first flat cycles would halt at step ~<n> of <n> (~<n>% of budget) because the seed was unreachabl"
---

## Occurrence 1 — 2026-09-21T11:05:20-03:00

**Error:**
S7 composite seed used isolation-C full-holdout CE for puritan (1.722) and confession (1.662) instead of S6 in-train @ ckpt-2050 (1.751 / 1.668). Combined with patience=2 and seeded bests, first flat cycles would halt at step ~525 of 2064 (~25% of budget) because the seed was unreachable on EVAL_DOCS_PER_BUCKET=16.

**Fix:**
Corrected S7_DEFAULT_COMPOSITE_SEED_BESTS to in-train values (puritan 1.751, confession 1.668). Retuned S7 to patience=4, epsilon=0.003, eval/save_steps=50, warmup_ratio=0.04. Documented that isolation-C CE must never replace in-train seeds.

<!-- memory-fabric:store/failures/s-n-vast-c-b0dd9b03d4 -->
---
store_path: failures/s-n-vast-c-b0dd9b03d4
title: "S6 Vast C-eval FAIL: SHA256 mismatch — EXPECTED was Hub-v2 319d17a3… after sourc"
summary: "S6 Vast C-eval FAIL: SHA256 mismatch — EXPECTED was Hub-v2 319d17a3… after sourcing /workspace/.sft_env from vast_inject_hf_token, while GOT was S6 ckpt-2050 6aab9194…"
priority: medium
tags: [c-eval, cpt, failure, fix, s6, sha256, vast]
schema_version: 1.3
last_updated: "2026-09-18T11:46:03-03:00"
occurrences: 1
error_signature: "s<n> vast c-eval fail: sha<n> mismatch — expected was hub-v<n> <hex>… after sourcing <path> from vast_inject_hf_token, while got was s<n> ckpt-<n> <hex>…"
---

## Occurrence 1 — 2026-09-18T11:46:03-03:00

**Error:**
S6 Vast C-eval FAIL: SHA256 mismatch — EXPECTED was Hub-v2 319d17a3… after sourcing /workspace/.sft_env from vast_inject_hf_token, while GOT was S6 ckpt-2050 6aab9194…

**Fix:**
In vast_remote_c_eval.sh, capture PINNED_ADAPTER_SHA256 before sourcing .sft_env, then unconditionally export EXPECTED_ADAPTER_SHA256=$PINNED_ADAPTER_SHA256 afterward (:- default does not override a set Hub-v2 value). Also wrap fetch scp in ErrorActionPreference Continue so Vast SSH banner on stderr does not abort before destroy.

<!-- memory-fabric:store/failures/segmentation-fault-exit-n-0bc8cb8155 -->
---
store_path: failures/segmentation-fault-exit-n-0bc8cb8155
title: "Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking "
summary: "Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking OK on Vast Unsloth 2026.9.2 + TRL 0.24 + Qwen3.5 4bit"
priority: medium
tags: [failure, fix, gate0, peft, segfault, sft, unsloth, vast]
schema_version: 1.3
last_updated: "2026-09-06T00:42:31-04:00"
occurrences: 2
error_signature: "segmentation fault (exit <n>) at first sfttrainer.train() step after s<n> masking ok on vast unsloth <n>.<n>.<n> + trl <n>.<n> + qwen<n>.<n> <n>bit. also verify_sft_stop_tokens phase<n> segfaulted. log shows num_items_in_batch warning then silent sigsegv. fake nvml_reader missing."
---

## Occurrence 1 — 2026-09-05T23:50:01-04:00

**Error:**
Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking OK on Vast Unsloth 2026.9.2 + TRL 0.24 + Qwen3.5 4bit. Also verify_sft_stop_tokens phase2 segfaulted. Log shows num_items_in_batch warning then silent SIGSEGV. Fake nvml_reader missing.

**Fix:**
NOT FIXED YET. TypeError dataset_text_field is fixed (SFTConfig-only path works through S3). Segfault at step 0 persists with batch 1, seq 512/4096, with/without DataCollatorForSeq2Seq override, and with use_gradient_checkpointing=True instead of unsloth. Next: investigate Unsloth/bitsandbytes/CUDA on Vast fractional GPU; try load_in_4bit=False or pin older unsloth; check /opt/fake/nvml_reader.

## Occurrence 2 — 2026-09-06T00:42:31-04:00

Segmentation fault (exit 139) at first SFTTrainer.train() step after S3 masking OK on Vast Unsloth 2026.9.2 + TRL 0.24 + Qwen3.5. Also Unsloth forward/backward SIGSEGV on full RTX 4090 (4bit and bf16). Fake nvml_reader missing on fractional hosts.

Do not use Unsloth on this Vast stack for GATE-0. Prefer full GPU (gpu_frac>=1) with cuda_max_good>=12.6. Use SFT_BACKEND=peft (transformers AutoModelForCausalLM bf16 + PEFT LoRA + TRL SFTTrainer). Avoid fractional GPUs (NVML spoofs 3090). Reduce seq/batch if OOM (2048/1/16 worked). Fix monitor to ignore setup Tracebacks.

<!-- memory-fabric:store/failures/sft-capacity-watcher-kept-1f40d3c1fe -->
---
store_path: failures/sft-capacity-watcher-kept-1f40d3c1fe
title: "SFT capacity watcher kept idle RunPod GPU pod billing after orchestrate failed o"
summary: "SFT capacity watcher kept idle RunPod GPU pod billing after orchestrate failed on sft_inject_hf_token.ps1; default idle delete was 20 min instead of immediate terminate on failed launch"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-02T17:00:27-04:00"
occurrences: 1
error_signature: "sft capacity watcher kept idle runpod gpu pod billing after orchestrate failed on sft_inject_hf_token.ps<n>; default idle delete was <n> min instead of immediate terminate on failed launch"
---

## Occurrence 1 — 2026-09-02T17:00:27-04:00

**Error:**
SFT capacity watcher kept idle RunPod GPU pod billing after orchestrate failed on sft_inject_hf_token.ps1; default idle delete was 20 min instead of immediate terminate on failed launch

**Fix:**
Deleted pod ph9wzckj6nttpa (sft-gate0, GPU util 0). Killed sft_watch_capacity and sft_monitor_until_done processes. Root cause: watch_status orchestrate_failed_retry keeps pod for SFT_IDLE_DELETE_MIN (20) retries instead of force-delete after inject/orchestrate failure.

<!-- memory-fabric:store/bugs/sft-tokenizer-mismatch-vinfos-spepacer -->
---
store_path: bugs/sft-tokenizer-mismatch-vinfos-spepacer
title: "Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)"
summary: -----
priority: medium
tags: [bugs, lora, tokenizer, qwen]
schema_version: 1.3
last_updated: "2026-06-13T22:03:20-04:00"
review_status: stale
---

-----
store_path: bugs/sft-tokenizer-mismatch-vinfos-spepacer
title: "Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)"
summary: "Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)"
priority: high
tags: [bugs, lora, tokenizer, qwen]
schema_version: 1.3
last_updated: "2026-06-13T22:10:00-04:00"
---

# Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)

## Context
During Phase 2 SFT training in Notebook E (`E_qa_training.ipynb`), a tokenizer mismatch led to `<|im_end|>` being split into subwords (`vinfos`/`spepacer`), which the model learned as the turn terminator. When a clean base model and tokenizer were used, the problem appeared resolved, but a new set of Chinese/system garbage tokens (`具有战士`/`rPid`/`sPid`) surfaced at paragraph boundaries.

## Root Cause Analysis
- **PEFT Weight Untying Mismatch:** Qwen 2.5 uses `tie_word_embeddings=True` to share weights between `embed_tokens` (input embeddings) and `lm_head` (output logits).
- When `"embed_tokens"` and `"lm_head"` are targeted in LoRA `target_modules`, PEFT creates separate adapters, untying these layers.
- In Qwen 2.5, this weight-untying causes model corruption, resulting in nonsensical output (like `具有战士` and `rPid`) at token prediction boundaries.
- Because Qwen 2.5 base model already has correct pre-trained weights for `<|im_start|>` (151644) and `<|im_end|>` (151645), we do NOT need to train these embedding layers. Keeping them frozen and tied is both safe and sufficient.

## Fixes Implemented
1. **Reverted LoRA Embedding Targets:** Removed `"embed_tokens"` and `"lm_head"` from `target_modules` in Notebook E (`E_qa_training.ipynb`) to keep embeddings properly frozen and tied.
2. **Fixed Notebook E Syntax Error:** Removed the unexpected indentation from the pre-fix check lines (24-27) in Cell 6 of Notebook E.
3. **Dynamic Adapter Directory Check:** Restored dynamic verification in `F_qa_eval.ipynb` Cell 4 to load the new adapter from `/kaggle/working/spurgeon_lora_qa` if present, preventing the use of stale adapters from Kaggle input datasets.

<!-- memory-fabric:store/fine-tuning/sft-track-a-batch1-complete -->
---
store_path: fine-tuning/sft-track-a-batch1-complete
title: "SFT Track A batch 1 complete"
summary: "- Teacher dry-run + Groq apply 50 rows; merge 24; zip + readiness PASS"
priority: medium
tags: [sft, bulk-rewrite, batch1]
schema_version: 1.3
last_updated: "2026-08-29T09:43:48-04:00"
---

# SFT Track A batch 1 complete (ready state)

**When:** 2026-08-29

## Done this arc
- Teacher dry-run + Groq apply 50 rows; merge 24; zip + readiness PASS
- Fixed teacher defaults to `openai/gpt-oss-120b`; Windows UTF-8 print fix
- Decision recorded: SFT QA Spurgeon-only (no multi-writer assistant mix)

## Ready for next session
- Continue bulk: `--provider groq --limit 50` (resume from bulk_pending 50 lines)
- Or GPU dry-run only if operator says go (no CPT volume)

## Counts snapshot
train 2923; gold 20; bulk merged 24; pending attempts 50 (24 ok / 26 drop ~48%)

<!-- memory-fabric:store/pretraining/bugs/sftconfig-pickle -->
---
store_path: pretraining/bugs/sftconfig-pickle
title: "Fixed SFTConfig Pickling Mismatch on Kaggle"
summary: "Fixed SFTConfig Pickling Mismatch on Kaggle"
priority: medium
tags: [pretraining, unsloth, trl, sftconfig, pickle, bug-fix]
schema_version: 1.3
last_updated: "2026-06-07T06:33:34-04:00"
review_status: stale
---

# Fixed SFTConfig Pickling Mismatch on Kaggle

During training checkpoint saving, PyTorch's `torch.save` serializes the trainer configuration `trainer.args`.
When running Unsloth on Kaggle, the dynamic compilation cache `/kaggle/working/unsloth_compiled_cache/UnslothSFTTrainer.py` re-imports or re-defines modules dynamically.
This causes a class identity mismatch: `sys.modules['trl.trainer.sft_config'].SFTConfig` is not the exact same class object as `trainer.args.__class__` anymore, triggering a `PicklingError`.

To resolve this:
1. Migrated Notebook B (`B_training.ipynb`) to use `trl.SFTConfig` directly.
2. In Cell 9 (Launch Training), added a metaprogramming fallback block right before calling `trainer.train()`:
   ```python
   import sys
   import trl
   if hasattr(trainer, "args") and trainer.args.__class__.__name__ == "SFTConfig":
       import trl.trainer.sft_config
       trl.trainer.sft_config.SFTConfig = trainer.args.__class__
       sys.modules["trl.trainer.sft_config"].SFTConfig = trainer.args.__class__
       trl.SFTConfig = trainer.args.__class__
   ```
This aligns the module entries with the instantiated class object, allowing the pickler to locate it successfully.

<!-- memory-fabric:store/failures/stack-isolation-c-install-da57762e21 -->
---
store_path: failures/stack-isolation-c-install-da57762e21
title: "Stack-isolation C install failed: Unsloth 2026.8.22 pulls torchvision/xformers f"
summary: "Stack-isolation C install failed: Unsloth 2026.8.22 pulls torchvision/xformers for torch 2.11; re-pinning torch 2.8 with --no-deps left torchvision 0.26 operators broken (torchvision::nms)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-20T18:17:11-03:00"
occurrences: 1
error_signature: "stack-isolation c install failed: unsloth <n>.<n>.<n> pulls torchvision<path> for torch <n>.<n>; re-pinning torch <n>.<n> with --no-deps left torchvision <n>.<n> operators broken (torchvision::nms)"
---

## Occurrence 1 — 2026-09-20T18:17:11-03:00

**Error:**
Stack-isolation C install failed: Unsloth 2026.8.22 pulls torchvision/xformers for torch 2.11; re-pinning torch 2.8 with --no-deps left torchvision 0.26 operators broken (torchvision::nms)

**Fix:**
Force-reinstall torch==2.8.0 + torchvision==0.23.0 + torchaudio==2.8.0 from cu126 index; uninstall xformers; set UNSLOTH_SKIP_TORCHVISION_CHECK=1. Encoded in vast_remote_stack_isolation_c.sh / vast_stack_isolation_rerun.sh.

<!-- memory-fabric:store/pretraining/training-configuration -->
---
store_path: pretraining/training-configuration
title: "Pretraining Step 7 — Training Configuration (Notebook B) Plan"
summary: "Pretraining Step 7 — Training Configuration (Notebook B) Plan"
priority: medium
tags: [pretraining, training, lora, qlora, kaggle, unsloth]
schema_version: 1.3
last_updated: "2026-06-06T20:59:08-04:00"
review_status: stale
---

Documents the GPU settings, VRAM budget, hyperparameter configurations, and resumption logic for Step 7: Training Configuration of Phase 1 of the Charles Spurgeon continued pretraining pipeline.

### Details:
- **Notebook B (`training.ipynb`)** runs on 1x T4 GPU (16GB VRAM) with Internet ON.
- VRAM is budgeted carefully (~7.55 GB usage, leaving ~8.45 GB headroom) to eliminate any OOM risk.
- Pinned installation of `unsloth[kaggle-new]` is used; manual dependency upgrades are strictly prohibited.
- Configures SFTTrainer with sequence packing (`packing = True`) at context length 2048 to prevent compute waste.
- Optimizer set to `adamw_8bit` with peak learning rate 2e-4 and cosine decay.
- Limits saved checkpoints to `save_total_limit = 3` to respect Kaggle's 20GB disk limit.
- Handles cross-session checkpoint resumption by dynamically incrementing `num_train_epochs` to prevent SFTTrainer immediate-exit bugs.

<!-- memory-fabric:store/failures/typeerror-sfttrainer-init-got-aa61ff7a3c -->
---
store_path: failures/typeerror-sfttrainer-init-got-aa61ff7a3c
title: "TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_tex"
summary: "TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_text_field' (TRL>=0.18/0.24 with UnslothSFTTrainer **kwargs forward)"
priority: medium
tags: [failure, fix, gate0, sft, trl, unsloth, vast]
schema_version: 1.3
last_updated: "2026-09-05T22:25:35-04:00"
occurrences: 1
error_signature: "typeerror: sfttrainer.__init__() got an unexpected keyword argument <val> (trl>=<n>.<n><path> with unslothsfttrainer **kwargs forward)"
failure_key: typeerror
---

## Occurrence 1 — 2026-09-05T22:25:35-04:00

**Error:**
TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'dataset_text_field' (TRL>=0.18/0.24 with UnslothSFTTrainer **kwargs forward)

**Fix:**
Never pass dataset_text_field/packing/max_seq_length to SFTTrainer. Put them on SFTConfig only; use _filter_kwargs so Unsloth **kwargs cannot forward obsolete keys to TRL. Also set SFTConfig eos_token/pad_token to real vocab tokens (<|endoftext|>) and overwrite Unsloth <EOS_TOKEN>/<|vision_pad|> placeholders before trainer init; drop messages column and keep ChatML text + train_on_responses_only.

<!-- memory-fabric:store/failures/unicodeencodeerror-val-codec-can-896018dfa4 -->
---
store_path: failures/unicodeencodeerror-val-codec-can-896018dfa4
title: "UnicodeEncodeError: 'charmap' codec can't encode character '\\u258e' when vast_cp"
summary: "UnicodeEncodeError: 'charmap' codec can't encode character '\\u2192' in position 2 (Windows cp1252 console) when 10_fetch_puritans.py printed status arrows"
priority: medium
tags: [cpt, encoding, failure, fix, monitor, vast, windows]
schema_version: 1.3
last_updated: "2026-09-23T14:22:40-03:00"
occurrences: 3
error_signature: "unicodeencodeerror: <val> codec can<val><path>' in position <n> (windows cp<n> console) when <n>_fetch_puritans.py printed status arrows."
failure_key: unicodeencodeerror
---

## Occurrence 1 — 2026-08-27T11:02:21-04:00

**Error:**
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 2 (Windows cp1252 console) when 10_fetch_puritans.py printed status arrows.

**Fix:**
Replaced the Unicode arrow in the status print with ASCII '->'. Also set PYTHONIOENCODING=utf-8. Fetch had already written Owen Goold vol.1 before the crash; resume skipped that file.

## Occurrence 2 — 2026-08-27T15:23:32-04:00

UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 23 (Windows cp1252 console) when 07_build_theology_mix.py printed Paragraph dedup docs_in → docs_out

Replaced Unicode arrows in 07_build_theology_mix.py prints (paragraph dedup and bucket cap) with ASCII '->'. Re-run mix with PYTHONIOENCODING=utf-8. Same class of bug as the fetcher status-arrow crash.

## Occurrence 3 — 2026-09-23T14:22:40-03:00

UnicodeEncodeError: 'charmap' codec can't encode character '\u258e' when vast_cpt_s7_monitor_until_done.py prints Unsloth tqdm progress bars on Windows cp1252 redirected stdout; that exception skipped fetch + finished checks every poll cycle

Sanitize monitor log lines with safe_line() ASCII replace, reconfigure stdio to utf-8 errors=replace, and set PYTHONIOENCODING=utf-8 when orchestrate starts the monitor.

<!-- memory-fabric:store/bugs/unsloth-fast-patching-warnings -->
---
store_path: bugs/unsloth-fast-patching-warnings
title: "Unsloth Training Warnings & Fast Patching Resolution"
summary: "Unsloth Training Warnings & Fast Patching Resolution"
priority: medium
tags: [unsloth, lora, gemma4, bugfix]
schema_version: 1.3
last_updated: "2026-06-06T12:04:12-04:00"
review_status: stale
---

# Unsloth Training Warnings & Fast Patching Resolution

## 1. LoRA Dropout Performance Warning
* **Problem**: Setting `lora_dropout` to any non-zero value (e.g., `0.05`) in Unsloth triggers the following warning:
  ```
  Unsloth: Dropout = 0 is supported for fast patching. You are using dropout = 0.05.
  Unsloth will patch all other layers, except LoRA matrices, causing a performance hit.
  ```
* **Implication**: Unsloth uses highly optimized custom CUDA kernels for LoRA layers which require `lora_dropout = 0`. Setting it higher causes Unsloth to fall back to the slower default PEFT implementation for the LoRA adapter matrices, losing significant training speedup and VRAM efficiency.
* **Resolution**: Updated all configurations and notebooks to use `lora_dropout = 0` (or `0.0`), enabling full Unsloth optimization.

## 2. Gemma 4 Audio Tower Hook Registration Warning
* **Problem**: Loading multimodal Gemma 4 variants (such as `unsloth/gemma-4-E4B-it` or `unsloth/gemma-4-12b-it`) in Unsloth produces the initialization warning:
  ```
  [unsloth_zoo.log|WARNING]Unsloth: Failed to register input-embedding hook for `model.base_model.model.model.audio_tower`: `get_input_embeddings` not auto‑handled for Gemma4AudioModel; please override in the subclass.. Falling back to pre-forward hook.
  ```
* **Implication**: Gemma 4 is a multimodal model containing audio components (`audio_tower`/`Gemma4AudioModel`). Unsloth's auto-patcher does not natively handle embedding hooks for the audio tower and falls back to a standard pre-forward hook.
* **Status**: This warning is expected, benign, and can be safely ignored. For text-only fine-tuning tasks (such as Spurgeon style-transfer training), the audio tower is completely inactive and does not receive input sequences, so the fallback pre-forward hook has zero impact on training correctness or stability.

<!-- memory-fabric:store/failures/unsloth-sigsegv-exit-n-c04655b283 -->
---
store_path: failures/unsloth-sigsegv-exit-n-c04655b283
title: "Unsloth CPT+LoRA SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast RTX"
summary: "Unsloth SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast — including full RTX 4090 (4bit and bf16)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-16T07:54:00-03:00"
occurrences: 2
error_signature: "unsloth sigsegv (exit <n>) at first sfttrainer.train() step on vast — including full rtx <n> (<n>bit and bf<n>). also fractional gpu nvml spoof as <n>."
---

## Occurrence 1 — 2026-09-06T00:46:26-04:00

**Error:**
Unsloth SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast — including full RTX 4090 (4bit and bf16). Also fractional GPU NVML spoof as 3090.

**Fix:**
Do not use Unsloth on Vast for GATE-0. Prefer full GPU (gpu_frac>=1) with cuda_max_good>=12.6. Use SFT_BACKEND=peft (transformers AutoModelForCausalLM bf16 + PEFT LoRA + TRL). Persist peft + seq2048/batch1/accum16 in vast_inject_hf_token.ps1. Monitor ignores setup Tracebacks (train-log-only crash detection).

## Occurrence 2 — 2026-09-16T07:54:00-03:00

Unsloth CPT+LoRA SIGSEGV (exit 139) at first SFTTrainer.train() step on Vast RTX 4090 (torch 2.11+cu126, Qwen3.5-4B bf16)

Do not use Unsloth for CPT on Vast. Smoke confirmed same failure mode as SFT. Use PEFT on Vast or run Unsloth CPT on Runpod once volume/funds are available.

<!-- memory-fabric:store/failures/unsloth-sigsegv-on-vast-c00055092f -->
---
store_path: failures/unsloth-sigsegv-on-vast-c00055092f
title: "Unsloth SIGSEGV on Vast with system pip; conda-forge pytorch-cuda resolved to CP"
summary: "Unsloth SIGSEGV on Vast with system pip; conda-forge pytorch-cuda resolved to CPU"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-16T10:28:27-03:00"
occurrences: 1
error_signature: "unsloth sigsegv on vast with system pip; conda-forge pytorch-cuda resolved to cpu"
---

## Occurrence 1 — 2026-09-16T10:28:27-03:00

**Error:**
Unsloth SIGSEGV on Vast with system pip; conda-forge pytorch-cuda resolved to CPU

**Fix:**
Use Miniforge env + pip install torch cu126 into that env (not system site-packages; avoid conda-forge CPU pytorch). Smoke passed 3 Unsloth CPT steps on Vast 4090.

<!-- memory-fabric:store/failures/unslothtrainer-runtimeerror-you-must-b72157a8b4 -->
---
store_path: failures/unslothtrainer-runtimeerror-you-must-b72157a8b4
title: "UnslothTrainer RuntimeError: You must specify a formatting_func when MANUAL_PACK"
summary: "UnslothTrainer RuntimeError: You must specify a formatting_func when MANUAL_PACK train has input_ids but eval_dataset dict still has text columns"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-08-25T00:45:48-04:00"
occurrences: 1
error_signature: "unslothtrainer runtimeerror: you must specify a formatting_func when manual_pack train has input_ids but eval_dataset dict still has text columns"
failure_key: runtimeerror
review_status: stale
---

## Occurrence 1 — 2026-08-25T00:45:48-04:00

**Error:**
UnslothTrainer RuntimeError: You must specify a formatting_func when MANUAL_PACK train has input_ids but eval_dataset dict still has text columns

**Fix:**
Tokenize eval holdout buckets to input_ids/attention_mask/labels (truncate to MAX_SEQ_LENGTH) before UnslothTrainer when MANUAL_PACK=True in _gen_sota_notebooks.py

<!-- memory-fabric:store/failures/unslothtrainingarguments-typeerror-sftconfig-unexpected-652ebfdef4 -->
---
store_path: failures/unslothtrainingarguments-typeerror-sftconfig-unexpected-652ebfdef4
title: "UnslothTrainingArguments TypeError: SFTConfig unexpected keyword max_seq_length "
summary: "UnslothTrainingArguments TypeError: SFTConfig unexpected keyword max_seq_length (TRL 0.24)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-22T10:36:31-03:00"
occurrences: 1
error_signature: "unslothtrainingarguments typeerror: sftconfig unexpected keyword max_seq_length (trl <n>.<n>)"
failure_key: typeerror
---

## Occurrence 1 — 2026-09-22T10:36:31-03:00

**Error:**
UnslothTrainingArguments TypeError: SFTConfig unexpected keyword max_seq_length (TRL 0.24)

**Fix:**
TRL 0.24 renamed max_seq_length to max_length. train_cpt_sota.py now remaps on TypeError; vast_cpt_s7_remote_continue_b.sh pins trl>=0.18,<0.24.

<!-- memory-fabric:store/failures/valueerror-incorrect-image-source-9824630bd3 -->
---
store_path: failures/valueerror-incorrect-image-source-9824630bd3
title: "ValueError: Incorrect image source. Must be a valid URL starting with http:// or"
summary: "ValueError: Incorrect image source"
priority: medium
tags: [cpt, eval, failure, fix, kaggle, processor, qwen3.5]
schema_version: 1.3
last_updated: "2026-08-24T10:19:12-04:00"
occurrences: 1
error_signature: "valueerror: incorrect image source. must be a valid url starting with htt<path> or http<path> ... got sermon <n> | the necessity of increased faith. c_eval tokenizer(text) on qwen<n>.<n> vl processor treats first positional arg as images."
failure_key: valueerror
review_status: stale
---

## Occurrence 1 — 2026-08-24T10:19:12-04:00

**Error:**
ValueError: Incorrect image source. Must be a valid URL starting with http:// or https:// ... Got Sermon 32 | The Necessity of Increased Faith. C_eval tokenizer(text) on Qwen3.5 VL Processor treats first positional arg as images.

**Fix:**
Unwrap Processor to inner tokenizer and tokenize with encode/ids_for_text; never pass sermon strings positionally. PPL/probes/MCQ use tokenize_text() returning only input_ids + attention_mask.

<!-- memory-fabric:store/pretraining/vast-cpt-s6-prepare -->
---
store_path: pretraining/vast-cpt-s6-prepare
title: "Vast CPT S6 full-corpus prepare (no train)"
summary: "**Status:** Local+script readiness **PASS**"
priority: medium
tags: [cpt, s6, vast, conda, full-corpus, handoff]
schema_version: 1.3
last_updated: "2026-09-16T11:02:02-03:00"
evidence: [continued_pretrain/VAST_RUNBOOK_CPT.md, continued_pretrain/scripts/vast_cpt_orchestrate.ps1, continued_pretrain/scripts/vast_cpt_remote_continue_b.sh]
---

# Vast CPT S6 continue-B — prepared, not trained (2026-09-16)

**Status:** Local+script readiness **PASS**. Dry Vast search done. **No instance rented. No training started.**

## Job
Resume S6 continue-B on the **full v3 mix** (`a_output_v3`, 51417/520 docs, mix SHA256 `23dd3820…0973`, ~91.3M tokens, 4128 packed steps) using Miniforge Unsloth on Vast. Resume complete local `checkpoint-2050` (optimizer present, `eval_spurgeon_loss` 2.4987). `checkpoint-2100` is **not** local. Keep Hub v2 until finished B + winning C. Do **not** `S6_FRESH_START`.

## Proven stack
- Image `nvidia/cuda:12.4.1-devel-ubuntu22.04` + Miniforge env `unsloth_cpt` + torch **2.11.0+cu126 pip-in-env**
- System pip / official Unsloth Docker still fail (SIGSEGV / SSH)
- Smoke PASS earlier today: `CPT_UNSLOTH_SMOKE_PASS steps=3`

## Wired this session
- Runbook: `continued_pretrain/VAST_RUNBOOK_CPT.md`
- One-shot next session: `continued_pretrain/scripts/vast_cpt_orchestrate.ps1 -Go -StartMonitor`
- Payload packed: `D:\search-sermons-cpt\vast_cpt_s6\payload.tar` (~4.6 GB)
- Fetch **only** to D: (`C:` ~2 GB free)

## Dry search (no rent)
- Instances: `[]`
- Credit ~**$3.31** (too tight for a safe 4090 8–12 h wall at ~$0.54/hr)
- 4090 on-demand: NL ~$0.54/hr, HU ~$0.74/hr (`gpu_frac=1`, `cuda_max_good>=12.6`)
- 3090 Ampere 24 GB fallback: TW ~$0.24/hr (fits credit; use `-AllowLowCredit -OfferId`)
- `-Go` refuses if credit < $5 unless `-AllowLowCredit`

## Next session paste
```
Vast CPT S6 continue-B. Operator approved GPU go.
Do not smoke. Use Miniforge unsloth_cpt. Resume checkpoint-2050. Full a_output_v3.
cd continued_pretrain\scripts; .\vast_cpt_orchestrate.ps1 -Go -StartMonitor
If credit still under $5: add funds for 4090, or 3090 + -AllowLowCredit -OfferId <id>.
Fetch to D:\search-sermons-cpt\vast_cpt_s6. Destroy when done. Keep Hub v2.
```

<!-- memory-fabric:store/failures/vast-gate-n-sft-ca7b8e4d3c -->
---
store_path: failures/vast-gate-n-sft-ca7b8e4d3c
title: "Vast GATE-0 SFT crashed: TRL SFTTrainer ValueError eos_token '<EOS_TOKEN>' not i"
summary: "Vast GATE-0 SFT crashed: TRL SFTTrainer ValueError eos_token '<EOS_TOKEN>' not in vocab (Unsloth TokenizersBackend placeholder)"
priority: medium
tags: [failure, fix]
schema_version: 1.3
last_updated: "2026-09-05T21:24:43-04:00"
occurrences: 1
error_signature: "vast gate-<n> sft crashed: trl sfttrainer valueerror eos_token <val> not in vocab (unsloth tokenizersbackend placeholder). also earlier typeerror dataset_text_field on sfttrainer with newer trl."
failure_key: "valueerror|gate-0"
---

## Occurrence 1 — 2026-09-05T21:24:43-04:00

**Error:**
Vast GATE-0 SFT crashed: TRL SFTTrainer ValueError eos_token '<EOS_TOKEN>' not in vocab (Unsloth TokenizersBackend placeholder). Also earlier TypeError dataset_text_field on SFTTrainer with newer TRL.

**Fix:**
Force pad/eos to <|endoftext|> on outer+inner tokenizer always; re-apply after get_peft_model; SFTConfig eos/pad_token + filter kwargs so Unsloth does not forward obsolete trainer args. Re-rent after fix.

<!-- memory-fabric:store/fine-tuning/vast-gate0-candidate -->
---
store_path: fine-tuning/vast-gate0-candidate
title: "Vast.ai GATE-0 candidate"
summary: "While Vultr GPU is blocked ~30 days, **Vast.ai can run GATE-0** if we rent a reliable SSH GPU and reuse remote scripts (`sft_remote_setup.sh` / merge / train)"
priority: medium
tags: [cost, brl]
schema_version: 1.3
last_updated: "2026-09-05T18:19:51-04:00"
---

# Vast.ai for GATE-0 SFT (candidate)

While Vultr GPU is blocked ~30 days, **Vast.ai can run GATE-0** if we rent a reliable SSH GPU and reuse remote scripts (`sft_remote_setup.sh` / merge / train).

## Fit
- Job: merge Hub CPT LoRA v2 → train qa_mix_v2 SFT LoRA → fetch adapter → destroy.
- Model ~4B + LoRA: **16–24 GB VRAM** enough (4090 preferred).
- Unsloth is first-class on Vast (Studio template exists); we can also use plain CUDA image + our setup.

## Risks / ops
- Spot/interruptible hosts may kill mid-train — prefer high reliability / on-demand if available.
- Pin **torch 2.11** (ScalingType) — do not trust random image torch versions.
- SSH: some Unsloth docker tags conflict with Vast sshd; use stable image or fix on-start.
- Billing: destroy when done; same spend discipline as Vultr risk controls.

## Status
Not implemented yet — no `vast_*.ps1` in repo. Manual rent + SSH + existing `.sh` is enough for one GATE-0 run.

## Cost ballpark BRL (2026-09-05, FX ~R$5.13/USD)

Assumes RTX 4090 ~US$0.30–0.40/hr (Vast median / RunPod community); destroy when done.

| Job | Hours (typical) | USD | BRL (~) |
|-----|-----------------|-----|--------|
| CPT LoRA **merge** alone | 0.5–1.5 (incl setup) | $0.20–0.60 | **R$1–3** |
| GATE-0 **SFT** (+ merge same VM) | 8–12 wall | $2.5–5 (4090) / $8–12 (Vultr A16) | **R$13–26** / **R$41–62** |
| CPT **resume** (S6-style continue B) | 8–16 wall @ 4090 | $2.5–6.5 | **R$13–33** |

Buffers (retries, idle, download): add ~20–50%. Not a quote — live marketplace rates vary.

<!-- memory-fabric:store/fine-tuning/vast-gate0-next-session -->
---
store_path: fine-tuning/vast-gate0-next-session
title: "DONE: Vast GATE-0 + merge/GGUF/Ollama complete"
summary: "**Status:** COMPLETE (2026-09-06 / 2026-09-07)"
priority: medium
tags: [huggingface, sft, ollama, vast, complete, done]
schema_version: 1.3
last_updated: "2026-09-06T20:06:23-04:00"
evidence: [fine_tuning/scripts/train_sft_sota.py, fine_tuning/scripts/smoke_test_ollama.py, fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf]
---

# DONE — Vast GATE-0 SFT + merge → GGUF → Ollama

**No pending next-session work for GATE-0 train or Ollama path.**

## GATE-0 train (prior)
- Instance **50011937** destroyed after SFT finished
- Train: **408/408**, epoch 2.0, `train_loss≈1.874`
- Local adapter: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_lora_v2/lora/`
- Local CPT merge: `fine_tuning/kaggle/vast_sft_gate0/theology_cpt_v2_merged_hf/`
- Hub (private): https://huggingface.co/rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2

## Merge → GGUF → Ollama (completed)
- Merge instance **50091768** (Quebec RTX 4090) destroyed after fetch
- PEFT merge on CausalLM → `/workspace/spurgeon_qa_merged_hf` (256/256 keys; ConditionalGeneration attempt was wrong)
- GGUF: `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf` (~2.6GB) + `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf`
- Ollama: `spurgeon-qa-v2`; `smoke_test_ollama.py` exit 0

## Related DONE memories

F §5 eval / EXPORT still gated (`SFT_EXPORT=0`) — optional follow-up, not blocking Ollama.

<!-- memory-fabric:store/fine-tuning/vast-unsloth-conda-smoke-pass -->
---
store_path: fine-tuning/vast-unsloth-conda-smoke-pass
title: "Vast Unsloth CPT smoke PASS with Miniforge conda env"
summary: "**Verdict:** **PASS** (`CPT_UNSLOTH_SMOKE_PASS steps=3`)"
priority: medium
tags: [vast, unsloth, conda, cpt, smoke, pass]
schema_version: 1.3
last_updated: "2026-09-16T10:28:25-03:00"
---

# Vast Unsloth CPT smoke via Miniforge — PASS

**Date:** 2026-09-16
**Verdict:** **PASS** (`CPT_UNSLOTH_SMOKE_PASS steps=3`)

## What worked
- Image: `nvidia/cuda:12.4.1-devel-ubuntu22.04` (SSH-safe)
- **Miniforge** env `unsloth_smoke` (Python 3.11)
- torch **2.11.0+cu126 via pip inside the conda env** (not system pip; not conda-forge CPU pytorch)
- unsloth + trl/peft via pip in that env
- `unset LD_LIBRARY_PATH`
- 3 train steps completed; loss decreased; instance destroyed

## What failed earlier
- System pip on same image → SIGSEGV 139
- `unset LD_LIBRARY_PATH` alone → still SIGSEGV
- Official Unsloth Docker → SSH unusable on Vast
- First conda attempt: `conda install pytorch-cuda=12.4` resolved to **CPU** pytorch → AssertionError

## Implication
Vast + Unsloth CPT is viable **if** training runs inside a clean conda/miniforge env with CUDA torch installed into that env. System-site pip Unsloth remains broken.

Scripts: `vast_cpt_smoke_conda.ps1`, `vast_cpt_smoke_remote_conda.sh`
Log: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke_conda.log`

<!-- memory-fabric:store/failures/vast-unsloth-cpt-sigsegv-smoke -->
---
store_path: failures/vast-unsloth-cpt-sigsegv-smoke
title: "Vast Unsloth CPT+LoRA smoke SIGSEGV (exit 139)"
summary: "**Verdict:** **FAIL** — same class of crash as SFT Unsloth on Vast"
priority: medium
tags: [vast, unsloth, cpt, superseded]
schema_version: 1.3
last_updated: "2026-09-16T10:32:23-03:00"
---

# Vast Unsloth CPT+LoRA smoke — SIGSEGV

**Date:** 2026-09-16
**Verdict:** **FAIL** — same class of crash as SFT Unsloth on Vast.

## Setup
- Offer ~$0.47/hr RTX 4090 full GPU (`gpu_frac>=1`, `cuda_max_good>=12.6`)
- Image `nvidia/cuda:12.4.1-devel-ubuntu22.04`
- torch `2.11.0+cu126`, Unsloth 2026.9.4, Qwen3.5-4B-Base bf16 LoRA r=16
- Scripts: `continued_pretrain/scripts/smoke_vast_unsloth_cpt.py`, `vast_cpt_smoke_remote.sh`, `vast_cpt_smoke.ps1`

## Observation
- Import, `FastLanguageModel`, LoRA attach, tokenize — OK
- `trainer.train()` first step → **Segmentation fault, exit 139**
- Log marker: `CPT_UNSLOTH_SMOKE_FAIL sigsegv_exit_139`
- Local copy: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke.log`

## Implication
- **Vast + PEFT LoRA (SFT path):** known good
- **Vast + Unsloth CPT LoRA:** not viable for S6 resume on Vast
- Prefer Runpod (or PEFT CPT port) for Unsloth CPT; do not rent Vast for Unsloth CPT training

# Vast Unsloth CPT — use Miniforge (resolved)

**Update 2026-09-16:** Earlier implication “do not use Unsloth CPT on Vast” is **superseded** for the Miniforge path.

- System pip / official Unsloth Docker: still fail (SIGSEGV / SSH)
- **Miniforge + torch cu126 pip-in-env:** smoke PASS — see `fine-tuning/vast-unsloth-conda-smoke-pass`
- Next: wire full S6 continue-B to that recipe, or unblock Runpod

<!-- memory-fabric:store/episodic/2026-07-11 -->
---
store_path: episodic/2026-07-11
title: "Episodic Journal — 2026-07-11"
summary: "Episodic Journal — 2026-07-11"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-07-10T21:34:01-04:00"
review_status: stale
---

## cpt-sota-pipeline

Analyzed B_training.ipynb as solid Phase-1 Spurgeon CPT but not SOTA for multi-author theology. Implemented a parallel SOTA track without overwriting the baseline: theology mix script, A/B/C sota notebooks (Unsloth dual-LR + embed/lm_head), config JSON, data source layout, and README updates.

**Key decisions:**
- Never overwrite B_training.ipynb; SOTA lives in new files only
- Unsloth CPT recipe: embed_tokens+lm_head, UnslothTrainer dual LR 5e-5/5e-6, r=64+rsLoRA
- Data mix: Spurgeon 2.5x oversample + Puritans/confessions/Bible + ~10% replay
- Highest ROI is multi-source data; training recipe alone is secondary

**Files changed:**
- `continued_pretrain/scripts/07_build_theology_mix.py`
- `continued_pretrain/scripts/_gen_sota_notebooks.py`
- `continued_pretrain/notebooks/A_data_prep_sota.ipynb`
- `continued_pretrain/notebooks/B_training_sota.ipynb`
- `continued_pretrain/notebooks/C_eval_sota.ipynb`
- `continued_pretrain/configs/train_config_cpt_theology_sota.json`
- `continued_pretrain/README.md`
- `data/SOURCES_SOTA_CPT.md`
- `data/puritans/.gitkeep`
- `data/confessions/.gitkeep`
- `data/bible/.gitkeep`
- `.gitignore`

<!-- memory-fabric:store/episodic/2026-08-12 -->
---
store_path: episodic/2026-08-12
title: "Episodic Journal — 2026-08-12"
summary: "Episodic Journal — 2026-08-12"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-12T09:00:43-04:00"
review_status: stale
---

## opcua-scada-simulation-platform

Created a full-featured OPC UA Industrial Engine Simulation & Web SCADA platform for learning OPC UA concepts, address space hierarchy, monitored items, RPC methods, and client integration (UaExpert/Node-RED).

**Key decisions:**
- Used Python asyncua for custom OPC UA server simulation with industrial physics model
- Built FastAPI + WebSockets Web SCADA interface with live gauges and HTML5 canvas chart
- Implemented both OPC UA RPC Methods and direct Node writing for comprehensive learning

**Files changed:**
- `opcua_simulation/server/engine_physics.py`
- `opcua_simulation/server/opcua_server.py`
- `opcua_simulation/scada_backend/app.py`
- `opcua_simulation/static/index.html`
- `opcua_simulation/static/style.css`
- `opcua_simulation/static/app.js`
- `opcua_simulation/run_all.py`
- `opcua_simulation/README.md`

## copy-plan-to-agy-customizations

Copied implementation_plan.md, plan.md, and the complete opcua_simulation project files to ../agy-customizations as requested by the user.

- Copied implementation plan and complete OPC UA simulation codebase to ../agy-customizations

- `../agy-customizations/implementation_plan.md`
- `../agy-customizations/plan.md`
- `../agy-customizations/opcua_simulation/`

<!-- memory-fabric:store/episodic/2026-08-24 -->
---
store_path: episodic/2026-08-24
title: "Episodic Journal — 2026-08-24"
summary: "CPT B completed 250 steps on T4 (train 4356 rows)"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-24T17:04:05-04:00"
review_status: stale
---

## cpt-b-done-c-started

CPT B completed 250 steps on T4 (train 4356 rows). Best eval_mix_loss at checkpoint-50 (2.32) vs 2.46 at 250. Pushed C_eval_sota v1 with kernel source from B and corpus holdouts; RUN_MERGE=False. C queued on NvidiaTeslaT4.

## cpt-c-eval-path-fix

Fixed C_eval FileNotFoundError by resolving adapters under /kaggle/input/notebooks/<user>/<slug>/ instead of /kaggle/input/<slug>/. Regenerated notebooks, added path unit tests, pushed C v2 to Kaggle T4. After ~15 minutes the kernel was still QUEUED with empty logs (GPU queue, not another traceback).

**Key decisions:**
- Walk adapter_config.json under theology_cpt_lora then checkpoint-50
- Prefer HF theology_holdouts from B kernel over corpus txt
- Push C via 15_push_kaggle_cpt.py --only-c

**Files changed:**
- `continued_pretrain/scripts/test_kaggle_path_resolve.py`
- `continued_pretrain/scripts/15_push_kaggle_cpt.py`

## cpt-c-eval-vl-tokenize

Confirmed C v2 ERROR. Adapter mount worked; Qwen3.5 Processor treated Spurgeon holdout text as an image. Fixed eval/probes/MCQ to unwrap the text tokenizer, regenerated notebooks, unit-tested the VL positional trap, pushed C v3 to Kaggle T4.

- C v2 adapter path OK; crash was VL Processor images= first positional
- Tokenize via inner encode; drop vision tensors

## cpt-c-eval-handoff

Pulled C_eval v3 COMPLETE metrics and scored against §5. Gate fails: all holdout PPL buckets worse than base (+9–18%), Heidelberg MCQ +9.5 pts (need +10). Wrote handoff memory pretraining/cpt-v2-c-eval-gate-verdict for the next session.

- §5 gate FAIL — do not merge CPT adapter
- Heidelberg +9.5 pts almost passes; all domain PPL worse than base
- Next session: diagnose regression OR start SFT stock dry-run

- `continued_pretrain/kaggle/c_output/theology_cpt_eval_metrics.json`

## cpt-eval-docs-handoff

Saved full C_eval gate report, root causes, and session handoff to continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md and continued_pretrain/CPT_V2_KAGGLE_STATUS.md; updated memory pretraining/cpt-v2-c-eval-root-causes and gate-verdict.

- `continued_pretrain/kaggle/c_output/C_EVAL_GATE_REPORT.md`
- `continued_pretrain/CPT_V2_KAGGLE_STATUS.md`

## cpt-rc1-manual-pack

Implemented RC1 fix in B_training generator: manual stream packing for Qwen3.5 (Processor models ignore native packing). Added text_tokenizer/ids_for_text helpers, build_manual_packed_dataset(), packing=False, D1 gate, and run_config fields. Regenerated local notebook only — not pushed to Kaggle per user request.

- RC1 fix uses manual stream packing with inner text tokenizer; native packing=False for Qwen3.5
- D1 gate fails if packed rows still equal raw doc count
- Kaggle push deferred until further improvements

<!-- memory-fabric:store/episodic/2026-08-25 -->
---
store_path: episodic/2026-08-25
title: "Episodic Journal — 2026-08-25"
summary: "Implemented RC2–RC4 in B/C notebook generator: lighter hparams and early stop on spurgeon holdout loss, HF theology_holdouts path finder (fixes mix-only eval), D4 embed warning, C ADAPTER_OVERRIDE and"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-25T11:47:27-04:00"
review_status: stale
---

## cpt-rc2-rc4-local

Implemented RC2–RC4 in B/C notebook generator: lighter hparams and early stop on spurgeon holdout loss, HF theology_holdouts path finder (fixes mix-only eval), D4 embed warning, C ADAPTER_OVERRIDE and probe repetition warnings. Regenerated local notebooks; did not push to Kaggle.

**Key decisions:**
- Early-stop on eval_spurgeon_loss not mix
- Anti-overfit: r=32 LR 2e-5 MAX_STEPS=100
- HF holdout root only — never corpus txt
- No Kaggle push

**Files changed:**

## cpt-rc1-rc4-handoff

Saved next-session handoff via memory-fabric. CPT v2 gate remains FAIL on Kaggle v3. Local v4 recipe (manual pack, lighter hparams, spurgeon early-stop, C ADAPTER_OVERRIDE) is in the generator and notebooks but not pushed. Next step when asked: push B, train, then C.

- RC1–RC4 local only — no Kaggle push until asked
- Early-stop on eval_spurgeon_loss with HF theology_holdouts
- Ship on holdout PPL not MCQ alone

## cpt-corpus-expand-b-v6

Expanded CPT corpus (~51.5M chars / 8245 docs) with more Puritans/Edwards/Reformed PD texts, rebuilt mix with 10% replay, uploaded Kaggle corpus, refreshed A dataset, and completed B training v6 on T4 (manual pack, batch 1x16). C eval not re-run yet; merge still blocked.

- Grow non-Spurgeon domain first so Spurgeon in-mix rises under 45% share (weight 0.087→0.164)
- Tokenize eval datasets when MANUAL_PACK to avoid Unsloth formatting_func error
- T4 VRAM: batch 1x16 and TRAIN_EMBEDDINGS=False after OOM
- Do not merge until new C §5 holdout PPL passes

- `continued_pretrain/scripts/17_build_general_replay.py`

## cpt-c-v4-gate-fail

Pushed and ran Kaggle C_eval v4 against B v6 theology_cpt_lora. C COMPLETE; §5 holdout PPL FAIL (spurgeon/puritan/confession still worse than base; general within +10%). Updated gate report and handoff. Do not merge.

- Evaluated final LoRA only (no ADAPTER_OVERRIDE)
- Ship gate is holdout PPL; MCQ alone insufficient
- Blocked merge/publish on §5 FAIL despite large improvement vs C v3

- `continued_pretrain/kaggle/c_logs_v4.txt`

## cpt-v2-gate-fail-analysis

Deep analysis of why CPT v2 C v4 missed the §5 gate on B v6. C already evaluated checkpoint-25 (SHA256 match with theology_cpt_lora), not a broken last-step adapter. Root cause is undertraining plus a VRAM-fallback recipe (no embed LoRA, r=32, 25 steps / ~0.82M tokens vs ~476-step epoch). The P1 early-stop ‘metric never logged’ story is a misread of HuggingFace multi-eval log spam; trainer_state shows eval_spurgeon_loss and best=25.

- Do not re-run C on checkpoint-25; that is already the scored adapter.
- Hitting §5 15% PPL requires restoring CPT embeddings and training far more of one epoch, not another 100-step LoRA-only run.
- Optional C on ckpt-50/75 is expected to be worse because B eval losses rose after step 25.

## cpt-v7-recipe-impl

Implemented the CPT gate-miss plan: corrected P1 (metric was logged; C scored ckpt-25), regenerated B/C sota notebooks as v7 (embed LoRA, ~476 steps, quiet EarlyStopping, 8-doc eval, last-ckpt PPL), and updated runbook/config/handoff so C waits for B v7 and does not override B v6 checkpoint-25.

- C v4 scored checkpoint-25; do not re-C that adapter.
- B v7 default TRAIN_EMBEDDINGS=True at batch 1x16 with MAX_STEPS clamped to one packed epoch.
- Ship only on section 5 holdout PPL after B v7, not MCQ.


## cpt-v7-handoff-stop

Clarified stop point for next session: v7 B/C notebooks were regenerated in place (same Kaggle slugs, not a new kernel). Nothing was pushed or run on Kaggle. Last live run remains B v6 + C v4. Next action is kaggle push of B_training_sota on T4.

- B v7 exists only as regenerated local notebooks; Kaggle was not pushed or started.

## cpt-other-failure-modes

Analyzed additional CPT failure modes beyond token budget and frozen embeddings: harmful early LoRA drift, packed 2048 train vs independent truncated eval, Qwen3.5 float32/4bit hybrid tax, Spurgeon weight 0.164 undersampling, and tiny holdouts. Documented what B v7 will not fix.

- Uniform +2% PPL matches LoRA drift plus packed-vs-eval mismatch, not OCR or missing EOS.
- B v7 (embeds + 1 epoch) does not by itself fix packing isolation, Spurgeon undersample, or the 15% bar vs 15.6M mix.

## cpt-save-next-session

Saved next-session handoff: local B v7 notebooks not on Kaggle; C v4 still the last live run; additional failure modes (packed-vs-eval, LoRA drift, Spurgeon 0.164, tiny holdouts, 15% bar vs 15.6M mix) recorded in CPT_V2_KAGGLE_STATUS.md and memory.

- Saved extra CPT failure modes (packing vs eval, LoRA drift, Spurgeon undersample) into status + handoff so next session does not treat B v7 as a complete fix.

<!-- memory-fabric:store/episodic/2026-08-26 -->
---
store_path: episodic/2026-08-26
title: "Episodic Journal — 2026-08-26"
summary: "Pushed CPT B through Kaggle kernel v11"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-26T15:08:54-04:00"
review_status: stale
---

## cpt-v2-b-v11-complete

Pushed CPT B through Kaggle kernel v11. Embed LoRA trained on T4 after eval-OOM, lm_head dtype, and disk-full fixes. B v11 COMPLETE: early-stop at step 75 with eval_spurgeon rising 2.349→2.383; best checkpoint-25 SHA256-matches theology_cpt_lora. Did not run C or merge. Next B is LR 1e-5.

**Key decisions:**
- Do not run C on B v11: eval_spurgeon rose 2.349→2.383; early-stop at 75; best remains ckpt-25.
- Next B uses LEARNING_RATE=1e-5; keep embed LoRA plus eval-size, lm_head dtype hook, and save_only_model disk caps.
- v7–v10 failures (eval OOM, float vs Half, disk full) were fixed in-generator before v11 COMPLETE.

**Files changed:**
- `continued_pretrain/kaggle/B_training_sota/B_training_sota.ipynb`

## cpt-v2-b-v11-save

Saved a complete CPT v2 handoff so a new chat can continue after B v11 COMPLETE. Status file and memory pretraining/cpt-v2-next-session-handoff now record: early-stop 75, eval_spurgeon ROSE 2.349/2.363/2.383, best=ckpt-25 SHA256 3e51fc0abab98402ff9cb6ccde3ecfa80bdbbe03884f95fa8490ea54d969397c, no C, no merge, next LR 1e-5 (generator still 2e-5, run not started). Paste-for-new-chat block included. Local kaggle kernels output download to b_output_v11 was still running (~10+ min, no stdout, dest empty) — not blocked on.

- Do not run C on B v11 (eval_spurgeon rose 2.349→2.363→2.383; best=ckpt-25).
- Do not merge. Last C remains v4 §5 FAIL on B v6 ckpt-25.
- Next B LEARNING_RATE=1e-5 is documented only; generator still has 2e-5; no Kaggle push this save.
- Keep TRAIN_EMBEDDINGS=True, EVAL_DOCS=2, spurgeon-only eval, lm_head dtype-align hook, save_only_model + SAVE_TOTAL_LIMIT=1, T4.

- `.ai-memory/memory-store/pretraining/cpt-v2-next-session-handoff.md`

## cpt-v2-b-v12-lr-1e-5

Set LEARNING_RATE to 1e-5 in the SOTA generator, regenerated notebooks, and pushed B kernel v12 on T4. Kaggle is RUNNING with Tesla T4 / sm_75, lr=1e-5, TRAIN_EMBEDDINGS=True, EVAL_DOCS=2, spurgeon-only eval. Did not push C and did not merge. Last C remains v4 §5 FAIL on B v6 ckpt-25.

- Halved body LR to 1e-5 after B v11 eval_spurgeon rose 2.349→2.383 at 2e-5; kept embedding LR 5e-6 and all v11 eval/save fixes
- C only if v12 eval_spurgeon does not rise by step 50; if it still rises, stop — packing/undersample still unfixed
- Same slug theology-cpt-v2-b-training-sota (kernel v12), not a new kernel

- `continued_pretrain/kaggle/_poll_b_v7.py`

## cpt-v2-b-v12-push

Set LEARNING_RATE to 1e-5 (was 2e-5), regenerated the SOTA notebooks, and pushed B kernel v12 on Kaggle T4 (same slug rafaelvieira1/theology-cpt-v2-b-training-sota). Live logs confirmed Tesla T4 / sm_75 / torch 2.10+cu128 (not P100) with lr=1e-05, emb_lr=5e-06, train_embed=True, eval_docs=2, eval_buckets=['spurgeon']. Did not run C, did not merge, and did not push another kernel version; next session waits for v12 eval and C only if eval_spurgeon does not rise by step 50.

- Set LEARNING_RATE=1e-5 (was 2e-5 on v11) and regenerated B notebook from _gen_sota_notebooks.py.
- Pushed B kernel v12 on NvidiaTeslaT4 (same slug); did not push C and did not merge.
- T4 confirmed in live logs (Tesla T4 / sm_75 / torch 2.10+cu128; not P100). C only if eval_spurgeon does not rise by step 50.
- Left local poller continued_pretrain/kaggle/_poll_b_v7.py running; OUT is continued_pretrain/kaggle/b_logs_v12_raw.txt.

- `continued_pretrain/kaggle/b_logs_v12_raw.txt`

## cpt-v2-b-v12-complete

B v12 COMPLETE on Kaggle T4 at LEARNING_RATE=1e-5. Early-stop at step 75; eval_spurgeon rose 2.340 → 2.345 → 2.361; best=ckpt-25; SHA256 match ffe193feb33b7fd3a7af745b50e4745998cafcee96c42678c85ef943614b886a. Did not run C or merge. Halving LR vs v11 did not stop drift.

- Do not run C on B v12: eval_spurgeon rose by step 50 at LR 1e-5 (2.340	o2.345	o2.361).
- Do not push another B at this recipe; next work is packing/undersample, not more GPU steps.

- `continued_pretrain/kaggle/b_logs_v12_kaggle.txt`

## cpt-isolated-pack

Implemented document-isolated manual packing for CPT v2 after B v12 eval rose at 1e-5. pack_document_isolated no longer splices leftover-of-A onto start-of-B; post-EOS labels are ignore_index so CE does not train across documents. Regenerated SOTA notebooks. Mix keep-all-spurgeon is in 07_build_theology_mix.py but the corpus was not rebuilt or uploaded. Did not run C or push Kaggle.

- Document-isolated packing: EOS-aligned greedy pack; labels=-100 at first token of later docs in a row; continuation prefix ignored on long-doc splits. packing=False stays (GatedDeltaNet). D1 no longer fails when packed rows ≈ raw docs.
- Mix keep-all-spurgeon implemented (oversample others, cap 5x) but mix not rebuilt and not uploaded to Kaggle.
- No C, no merge, no Kaggle B push.

- `continued_pretrain/scripts/test_manual_pack.py`

## isolated-pack-review

Defect-first review of uncommitted document-isolated CPT packing. Found leftover-of-long-A spliced onto start-of-B; flushed each split-doc window; passed Seq2Seq collator so labels=-100 survive; D2 now scans all rows and collates. Tests PASS. Notebooks regenerated. Did not push Kaggle, run C, merge, or rebuild mix.

- Split-doc tails never share a row with the next document
- Use DataCollatorForSeq2Seq not LM collator so post-EOS -100 is not cloned away
- MAX_STEPS still clamps down only from 476; status ~511 was wrong
- B packing path is push-safe after human D1/D2 read; still do not C or merge

## cpt-v2-session-handoff

Registered CPT v2 continuation: B v12 COMPLETE with eval_spurgeon rising at LR 1e-5; no C/merge. Isolated packing reviewed and left unpushed. Documented 2026 Unsloth/HF recipes (no GDN packing, no QLoRA, bf16 4B on Ampere, one-doc padded rows) for the next session.

- Do not C/merge on B v12.
- Isolated pack is reviewed locally but GDN can still leak if two complete docs share a row; prefer one padded doc per row.
- Official Qwen3.5 path is bf16 LoRA not 4-bit; T4 cannot do bf16.
- Do not push another LR-only B.

## cpt-v2-one-doc-padded

Continued CPT v2 from the v12 handoff without running C or merging. Implemented pack_one_doc_padded as the generator default (one doc or 2048 window per row), GDN LoRA on the padded path, and GPU_PROFILE t4/ampere. Tests pass; notebooks regenerated and not pushed.

- Default PACKING_MODE is one_doc_padded (never concat two docs) because isolated pack still leaks GDN state.
- PAD_TO_MAX=False so T4 batch-1 does not feed pad tokens if GDN ignores attention_mask.
- GDN LoRA in_proj_qkv/in_proj_z/out_proj on padded path only; never in_proj_a/b.
- GPU_PROFILE t4 vs ampere switch for 4-bit vs bf16 LoRA. Did not push Kaggle, run C, or merge.

## cpt-v2-b-v13-push

Continued CPT v2 from handoff: verified local one_doc_padded generator/tests, pushed B kernel v13 to Kaggle (T4). D1/D2 PASS — 10779 rows from 8162 docs, multi_doc_rows=0; MAX_STEPS stayed 476/674. Training started. Poller watching eval_spurgeon. No C, no merge.

- Pushed one_doc_padded B as v13 (not another LR-only/stream B)
- Did not run C or merge
- D1/D2 human gate passed with multi_doc_rows=0 before training continued

- `continued_pretrain/kaggle/_poll_b_v13.py`
- `continued_pretrain/kaggle/b_logs_v13_raw.txt`

<!-- memory-fabric:store/episodic/2026-08-29 -->
---
store_path: episodic/2026-08-29
title: "Episodic Journal — 2026-08-29"
summary: "Terminated SFT Phase B dry-run pod 47zu29u0yth5a3 (sft-phase-b-dry); list-pods is empty and CPT S6 volume 7hb931c5oe was left untouched"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-29T19:20:47-04:00"
---

## sft-mix-v2-pod-kill

Terminated SFT Phase B dry-run pod 47zu29u0yth5a3 (sft-phase-b-dry); list-pods is empty and CPT S6 volume 7hb931c5oe was left untouched. Built qa_mix_v2 locally: 2923/153/100 train/val/test with 11.9% train refusals and sermon-header multi-chunk contexts matching serve k=4. Packaged spurgeon-qa-mix-v1.zip and 13_sft_local_readiness PASS. No GPU training started.

**Key decisions:**
- Terminated dry-run pod via MCP delete-pod; did not touch volume 7hb931c5oe.
- v2 mix rewraps existing QA into format_context multi-chunk headers (k weighted to 4) instead of a new teacher API set.
- Refusals synthesized by pairing questions with unrelated sermon chunks to hit 10-15% train.
- D_sota tokenizer is AutoTokenizer.from_pretrained, not FastLanguageModel.get_tokenizer.

**Files changed:**
- `fine_tuning/kaggle/sft_phase_b_session.json`
- `fine_tuning/scripts/build_qa_mix_v2.py`
- `fine_tuning/data/qa_mix_train.jsonl`
- `fine_tuning/data/qa_mix_val.jsonl`
- `fine_tuning/data/qa_test_frozen.jsonl`
- `fine_tuning/data/qa_mix_manifest.json`

## session-end-handoff

Saved next-session handoff. CPT S6 incomplete on volume 7hb931c5oe. SFT mix v2 ready (serve-shaped, 11.9% refusals). No pods running. Continue from fine-tuning/next-session-handoff.

- Killed SFT dry-run pod before training; mix must match app before GPU
- qa_mix_v2 is current SFT data; keep Hub v2; S6 B resume later from checkpoint-2100


## cpt-ollama-smoke-test

Created Ollama model `spurgeon-cpt` from `continued_pretrain/models/unsloth.F16.gguf` using the existing Modelfile. Ran CPT probe smoke test (9 prompts: style, doctrine, forgetting) — all PASS, no vocab-shift corruption (pist/spep). Added `continued_pretrain/scripts/smoke_test_ollama_cpt.py` for repeatable testing.

- Used existing local GGUF at continued_pretrain/models/unsloth.F16.gguf rather than exporting fresh from LoRA
- Ollama model name: spurgeon-cpt

- `continued_pretrain/scripts/smoke_test_ollama_cpt.py`

## qa-gold-rewrite-pilot

Built a 20-row gold assistant rewrite of qa_mix_v2 train examples (16 answerable, 4 refusal, seed 3407). Mechanical review passed: citations match headers and answerable quotes appear in CONTEXT. Training mix and Kaggle zip were left unchanged.

- Pilot is review gold only; did not replace qa_mix or the Kaggle zip.
- Rewrite assistant only; quotes must be substrings of that row's CONTEXT.
- Pilot-11 dropped the original Lord's Table claim because it is not in the v2 context.

- `fine_tuning/scripts/sample_qa_rewrite_pilot.py`
- `fine_tuning/scripts/write_qa_gold_rewrite.py`
- `fine_tuning/scripts/review_qa_gold_rewrite.py`
- `fine_tuning/data/qa_rewrite_pilot/sample.json`
- `fine_tuning/data/qa_rewrite_pilot/qa_gold_rewrite_pilot.jsonl`
- `fine_tuning/data/qa_rewrite_pilot/pilot_manifest.json`

## qa-gold-merge-handoff

Merged the 20 gold rewritten assistants into qa_mix_train.jsonl and rebuilt the Kaggle zip. Readiness still PASS. Scaffolded OpenRouter/Groq bulk rewrite plus review/merge scripts for the next session; no teacher API and no GPU this turn.

- Merged 20 gold assistants into train only; val and frozen test unchanged.
- Bulk teacher defaults to dry-run; next session must pass --apply with an API key.
- Bulk writes bulk_pending.jsonl and is merged only after mechanical review.

- `fine_tuning/scripts/merge_qa_gold_rewrite.py`
- `fine_tuning/scripts/rewrite_qa_answers_teacher.py`
- `fine_tuning/scripts/qa_rewrite_checks.py`
- `fine_tuning/scripts/review_qa_rewrite_bulk.py`
- `fine_tuning/scripts/merge_qa_bulk_rewrite.py`

## qwen35-sft-special-tokens

Locked the Qwen3.5-4B SFT special-token contract: ChatML turn stop is im_end (248046), native eos/pad stay endoftext (248044) and vision_pad (248055). Audited the tokenizer, regenerated D/E/F with processor unwrap, S3 label checks, and Seq2Seq collator, and fixed the Ollama Modelfile.

- Do not set tokenizer.eos_token to im_end; generate with eos_token_id=[im_end, endoftext].
- Base has no chat_template — inject plain ChatML, not Instruct thinking/vision jinja.
- Never assert len(tokenizer)==vocab_size on Qwen3.5 (added specials make len larger). Native pad is vision_pad 248055.

- `fine_tuning/scripts/audit_qwen35_special_tokens.py`
- `fine_tuning/data/qwen35_special_token_audit.json`

## sft-handoff-save

Persisted the Qwen3.5 SFT special-token contract as complete and rewrote fine-tuning/next-session-handoff so the next session starts on bulk QA rewrite (limit 50), then optional stock-base D→E→F. CPT S6 remains incomplete on volume 7hb931c5oe and must not share an SFT pod.

- Default next-session track is bulk QA rewrite (limit 50) then optional stock-base D/E/F; CPT S6 resume is a separate operator pick.
- Special-token contract is complete — do not re-audit unless tokenizer source changes.

- `fine-tuning/next-session-handoff`
- `fine-tuning/qwen35-sft-special-tokens`

## sft-track-a-batch1

Completed SFT Track A batch 1: teacher dry-run, Groq apply for 50 rows (24 ok merged), repackaged zip, readiness PASS. Fixed decommissioned teacher model defaults and Windows UTF-8 print crash. GPU dry-run prep complete but not started (awaiting operator go).

- Used Groq openai/gpt-oss-120b after OpenRouter free slugs and Groq llama-3.3-70b-versatile both 404/decommissioned
- Merged 24/50 passing bulk rows; 26 dropped on quote/citation/refusal contract
- GPU D→E→F remains gated on explicit operator approval

- `fine_tuning/data/qa_rewrite_pilot/bulk_pending.jsonl`

## sft-ready-handoff

Persisted ready-to-continue handoff for SFT Track A: batch 1 done (24/50 merged), Spurgeon-only QA decision, next commands for bulk resume or gated GPU dry-run.

- SFT QA main mix stays Spurgeon-only; CPT is the multi-writer stage
- Next session default = continue Groq bulk rewrite; GPU still operator-gated

- `.ai-memory via memory-fabric: fine-tuning/next-session-handoff, fine-tuning/qa-mix-spurgeon-only-decision, fine-tuning/sft-track-a-batch1-complete`

## knowledge-not-persona

Replaced the Spurgeon persona contract with a knowledge-assistant prompt (depth plus a light register, no vocatives or preacher roleplay). Remapped ~3k jsonl system messages, rewrote 20 gold assistants, locally passed 24 bulk rows, stripped 448 leading vocative prefixes, regenerated D/E/F SOTA notebooks, and rebuilt the Kaggle zip. Readiness PASS; GPU still blocked.

- Live chat is a knowledge Q&A assistant over Spurgeon and Puritan texts, not Spurgeon-as-character.
- Groq and SFT share SPURGEON_SFT_SYSTEM_PROMPT; SYSTEM_PROMPT_NEUTRAL is an alias.
- Do not rebuild qa_mix_v2; remap systems and rewrite 44 style-teacher rows.
- Puritans are a source class in the prompt; RAG stays sermons-only until indexed.
- Groq bulk --rerun-ok hung; 24 bulk rows got a local vocative/roleplay pass instead of a full teacher rewrite.

- `config.py`
- `utils/prompts.py`
- `app.py`
- `fine_tuning/scripts/remap_qa_mix_system_prompt.py`

## dream-split-tool

Ran Memory Fabric deep dream via Cursor split-tool: prepare_dream_payload, client consolidation of high-signal sections, apply_dream_results (apply=True). Promoted Ask Spurgeon architecture, tombstoned OPC UA contamination, stubbed pending map-notes, slimmed S6 interrupted pointer, refreshed SFT handoff/debt. Index regenerated (ask-spurgeon-rag + handoffs present).

- Split-tool dream used this chat model instead of Ollama/Gemini
- Partial consolidation only (8 files) because full 230k prompt is too large for one pass
- OPC UA store entry marked contamination for human delete
- Ollama provider disabled during apply to avoid broken host/model summary loops

- `.ai-memory/debt.md`
- `.ai-memory/memory-store/architecture/ask-spurgeon-rag.md`
- `.ai-memory/memory-store/architecture/map-notes-pending-review.md`
- `.ai-memory/memory-store/architecture/opcua-scada-simulation-platform.md`
- `.ai-memory/memory-store/decisions/map-notes-pending-review.md`
- `.ai-memory/memory-store/fine-tuning/next-session-handoff.md`
- `.ai-memory/memory-store/fine-tuning/qa-knowledge-not-persona.md`
- `.ai-memory/memory-store/pretraining/cpt-v3-s6-interrupted.md`
- `.ai-memory/memory-store/index.md`

## dream-followups-cleanup

Completed dream follow-ups: dropped+deleted map-notes stubs and OPC UA contamination; fixed .env OLLAMA_HOST (no inline comment), unset Dream ollama provider, pointed OLLAMA_MODEL at installed spurgeon-cpt; deleted three superseded S5 CPT stubs; light dream --apply refreshed indexes.

- Dropped (not re-promoted) map-notes stubs because content already lived in ask-spurgeon-rag and granular decisions
- Disabled MEMORY_FABRIC_LLM_PROVIDER=ollama for Dreaming; kept OLLAMA_MODEL=spurgeon-cpt as installed local only
- Deleted three superseded S5 CPT stubs as light clutter pass

- `.env`
- `.ai-memory/memory-store/pretraining/cpt-corpus-v3-s5-b-running.md`
- `.ai-memory/memory-store/pretraining/cpt-corpus-v3-s5-c-ready.md`
- `.ai-memory/memory-store/pretraining/cpt-corpus-v3-s5-handoff.md`

## cpt-deep-dream-clutter

Ran CPT clutter deep dream (split-tool): added cpt-current, stubbed old v2/s2-s4 handoffs, refreshed future-checklist, deleted five superseded paste/preflight notes, light dream regenerated index.

- Added pretraining/cpt-current as single live CPT pointer
- Deleted stale continue-mode paste handoffs that contradicted HF resume + CPT_RUN_MODE=fresh

- `.ai-memory/memory-store/pretraining/cpt-current.md`
- `.ai-memory/memory-store/pretraining/cpt-future-checklist.md`
- `.ai-memory/memory-store/pretraining/cpt-v3-next-session-handoff.md`
- `.ai-memory/memory-store/pretraining/cpt-s6-continue-b-run-handoff.md`

## qa-sources-rewrite

Implemented QA audit + multi-source rewrite plan: Phase 0 harden (vocatives, teacher timeouts/429 abort, audit GATE), Phase 1 multi-provider teachers + batches (Groq/OpenRouter) raising quote coverage ~4.3%→9.0% and unique teacherish to 93, Phase 2 Puritan Catechism CONTEXT slice + Chroma ingest + merge (90 rows). Fixed bulk merge double-count. Free quotas exhausted (Groq TPD, OpenRouter 50 RPD); continue toward 400 teacherish when Gemini key or quota reset. Zip rebuilt; readiness PASS; no GPU.

- OpenRouter default openrouter/free or nemotron:free (classic :free slugs often 404)
- merge_qa_bulk_rewrite uses unique bulk_source_lines
- Catechism merge only after Chroma ingest; dedupe by Q.N+QUESTION
- No GPU until quote gate + operator go

- `fine_tuning/scripts/audit_qa_mix_quality.py`
- `fine_tuning/scripts/ingest_catechism.py`
- `fine_tuning/scripts/build_catechism_qa_slice.py`
- `fine_tuning/scripts/merge_catechism_qa_slice.py`

## qa-bulk-rewrite-smoke-retry

Retried Gemini smoke with updated API key — key works (no auth errors) but 0/3 passed quote validation. Cerebras smoke 1/3 (below ≥2/3 bar). Did not launch new bulk batches per stop/go protocol. Merged 79 pending bulk rows (6 new unique answers) through review→merge→12_package→audit→13_sft_local_readiness. Metrics: quote 9.1% (243/2657), teacherish 99, caricature 0. Gates not met; keep rewriting.

- Held bulk batches until smoke ≥2/3 — both providers below bar
- Merged accumulated pending ok rows from prior interrupted Gemini batch


## qa-quote-fidelity-prompt-fix

Strengthened TEACHER_SYSTEM rule 5 for verbatim CONTEXT quote copy-paste with BAD/GOOD examples. Re-smoke: Gemini 0/3, Cerebras 2/3 (pass). Ran Cerebras batch 50 (22 ok), merged 24 new answers; quote coverage rose 9.1%→9.8%, teacherish 99→123, caricature 0; 13_sft PASS. Gates still below 10% quote threshold.

- Use Cerebras not Gemini for bulk quote rewrites
- Do not weaken qa_rewrite_checks validation — fix prompt instead

## qa-bulk-rewrite-session4

Ran two Cerebras bulk QA rewrite batches (50 rows each). Batch 1: 29/50 ok (58%); batch 2: 28/50 ok (56%). Merged 57 new answers total. Quote coverage crossed the 10% gate: 9.8% → 11.5% (306/2657). Teacherish rose 123 → 180. Caricature remains 0. Full pipeline (review, merge, package, audit, readiness) passed after each batch. Did not run build_qa_mix_v2 or GPU per operator hold.

- 10% quote gate now met at 11.5% — continue batches toward 15% before GPU
- Cerebras gpt-oss-120b remains primary provider; Gemini still unsuitable
- No build_qa_mix_v2 or GPU D→E→F without explicit operator go

## qa-rewrite-session-5

Fixed Cerebras gpt-oss 'content' KeyError on dataset row 307 by adding robust _extract_chat_content() response parsing with retry. Ran 3 Cerebras batches (50 each): 82 new ok rows merged. Quote coverage rose 11.5%→14.0% (373/2656); teacherish 180→262; caricature stayed 0. Line 307 no longer API-fails. 13_sft_local_readiness PASS.

- Parse content/text/reasoning/legacy text from OpenAI-compatible responses instead of direct ['content'] access
- Retry on bad response shape rather than aborting immediately

<!-- memory-fabric:store/episodic/2026-08-30 -->
---
store_path: episodic/2026-08-30
title: "Episodic Journal — 2026-08-30"
summary: "Resolved parallel Groq+Cerebras rewrite conflict: stopped Cerebras, let Groq finish, deduped bulk_pending.jsonl (648→637, 11 dupes removed), re-ran full pipeline"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-30T16:13:10-04:00"
---

## qa-rewrite-15pct-gate-dedupe

Resolved parallel Groq+Cerebras rewrite conflict: stopped Cerebras, let Groq finish, deduped bulk_pending.jsonl (648→637, 11 dupes removed), re-ran full pipeline. 15% quote gate now met at 15.6% (415 quoted answerable); teacherish 320, caricature 0. Established one-provider-at-a-time rule for --apply.

**Key decisions:**
- One provider at a time on rewrite --apply (no file locking on bulk_pending.jsonl)
- Groq primary while Cerebras daily quota resets
- 15% quote gate met — GPU still on operator hold

**Files changed:**
- `fine_tuning/data/qa_rewrite_pilot/bulk_pending.jsonl.bak.20260830T004257Z`

## qa-bulk-rewrite-session-6

Ran 2 Cerebras bulk QA rewrite batches (batch 2 partial due to daily token quota). Batch 1: 26/50 ok (52%). Batch 2 hit token_quota_exceeded mid-run; 33 new ok rows accumulated and merged. Quote gate crossed at 416/2655 (15.7%). Teacherish rose to 321 (79 short of ≥400 target). Caricature remains 0. Pipeline review→merge→12_package→audit→13_sft all PASS.

- 15% quote coverage gate now met (15.7%)
- Cerebras daily token quota is new blocker; resume when quota resets


## qa-bulk-groq-session6

Switched bulk QA rewrites from exhausted Cerebras to Groq. Smoke passed 2/3. Ran two partial Groq batches (120b then 20b); both hit TPD 200k limit. Merged 28 new answers; 15% quote gate met at 15.7%; teacherish rose to 321. Both Groq models and Cerebras exhausted for today.

- Groq gpt-oss-120b primary; fall back to 20b on TPD
- Cerebras remains blocked until daily reset
- 15% quote gate considered met; shift focus to teacherish ≥400

## qa-rewrite-handoff

Persisted QA rewrite pipeline state for cross-session resume. Quote coverage gate MET at 15.8% (419/2655); teacherish at 324 (gold 20 + bulk 304 unique), ~76 short of ≥400 target. Caricature 0, SFT readiness PASS, 3013 train rows. Resume from line 649 in qa_mix_train.jsonl. Documented provider status (Groq 120b TPD exhausted, 20b available), batch commands, hard operational rules, and stop/go gates in memory handoff files.

- Quote ≥10% gate considered MET at 15.8% — can focus on teacherish count
- ONE provider at a time on --apply to avoid bulk_pending.jsonl dupes
- Do NOT run build_qa_mix_v2.py or GPU D→E→F until operator explicitly approves
- Groq 120b preferred after ~3 AM ET reset; Groq 20b usable now at ~30% pass rate
- TEACHER_SYSTEM rule 5 strengthened for verbatim quote fidelity


## qa-rewrite-teacherish-gate

Continued bulk QA rewrite from train line 649. Groq 120b then 20b both hit TPD; Cerebras completed two batches (31/50 and 24/50). Teacherish gate MET at 401 (gold 20 + bulk 381). Quote coverage 18.0% (478/2655), caricature 0, SFT readiness PASS. Zip rebuilt. Next unprocessed line 803 if operator wants more lift; GPU still needs explicit go.

- Stopped Groq 120b/20b as soon as TPD retries started (do not burn 45s x4 per row).
- Switched remaining work to Cerebras after both Groq models exhausted TPD.
- Did not run build_qa_mix_v2.py or GPU D-E-F (operator hold).

## qa-rewrite-continue-providers

Continued optional QA rewrite lift from line 803. Teacherish rose 401→489; quote 18.0%→20.2%. Cerebras and both Groq models hit daily quotas. OpenRouter ~12% pass; Gemini smoke 3/5 still usable. Merged zip rebuilt; resume at line 1008.

- Used Cerebras then Groq then OpenRouter then Gemini as quotas exhausted.
- Stopped Groq TPD retry loops rather than burning wall clock.
- Did not start GPU or build_qa_mix_v2.

## qa-rewrite-gemini-openrouter

Continued QA rewrite with Gemini (6 OK then quota) and two OpenRouter batches (12+17 OK). Teacherish 489→524; quote 20.7%; resume line 1125. Cerebras/Groq/Gemini all quota-exhausted; OpenRouter still available.

- Gemini exhausted mid-batch; switched to OpenRouter as sole remaining cloud teacher.
- Did not run GPU or build_qa_mix_v2.

## qa-rewrite-openrouter-continue

Continued QA rewrite with OpenRouter only (other providers still quota-exhausted). Two batches: 15/50 + 14/50 OK. Teacherish 524→553; quote 20.7%→21.5%; bulk 504→533. Resume line 1226. Zip rebuilt; SFT readiness PASS.

<!-- memory-fabric:store/episodic/2026-08-31 -->
---
store_path: episodic/2026-08-31
title: "Episodic Journal — 2026-08-31"
summary: "Verified live QA mix against serve contract and F5 targets"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-31T16:42:41-04:00"
---

## qa-prompt-strategy-verify

Verified live QA mix against serve contract and F5 targets. Gates green (quote 21.5%, teacherish 553, caricature 0, readiness PASS); one canonical system prompt everywhere. Locked decision: diversify task slices (catechism short at 3%, multi-turn missing), not multiple prompts. Documented overlay-safe builder plan for catechism expansion and new multi-turn slice.

**Key decisions:**
- Do not train multiple system prompts or user wrappers for SFT.
- Improve via task slices under one serve contract: catechism to ~8%, then multi-turn 2–5%.
- Catechism/multi-turn adds must be overlay-safe side-JSONL + append merge — never build_qa_mix_v2 wipe.

**Files changed:**
- `.ai-memory/memory-store/fine-tuning/qa-prompt-strategy-verify.md`
- `.ai-memory/memory-store/fine-tuning/qa-prompt-type-decision.md`
- `.ai-memory/memory-store/fine-tuning/qa-overlay-safe-slice-builders.md`

## qa-slice-expansion

Implemented overlay-safe catechism expansion (+151 variants → 241/7.4%) and new multiturn slice (100/3.1%). Audits green (quote 27.9%, refusal ~11%, readiness PASS); Kaggle zip repackaged. Still no GPU.

- Expanded catechism via QUESTION phrasing variants under one system prompt (7.4%).
- Added 100 multiturn rows mirroring build_chat_messages (bare history + CONTEXT follow-up).
- Append-only merges only; no build_qa_mix_v2 wipe.

- `fine_tuning/scripts/build_multiturn_qa_slice.py`
- `fine_tuning/scripts/merge_multiturn_qa_slice.py`
- `fine_tuning/data/qa_catechism_variants.jsonl`
- `fine_tuning/data/qa_multiturn_slice.jsonl`

## qa-rewrite-continue

Continued QA teacher rewrite pipeline from line 1226. Processed through 1338 via OpenRouter (16 ok) and Groq 20b (6 ok). Merged 37 new answers into train; quote coverage rose to 28.7%, teacherish to 586. OpenRouter free daily limit exhausted; Groq 20b still usable with rate limits. Repackaged Kaggle zip.

- Continued teacher rewrite from line 1226; OpenRouter daily limit hit mid-batch.
- Groq 20b used as fallback with 429 backoff.
- Merged +37 new ok answers; quote 28.7%, teacherish 586.


## qa-rewrite-1506-1596

Continued QA teacher rewrite with Cerebras from line 1506 through 1596 (3×30 batches). Merged ~74 new answers; quote coverage rose to 32.4%, teacherish to 724. Kaggle zip repackaged. Resume at line ~1597.

- Continued Cerebras teacher rewrite from line 1506 through 1596.
- Three batches (~53 ok / 37 drop); quote 31.0% → 32.4%, teacherish 724.

- `fine_tuning/data/kaggle_upload/spurgeon-qa-mix-v1-new.zip`

## qa-rewrite-multi-provider

Continued QA rewrite from line 1597 using Groq, OpenRouter, Gemini, and Cerebras. Merged ~36 new answers; quote 33.3%, teacherish 760. Groq/OpenRouter/Gemini hit daily limits; Cerebras remains the best yield. Resume ~1697.

- Rotated providers: Groq TPD, OpenRouter daily free limit, Gemini quota, Cerebras still best.
- Killed stuck Groq/Gemini 429 retry loops to avoid burning time.

<!-- memory-fabric:store/episodic/2026-09-01 -->
---
store_path: episodic/2026-09-01
title: "Episodic Journal — 2026-09-01"
summary: "Verified QA teacher rewrite resume point (line 1786 per handoff, confirmed live)"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-01T12:09:52-04:00"
---

## qa-rewrite-verify-continue

Verified QA teacher rewrite resume point (line 1786 per handoff, confirmed live). Ran Cerebras batch lines 1786–1815: 13 ok / 17 dropped. Review PASS, merged +13 unique bulk answers. Quote 34.5%→34.9%, teacherish 805→818. Next line 1816.

**Key decisions:**
- Continued with Cerebras as best-yield provider despite 429 backoff

**Files changed:**

## qa-rewrite-continue-2batches

Continued QA teacher rewrite with two Cerebras batches (1816–1875). Each batch 16 ok / 14 dropped. Merged +32 unique bulk answers. Quote 34.9%→35.5%, teacherish 818→846. Next line 1876.

## qa-rewrite-multi-provider-rotation

Built rewrite_qa_rotate_providers.py and ran full provider rotation. Cerebras lifted quote to ~40% then token quota; groq/openrouter/gemini exhausted but groq-20b still sporadic in round 2. Fixed Unicode print crash and Windows merge PermissionError with retries. Bulk merged ~1106, quote ~42.6%, teacherish ~1126.

- Multi-provider rotation via rewrite_qa_rotate_providers.py
- Skip cerebras after token_quota; resume groq/openrouter/gemini

- `fine_tuning/scripts/rewrite_qa_rotate_providers.py`

<!-- memory-fabric:store/episodic/2026-09-02 -->
---
store_path: episodic/2026-09-02
title: "Episodic Journal — 2026-09-02"
summary: "Saved QA rewrite stop point to memory: pass 1 complete (3244/3244 attempted), 1466 ok / 1778 drops remaining for --retry-drops, 1465 bulk merged, quote 49.1%, teacherish 1485"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-02T18:43:32-04:00"
---

## qa-rewrite-stop-point-memory

Saved QA rewrite stop point to memory: pass 1 complete (3244/3244 attempted), 1466 ok / 1778 drops remaining for --retry-drops, 1465 bulk merged, quote 49.1%, teacherish 1485. Documented SFT vs continue-rewrite tradeoffs and resume commands.

**Key decisions:**
- Pass 1 QA rewrite complete; pass 2 retry-drops paused at 1778 drops
- Dry-run SFT unblocked; rewrite is optional optimization
- Final CPT-merged SFT waits S6 + operator go

**Files changed:**

## qa-rewrite-pass2-continue

Continued Pass 2 QA teacher rewrite (`--retry-drops`). Ran OpenRouter batch (3/15 ok) plus background multi-provider rotation (openrouter,gemini,cerebras,groq, max-rounds 3). Merged new ok rows through review→merge→audit pipeline. Teacherish rose 1492→1537, quote coverage 49.3%→50.8%, bulk merged 1472→1517. 1741 drop rows remain. SFT readiness PASS. Background rotation still running on cerebras.

- Continue Pass 2 retry-drops for optional lift despite gates already met
- Prefer OpenRouter when available; Cerebras steady; Groq rate-limited

- `fine_tuning/data/qa_rewrite_pilot/rotate_session_log.txt`

## qa-rewrite-memory-save

Saved QA rewrite state to memory. Pass 2 retry-drops in progress: teacherish 1559 (bulk 1539 + gold 20), quote 51.5%, 1510 ok / 1734 drops in bulk_pending, 1539 bulk merged into train. Background rotation still running on Cerebras. SFT readiness PASS; dry-run unblocked. Repackage zip before Kaggle upload.

- Pass 2 retry-drops continues as optional lift; all SFT gates met
- OpenRouter preferred for retry pass rate; Groq rate-limited

## runpod-sft-gate0-impl

Implemented full RunPod SFT GATE-0 orchestration: merge_cpt_lora.py, train_sft_sota.py, eval_sft_sota.py, sft_* PowerShell/bash stack, RUNPOD_RUNBOOK_SFT.md, capacity watcher. Local prep PASS. GPU merge/train blocked on US-IL-1 capacity (no 4090/A6000/L40S instances); capacity watcher deployed.

- Detached Python scripts over Jupyter for RunPod billing safety
- Hub v2 LoRA isolated at theology_cpt_lora_hub_v2 to protect CPT S6 volume paths
- GPU fallback order: 4090 → A6000 → L40S in US-IL-1

- `fine_tuning/scripts/merge_cpt_lora.py`
- `fine_tuning/scripts/train_sft_sota.py`
- `fine_tuning/scripts/eval_sft_sota.py`
- `fine_tuning/scripts/sft_*.ps1`
- `fine_tuning/scripts/sft_*.sh`
- `fine_tuning/scripts/sft_*.py`
- `fine_tuning/RUNPOD_RUNBOOK_SFT.md`

## memory-save-runpod-sft

Saved RunPod SFT GATE-0 implementation memories: expanded runpod-sft-gate0-implementation, updated next-session-handoff with RunPod as primary next step, added runpod-sft-gate0-decisions. GPU merge/train still blocked on US-IL-1 capacity; sft_watch_capacity.py running.

- RunPod SFT GATE-0 orchestration complete; GPU blocked US-IL-1 capacity
- Detached scripts over Jupyter; Hub v2 LoRA isolated from CPT S6 paths
- Capacity watcher polls 4090→A6000→L40S every 600s

- `fine_tuning/scripts/sft_*`
- `.ai-memory/memory-store/fine-tuning/runpod-sft-gate0-implementation.md`

## sft-gate0-readiness

Revised SFT GATE-0 readiness. Local mix/quality/orchestration PASS after repacking the QA zip. Found two launch blockers (private Hub v2 LoRA with no HF_TOKEN on the pod; merge preflight failing before download) and fixed them. Duplicate capacity watchers were killed and replaced with one 600s watcher. Training still waits on US-IL-1 GPU capacity.

- GATE-0 SFT is data-ready; GPU blocked on US-IL-1 + volume 7hb931c5oe.
- Hub v2 LoRA is private so HF_TOKEN must be injected into the pod env.
- Merge preflight must download the adapter before the existence/SHA check.
- Keep a single 600s capacity watcher on .venv Python 3.13.

- `fine_tuning/scripts/sft_provision_pod_mcp.py`
- `fine_tuning/scripts/sft_provision_pod.ps1`
- `fine_tuning/scripts/sft_runpod_common.ps1`
- `fine_tuning/scripts/sft_start_capacity_watch.ps1`

## sft-stop-token-phases

Completed phased stop-token verification for SFT v2: added STOP_TOKEN_PHASES.md runbook, integrated stop metrics into eval_sft_sota.py and smoke_test_ollama.py, S3 audit in train_sft_sota.py, phases 0-1 in 13_sft_local_readiness.py, pod sync/merge wiring for phase 2, Modelfile endoftext stop. Local phases 0-1 PASS.

- Stop-token gates split into phases 0-5 with explicit pass criteria
- Modelfile adds <|endoftext|> as secondary stop for Ollama serve
- Phase 2 auto-runs after GATE-0 merge on pod unless SFT_SKIP_STOP_PHASE2=1

- `fine_tuning/STOP_TOKEN_PHASES.md`
- `fine_tuning/scripts/sft_stop_token_utils.py`
- `fine_tuning/scripts/verify_sft_stop_tokens.py`
- `fine_tuning/scripts/sft_sync_to_pod.ps1`
- `fine_tuning/scripts/sft_remote_merge.sh`

## sft-usil1-live-run

US-IL-1 RTX 4090 pod k7s2a1cyr0cpp8 provisioned; GATE-0 merge completed on volume. Hardened capacity watcher for billing (no idle pods, local artifact fetch, monitor deletes pod on completion). Fixed HF_TOKEN injection; SFT train launching on pod with monitor PID 14072.

- Idle pod auto-delete after 20min without GPU work
- HF_TOKEN via /workspace/.sft_env for non-interactive SSH
- Phase 2 stop probe warn-only before SFT
- Local artifact fetch includes GATE-0 merge when complete

- `fine_tuning/scripts/sft_watch_capacity.py`
- `fine_tuning/scripts/sft_pod_lifecycle.py`
- `fine_tuning/scripts/sft_fetch_artifacts.ps1`
- `fine_tuning/scripts/sft_inject_hf_token.ps1`
- `fine_tuning/scripts/sft_remote_train.sh`
- `fine_tuning/scripts/sft_launch_train.ps1`
- `fine_tuning/scripts/sft_monitor_until_done.py`

## sft-hf-inject-fix

Fixed SFT HF token inject (huggingface_hub timing + PowerShell $ escaping). Fixed session JSON BOM. Repackaged QA zip. Restarted capacity watcher; pod gt5ureujk6c8dh provisioned, inject passed, train_sft_sota.py running with monitor active.

- HF inject verifies via remote Python urllib, not huggingface_hub or curl through PowerShell
- Orchestrate failure force-deletes idle GPU pod immediately

<!-- memory-fabric:store/episodic/2026-09-04 -->
---
store_path: episodic/2026-09-04
title: "Episodic Journal — 2026-09-04"
summary: "Saved Vultr SFT planning for next session: API key present but IP-allowlisted (401 on 159.26.98.242); cheapest usable GPU with stock is A16 32GB blr (~$0.94/hr); SFT resume still needs torch/trl fix; "
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-04T08:44:01-04:00"
---

## vultr-sft-planning-memory

Saved Vultr SFT planning for next session: API key present but IP-allowlisted (401 on 159.26.98.242); cheapest usable GPU with stock is A16 32GB blr (~$0.94/hr); SFT resume still needs torch/trl fix; CPT LoRA available locally/Hub. Updated next-session-handoff to prioritize Vultr.

**Key decisions:**
- Continue GATE-0 SFT planning on Vultr next session using existing credits
- Recommended Vultr plan: vcg-a16-12c-128g-32vram until A40 24GB stock returns
- Agent cannot provision until Vultr API IP allowlist is updated

## vultr-sft-impl

Implemented the Vultr GATE-0 merge+SFT runbook and thin orchestration (provision/sync/launch/fetch/destroy), plus torch 2.11 ScalingType smoke and CPU PEFT merge fallback. Local readiness passed after repacking the QA zip. Live provision did not start: Vultr API still returns 401 Unauthorized IP for 159.26.98.242 after 45+90 minute waits. Next step is allowlist that IP or pass -SshHost from a console VM, then run vultr_orchestrate.ps1.

- One Vultr A16 VM for merge+SFT; treat as 2x16GB not 32GB contiguous
- Pin torch 2.11 and smoke ScalingType before billed train
- CPU PEFT merge fallback on GPU OOM
- Destroy instance after fetch; do not stop

**Files changed:**
- `fine_tuning/VULTR_RUNBOOK_SFT.md`
- `fine_tuning/scripts/vultr_orchestrate.ps1`
- `fine_tuning/scripts/vultr_common.ps1`
- `fine_tuning/scripts/sft_remote_setup.sh`

## vultr-gate0-blocked

Vultr GATE-0 path is script-complete (orchestrate, torch 2.11 setup smoke, CPU merge fallback, A16 env, readiness PASS) but live provision never started. Vultr API still 401 Unauthorized IP for 159.26.98.242 after 45m+90m waits; post-subagent probe confirmed still blocked. No GPU instance billed.

- Do not leave idle Vultr GPU; destroy when done
- Treat A16 32vram as 2x16GB; CUDA_VISIBLE_DEVICES=0 BATCH=1 GRAD_ACCUM=16
- Operator must allowlist agent IP or pass -SshHost after console create

- `fine_tuning/scripts/vultr_*.ps1`

## vultr-spend-risk

Documented Vultr GATE-0 spend risk controls in memory (fine-tuning/vultr-spend-risk-controls) and planted the same rules in VULTR_RUNBOOK_SFT.md: one short-lived GPU, destroy on fail/done, 8h wall, modest limit request, expected $8-12 run cost.

- Limit increase is a ceiling only; pay hourly for live GPU
- Mandatory destroy on fail/done; 8h wall; one VM; expect ~$8-12 GATE-0

- `.ai-memory/memory-store/fine-tuning/vultr-spend-risk-controls.md`

<!-- memory-fabric:store/episodic/2026-09-05 -->
---
store_path: episodic/2026-09-05
title: "Episodic Journal — 2026-09-05"
summary: "Operator completed Vast.ai setup: $6 credit, VAST_API_KEY + HF_TOKEN in .env, runpod_cpt SSH on account, vastai CLI in .venv"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-05T19:58:15-04:00"
---

## vast-setup-handoff

Operator completed Vast.ai setup: $6 credit, VAST_API_KEY + HF_TOKEN in .env, runpod_cpt SSH on account, vastai CLI in .venv. Dry-checked 4090 offers (~$0.22–0.37/hr). No GPU rented. Saved handoff at fine-tuning/vast-gate0-next-session for next session (runbook/scripts first, rent only on explicit approval).

**Key decisions:**
- Vast is the interim GATE-0 host while Vultr GPU locked ~30 days
- Do not rent until operator says go
- Next: VAST runbook + thin scripts, then merge+SFT under $6

**Files changed:**
- `.env (VAST_API_KEY added by operator)`

## vast-gate0-scripts

Implemented Vast.ai GATE-0 merge+SFT path: VAST_RUNBOOK_SFT.md, full vast_*.ps1 orchestration, vast_monitor_until_done.py (10h wall), and SFT_GPU_PROFILE=4090 in remote setup/train. Dry search showed ~$0.22/hr 4090s; local readiness PASS. No GPU rented.

- Reuse /workspace remote scripts with 4090 BATCH=2/ACCUM=8 (not Vultr A16)
- On-demand only; pytorch image + torch 2.11 setup; destroy not stop
- Rent blocked until operator says go

- `fine_tuning/VAST_RUNBOOK_SFT.md`
- `fine_tuning/scripts/vast_common.ps1`
- `fine_tuning/scripts/vast_orchestrate.ps1`
- `fine_tuning/scripts/vast_monitor_until_done.py`

## vast-gate0-go

Operator said go. Rented Vast 4090; first pytorch image hung on pull and was destroyed. Re-rented with nvidia/cuda:12.4.1-devel. Fixed destroy -y and launch pgrep bug. Setup/train is installing torch 2.11; monitor running. SSH: root@137.175.76.24:49025 with runpod_cpt key.

- Destroyed hung pytorch-image instance; switched to nvidia/cuda devel
- Fixed destroy -y and launch pgrep false positive
- GATE-0 running on instance 49992506

- `fine_tuning/scripts/vast_destroy.ps1`
- `fine_tuning/scripts/vast_launch.ps1`
- `fine_tuning/scripts/vast_wait_ssh.ps1`

## vast-gate0-setup-harden

Hardened sft_remote_setup.sh for nvidia/cuda images (ensure unzip + prefer apt python3.11 before 3.11–3.13 assert, fail-closed on 3.14). Updated vast_provision onstart best-effort and VAST_RUNBOOK notes. DefaultImage already nvidia/cuda:12.4.1-devel-ubuntu22.04. Confirmed instance 49992506 pipeline still running SETUP (torch pip install); no re-rent/destroy/restart.

- Prefer apt python3.11 on CUDA 3.10 bases; deadsnakes fallback; keep unzip in setup before qa zip extract
- DefaultImage already aligned with live nvidia/cuda image — docs/onstart only

- `fine_tuning/scripts/vast_provision.ps1`

<!-- memory-fabric:store/episodic/2026-09-06 -->
---
store_path: episodic/2026-09-06
title: "Episodic Journal — 2026-09-06"
summary: "Resumed Vast GATE-0 after instance 49991334 was destroyed on SSH timeout during pytorch image pull"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-06T19:33:39-04:00"
---

## vast-gate0-launch

Resumed Vast GATE-0 after instance 49991334 was destroyed on SSH timeout during pytorch image pull. Re-provisioned 49992506 on nvidia/cuda:12.4.1-devel-ubuntu22.04; SSH/nvidia-smi/sync/HF inject succeeded. Fixed Python 3.10 bootstrap in sft_remote_setup and relaunched after pgrep false-positive. CPT merge completed; train_sft_sota.py is running; vast_monitor_until_done.py started in background.

**Key decisions:**
- Default to smaller CUDA image (already in vast_common) instead of full pytorch pull
- Bootstrap Python 3.11+ on cuda Ubuntu images before torch/Unsloth install
- Keep single live instance 49992506; do not dual-rent

**Files changed:**
- `fine_tuning/kaggle/vast_sft_session.json`

## vast-gate0-trl-fix

Fixed Vast GATE-0 SFT TypeError (dataset_text_field on SFTTrainer under TRL 0.24/Unsloth). Synced train_sft_sota.py, relaunched on replacement instance 49999424 after monitor destroyed 49992506. Confirmed training past crash: SFTTrainer kwargs clean, S3 masking OK (8.0%), 408 steps started (PID 6727).

- TRL 0.24: dataset_text_field only on SFTConfig; never pass to SFTTrainer (Unsloth **kwargs forwards and crashes)
- Force eos/pad to <|endoftext|> to avoid Unsloth <EOS_TOKEN> TRL validation failure
- Drop messages column; keep ChatML text + train_on_responses_only
- After 49992506 monitor-destroy, relaunched on 49999424 with full setup+merge+train


Fixed TRL dataset_text_field TypeError and confirmed SFTTrainer construction + S3 masking on Vast 49999424. Training then segfaults (exit 139) at the first step — separate blocker. CPT merge is done on the replacement instance; monitor running.

- dataset_text_field only on SFTConfig for TRL 0.24+Unsloth
- Confirmed past TypeError via S3 masking OK
- First train step SIGSEGV is a separate Unsloth/CUDA/Vast issue

## vast-gate0-peft-unblock

Unblocked Vast GATE-0: diagnosed SIGSEGV (fractional GPU + Unsloth crash even on full 4090), destroyed bad hosts, provisioned Michigan full 4090 with CUDA 13.2, added SFT_BACKEND=peft path, and confirmed training past step 1 (1/408) with ~17GB VRAM. Restarted fixed vast_monitor_until_done.py.

- Prefer gpu_frac>=1 and cuda_max_good>=12.6 in Vast search
- GATE-0 on this Vast stack uses SFT_BACKEND=peft instead of Unsloth
- Monitor must not destroy on setup Tracebacks
- PEFT bf16 needs seq<=2048 batch=1 on 24GB for this model

- `fine_tuning/scripts/vast_inject_hf_token.ps1`

## vast-gate0-peft-followup

Health-checked Vast instance 50011937: train_sft_sota.py alive on PEFT at ~4/408 (~82s/it), loss not yet logged. Persisted PEFT defaults (peft/2048/1/16) in vast_inject_hf_token.ps1 and VAST_RUNBOOK_SFT.md; SearchQuery already had gpu_frac/cuda filters. Restarted local vast_monitor_until_done.py (train-log-only crash detection).

- Vast GATE-0 uses SFT_BACKEND=peft only (Unsloth SIGSEGVs even on full 4090)
- Persist peft + seq2048/batch1/accum16 in vast_inject_hf_token.ps1 for relaunches
- SearchQuery already requires gpu_frac>=1 and cuda_max_good>=12.6


## vast-sft-eval-oom-fix

Fixed GATE-0 SFT CUDA OOM at mid-train eval by forcing SFT_EVAL_STRATEGY=no and restarting PEFT training on instance 50011937. Train was idle-billing; now running again from step 0 (no prior checkpoint).

- Disable mid-train eval on Vast 24GB PEFT (SFT_EVAL_STRATEGY=no) to avoid OOM

## vast-gate0-eval-oom-relaunch

Vast GATE-0 SFT OOMed at step 20 during mid-train eval on instance 50011937 (idle GPU burn). Confirmed no checkpoints. Patched train_sft_sota.py to default SFT_EVAL_STRATEGY=no with eval batch 1 / empty_cache / checkpointing; synced and relaunched PEFT training fresh (merge already done). Monitor restarted. Training confirmed at step 2/408 ~85s/it ~17GB VRAM.

- Disable mid-train eval on 24GB @ seq 2048 (OOM in logits.float); keep peft/2048/batch1/accum16
- Do not destroy instance — idle burn fixed by relaunch; no resume checkpoint available

- `fine_tuning/scripts/_vast_oom_relaunch.sh`

## vast-idle-watch-15m

Added 15-minute Vast idle/GPU watchdog: checks train process + nvidia-smi util + step progress; one PEFT relaunch on unused/crash; destroy after ~30m still idle. Restarted monitor on 50011937 (healthy at step ~10, util 70%).

- 15-min idle GPU watchdog: one corrective relaunch then destroy (never stop) if unused

- `fine_tuning/scripts/vast_start_idle_watch.ps1`

## vast-sft-complete

Vast GATE-0 SFT finished 408/408 (loss~1.87). Fetched LoRA adapter + run config locally under vast_sft_gate0, destroyed instance 50011937, stopped idle monitors and 30m loop. Fixed vast_fetch paths for /kaggle/working outputs.

- GATE-0 SFT complete on Vast PEFT; fetch from /kaggle/working; destroy instance after fetch

- `fine_tuning/scripts/vast_fetch.ps1`
- `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_lora_v2/lora/`

## ollama-merge-deferred

User asked to defer local Ollama testing to next session. Confirmed path is merge SFT LoRA into CPT-merged HF → GGUF → ollama create (cannot load PEFT alone). Saved pending plan and next-session handoff in memory fabric; created Cursor goal for the merge/Ollama work.

- Defer merge/GGUF/Ollama to next session
- Document that Ollama requires merged GGUF, not raw LoRA
- Local CPT merge + SFT LoRA are sufficient inputs; F §5 export gate optional for local test

<!-- memory-fabric:store/episodic/2026-09-07 -->
---
store_path: episodic/2026-09-07
title: "Episodic Journal — 2026-09-07"
summary: "Provisioned Vast 50091768, remade CPT merge, PEFT-merged GATE-0 SFT LoRA into CPT base (after fixing CausalLM path bug), exported Q4_K_M GGUF, created local Ollama spurgeon-qa-v2, smoke_test_ollama.py"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-07T18:20:19-04:00"
---

## vast-sft-merge-ollama

Provisioned Vast 50091768, remade CPT merge, PEFT-merged GATE-0 SFT LoRA into CPT base (after fixing CausalLM path bug), exported Q4_K_M GGUF, created local Ollama spurgeon-qa-v2, smoke_test_ollama.py passed, destroyed instance.

**Key decisions:**
- Merge SFT LoRA on Vast with AutoModelForCausalLM (not ConditionalGeneration)
- Export Q4_K_M GGUF on Vast via Unsloth
- Ollama smoke treats done_reason=stop as im_end success

**Files changed:**
- `fine_tuning/scripts/merge_sft_lora.py`
- `fine_tuning/scripts/sft_remote_merge_sft.sh`
- `fine_tuning/scripts/vast_sync.ps1`

## vast-merge-gguf-ollama-complete

Completed Vast SFT merge → GGUF → Ollama path. Instance 50091768 (Quebec RTX 4090) ran PEFT merge_and_unload on CausalLM into /workspace/spurgeon_qa_merged_hf (256/256 keys; ConditionalGeneration attempt was wrong), produced spurgeon-qa-v2.Q4_K_M.gguf (~2.6GB), created Ollama model spurgeon-qa-v2, and smoke_test_ollama.py exited 0. Instance destroyed after fetch; full HF merge folder fetch incomplete but GGUF sufficient. Memory paths marked DONE; UpdateGoal unavailable in this session.

- Use AutoModelForCausalLM (not ConditionalGeneration) for SFT LoRA merge so PEFT loads 256/256 keys
- GGUF alone is sufficient for local Ollama; incomplete HF merge fetch is acceptable
- Destroy Vast merge instance after GGUF fetch to stop billing

- `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_gguf/spurgeon-qa-v2.Q4_K_M.gguf`
- `fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf`
- `fine-tuning/plans/ollama-merge-gguf`
- `fine-tuning/ollama-local-test-next-session`
- `fine-tuning/vast-gate0-next-session`

## merged-hf-local-hub

Confirmed full HF merge was missing after Vast; only GGUF was local. Rebuilt spurgeon_qa_merged_hf locally (~7.85GB), uploaded GGUF and merged HF to Hugging Face private repo rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-v2.

- Vast fetch never kept full HF merge; rebuilt locally from CPT+LoRA
- Uploaded GGUF + bf16 HF to private repo qwen3.5-4b-spurgeon-qa-v2

- `fine_tuning/scripts/merge_sft_lora_local.py`
- `fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf/`

## safe-sft-data-cleanup

Executed the accepted safe SFT data cleanup plan, deleting 22 approved junk artifacts totaling 57,159,002 bytes while preserving canonical training, evaluation, package, and reconstruction inputs. Final `13_sft_local_readiness.py --gate0` passed, 23 explicitly checked required files were present, and the focused git audit showed only the four approved tracked dataset deletions alongside pre-existing data modifications and untracked reconstruction assets.

- Deleted only exact plan-approved categories; no canonical or reconstruction source was removed.
- Measured all candidates before deletion, including ignored scratch file fine_tuning/data/ver.py discovered during final audit.

- `fine_tuning/data/qa_rewrite_pilot (approved batch, rotate, smoke, and backup artifacts only)`
- `fine_tuning/data/qa_train.jsonl_old`
- `fine_tuning/data/qa_val.jsonl_old`
- `fine_tuning/data/spurgeon_qa_train_final.jsonl_old`
- `fine_tuning/data/spurgeon_synthetic_starter.jsonl`
- `fine_tuning/data/ver.py`

<!-- memory-fabric:store/episodic/2026-09-08 -->
---
store_path: episodic/2026-09-08
title: "Episodic Journal — 2026-09-08"
summary: "Implemented a reproducible post-SFT evaluator with frozen-set hashing, deterministic quality checks, paired Ollama/HF/OpenAI backends, resumable batched semantic judging, artifact provenance, human-re"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-07T22:16:54-04:00"
---

## post-sft-evaluation

Implemented a reproducible post-SFT evaluator with frozen-set hashing, deterministic quality checks, paired Ollama/HF/OpenAI backends, resumable batched semantic judging, artifact provenance, human-review output, and fail-closed export gates. Executed the full 100-example SFT-vs-CPT comparison and 200 order-swapped Gemini judgments. The SFT substantially beat CPT and passed quality/format/stop gates, but release remains blocked because refusal recall was 54%, below the 85% gate.

**Key decisions:**
- Use identical raw ChatML prompts at temperature 0 for fair Ollama comparison
- Pin one judge model and reject mixed served-model evidence
- Persist progress and resume judging without regenerating model outputs
- Fail closed on dataset, GGUF, source-adapter, semantic, and stop-token evidence
- Do not release the current SFT because refusal recall is below threshold

**Files changed:**
- `config.py`
- `fine_tuning/POST_SFT_EVAL.md`
- `fine_tuning/data/qa_test_frozen.sha256`
- `fine_tuning/data/stop_token_phase3.json`
- `fine_tuning/data/stop_token_phase5.json`
- `fine_tuning/eval_results/post_sft_eval.json`
- `fine_tuning/eval_results/post_sft_eval_human_review.md`
- `fine_tuning/eval_results/ollama_smoke.json`
- `fine_tuning/scripts/evaluate.py`
- `fine_tuning/scripts/sft_eval_core.py`
- `fine_tuning/scripts/sft_export_if_gates.ps1`
- `tests/test_sft_eval.py`

Implemented a reproducible post-SFT evaluation harness with frozen-dataset hashing, paired Ollama/HF/OpenAI backends, deterministic integrity and refusal metrics, pinned order-swapped semantic judging, resumable batching, human-review output, and fail-closed export gates. Completed the 100-example SFT-vs-CPT evaluation: SFT improved groundedness substantially but failed release because refusal recall was 54% versus the 85% requirement.

- Use identical raw ChatML prompts at temperature 0 for SFT and CPT comparisons
- Pin and verify the independent judge model and evaluate both answer orders
- Persist generation and judge progress incrementally
- Fail release/export when any gate is missing or failed

<!-- memory-fabric:store/episodic/2026-09-16 -->
---
store_path: episodic/2026-09-16
title: "Episodic Journal — 2026-09-16"
summary: "Verified Phase 0 CPT S6 fixes (composite halt, continue+resume, monitor markers) and tests"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-16T11:23:15-03:00"
---

## cpt-s6-gpu-blocked

Verified Phase 0 CPT S6 fixes (composite halt, continue+resume, monitor markers) and tests. Attempted GPU resume: registered SSH key, but network volume 7hb931c5oe is 404 on this account and creating a replacement volume requires ≥$5 balance. Empty runpodctl apikey in config.toml; MCP REST v1 create returned 403. Fixed Get-RunpodApiKey to reject empty keys. No pod left running.

**Key decisions:**
- Phase 0 already complete; GPU resume blocked because volume 7hb931c5oe is gone and new volume needs ≥$5 balance.
- Do not train S6 on container disk only.
- Local resume fallback when funds restored: checkpoint-2050 (complete Adam state), not missing local 2100.

**Files changed:**

## vast-unsloth-cpt-smoke

Ran a live Vast RTX 4090 smoke for Unsloth CPT+LoRA (3 train steps). Load/LoRA/tokenize succeeded; trainer.train() first step segfaulted (exit 139). Instance destroyed. Confirms Vast+Unsloth remains unsafe for CPT; Vast+PEFT SFT path stays the known-good option.

- Vast is fine for PEFT LoRA (SFT proven) but Unsloth CPT LoRA SIGSEGVs at first train step on Vast 4090 — do not use Vast for Unsloth CPT/S6.
- Prefer Runpod (or a PEFT CPT port) for CPT Unsloth work.

- `continued_pretrain/scripts/smoke_vast_unsloth_cpt.py`
- `continued_pretrain/scripts/vast_cpt_smoke_remote.sh`
- `continued_pretrain/scripts/vast_cpt_smoke.ps1`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke.log`

## vast-unsloth-official-smoke

Tried cheap official Unsloth image smokes on Vast (core + vastai/unsloth-studio); SSH never came up. Force-destroyed an orphan Studio instance that blocked the GPU. Fallback nvidia/cuda smoke with unset LD_LIBRARY_PATH still SIGSEGV at trainer.train() step 0 (exit 139).

- Official Unsloth Docker images on Vast are not usable via our SSH provision path (sshd conflict / core exits).
- unset LD_LIBRARY_PATH does not fix Unsloth CPT SIGSEGV on Vast nvidia/cuda+pip.

- `continued_pretrain/scripts/vast_cpt_smoke_official.ps1`
- `continued_pretrain/scripts/vast_cpt_smoke_remote_official.sh`

## vast-unsloth-conda-pass

Ran Unsloth CPT smoke on Vast with Miniforge: 3 train steps PASS (no SIGSEGV). Earlier system-pip and LD_LIBRARY_PATH-only attempts failed; first conda attempt wrongly installed CPU torch. Instance destroyed.

- Vast Unsloth CPT works inside Miniforge env with CUDA torch pip-installed into the env.
- Do not use system pip or conda-forge CPU pytorch for Unsloth on Vast.

- `continued_pretrain/scripts/vast_cpt_smoke_conda.ps1`
- `continued_pretrain/scripts/vast_cpt_smoke_remote_conda.sh`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/cpt_unsloth_smoke_conda.log`

## session-end-handoff

Session end handoff saved. Vast Unsloth CPT smoke PASS with Miniforge. Runpod S6 still blocked (volume 404, balance, empty apikey). Local resume artifact is checkpoint-2050. Next: Vast S6 continue with conda recipe, or fix Runpod then orchestrate.

- Vast Unsloth CPT is viable via Miniforge + CUDA torch pip-in-env; system pip and official Unsloth images are not.
- Next session should either wire S6 continue-B to that Vast recipe or unblock Runpod (funds/volume/API key) and resume from checkpoint-2050.
- Keep Hub v2 until finished B + winning C.

- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_smoke/`

## vast-cpt-s6-prepare

Prepared and tested Vast CPT S6 continue-B on the full v3 corpus without renting a GPU or starting training. Local readiness passed (51417/520, SHA matches, complete checkpoint-2050). Dry-searched 4090/3090 offers, packed a 4.6GB payload on D:, and wired Miniforge orchestrate/sync/monitor scripts. Main remaining gate is Vast credit (~$3.31 vs ~$5+ for a safe 4090 wall).

- Do not train this session. Next GPU job is S6 continue-B on full a_output_v3 via Miniforge Unsloth on Vast, resuming checkpoint-2050.
- -Go refuses if Vast credit is under $5 unless -AllowLowCredit; 3090 is the credit-safe Ampere fallback.
- Fetch checkpoints only to D:\search-sermons-cpt\vast_cpt_s6 because C: is nearly full.

- `continued_pretrain/VAST_RUNBOOK_CPT.md`
- `continued_pretrain/scripts/vast_cpt_orchestrate.ps1`
- `continued_pretrain/scripts/vast_cpt_remote_continue_b.sh`
- `continued_pretrain/scripts/vast_cpt_local_readiness.py`
- `continued_pretrain/scripts/vast_cpt_sync.ps1`
- `continued_pretrain/scripts/vast_cpt_pack_payload.ps1`

## c-drive-cleanup

Freed C: from ~1.4 GB to ~39 GB free. Deleted stale S6 checkpoints (kept complete checkpoint-2050) and moved GATE-0 merged HF + GGUF folders to D: with junctions so existing paths still work. Did not start Vast training.

- Keep checkpoint-2050 on C: as the S6 resume source.
- Relocate large GATE-0 artifacts to D:\\search-sermons-cpt\\vast_sft_gate0 and junction them back into the repo.

- `continued_pretrain/kaggle/runpod_cpt_v3/s6_continue_b/checkpoints_sota`
- `fine_tuning/kaggle/vast_sft_gate0`

## train-assets-on-c

Moved S5 LoRA and Vast CPT payload onto C: with the corpus and checkpoint-2050. Updated Vast CPT scripts to use C: results path. Local readiness PASS; training not started.

- CPT train inputs (corpus, S5 LoRA, checkpoint-2050, payload, fetch dir) stay on C: under the repo.
- GATE-0 SFT merged/GGUF stay on D: via junctions; not required for CPT S6.

- `continued_pretrain/scripts/vast_cpt_common.ps1`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6`

<!-- memory-fabric:store/episodic/2026-09-18 -->
---
store_path: episodic/2026-09-18
title: "Episodic Journal — 2026-09-18"
summary: "Finished Vast CPT S6 continue-B cleanup: re-fetched artifacts to vast_cpt_s6/fetch, destroyed idle instance 51416115 (instances=[]), and documented why resume spiked spurgeon 2.4987→2.618 then composi"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-18T20:31:32-03:00"
---

## vast-cpt-s6-fetch-destroy-analyse

Finished Vast CPT S6 continue-B cleanup: re-fetched artifacts to vast_cpt_s6/fetch, destroyed idle instance 51416115 (instances=[]), and documented why resume spiked spurgeon 2.4987→2.618 then composite early-stopped at 2400 without beating best-2050. Canonical saved LoRA is the nested theology_cpt_lora path matching SHA 6aab9194….

**Key decisions:**
- Destroyed idle Vast 51416115 after fetch — stop credit burn
- Best LoRA remains checkpoint-2050 (SHA 6aab9194…); ignore outer stale S5 fetch copy
- No Hub overwrite; next session is C-eval only
- Resume spike is real multi-bucket degradation; composite early-stop behaved as designed on post-spike plateau

**Files changed:**
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/`

## cpt-s6-c-eval-handoff

Saved CPT memories so the next session runs S6 C-eval only on the Vast best LoRA (checkpoint-2050, SHA 6aab9194…), compares vs Ampere base and Hub v2, and does not start a new B or Hub overwrite.

- Best continue-B adapter remains checkpoint-2050 / nested fetch LoRA SHA 6aab9194…
- Next GPU work is C-eval only; Hub v2 kept until winning C
- No new B / no merge in the C session

- `pretraining/cpt-next-session-handoff`
- `pretraining/cpt-current`
- `pretraining/cpt-s6-c-eval-next-session`
- `pretraining/vast-cpt-s6-early-stop-handoff`

## s6-c-eval-vast

Ran fresh Vast S6 C-eval of ckpt-2050 LoRA (SHA 6aab9194…). Probe FAIL vs Ampere base (spurgeon +27.9% PPL); keep Hub v2. Shipped vast_cpt_c_eval.ps1 + vast_remote_c_eval.sh; fixed Hub-v2 SHA overwrite from HF inject. Instance 51446613 destroyed; metrics in vast_cpt_s6/c_eval/.

- Keep Hub v2 — S6 C probe FAIL (all buckets worse than Ampere base)
- No Hub overwrite, no merge
- Vast Miniforge C automation: pin EXPECTED_ADAPTER_SHA256 after .sft_env inject

- `continued_pretrain/scripts/vast_cpt_c_eval.ps1`
- `continued_pretrain/scripts/vast_remote_c_eval.sh`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/theology_cpt_eval_metrics.json`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/cpt_eval.log`

## s6-c-regression-diagnosis

Diagnosed S6 C +27.9% spurgeon regression. Added post-load tie_diag + embed→lm_head sync; confirmatory Vast re-C (US 4090) synced heads but PPL stayed 18.31. Tying hypothesis rejected. Hub v2 stays. Hardened vast_cpt_c_eval (geo filter, nohup poll).

- Embed→lm_head sync does not fix S6 C regression (max_abs_delta≈0.002, PPL unchanged)
- Keep Hub v2; Aug-28 same-SHA win is unproven
- CPT_EVAL_SYNC_TIED_HEAD kept as default-on hygiene

<!-- memory-fabric:store/episodic/2026-09-19 -->
---
store_path: episodic/2026-09-19
title: "Episodic Journal — 2026-09-19"
summary: "Operator asked to save memories"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-19T11:03:52-03:00"
---

## save-cpt-c-eval-memories

Operator asked to save memories. Refreshed canonical CPT store entries for S6 C-eval scorecard, regression diagnosis (tying rejected), current pointer, and next-session handoff. Hub v2 stays; no new GPU work.

**Key decisions:**
- Keep Hub v2 after S6 C probe FAIL
- Tying sync rejected as regression root cause
- Aug-28 same-SHA 13.34 treated as unproven

<!-- memory-fabric:store/episodic/2026-09-20 -->
---
store_path: episodic/2026-09-20
title: "Episodic Journal — 2026-09-20"
summary: "Implemented stack-isolation C for S6 SHA 6aab"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-20T19:01:32-03:00"
---

## s6-stack-isolation-c

Implemented stack-isolation C for S6 SHA 6aab. Recovered S5 pins (Unsloth 2026.8.22 / torch 2.8). Added CPT_EVAL_TRAIN_PROBE_DOCS + UNSLOTH_PIP_SPEC to eval. Runpod had no balance; ran on Vast with the S5 software pin. Result: spurgeon 12.85 (−10.2%) vs Vast false FAIL +27.9%. Train probe 16-doc loss 2.495 matches training. Hub v2 stays until separate overwrite approve.

**Key decisions:**
- S5 pin = Unsloth 2026.8.22 + torch 2.8.0 (from cpt_eval.log)
- Runpod unpaid → Vast host with same software pin
- Flip: Vast C-eval false FAIL; S6 LoRA spurgeon 12.85 (−10.2%)
- 16-doc train probe matches train loss; not the regression cause
- Hub overwrite still requires separate operator approve

**Files changed:**
- `continued_pretrain/scripts/vast_remote_stack_isolation_c.sh`
- `continued_pretrain/scripts/vast_stack_isolation_c.ps1`
- `continued_pretrain/scripts/vast_stack_isolation_rerun.sh`
- `continued_pretrain/scripts/runpod_remote_stack_isolation_c.sh`
- `continued_pretrain/scripts/runpod_stack_isolation_c.ps1`
- `continued_pretrain/kaggle/runpod_cpt_v3/stack_isolation_c/`

## memory-stack-isolation

Persisted and cross-linked stack-isolation findings: updated regression diagnosis as false FAIL, added durable S5 eval stack pin memory, refreshed S6 C-eval complete scorecard to point at isolation PASS (spurgeon 12.85).

- Vast +27.9% superseded as false FAIL
- CPT C must use Unsloth 2026.8.22 + torch 2.8 + torchvision 0.23.0
- Hub overwrite still needs explicit approve

- `.ai-memory/memory-store/pretraining/cpt-s6-c-eval-regression-diagnosis.md`
- `.ai-memory/memory-store/pretraining/cpt-eval-stack-pin-s5.md`
- `.ai-memory/memory-store/pretraining/cpt-s6-c-eval-complete.md`

<!-- memory-fabric:store/episodic/2026-09-21 -->
---
store_path: episodic/2026-09-21
title: "Episodic Journal — 2026-09-21"
summary: "Committed and pushed CPT C-eval stack pin, S6 stack-isolation tooling/scripts, and related memory-store updates to origin/main as cca6aee"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-21T11:05:46-03:00"
---

## commit-push-s6-isolation

Committed and pushed CPT C-eval stack pin, S6 stack-isolation tooling/scripts, and related memory-store updates to origin/main as cca6aee.

**Files changed:**
- `.ai-memory/memory-store/pretraining/cpt-s6-stack-isolation-c.md`

## memory-deep-dream

Verified Memory Fabric health and executed a deep dream consolidation. Quality score improved by +6 points (88 to 94) and cleared the stale dream warning.

**Key decisions:**
- Ran deep dream maintenance to consolidate indices and resolve stale dream warning

## llm-dream-split-tool

Ran LLM-assisted deep dream using the Split-Tool Protocol. Prepared payload with prepare_dream_payload_tool, synthesized improved summaries for bug entries and contradictions with the assistant LLM, and applied the consolidation via apply_dream_results_tool (100/100 pass).

- Executed LLM Dreaming via Memory Fabric Split-Tool Protocol, passing structured summaries and contradiction review from the assistant LLM

## full-deep-dream

Executed a full deep dream consolidation with LLM synthesis, evaluation reporting (saved to .ai-memory/evals/latest.md), quality scoring (+6 delta, 100/100 score), and generation of rewrite candidates for long episodic entries.

- Completed full deep dream with evaluation report generation and rewrite task identification via the Split-Tool Protocol

## upgrade-memory-fabric-1.4.2

Verified ai-memory / memory-fabric against PyPI latest (1.4.2). Project `.venv` was already on 1.4.2; upgraded the Cursor MCP `uv tool` install from 1.4.1 → 1.4.2 after stopping locked `memory-fabric-mcp` processes. Also cleaned/reinstalled a broken Python 3.14 user-site leftover to 1.4.2. `sync-agents --check` reported agent instruction files in sync. Doctor ok with existing store-hygiene warnings only.

- Cursor `~/.cursor/mcp.json` uses the uv-tool binary (source of truth for live MCP)
- On Windows, stop running `memory-fabric-mcp` processes before `uv tool upgrade` (file lock)

## hub-s6-overwrite

Uploaded S6 nested LoRA SHA 6aab to private Hub …-theology-cpt-lora-v2. Updated eval default EXPECTED_ADAPTER_SHA256 to 6aab. Wrote hub-overwrite + next-cpt-improvements-prep memories; next work is plan-only CPT improvements (LR/Adam/§5), not immediate train.

- Operator approved Hub overwrite with S6 6aab
- Legacy v2 SHA kept only as HUB_CPT_ADAPTER_SHA256_V2_LEGACY / local runpod_cpt_v2
- Next session is CPT improvements prep only — no B until go


## cpt-s7-improvements-prep

Drafted the S7 CPT continue plan from S6 LoRA (SHA 6aab) without starting a GPU. Phase A is new Adam, ~2e-6 body LR, same v3 mix, C on Unsloth 2026.8.22/torch 2.8. Catalogued further levers (confession unique tokens, seeded composite, freeze embeds, merge+r=64) and the volume auto-resume landmine.

- S7 Phase A is adapter-only new Adam from S6 LoRA 6aab, not HF-resume of 2050/2100/2400 (PREV_RUN_CHECKPOINT must be empty string).
- Do not clone S6's 4e-6 peak; recommended body ~2e-6 / emb ~8e-7 with short warmup and seeded composite including puritan+confession.
- Same a_output_v3 mix on first GPU go; unique confession/puritan tokens (Phase B) and merge+r=64 (Phase C) only if A plateaus.
- Train and C on Unsloth 2026.8.22 / torch 2.8; skip WSD.
- No GPU provisioned this session.

- `pretraining/cpt-next-cpt-improvements-prep`

## cpt-s7-phase-a-prep

Implemented S7 Phase A prep with no GPU: CPT_CONTINUE_PROFILE=s7 (2e-6 / 8e-7, 2064 steps, seeded 4-metric composite, checkpoints_s7), regenerated train_cpt_sota.py, added s7_remote_continue_b.sh with stack pin, extended unit tests (32 passed), and wrote NEXT_CPT_S7.md. Next session is operator GPU go only.

- CPT_CONTINUE_PROFILE=s7 keeps S6 continue defaults unchanged (4e-6 / min_steps 0.4 epoch).
- S7 writes checkpoints_s7 and never auto-resumes leftover checkpoints_sota; first launch forces PREV_RUN_CHECKPOINT empty.
- Composite early-stop accepts initial_bests seeded from S6 so first-eval spikes cannot become the halt baseline.
- Train install honors UNSLOTH_PIP_SPEC; S7 launcher pins Unsloth 2026.8.22 / torch 2.8 and omits xformers.

- `continued_pretrain/scripts/s7_remote_continue_b.sh`
- `continued_pretrain/NEXT_CPT_S7.md`

## s7-improvements-pass

Implemented the S7 CPT improvements pass (no GPU): corrected unreachable isolation-C seed bests to S6 in-train values, retuned halt cadence (patience 4 / ε 0.003 / eval 50 / warmup 0.04), parameterized the monitor for 2064 steps, added LR floor + freeze-embeds + general bucket levers, S5BestAdapterExporter, AbortOnSeedRegressionCallback, and s7_remote_c_eval.sh. Regenerated train/eval scripts; all cpt_runtime and monitor tests passed.

- S7 composite seeds must be S6 in-train @ 2050 (1.751/1.668), never isolation-C CE
- patience 4 + eval_steps 50 so earliest halt is step 650 not 525
- HF best stays spurgeon; §5 candidate exported to theology_cpt_lora_s5best
- eval_cpt_sota.py default SHA left at S6 6aab; S7 C wrapper uses skip or explicit SHA

- `continued_pretrain/scripts/s7_remote_c_eval.sh`

<!-- memory-fabric:store/episodic/2026-09-22 -->
---
store_path: episodic/2026-09-22
title: "Episodic Journal — 2026-09-22"
summary: "Parked a next-cycle plan to add John Downame (with confession/ST unique-token growth) after S7 Phase A"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-22T17:55:58-03:00"
---

## park-downame-phase-b

Parked a next-cycle plan to add John Downame (with confession/ST unique-token growth) after S7 Phase A. Saved as pretraining/cpt-phase-b-downame-next-cycle and linked from the CPT handoff. Phase A stays on a_output_v3 with no mix rebuild.

**Key decisions:**
- Downame is Phase B only — not Phase A mix
- Pair Downame with confession expansion, not Puritan alone

## phase-b-downame-corpus

Implemented Phase B corpus prep: Downame Christian Warfare + Guide to Godliness on disk from EEBO-TCP, S5 confession catalog wired but not fetched (negative headroom under 6% cap), 07 now pins puritan/confession holdouts, v3 holdout snapshot saved, playbook and memory updated. Mix rebuild to a_output_v4 remains deferred until Phase A finishes.

- Fetched John Downame via EEBO-TCP A20752/A20762; train-only
- Skipped S5 Shaw/Sum fetch because confession headroom was −3.39 MB after Downame
- Pinned puritan/confession holdouts in 07 like Spurgeon; snapshot in holdouts_pinned_v3
- Deferred mix rebuild and a_output_v4 until Phase A completes

**Files changed:**
- `data/puritans/downame/christian_warfare.txt`
- `data/puritans/downame/guide_to_godliness.txt`
- `continued_pretrain/data/holdouts_pinned_v3/`

## s7-gpu-go-balance-block

Attempted S7 Phase A GPU launch after operator go. Runpod MCP authenticated; zero pods/volumes. Network volume create failed (≥$5 required). Secure 4090 EU-RO-1 out of stock; Secure L4 create returned 402 balance too low. Confirmed local a_output_v3 (23dd) and nested S6 LoRA 6aab ready. No pod left running.

- Will not train without funds; avoided leaving billable orphans
- Prefer network volume + Secure GPU once balance restored; persistent mount only as fallback

## s7-vast-phase-a-running

Implemented S7 Vast lane, packed/synced a_output_v3 + 6aab LoRA to instance 52063161 (RTX 4090). Fixed TRL max_seq_length crash and nohup launch. Training running at 2064 max_steps with torch 2.8 / Unsloth 2026.8.22; monitor polling with TotalSteps 2064.

- Vast primary for S7 Phase A after Runpod balance block
- nohup whole launcher so Miniforge survives SSH
- TRL 0.24 max_seq_length remapped to max_length; pin trl<0.24 on new envs

- `continued_pretrain/scripts/vast_cpt_s7_remote_continue_b.sh`
- `continued_pretrain/scripts/vast_cpt_s7_orchestrate.ps1`
- `continued_pretrain/scripts/vast_cpt_s7_launch.ps1`
- `continued_pretrain/scripts/vast_cpt_s7_fetch.ps1`
- `continued_pretrain/scripts/vast_cpt_s7_monitor_until_done.py`
- `continued_pretrain/VAST_RUNBOOK_CPT_S7.md`

## s7-earlystop-fetch

S7 Phase A CPT finished on Vast with COMPOSITE EARLY-STOP at step 1250 (max was 2064). Final LoRA SHA 1381e5ee… and s5best SHA 06354dfc… (step 1200) verified locally under vast_cpt_s7/fetch. Monitor did not auto-fetch/destroy; manual fetch completed; instance destroy attempted (credit still ~$4.5 with instance live until confirmed destroyed).

- Prefer local theology_cpt_lora_s5best (step 1200) for upcoming C eval; final HF LoRA equals checkpoint-1250
- Destroy Vast instance 52063161 after artifact verify to stop billing

- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_lora`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/theology_cpt_lora_s5best`

## s7-handoff-c-next

Saved next-session handoff: operator will run S7 isolation C next. Updated cpt-next-session-handoff and cpt-current with s5best SHA, stack pin, and win/keep gates.

- Next session is isolation C only; prefer s5best SHA 06354dfc…; Hub stays S6 until C wins

## s7-isolation-c

Ran S7 isolation C on Vast with the correct stack pin. Added vast_cpt_s7_c_eval.ps1, rented RTX 4090, evaluated s5best 06354dfc…, fetched metrics, destroyed instance. Spurgeon 12.45 (−13%); §5 puritan/confession −8.6%/−6.0% FAIL vs −15% bar. Hub stays S6.

- Used Miniforge stack-isolation C (Unsloth 2026.8.22 + torch 2.8), not vast_remote_c_eval.sh torch 2.11
- Evaluated s5best SHA 06354dfc (step 1200), not final 1381e5ee
- §5 FAIL — keep Hub S6; no overwrite; next is Phase B

- `continued_pretrain/scripts/vast_cpt_s7_c_eval.ps1`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/theology_cpt_eval_metrics.json`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/cpt_eval.log`

## s7-best-adapter-memory

Confirmed S7 s5best is the best CPT adapter on isolation-C scorecard (spurgeon 12.45 beats S6 12.85). Saved leaderboard + updated cpt-current and next-session handoff. Hub still S6 locally-only win.

- S7 s5best 06354dfc is best measured CPT adapter (spurgeon 12.45 vs S6 12.85)
- Hub remains S6 until operator overwrite approve
- §5 still FAIL — Phase B next

## hub-s7-overwrite

Uploaded S7 s5best LoRA (SHA 06354dfc) to private Hugging Face repo rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2, replacing S6 6aab. Updated eval/generator SHA defaults and Hub memories.

- Operator-approved Hub overwrite of private qwen3.5-4b-theology-cpt-lora-v2 with S7 s5best 06354dfc
- Kept repo private; no merge/GGUF
- Updated eval default EXPECTED_ADAPTER_SHA256 to S7


## save-hub-s7-memories

Saved/refreshed CPT memories after Hub S7 overwrite: cpt-current, cpt-best-adapter-leaderboard, cpt-hub-s7-overwrite (code defaults), and fixed cpt-next-session-handoff which still incorrectly said keep Hub S6.

- Hub production is S7 s5best 06354dfc (not S6)
- Next session handoff corrected to Phase B with Hub=S7
- Leaderboard refreshed as best+Hub

<!-- memory-fabric:store/episodic/2026-09-23 -->
---
store_path: episodic/2026-09-23
title: "Episodic Journal — 2026-09-23"
summary: "Implemented the recommended wave-5 Puritan shortlist: wired _wave5_catalog, fetched all 9 titles (~8.47M chars) via EEBO-TCP/CCEL, confirmed long-s already normalized, and stopped before mix rebuild o"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-09-23T18:15:50-03:00"
---

## wave5-puritan-fetch

Implemented the recommended wave-5 Puritan shortlist: wired _wave5_catalog, fetched all 9 titles (~8.47M chars) via EEBO-TCP/CCEL, confirmed long-s already normalized, and stopped before mix rebuild or CPT. Confession S5, Gillespie, and catechism near-dupes were left out.

**Key decisions:**
- Treat the plan's Recommend list as the approved subset.
- Keep new texts train-only with holdouts pinned.
- Do not fetch confession S5; extra Puritan mass is not enough to close the 6% headroom gap.

**Files changed:**
- `data/puritans/ambrose/looking_unto_jesus.txt`
- `data/puritans/swinnock/works_1665.txt`
- `data/puritans/swinnock/incomparableness_of_god.txt`
- `data/puritans/venning/plague_of_plagues.txt`
- `data/puritans/binning/sinners_sanctuary.txt`
- `data/puritans/preston/breastplate_of_faith_and_love.txt`
- `data/puritans/durham/unsearchable_riches_of_christ.txt`
- `data/puritans/vincent/true_christians_love_of_the_unseen_christ.txt`
- `data/puritans/guthrie/christians_great_interest.txt`

## phase-b-mix-v4

Rebuilt the theology mix with pinned v3 holdouts so Downame and the nine wave-5 Puritans entered the CPT corpus, verified ~94.7M tokens, and packed a_output_v4 (mix SHA 37a3ba50…). a_output_v3 was not overwritten. No CPT train was started.

- Pin holdouts from holdouts_pinned_v3 so wave 5 and Downame stay train-only.
- Pack only a_output_v4; leave a_output_v3 SHA 23dd untouched.
- Stop before GPU continue-B.


## next-cpt-preprocess-plan

Planned data preprocessing for the next CPT. Phase B local prep is already packed as a_output_v4 (SHA 37a3ba50, ~94.7M tokens). The plan locks that artifact for the GPU continue from Hub S7, lists the verification-only checklist, and defers any new fetch or mix rebuild until after that run's C.

- Do not rebuild the mix or fetch confession S5 before the Phase B GPU.
- Next train consumes a_output_v4; one_doc_padded packing stays on the GPU.
- A later corpus cycle (a_output_v5) starts only if new unique text is approved after C.

## cpt-v4-reweight-memory

Saved the CPT prep decision for the Downame and wave 5 corpus. The next run continues Hub S7 s5best on the full mix, reweighted so the eleven unseen files are about 15% of steps while Spurgeon, older Puritans, confession, Bible, and replay stay the majority.

- Continue S7 s5best on a reweighted full mix, not a new-authors-only CPT.
- Target about 15% steps on the 11 unseen files via one pass plus a subsample of the already-trained shelf.
- Keep pinned v3 holdouts; new Adam; do not resume a_output_v3.

## next-cpt-preprocess

Implemented the next-CPT preprocess plan: corpus-wide audit of every mix bucket, no source rewrite and no mix rebuild because the audit was clean. Locked a_output_v4 SHA 37a3ba50 for the S7 continue, left a_output_v3 frozen, and pointed Phase B pack/sync/readiness at that v4 superset plus local s5best 06354dfc. GPU copy still waits for operator go.

- Do not rebuild a_output_v4 after a clean audit
- Do not normalize pinned holdouts that still contain long-s
- Phase B copy uses a_output_v4 and S7 s5best, not S6 or a_output_v3

- `continued_pretrain/scripts/audit_cpt_mix_sources.py`
- `continued_pretrain/scripts/normalize_early_modern_orthography.py`
- `continued_pretrain/scripts/05_build_corpus.py`
- `continued_pretrain/scripts/vast_cpt_s7_common.ps1`
- `continued_pretrain/scripts/vast_cpt_s7_pack_payload.ps1`
- `continued_pretrain/scripts/vast_cpt_s7_sync.ps1`
- `continued_pretrain/scripts/vast_cpt_s7_local_readiness.py`

## phase-b-v5-reweight-prep

Prepared Phase B continue without GPU: built an isolated 15% new-author reweight mix (a_output_v5 SHA 61e83057, ~25.1M tokens, 15,420 docs), pointed Vast/S7 launchers at that pack plus Hub S7 s5best, and dropped the v3 mix-val seed. Audit CLEAN / CONTINUE_READY. Dry orchestrate listed 4090 offers and rented nothing.

- Keep the full mix; raise the 11 unseen books to 15% of chars via one pass plus a subsample of the already-trained shelf.
- Write the reweight to isolated mix_v5 / a_output_v5; leave v3 and uniform v4 frozen.
- Drop eval_mix_loss from composite seeds; set CONTINUE_MAX_STEPS=955 (one packed epoch) and EARLY_STOP_MIN_STEPS=400.
- No GPU rent, no Hub overwrite.

- `continued_pretrain/data/mix_v5/theology_mix_train.txt`

## vast-4090-readiness-check

Checked Vast 4090 readiness for S7→v5 continue. Old SIGSEGV path is already superseded by Miniforge + torch 2.8 / Unsloth 2026.8.22 (S7 Phase A completed on a 4090). Fixed leftover sync SHA check that still wanted S6 6aab, and pointed pack/sync at the v5 manifest. Local C: has only ~2.1 GB free so default payload.tar pack is unsafe; Vast credit was ~$4.14 under the $5 go gate.

- Phase B sync must verify S7 s5best 06354dfc, not leftover S6 6aab.
- Skip local payload.tar on C: when free disk is ~2 GB; scp files directly with -SkipPack.

- `continued_pretrain/scripts/test_vast_cpt_s7_prepare.py`

## projetos-disk-cleanup

Freed C: from 2.0 GB to 82.0 GB by deleting regenerable node_modules/Android builds in four Projetos apps and removing superseded CPT/SFT blobs. Archived S6 trees, S5/v2 adapters, and unused GGUFs to D:\search-sermons-cpt\archive-2026-09-23\. Phase B keep-list (a_output_v5 + S7 s5best) and GATE-0 junctions remain on C:.

- Delete regenerable mobile caches first so C: had headroom for S6/GGUF copies.
- Delete S7 intermediate checkpoints and payload instead of archiving; pack script rebuilds payload for v5.
- Move S6/S5/v2 history and unused GGUFs to D: archive rather than delete.
- Skip unsloth.F16.gguf symlink after admin privilege failure; file lives only on D: until operator links it.

- `D:\search-sermons-cpt\archive-2026-09-23\`
- `controle-medico/node_modules (deleted)`
- `irglobal-app/node_modules (deleted)`
- `app-us/node_modules (deleted)`
- `ai-personal/node_modules (deleted)`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6 (moved)`
- `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7/fetch/checkpoints_s7 (deleted)`
- `fine_tuning/models/*.gguf (moved)`

## cpt-s7-phase-b-vast-go

Prepared and launched CPT S7 Phase B on Vast.ai: packed a_output_v5 + S7 s5best, rented RTX 4090 instance 52264974, and confirmed walk-away gates (new Adam, SHA 06354dfc, torch 2.8 / Unsloth 2026.8.22, max_steps 955). Training is running (~60/955, GPU 100%). Fixed the Windows monitor charmap crash so fetch+destroy still happens when B finishes.

- Used -AllowLowCredit because live credit was $4.14 vs $5 gate; cheapest NYC 4090 at $0.448/hr should finish in ~$2-3.
- Copied a_output_v5 + local s5best with a new Adam; did not HF-resume v3 or ship checkpoints_sota.
- Restarted the local monitor after patching ASCII-safe progress-bar printing.


## cpt-s7-phase-b-early-stop

Phase B on Vast ended by design: composite early-stop at step 750/955 after holdout CE flattened (patience 4, epsilon 0.003). Monitor fetched adapters and destroyed instance 52264974. HF best is checkpoint-700 SHA 6d003041; new s5best is step 600 SHA ddbbee3a. Hub stays Phase A 06354dfc until isolation C.

- Treat the stop as intended S7 composite halt, not a crash or credit kill.
- Do not overwrite Hub until isolation C on the nested Phase B adapters.

## cpt-s7-replay-pack

Finished the post-plateau CPT plan. Isolation C on nested Phase B s5best ddbbee3a slightly beat Hub but missed §5 (12.39 / 5.50 / 5.25). Packed holdout-sibling mix_v6 + a_output_v6 and wired S7 continue to init ddbbee3a with a halt composite that drops mix-val. No GPU rented; Hub stays 06354dfc.

- Do not retrain a_output_v5 after the Phase B plateau.
- Init the replay from Phase B C-winner ddbbee3a (B slightly beat Hub) with new Adam and LR 2e-6.
- New pack mix_v6 / a_output_v6: 25% holdout siblings, Spurgeon 35% floor, new-authors 5% cap. Confession 9.2% is sibling upweight of existing S4 text.
- Halt on Spurgeon + Puritan + confession only; drop eval_mix_loss.
- Keep Hub 06354dfc until a winning C. Session/results under vast_cpt_s7_replay so Phase B fetch is not overwritten.
- No GPU until operator go.

- `continued_pretrain/data/mix_v6/`
- `continued_pretrain/kaggle/a_output_v6/`

<!-- memory-fabric:store/fine-tuning/cpt-merged-hf-local-complete -->
---
store_path: fine-tuning/cpt-merged-hf-local-complete
title: "Local complete CPT merged HF"
summary: "Complete CPT merge HF is now local (scp from Vast instance `50011937`)"
priority: low
tags: [cpt, sft, vast, merged-hf]
schema_version: 1.3
last_updated: "2026-09-06T02:32:53-04:00"
---

## Status (2026-09-06)

Complete CPT merge HF is now local (scp from Vast instance `50011937`).

- **Local path:** `fine_tuning/kaggle/vast_sft_gate0/theology_cpt_v2_merged_hf`
- **Remote source:** `/workspace/theology_cpt_v2_merged_hf` on Vast `50011937` (ssh `root@75.129.99.99:5250`)
- **Verified:** yes — sizes match remote:
  - `config.json` 3344
  - `tokenizer_config.json` 7163
  - `model-00001-of-00002.safetensors` 4972947968
  - `model-00002-of-00002.safetensors` 4105672464
  - `model.safetensors.index.json` 66236
  - total ~8.47 GB
- Incomplete local copy moved aside to `theology_cpt_v2_merged_hf.incomplete.bak`
- Runpod incomplete path `fine_tuning/kaggle/runpod_sft_gate0/theology_cpt_v2_merged_hf` left unchanged
- HF still has LoRA adapter only, not merged HF
- Training/instance not interrupted

<!-- memory-fabric:store/pretraining/cpt-s6-c-eval-complete -->
---
store_path: pretraining/cpt-s6-c-eval-complete
title: "S6 C-eval: Vast false FAIL; isolation PASS 12.85"
summary: "Path: `vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/`"
priority: low
tags: [cpt, s6, c-eval, hub-v2, stack-isolation]
schema_version: 1.3
last_updated: "2026-09-20T19:01:32-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/c_eval/theology_cpt_eval_metrics.json, pretraining/cpt-s6-c-eval-regression-diagnosis]
---

# S6 C-eval COMPLETE — Vast false FAIL; stack-isolation PASS

## Adapter
Path: `vast_cpt_s6/fetch/theology_cpt_lora/theology_cpt_lora/`  
SHA256: `6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c` (ckpt-2050)

## Vast C (Unsloth 2026.9.6 / torch 2.11) — do not trust for Hub decision
spurgeon 18.31 (**+27.9%**). Probe FAIL. Artifacts: `vast_cpt_s6/c_eval/`.

## Stack-isolation C (Unsloth 2026.8.22 / torch 2.8) — canonical for this SHA
spurgeon **12.85 (−10.2%)**, puritan −7.2%, confession −6.0%, general −1.8%. Probe **PASS**. §5 −15% still FAIL.  
Full: `pretraining/cpt-s6-stack-isolation-c`. Artifacts: `kaggle/runpod_cpt_v3/stack_isolation_c/`.

## Hub
Still keep `…-theology-cpt-lora-v2` until **explicit** overwrite approve (S6 beats Hub v2 13.28 on isolation scorecard).

<!-- memory-fabric:store/pretraining/cpt-s7-isolation-c-complete -->
---
store_path: pretraining/cpt-s7-isolation-c-complete
title: "S7 isolation C complete: spurgeon 12.45; §5 FAIL"
summary: "S7 Phase A **s5best** SHA `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` (step 1200) on **Unsloth 2026.8.22 + torch 2.8.0+cu126** (Vast Miniforge `unsloth_cpt_s5pin`)"
priority: low
tags: [cpt, s7, c-eval, vast, isolation, scorecard]
schema_version: 1.3
last_updated: "2026-09-22T16:55:19-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/theology_cpt_eval_metrics.json, continued_pretrain/scripts/vast_cpt_s7_c_eval.ps1, pretraining/cpt-s6-stack-isolation-c]
---

# S7 isolation C COMPLETE (2026-09-22)

## Bottom line
S7 Phase A **s5best** SHA `06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432` (step 1200) on **Unsloth 2026.8.22 + torch 2.8.0+cu126** (Vast Miniforge `unsloth_cpt_s5pin`).

**§5 −15% puritan+confession: FAIL** (−8.6% / −6.0%). Spurgeon **improved** vs S6 isolation C. **No Hub overwrite** this session.

## Host
- Vast instance `52108817` (label `cpt-s7-isolation-c`), RTX 4090, destroyed after fetch.
- Launcher: `continued_pretrain/scripts/vast_cpt_s7_c_eval.ps1`
- Remote: `vast_remote_stack_isolation_c.sh` (NOT torch-2.11 `vast_remote_c_eval.sh`)
- Artifacts: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s7_c/`

## Scorecard (a_output_v3 holdouts, Ampere bf16)

| Bucket | Base | S7 s5best | Δ% | S6 isolation C |
|--------|------|-----------|-----|----------------|
| spurgeon | 14.31 | **12.45** | **−13.0%** | 12.85 (−10.2%) |
| puritan | 6.03 | 5.52 | −8.6% | 5.60 (−7.2%) |
| confession | 5.61 | 5.27 | −6.0% | 5.27 (−6.0%) |
| general | 12.04 | 11.95 | −0.8% | 11.83 (−1.8%) |

Train probe spurgeon@16: ppl **11.88** (−10.6% vs base 13.30).

## Gate vs Hub S6
- Hub stays S6 `6aab9194…` until operator approve.
- §5 win bar (≤−15% puritan+confession): **not met**.
- Spurgeon 12.45 is **better** than S6 12.85 and well under 13.3 keep-bar.
- Puritan 5.52 slightly better than S6 5.60; confession ties 5.27.
- Next: Phase B mix `a_output_v4` (Downame) — do not Hub overwrite on §5 alone.

## Stack pin used
Unsloth 2026.8.22, torch 2.8.0+cu126, torchvision 0.23, no xformers, `CPT_EVAL_TRAIN_PROBE_DOCS=16`.

<!-- memory-fabric:local/debt -->
---
section: debt
summary: "App debt (hybrid search, rate limits) plus 2026-08-29 memory-fabric LLM/host hygiene notes."
priority: low
tags: [debt, risk]
schema_version: 1.3
last_updated: "2026-08-29T11:07:00-04:00"
summary_hash: 089c37fc31054b93e50d68038bbf1c4d
review_status: stale
---

# Technical Debt & Roadmap

This section tracks outstanding technical debt, limitations, and future development opportunities.

## Known Technical Debt & Limits

- **Pure Vector Search Limitation**: Search relies on semantic vector queries and can miss exact bible-reference keywords (e.g. "Romans 8:28"). Hybrid BM25 + vector is needed.
- **PDF Text Quality**: Raw PDF/OCR is worse than community markdown; prefer markdown sources for ingest.
- **Session-Based Rate Limiting**: 8 queries/hour in Streamlit session memory is bypassable by reload; production needs server-side IP/token limits.
- **Memory fabric hygiene (2026-08-29)**: Many store files were missing from `memory-store/index.md` until deep dream; `OLLAMA_HOST` in `.env` had an inline `#` comment breaking the URL; `MEMORY_FABRIC_LLM_PROVIDER=ollama` pointed at missing `gemma4` while only `spurgeon-cpt` was pulled. Prefer Gemini free or Cursor split-tool for Dreaming.

## Roadmap & Pending Features

- **Multi-Author Interface**: Schema is author-aware; UI/prompts still assume Spurgeon-only.
- **Weekly Automated Ingestion**: Pull updates from `lyteword/chspurgeon-sermons` on a schedule.
- **Mobile Styling**: Extra CSS for Streamlit sidebar/readability on small screens.

<!-- memory-fabric:store/pretraining/vast-cpt-s6-early-stop-handoff -->
---
store_path: pretraining/vast-cpt-s6-early-stop-handoff
title: "Vast S6 early-stop — analyse + destroy (from side chat)"
summary: "Operator asked side chat to notify the **waiting principal CPT session**: analyse why continue-B stopped improving, and **destroy the idle Vast pod** if that makes sense (it does)"
priority: low
tags: [cpt, s6, vast, resolved]
schema_version: 1.3
last_updated: "2026-09-18T11:16:07-03:00"
evidence: [continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_session.json, continued_pretrain/scripts/train_cpt_sota.py, continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/vast_cpt_monitor.log]
---

# Principal session — act now (side-chat handoff 2026-09-18)

Operator asked side chat to notify the **waiting principal CPT session**: analyse why continue-B stopped improving, and **destroy the idle Vast pod** if that makes sense (it does).

## Live facts
- Instance **51416115** (`cpt-s6-continue-b`) still **running / billed** ~$0.59/hr — GPU **idle** (0% / 0 MiB).
- Training **finished** via `COMPOSITE EARLY-STOP @ step 2400/4128` (not a crash, not half-corpus).
- Full corpus was packed: 51417 docs → `packed_epoch_steps=4128`. Resume from **2050**; stop at **2400**.
- Best saved adapter = **checkpoint-2050** (`eval_spurgeon_loss` **2.4987**). Post-2050 steps did **not** beat that.
- Local fetch path: `continued_pretrain/kaggle/runpod_cpt_v3/vast_cpt_s6/fetch/` — monitor was mid-scp after stop; **re-fetch LoRA + run_config + log before destroy** (local `theology_cpt_lora` mtime may predate the finish).

## Why it stopped / why not improving (analyse this)
Continue-B composite early-stop (on by design):
- metrics: `eval_spurgeon_loss` + `eval_mix_loss`
- patience=2, epsilon=0.005, min_steps≈0.4×4128≈1652

After HF resume from 2050, Spurgeon holdout **spiked** then only partially recovered:
- 2050: **2.4987** (best overall / what was saved)
- 2075: **2.618** (spike right after resume)
- 2325: 2.5115 (composite window “best”)
- 2350–2400: gains &lt; epsilon → flat streak=2 → halt

So: full-corpus schedule, intentional early-stop; continued steps after 2050 did not improve the kept LoRA.

## Required principal actions (in order)
1. Confirm remote log still shows early-stop + `OK: saved LoRA matches best_model_checkpoint`.
2. `vast_cpt_fetch.ps1` (or finish monitor fetch) — ensure `fetch/theology_cpt_lora`, `cpt_train.log`, `theology_cpt_run_config.json`, complete ckpts.
3. **Destroy instance 51416115** (`fine_tuning/scripts/vast_destroy.ps1`) — stop credit burn. Do not leave idle 4090 up for analysis.
4. Write analysis: resume spike root cause (optimizer/state, LR continue, eval noise, composite vs HF best at 2050); decide C-eval vs keep Hub v2; **no Hub overwrite** yet.
5. Update `pretraining/cpt-current` + session journal.

## Do not
- Re-rent / resume another B until analysis recorded.
- `S6_FRESH_START`.
- Overwrite Hub v2.

## Resolved 2026-09-18 (principal)
1. Re-ran `vast_cpt_fetch.ps1` — complete.
2. Destroyed **51416115**; `instances=[]`.
3. Analysis written: `pretraining/vast-cpt-s6-resume-spike-analysis`. Canonical LoRA nested path SHA `6aab9194…` (=2050). Next = C-eval; Hub v2 kept.

## Closed for next session
Fetch + destroy + analysis done. **Do not** re-open destroy/fetch. Next session follows `pretraining/cpt-next-session-handoff` → **C-eval only**.
