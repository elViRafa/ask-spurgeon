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
last_updated: "2026-08-23T11:10:53-04:00"
consolidation_hash: dc4febef829d2344ced791190b2a66be
contradictions: ["`bugs/lora-frozen-embeddings-special-tokens` and `bugs/sft-tokenizer-mismatch-vinfos-spepacer` disagree about `im_start` (pos vs neg) - review for conflict [polarity]", "`bugs/lora-frozen-embeddings-special-tokens` and `bugs/unsloth-fast-patching-warnings` disagree about `lora` (neg vs pos) - review for conflict [polarity]", "`bugs/ollama-tokenizer-corruption-fix` and `decisions/gemma4-local-ollama` disagree about `gguf` (neg vs pos) - review for conflict [polarity]", "`bugs/ollama-tokenizer-corruption-fix` and `pretraining/merge-and-export` disagree about `gguf` (neg vs pos) - review for conflict [polarity]", "`bugs/sft-tokenizer-mismatch-vinfos-spepacer` and `bugs/unsloth-fast-patching-warnings` disagree about `lora` (neg vs pos) - review for conflict [polarity]", "`bugs/unsloth-fast-patching-warnings` and `decisions/map-notes-pending-review` disagree about `cuda` (pos vs neg) - review for conflict [polarity]", "`bugs/unsloth-fast-patching-warnings` and `pretraining/environment-setup` disagree about `cuda` (pos vs neg) - review for conflict [polarity]", "`bugs/unsloth-fast-patching-warnings` and `pretraining/model-choice` disagree about `vram` (pos vs neg) - review for conflict [polarity]", "`pretraining/cpt-v2-implementation-fable5` and `pretraining/cpt-v2-plan-fable5` disagree about `mcq` (pos vs neg) - review for conflict [polarity]"]
consolidation_warnings: []
summary_hash: c81ed9efe309125e42b693ba950f4f04
---

# Project Memory Index

Updated by Memory Fabric Dreaming mode `light`.

| Section | Priority | Summary | Key Topics |
| --- | --- | --- | --- |
| `architecture` | high | Generated map of memory-store/architecture/ (2 entries). | • **OPC UA Industrial Engine & SCADA Simulation Platform** ...<br>• **Architecture Map Notes (Pending Review)** (`architectur... |
| `bugs` | medium | Generated map of memory-store/bugs/ (6 entries). | • **Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)*...<br>• **Bug Fix: Unsloth Embedding Offload on Read-Only Filesys...<br>• **Gemma 4 Chat Template Processor Fix** (`bugs/gemma4-cha... |
| `debt` | low | Tracks technical debt (e.g., pure vector search, rate limiting) and roadmap items like multi-author support and automated ingestion. | • Known Technical Debt & Limits<br>• Roadmap & Pending Features |
| `decisions` | medium | Generated map of memory-store/decisions/ (3 entries). | • **Gemma 4 Fine-Tuning Transition** (`decisions/gemma4-fin...<br>• **Gemma 4 Local Ollama Deployment** (`decisions/gemma4-lo...<br>• **Decisions Map Notes (Pending Review)** (`decisions/map-... |
| `episodic` | medium | Generated map of memory-store/episodic/ (6 entries). | • **Episodic Journal — 2026-07-11** (`episodic/2026-07-11`,...<br>• **Episodic Journal — 2026-07-12** (`episodic/2026-07-12`,...<br>• **Episodic Journal — 2026-07-13** (`episodic/2026-07-13`,... |
| `failures` | medium | Generated map of memory-store/failures/ (1 entries). | • **asyncua write_value BadTypeMismatch when writing int to... |
| `fine-tuning` | medium | Generated map of memory-store/fine-tuning/ (3 entries). | • **Gemma 4 Local Dataset Generation Analysis** (`fine-tuni...<br>• **Gemma 2 Fine-Tuning Support** (`fine-tuning/gemma-suppo...<br>• **Reverting Custom Model, Weight Copying, and ChatML in Q... |
| `framework-rules` | medium | Defines coding standards, required libraries (Streamlit, LlamaIndex), environment setup (.env), and database rules for the codebase. | • 1. Runtime Environment<br>• 2. Core Libraries & Packages<br>• 3. Vector Database Rules<br>• 4. Agent Memory Guidelines |
| `grok` | medium | Generated map of memory-store/grok/ (1 entries). | • **Grok Integration with Memory Fabric (MCP + Docs + Nativ... |
| `pretraining` | medium | Generated map of memory-store/pretraining/ (15 entries). | • **Confessions + Institutes corpus (WCF, 1689, Calvin)** (...<br>• **CPT SOTA Assessment + Implementation (2026-07)** (`pret...<br>• **CPT v2 implementation (Fable 5 plan)** (`pretraining/cp... |
| `schemas` | high | Defines data contracts, metadata schemas for ingested texts, and environment variable configurations. | • 1. Document & Chunk Metadata Schema<br>• 2. Ingestion Parameters<br>• 3. Environment Variables (Configuration Schema) |
| `ubiquitous-language` | medium | Defines consistent domain language used throughout the codebase for clarity and shared understanding. | None recorded |

## Memory Store

Please see the dedicated [Memory Store Index](memory-store/index.md) for a map of available semantic memory store files.

<!-- memory-fabric:local/architecture -->
---
section: architecture
summary: "Generated map of memory-store/architecture/ (2 entries)."
priority: high
tags: [architecture]
schema_version: 1.3
last_updated: "2026-08-23T11:09:38-04:00"
generated: true
generated_from: memory-store/architecture
store_fingerprint: d6dfb691840181de6ae69f32e935a35f
body_hash: ca96f8565333e20a1ed2497f0ff6129a
---

# Architecture Map

Generated by Memory Fabric from `memory-store/architecture/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **OPC UA Industrial Engine & SCADA Simulation Platform** (`architecture/opcua-scada-simulation-platform`, high) — OPC UA Industrial Engine & SCADA Simulation Platform
- **Architecture Map Notes (Pending Review)** (`architecture/map-notes-pending-review`, medium) — Hand-written notes folded from architecture.md; split into granular memories and delete.

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

<!-- memory-fabric:store/pretraining/cpt-v2-implementation-fable5 -->
---
store_path: pretraining/cpt-v2-implementation-fable5
title: "CPT v2 implementation (Fable 5 plan)"
summary: "CPT v2 implementation (Fable 5 plan)"
priority: high
tags: [pretraining, cpt, v2, qwen3.5, mix, notebooks]
schema_version: 1.3
last_updated: "2026-07-13T09:34:46-04:00"
evidence: ["[REDACTED_SECRET].md", continued_pretrain/scripts/07_build_theology_mix.py, continued_pretrain/scripts/_gen_sota_notebooks.py]
review_status: stale
---

# CPT v2 implementation status (2026-07-13)

Implemented plan `[REDACTED_SECRET].md` in code (Kaggle train/eval still operator-run).

## Code delivered

- **`07_build_theology_mix.py` v2:** `max_chunk_chars=7000` (Spurgeon chunked), G2 multi-bucket guard (`--allow-spurgeon-only`), paragraph dedup + top-20, `--target-spurgeon-share` weight, `--max-bible-share` (default 0.04), optional `--author-tags` (E1).
- **`06_verify_tokens.py`:** `--mix` writes `verified_tokens` into manifest (D3).
- **`08_fetch_pd_sources.py`:** verified Gutenberg IDs only (Bunyan pilgrim/holy_war/badman, KJV). Always spot-check titles.
- **`09_build_catechism_mcq.py`:** WSC + Heidelberg MCQ JSON.
- **`_gen_sota_notebooks.py` = G3 source of truth** for A/B/C sota notebooks. Flagship `unsloth/Qwen3.5-4B-Base`, dual LR emb 1e-5, warmup_ratio 0.03, per-bucket eval, D1/D2/D4 cells, 9B VRAM probe, C_eval with EVAL_BASE + greedy probes + MCQ + merge gate.
- Config/README/SOURCES updated; curated WSC train + Heidelberg holdout.

## Current mix (seed data)

- Sources: Bunyan×3, KJV, WSC; Heidelberg in `holdouts_manual/` only.
- Shares ~ spurgeon 51% / puritan 45% / bible 4% / confession 1%; max_doc 7000.
- MCQ: 50 WSC + 42 Heidelberg items.
- **Still need more Puritans (Owen/Watson/etc.) + confessions + FineWeb replay** before flagship scale.

## Operator next steps (Kaggle)

1. Expand PD corpus under `data/puritans|confessions` (spot-check titles).
2. Rebuild mix + `06_verify_tokens.py --mix`.
3. Upload corpus; A_sota → B_sota (M1/D1–D4) → C_sota.
4. Pin Unsloth commit after first good session (G1).

<!-- memory-fabric:store/pretraining/cpt-v2-plan-fable5 -->
---
store_path: pretraining/cpt-v2-plan-fable5
title: "CPT v2 improvement plan (Fable 5 review, 2026-07-12)"
summary: "CPT v2 improvement plan (Fable 5 review, 2026-07-12)"
priority: high
tags: [pretraining, cpt, base-model, qwen3.5, vram, flagship]
schema_version: 1.3
last_updated: "2026-07-13T09:18:31-04:00"
evidence: ["[REDACTED_SECRET].md", continued_pretrain/notebooks/B_training_sota.ipynb, continued_pretrain/scripts/07_build_theology_mix.py]
review_status: stale
---

# CPT v2 improvement plan — key findings (2026-07-12)

Full plan: `[REDACTED_SECRET].md`

## Critical findings (verify before next training run)

1. **Suspected 2048-token truncation bug (F1, highest impact).** Baseline B_training.ipynb run shows 216 steps/epoch = ceil(3451 docs / 16), i.e. ONE packed row per raw document → each ~9k-token sermon was likely clipped to its first 2048 tokens before packing. Only ~7.1M of ~30M tokens/epoch trained. Diagnostic cell (D1) in plan; fix = chunk all docs to ≤7,000 chars in 07_build_theology_mix.py (Spurgeon loader currently does NOT chunk; load_tree chunks at 40k chars — both wrong).
2. **Qwen2.5-3B has tie_word_embeddings=true** — targeting `lm_head` in LoRA (as B_training_sota.ipynb does) may no-op, error, or force untying. Diagnostic D4 in plan; fallback = embed_tokens only.
3. **The theology mix on disk is 100% Spurgeon** (manifest 2026-07-11: buckets={spurgeon: 1.0}, replay 0, puritan/confession/general holdouts 0 bytes). data/puritans|confessions|bible are empty. Data acquisition is the real blocker, not the recipe.
4. **EOS boundaries unproven** in packed stream (A_sota strips <|endoftext|>, Qwen tokenizer doesn't auto-append EOS). Diagnostic D2.
5. `07_build_theology_mix.py` exits 0 with a valid-looking Spurgeon-only mix when source dirs are empty — needs a ≥2-bucket guard.
6. `*_sota` notebooks are generated by `scripts/_gen_sota_notebooks.py` — v2 edits must go in generator OR generator retired, never both.

## v2 recipe deltas (from v1 sota)

- warmup_ratio 0.03 (not fixed 100 steps); embedding_learning_rate 1e-5 (5e-6 fallback on fp16 spikes)
- Per-bucket eval_dataset dict during training (mix/spurgeon/puritan/general, ≤8 docs each)
- load_best_model_at_end on eval_mix_loss; save_total_limit 2
- Pin unsloth commit; run config records manifest SHA256 + pip freeze
- Share-targeted spurgeon_weight (target 40–50% share): w = share×other_chars/(128M×(1−share)) — with ~50M chars Puritans w≈0.7–1.0, NOT the default 2.5
- Held-out doctrine eval: Heidelberg Catechism + Belgic Confession excluded from training; catechism MCQ log-likelihood metric (WSC=absorption, Heidelberg=generalization)

## Success gate (ship v2)

Spurgeon PPL ≤ Phase-1×1.03; puritan/confession PPL ≥15% better than base; general PPL ≤10% worse; Heidelberg MCQ +10pts vs base.

## Base model decision (added 2026-07-12, plan §4.1)

Qwen2.5-3B is NOT the best choice anymore: Qwen *Research* License (non-commercial — blocker for shipping Ask Spurgeon), two generations old, tied embeddings (root of F3). Web-verified July 2026 landscape:

- **v2 default: Qwen3.5-4B-Base** — Apache 2.0, ~1.3× step time vs 3B (1–2 Kaggle sessions/epoch), likely tied embeddings → train embed_tokens only per D4. Gate M1 before switching: HF config `tie_word_embeddings`, Unsloth 4-bit build exists, D4 passes.
- **Flagship: Qwen3.5-9B-Base** — Apache 2.0, untied expected → full dual-LR embed+lm_head recipe, ~2.6× time (2–3 sessions/epoch). Run after data v2 + 4B run validate pipeline (E3).
- **Fallback: Mistral-7B-v0.3** — untied, 33k vocab = ~5× cheaper embed/head training; Unsloth's CPT reference model; weakest base knowledge.
- Rejected: Llama-3.2-3B (no edge), Qwen3-4B (superseded), Gemma-4-E4B (exotic MatFormer/multimodal arch + 256k vocab + this project's past Gemma template bugs), Gemma-2-9B, ≥12B models (T4 limit).

Caveat: PPL is tokenizer-dependent — after base swap compare %Δ-vs-own-base per bucket, never absolute PPL across bases; Phase-1 comparison then via probes + catechism MCQ.

Qwen3.5/Gemma-4 details are post-cutoff, from July 2026 sources (HF model cards) — hence M1 gate.

## Base-model tiering revision (2026-07-13)

- **Flagship is now `Qwen3.5-4B-Base`**, not merely the dev-cycle default. Full untied dual-LR recipe (if untied) or embed-only fits comfortably on T4 16 GB at seq 2048 / batch 2, 1–2 sessions/epoch.
- **`Qwen3.5-9B-Base` demoted** to a concession-gated experiment (E3): full dual-LR embed+lm_head is over-budget on single T4 at seq 2048. Embedding VRAM estimate ~2.5 GB ±0.5 (hidden size / layer count not web-verified) — not enough to change the over-budget verdict.
- **Mandatory 9B VRAM probe** before multi-session commit: ~20 steps, then `torch.cuda.max_memory_reserved()`; proceed only if peak reserved < ~15 GB with headroom. Fail → stay on 4B or re-probe only after explicit concessions (embed-only / shorter seq / batch 1).
- **T4×2 escape hatch (risk register):** dual-T4 32 GB can train 9B + embed + head via plain HF + PEFT + bitsandbytes `device_map="auto"` (drop Unsloth). Cost: lose ~2× Unsloth speed/kernels; notebooks are Unsloth-based. Generally not worth it vs 4B.
- Plan file: `[REDACTED_SECRET].md` (§4.1 verdict, E3, risk register, checklist).

<!-- memory-fabric:store/pretraining/cpt-v2-ready-for-kaggle -->
---
store_path: pretraining/cpt-v2-ready-for-kaggle
title: "CPT v2 ready for Kaggle (post local pipeline)"
summary: "CPT v2 ready for Kaggle (post local pipeline)"
priority: high
tags: [pretraining, cpt, kaggle, m1, mix, v2]
schema_version: 1.3
last_updated: "2026-07-13T10:40:05-04:00"
evidence: [continued_pretrain/KAGGLE_RUNBOOK_V2.md, "[REDACTED_SECRET].md", continued_pretrain/data/theology_mix_manifest.json]
review_status: stale
---

# CPT v2 — ready for Kaggle (2026-07-13)

## Local pipeline complete

- Multi-source mix with chunking ≤7k, share targets, 10% PD general replay (Gutenberg classics).
- Shares ~ spurgeon 40.5% / puritan 41% / confession 5% / bible 3.6% / general 10%.
- D3: ~8.2M tokens (gpt2 sample ratio); max_doc 7000; 0 docs >8k.
- Holdouts: spurgeon/puritan/confession/general non-empty; Heidelberg + Belgic in holdouts_manual.
- MCQ: 50 WSC + 42 Heidelberg.
- Package: `12_package_kaggle_corpus.py` → zip for dataset upload.
- Runbook: `continued_pretrain/KAGGLE_RUNBOOK_V2.md`.

## M1 (partial pass)

- `Qwen/Qwen3.5-4B-Base` + `unsloth/Qwen3.5-4B-Base` exist.
- **`tie_word_embeddings=true`** → notebooks default `TRAIN_LM_HEAD=False`.
- Hybrid `qwen3_5` (linear_attention + full_attention + vision_config) — **must prove Unsloth train on T4**; fallback Qwen2.5-3B.
- Details: `data/M1_BASE_MODEL_GATE.md`.

## Remaining (operator / Kaggle only)

1. Upload corpus zip as `theology-cpt-corpus`
2. A_sota → dataset `theology-cpt-dataset`
3. B_sota session 1: D1/D2/D4 + s/step + MAX_STEPS; pin Unsloth after success
4. Train 1 epoch; C_sota eval; merge only if §5 passes

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

<!-- memory-fabric:store/bugs/ollama-tokenizer-corruption-fix -->
---
store_path: bugs/ollama-tokenizer-corruption-fix
title: "Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)"
summary: "Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)"
priority: high
tags: [bugs, tokenizer, gguf, ollama, alignment]
schema_version: 1.3
last_updated: "2026-06-11T17:07:59-04:00"
review_status: stale
---

# Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms/ +lsi / {lng)

## Context & Root Cause Discovery
During Phase 1 pre-training, the model was exported to GGUF format. When Unsloth/llama.cpp processes GGUF vocabulary export, it prepends a header/dummy token (e.g. `Q\x02\x00\x00\x00\x00\x00`) at index 0, causing all subsequent vocabulary tokens and embedding weights to shift by exactly +1 (e.g. standard token `i` maps to GGUF token `i+1`).

When Notebook E and Notebook F loaded this base model using Unsloth but loaded a "clean" tokenizer directly from `"unsloth/Qwen2.5-3B-Instruct"`:
1. **Misalignment:** The tokenizer used standard token mappings, while the model's embedding matrix and language modeling head weights were shifted by +1.
2. **Special Tokens Shift:** `<|im_start|>` (standard ID `151644`) mapped to GGUF ID `151645`, and `<|im_end|>` (standard ID `151645`) mapped to GGUF ID `151646`.
3. **Turn Terminator Failure:** During inference, the model generated GGUF token ID `151646` (`<|im_end|>`), but the standard tokenizer decoded it as `<|object_ref_start|>` or failed to recognize it as a stop token.
4. **Junk Token Generation:** At paragraph and turn breaks, the model generated shifted tokens:
   - GGUF `\n\n` (ID `272`) -> decoded by standard tokenizer as `_Parms` (standard ID `78933` / GGUF `78934` `.adjust`).
   - GGUF `\n` (ID `199`) -> decoded as `+lsi` (standard ID `70237` / GGUF `70238` `igrants`).
   - GGUF `唾` (ID `117975`) -> decoded as `具有战士` (standard ID `117975` / GGUF `117976`).
   - GGUF ` preacher` (ID `88754`) -> decoded as `{lng` (standard ID `88754` / GGUF `88755`).

## Solution
Instead of forcing the clean `"unsloth/Qwen2.5-3B-Instruct"` tokenizer, Notebook E and Notebook F have been patched to load the tokenizer directly from the base model folder (`MODEL_NAME` / `BASE_MODEL_NAME`):
```python
# In Notebook E
tokenizer = [REDACTED_SECRET](MODEL_NAME)

# In Notebook F
tokenizer = [REDACTED_SECRET](BASE_MODEL_NAME)
```
Since the tokenizer in the base model folder was saved during the Phase 1 GGUF export, its `tokenizer.json` contains the exact same shifted vocabulary as the model weights. Loading it aligns the tokenizer and the model embeddings 100% perfectly, resolving the runaway generations, junk character emissions, and paragraph-break corruption.

<!-- memory-fabric:store/architecture/opcua-scada-simulation-platform -->
---
store_path: architecture/opcua-scada-simulation-platform
title: "OPC UA Industrial Engine & SCADA Simulation Platform"
summary: "OPC UA Industrial Engine & SCADA Simulation Platform"
priority: high
tags: [opcua, scada, python, asyncua, fastapi, simulation]
schema_version: 1.3
last_updated: "2026-08-12T08:59:21-04:00"
---

Implemented an OPC UA Industrial Engine & SCADA simulation platform using Python asyncua and FastAPI.
Features:
- OPC UA Server: `opc.tcp://0.0.0.0:4840/freeopcua/server/` with namespace `http://opcua.simulation.engine`.
- Device hierarchy: `Objects/IndustrialEngine/` with Folders `Status`, `Sensors`, `Controls`, `Alarms`.
- Telemetry & Physics: RPM, Coolant Temperature, Oil Pressure, Vibration, Total Hours, Trip Counter.
- RPC Methods: `StartEngine`, `StopEngine`, `SetTargetSpeed`, `ResetFault`, `InjectFault`.
- Web SCADA Dashboard: Modern glassmorphism UI running on FastAPI (`http://localhost:8000`), with real-time SVG gauges, multi-pen canvas oscilloscope, OPC UA Node Inspector tree browser, and alarm log.

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
---

## Occurrence 1 — 2026-08-12T08:59:14-04:00

**Error:**
asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node without explicit Variant wrapper

**Fix:**
Wrap variables explicitly using ua.Variant(value, ua.VariantType.UInt16) or ua.VariantType.Double before calling node.write_value()

<!-- memory-fabric:local/bugs -->
---
section: bugs
summary: "Generated map of memory-store/bugs/ (6 entries)."
priority: medium
tags: [bugs]
schema_version: 1.3
last_updated: "2026-07-09T20:55:33-04:00"
generated: true
generated_from: memory-store/bugs
store_fingerprint: a1f2f6c4634f180246ea08ae1d430920
body_hash: 2b2ee3a54693ee207e65bee4b68e32f8
---

# Bugs Map

Generated by Memory Fabric from `memory-store/bugs/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)** (`bugs/ollama-tokenizer-corruption-fix`, high) — Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)
- **Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem** (`bugs/unsloth-embedding-offload-readonly`, high) — Bug Fix: Unsloth Embedding Offload on Read-Only Filesystem
- **Gemma 4 Chat Template Processor Fix** (`bugs/gemma4-chat-template-fix`, medium) — Gemma 4 Chat Template Processor Fix
- **Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA** (`bugs/lora-frozen-embeddings-special-tokens`, medium) — Bug Fix: Training embed_tokens and lm_head when resizing vocabulary for special tokens in LoRA
- **Bug Fix: Resolving SFT Tokenizer Mismatch (vinfos/spepacer)** (`bugs/sft-tokenizer-mismatch-vinfos-spepacer`, medium) — -----
- **Unsloth Training Warnings & Fast Patching Resolution** (`bugs/unsloth-fast-patching-warnings`, medium) — Unsloth Training Warnings & Fast Patching Resolution

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
summary: "Generated map of memory-store/decisions/ (3 entries)."
priority: medium
tags: [decisions, adr]
schema_version: 1.3
last_updated: "2026-07-09T20:55:33-04:00"
generated: true
generated_from: memory-store/decisions
store_fingerprint: 6f919334e005a31fc6d272578d80b89b
body_hash: 4e65a45325db3d2d6e073b5ab909bedf
---

# Decisions Map

Generated by Memory Fabric from `memory-store/decisions/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Gemma 4 Fine-Tuning Transition** (`decisions/gemma4-finetuning`, medium) — Guides the upgrade of fine-tuning pipelines from Gemma 2 to the efficient, newer Gemma 4 12B model.
- **Gemma 4 Local Ollama Deployment** (`decisions/gemma4-local-ollama`, medium) — Gemma 4 Local Ollama Deployment
- **Decisions Map Notes (Pending Review)** (`decisions/map-notes-pending-review`, medium) — Hand-written notes folded from decisions.md; split into granular memories and delete.

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
summary: "Generated map of memory-store/episodic/ (6 entries)."
priority: medium
tags: [episodic]
schema_version: 1.3
last_updated: "2026-08-23T10:13:30-04:00"
generated: true
generated_from: memory-store/episodic
store_fingerprint: 487cb3909649aed6b6b698ff18fdae42
body_hash: f81dabf934045a0632ea43d13ced1e0c
---

# Episodic Map

Generated by Memory Fabric from `memory-store/episodic/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Episodic Journal — 2026-07-11** (`episodic/2026-07-11`, low) — Episodic Journal — 2026-07-11
- **Episodic Journal — 2026-07-12** (`episodic/2026-07-12`, low) — Episodic Journal — 2026-07-12
- **Episodic Journal — 2026-07-13** (`episodic/2026-07-13`, low) — Episodic Journal — 2026-07-13
- **Episodic Journal — 2026-07-14** (`episodic/2026-07-14`, low) — Episodic Journal — 2026-07-14
- **Episodic Journal — 2026-08-12** (`episodic/2026-08-12`, low) — Episodic Journal — 2026-08-12
- **Episodic Journal — 2026-08-23** (`episodic/2026-08-23`, low) — Upgraded and configured memory-fabric / ai-memory to v1.4.0 with field diary enabled (counts+queries)

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
summary: "Generated map of memory-store/failures/ (1 entries)."
priority: medium
tags: [failures]
schema_version: 1.3
last_updated: "2026-08-23T11:09:38-04:00"
generated: true
generated_from: memory-store/failures
store_fingerprint: 9d6c62d3c81c8fd8fee2a48a23649db2
body_hash: dab54d9a054189dd254da37e77372a6a
---

# Failures Map

Generated by Memory Fabric from `memory-store/failures/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi** (`failures/asyncua-write-value-badtypemismatch-188c68c9d2`, medium) — asyncua write_value BadTypeMismatch when writing int to UInt16 or Double node wi

<!-- memory-fabric:local/fine-tuning -->
---
section: fine-tuning
summary: "Generated map of memory-store/fine-tuning/ (3 entries)."
priority: medium
tags: [fine-tuning]
schema_version: 1.3
last_updated: "2026-07-09T20:55:33-04:00"
generated: true
generated_from: memory-store/fine-tuning
store_fingerprint: fe98e678bd0fb9971d56ae6dff68c619
body_hash: 278ba5e10b62da73cf21411862d41055
---

# Fine Tuning Map

Generated by Memory Fabric from `memory-store/fine-tuning/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Gemma 4 Local Dataset Generation Analysis** (`fine-tuning/data-generation-gemma4`, medium) — Gemma 4 Local Dataset Generation Analysis
- **Gemma 2 Fine-Tuning Support** (`fine-tuning/gemma-support`, medium) — Gemma 2 fine-tuning support scripts and configs.
- **Reverting Custom Model, Weight Copying, and ChatML in Qwen 2.5 SFT** (`fine-tuning/qwen-sft-alpaca-reversion`, medium) — Reverting Custom Model, Weight Copying, and ChatML in Qwen 2.5 SFT

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

<!-- memory-fabric:store/bugs/gemma4-chat-template-fix -->
---
store_path: bugs/gemma4-chat-template-fix
title: "Gemma 4 Chat Template Processor Fix"
summary: "Gemma 4 Chat Template Processor Fix"
priority: medium
tags: [gemma4, chat-template, bugfix, unsloth]
schema_version: 1.3
last_updated: "2026-06-05T12:50:30-04:00"
review_status: stale
---

# Bug Fix: Gemma 4 Multimodal Chat Template Processor Error

## Problem
When training or doing inference with Gemma 4 (`unsloth/gemma-4-E4B-it` or `unsloth/gemma-4-12b-it-bnb-4bit`) in Unsloth / transformers, the `from_pretrained` method returns a `Gemma4Processor` instead of a standard text `Tokenizer` because Gemma 4 has multimodal inputs.

When `apply_chat_template(conversation, tokenize=True)` is called on the processor, the processor mixin tries to extract multimodal content (images/videos) by looping over `message["content"]`:
```python
visuals = [content for content in message["content"] if content["type"] in ["image", "video"]]
```
For standard text training and inference datasets where `content` is a string (e.g. `{"role": "user", "content": "question"}`), this loops over characters of the string. Attempting to access `content["type"]` on character strings fails with:
`TypeError: string indices must be integers, not 'str'`.

## Solution
To bypass the processor's multimodal parsing for text-only inputs, we retrieve and use the underlying text tokenizer's chat template directly:
```python
raw_tokenizer = getattr(tokenizer, "tokenizer", tokenizer)
inputs = raw_tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt"
).to("cuda")
```
This has been applied to the following training files:
1. `[REDACTED_SECRET].ipynb` (Inference Cell & Dataset Preparation)
2. `[REDACTED_SECRET].ipynb` (Inference Cell & Dataset Preparation)
3. `fine_tuning/scripts/train_spurgeon_qlora.py` (Dataset formatting function)

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

<!-- memory-fabric:store/decisions/gemma4-local-ollama -->
---
store_path: decisions/gemma4-local-ollama
title: "Gemma 4 Local Ollama Deployment"
summary: "Gemma 4 Local Ollama Deployment"
priority: medium
tags: [gemma4, ollama, gguf, quantization, cleanup]
schema_version: 1.3
last_updated: "2026-06-06T14:08:24-04:00"
review_status: stale
---

# Gemma 4 Local Ollama Deployment

To run the custom fine-tuned model `rafaelvieirar1r/gemma-4-12b-spurgeon-generator` locally in Ollama under strict local disk limits, the following procedure is verified:

## 1. Tokenizer List Parsing Bug Fix
When converting Gemma 4 models using `llama.cpp/convert_hf_to_gguf.py`, older/standard versions of `transformers` (e.g., `4.57.x`) raise `AttributeError: 'list' object has no attribute 'keys'` because the config file contains a list for `extra_special_tokens` instead of a dictionary.
We resolved this by monkey-patching `SpecialTokensMixin._set_model_specific_special_tokens` in `llama.cpp/convert_hf_to_gguf.py` to convert `special_tokens` to a dictionary if it is passed as a list:
```python
if isinstance(special_tokens, list):
    special_tokens = {f"extra_special_token_{i}": tok for i, tok in enumerate(special_tokens)}
```

## 2. Remote Streaming Conversion & Double Quantization
A 12B model in FP16 weighs 24 GB, which would exceed or trigger low-disk warnings on machines with less than 30 GB free space (like our local C drive with 24.17 GB free at the start of the task).
To circumvent this:
1. We stream/quantize the Hugging Face hub weights directly over the network to a temporary `Q8_0` GGUF using the `--remote` flag:
   ```bash
   .venv\Scripts\python.exe llama.cpp/convert_hf_to_gguf.py rafaelvieirar1r/gemma-4-12b-spurgeon-generator --remote --outtype q8_0 --outfile [REDACTED_SECRET].gguf
   ```
   This outputs an 8.0 GB `Q8_0` file rather than a 24 GB file.
2. We quantize the `Q8_0` GGUF down to `Q4_K_M` locally using `llama-quantize.exe` (with `--allow-requantize`):
   ```bash
   .\\llama.cpp\\build\\bin\\Release\\llama-quantize.exe --allow-requantize .\\fine_tuning\\models\\Spurgeon-Gemma4-12B-Q8_0.gguf .\\fine_tuning\\models\\Spurgeon-Gemma4-12B-Q4_K_M.gguf Q4_K_M
   ```
   This generates the target 5.3 GB `Spurgeon-Gemma4-12B-Q4_K_M.gguf` file.
3. We delete the intermediate `Q8_0` file to free up local storage.

## 3. Importing into Ollama
We load the quantized GGUF file into local Ollama using the custom `Modelfile.gemma4` located under `fine_tuning/models/`:
```bash
ollama create spurgeon-gemma4 -f Modelfile.gemma4
```
This registers `spurgeon-gemma4:latest` locally, making it available for local inference.

## 4. Local Disk Cleanup (8B f16 Reclaim)
When registering a new GGUF version in Ollama, Ollama copies/duplicates the GGUF file to its internal blob directory (`C:\Users\rafael\.ollama\models\blobs\...`). Under tight disk space conditions, this requires having at least double the model size (~10.6 GB) free on the C: drive.
To free up sufficient space during conversion, we deleted the obsolete local 16GB `Spurgeon-8B-f16.gguf` file (which had already been uploaded to the remote Hugging Face repository in an earlier phase). This safely reclaimed 16 GB, resolving the `not enough space on the disk` error during the `ollama create` command.

<!-- memory-fabric:local/grok -->
---
section: grok
summary: "Generated map of memory-store/grok/ (1 entries)."
priority: medium
tags: [grok]
schema_version: 1.3
last_updated: "2026-07-09T20:55:33-04:00"
generated: true
generated_from: memory-store/grok
store_fingerprint: cefde72f2c79450a3669cf47b1e1c31a
body_hash: ec354192c5dc09a8da606b85326d70ab
---

# Grok Map

Generated by Memory Fabric from `memory-store/grok/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Grok Integration with Memory Fabric (MCP + Docs + Native Layer)** (`grok/integration`, high) — Grok Integration with Memory Fabric (MCP + Docs + Native Layer)

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

<!-- memory-fabric:store/architecture/map-notes-pending-review -->
---
store_path: architecture/map-notes-pending-review
title: "Architecture Map Notes (Pending Review)"
summary: "Hand-written notes folded from architecture.md; split into granular memories and delete."
priority: medium
tags: [needs-review, legacy-map]
schema_version: 1.3
last_updated: "2026-08-23T11:09:38-04:00"
---

## Folded from `architecture.md` on 2026-08-23T11:09:38-04:00

# Architecture

The Ask Spurgeon application is a RAG (Retrieval-Augmented Generation) system built for search and conversation over Charles Haddon Spurgeon's sermon catalog (~3,500 sermons).

## Core Architecture Layers

- **UI Layer**: Built with **Streamlit** (`app.py`), presenting a conversational and search interface, exposing rich metadata filtering, and providing citation highlights.
- **Orchestration**: Managed via **LlamaIndex**, handling the retrieval pipeline, query compilation, and grounding of LLM prompts.
- **Embeddings**: Local CPU-friendly embedding generation via **FastEmbed** using the `BAAI/bge-small-en-v1.5` model.
- **Vector DB Layer**:
  - **ChromaDB**: Used for local fast development (persists under `./chroma_db`).
  - **Qdrant**: Used in production (Qdrant Cloud Free Tier) and realistic local testing (via Docker Compose).
- **LLM Layer**:
  - **Groq API**: Production default, querying `llama-3.3-70b-versatile` with automated fallback to `llama-3.1-8b-instant` under rate limit constraints.
  - **Custom Fine-tuned LLM**: Local or remote deployment of `spurgeon-8b` (a custom Llama-3.1-8B-Instruct fine-tuned via Unsloth and QLoRA on ~1,500 RAG grounded examples). Quantized to `Q4_K_M` GGUF and served via llama.cpp or Ollama.

## Key Subsystems

- **Bible Reference Extractor (`utils/bible_refs.py`)**: A robust parser that extracts and normalizes Bible verse references at both sermon and chunk levels, enabling users to filter search results by specific scriptural topics.
- **Author-Aware Design**: Chunk and document metadata stores an `author` key, facilitating future extensions to query multiple authors (e.g. Edwards, Calvin, Lloyd-Jones).

<!-- memory-fabric:store/decisions/map-notes-pending-review -->
---
store_path: decisions/map-notes-pending-review
title: "Decisions Map Notes (Pending Review)"
summary: "Hand-written notes folded from decisions.md; split into granular memories and delete."
priority: medium
tags: [needs-review, legacy-map]
schema_version: 1.3
last_updated: "2026-07-09T20:55:33-04:00"
review_status: stale
---

## Folded from `decisions.md` on 2026-07-09T20:55:33-04:00

# Decisions

Record durable decisions and rationale here.

## 1. Custom Model Fine-Tuning & Quantization (2026-06-01)
- **Base Model**: Llama-3.1-8B-Instruct.
- **Method**: QLoRA with Unsloth trained on ~1,500 synthetic examples grounded from RAG queries to emulate Spurgeon's writing style.
- **Quantization**: Merged the weights into 16-bit float and quantized to GGUF `Q4_K_M` (final size: 4.92 GB / 4.89 BPW).
- **Execution Target**: Saved locally under `fine_tuning/models/Spurgeon-8B-Q4_K_M.gguf`. Hosted on Hugging Face Spaces or run locally.

## 2. Memory Systems Integration (2026-06-01 to 2026-06-02)
- **Memory Fabric MCP**: Enabled local project memory management using the `memory-fabric` MCP server. Integrated via a project-root `.mcp.json` mapping to the executable.
- **Cross-Session Memory**: Enabled native Grok-level cross-session memory by setting `[memory] enabled = true` in `~/.grok/config.toml` and seeding a project summary in `~/.grok/memory/search-sermons/MEMORY.md`.

## 3. Deployment & Performance Optimization (2026-06-02)
- **Hugging Face CPU Build Fix**: Added `libopenblas-dev` package and set optimized compilation args (`CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS -DLLAMA_NATIVE=OFF"`) in the Dockerfile. Fixed slow source compiles of `llama-cpp-python`.
- **FastAPI Event Loop Hanger**:
  - Threading: Set `OPENBLAS_NUM_THREADS=1` to prevent conflicts with FastAPI.
  - Async Isolation: Wrapped synchronous model loading and inference inside `asyncio.to_thread` to prevent blocking the main asyncio event loop.
- **Hugging Face 404 Resolution**: Configured generator code to cleanly catch GGUF download exceptions. Promoted usage of Hugging Face Space secrets (`MODEL_REPO` and `MODEL_FILENAME`) to dynamically pull model files.

## 4. Local Execution Options (2026-06-02)
- **Option 1: Ollama (Preferred)**: Bundles native CUDA support without external SDK requirements. Uses a custom `Modelfile` to enforce correct chat prompt formats. Serves on `http://localhost:11434/v1`.
- **Option 2: Native CUDA Server**: Requires NVIDIA CUDA Toolkit 12.4. Launched via a powershell script (`.\fine_tuning\scripts\run_local_gpu.ps1`) that installs CUDA-compatible `llama-cpp-python` wheels, offloads all layers to the GPU, and runs the FastAPI server on `http://localhost:7860/v1`.

## 5. Grok + Memory Fabric Docs & Full Integration (2026-06-05)
- Installed the complete canonical `README.md` from the agentic-memory source into Grok's user-guide as `~/.grok/docs/user-guide/13-memory-fabric.md` (with header explaining it's for Grok help + this project).
- Updated Grok help skill, 07-mcp-servers.md, and 13-memory.md (native) with cross-references and examples for memory-fabric.
- Updated the project's own `~/.grok/memory/search-sermons/MEMORY.md` (Grok native layer) with accurate tool count (15) and reference to the installed docs.
- Added dedicated semantic memory store entry at `grok/integration` (via write_memory_store_tool) documenting the dual-layer setup, config, discovery via search_tool/use_tool, Windows specifics, and how to keep agent files fresh with sync-agents.
- Confirmed `sync-agents` produces no diff (templates already current).
- This completes making the full ai-memory (Memory Fabric) "pronto para uso no Grok" with discoverable docs, explicit agent instructions, and recorded integration decisions.

See the new store entry `grok/integration` and `13-memory-fabric.md` in Grok for full details.

## 6. Kaggle Model Saving Support (2026-06-05)
- **Problem**: The fine-tuning training notebook (`Spurgeon_Gemma4_Training_Kaggle.ipynb`) was Colab-centric, relying on `/content/drive/...` pathing and mounting Google Drive which does not work in Kaggle.
- **Solution**: Added dynamic environment detection (`Colab` vs `Kaggle` vs `Local`). When running on Kaggle, the notebook automatically configures output folders to point to `/kaggle/working/`.
- **Kaggle Upload**: Introduced Section 13 containing credentials loading via Kaggle Secrets (`UserSecretsClient`) and integration hooks for both `kagglehub.model_upload` (Model Hub) and the Kaggle API CLI (Dataset Hub) for programmatic weight uploads.

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

<!-- memory-fabric:local/pretraining -->
---
section: pretraining
summary: "Generated map of memory-store/pretraining/ (15 entries)."
priority: medium
tags: [pretraining]
schema_version: 1.3
last_updated: "2026-08-23T11:09:38-04:00"
generated: true
generated_from: memory-store/pretraining
store_fingerprint: 5813e7f049d78918f5b85beb3f245588
body_hash: 7235c2b672b36eb5963042c93f29b640
---

# Pretraining Map

Generated by Memory Fabric from `memory-store/pretraining/` — do not edit by hand. Write facts with `write_memory_store_tool`; Dreaming rebuilds this map.

- **Confessions + Institutes corpus (WCF, 1689, Calvin)** (`pretraining/confessions-corpus-fetch`, high) — Confessions + Institutes corpus (WCF, 1689, Calvin)
- **CPT SOTA Assessment + Implementation (2026-07)** (`pretraining/cpt-sota-assessment-2026-07`, high) — CPT SOTA Assessment + Implementation (2026-07)
- **CPT v2 implementation (Fable 5 plan)** (`pretraining/cpt-v2-implementation-fable5`, high) — CPT v2 implementation (Fable 5 plan)
- **CPT v2 improvement plan (Fable 5 review, 2026-07-12)** (`pretraining/cpt-v2-plan-fable5`, high) — CPT v2 improvement plan (Fable 5 review, 2026-07-12)
- **CPT v2 ready for Kaggle (post local pipeline)** (`pretraining/cpt-v2-ready-for-kaggle`, high) — CPT v2 ready for Kaggle (post local pipeline)
- **Pretraining Step 10 (Merge & Export to Hugging Face)** (`pretraining/merge-and-export`, high) — Pretraining Step 10 (Merge & Export to Hugging Face)
- **Puritan PD corpus fetch (Archive.org)** (`pretraining/puritan-corpus-fetch`, high) — Puritan PD corpus fetch (Archive.org)
- **Fixed SFTConfig Pickling Mismatch on Kaggle** (`pretraining/bugs/sftconfig-pickle`, medium) — Fixed SFTConfig Pickling Mismatch on Kaggle
- **Pretraining Step 1 — Data Collection Complete** (`pretraining/data-collection`, medium) — Pretraining Step 1 — Data Collection Complete
- **Pretraining Step 6 — Dataset Preparation (Notebook A) Plan** (`pretraining/dataset-preparation`, medium) — Pretraining Step 6 — Dataset Preparation (Notebook A) Plan
- **Pretraining Step 5 — Environment Setup & Configurations** (`pretraining/environment-setup`, medium) — Pretraining Step 5 — Environment Setup & Configurations
- **Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)** (`pretraining/eval-and-export`, medium) — Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)
- **Pretraining Step 4 — Model Choice & Technical Rationale** (`pretraining/model-choice`, medium) — Pretraining Step 4 — Model Choice & Technical Rationale
- **Pretraining Step 3 — Kaggle Notebook Structure** (`pretraining/notebook-structure`, medium) — Pretraining Step 3 — Kaggle Notebook Structure
- …and 1 more entries — see `memory-store/index.md`.

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

<!-- memory-fabric:store/episodic/2026-07-12 -->
---
store_path: episodic/2026-07-12
title: "Episodic Journal — 2026-07-12"
summary: "Episodic Journal — 2026-07-12"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-07-12T14:36:19-04:00"
review_status: stale
---

## cpt-v2-plan

Analyzed baseline B_training.ipynb and the v1 SOTA attempt (B_training_sota.ipynb + 07_build_theology_mix.py + A/C sota notebooks) and wrote a full CPT v2 improvement plan to [REDACTED_SECRET].md. Headline findings: suspected 2048-token document truncation in the baseline run (step-count math: 216 steps/epoch matches one row per doc), Qwen2.5-3B tied-embeddings conflict with the lm_head LoRA target, and the theology mix on disk being 100% Spurgeon because data/puritans|confessions|bible are empty. Plan is phased: diagnostics → data v2 (chunking ≤7k chars, dedup, share-targeted weighting, held-out Heidelberg/Belgic) → training v2 (per-bucket eval, best-model, pinned env) → eval v2 (base/Phase-1 deltas, catechism MCQ metric) → stretch experiments.

**Key decisions:**
- Verify F1 truncation and F3 tied-embeddings via diagnostic cells before any long training run
- Chunk all corpus docs to ≤7,000 chars at mix build (including Spurgeon loader) instead of relying on trainer packing
- Pick spurgeon_weight from target 40–50% char share, not fixed 2.5
- Hold Heidelberg Catechism + Belgic Confession out of training as doctrine-generalization eval
- Catechism MCQ log-likelihood as quantitative doctrine metric
- Single source of truth needed for *_sota notebooks vs _gen_sota_notebooks.py generator

**Files changed:**
- `[REDACTED_SECRET].md`

<!-- memory-fabric:store/episodic/2026-07-13 -->
---
store_path: episodic/2026-07-13
title: "Episodic Journal — 2026-07-13"
summary: "Episodic Journal — 2026-07-13"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-07-13T19:06:23-04:00"
review_status: stale
---

## cpt-v2-model-selection

Extended the CPT v2 plan with a web-verified base-model selection analysis (new §4.1): comparison table of 8 T4-viable candidates, two-tier verdict (Qwen3.5-4B-Base as v2 default, Qwen3.5-9B-Base as flagship, Mistral-7B-v0.3 fallback), M1 verification gate, and cross-base PPL comparability caveat. Surfaced that Qwen2.5-3B's research-only license is a commercial blocker. Updated TL;DR, Phase 0, E3, success criteria, checklist, risk register, and references for consistency.

**Key decisions:**
- v2 default base: Qwen3.5-4B-Base pending M1 gate (HF tie config, Unsloth 4-bit build, D4)
- Flagship run on Qwen3.5-9B-Base after data v2 validates
- Post-base-swap evals use %Δ-vs-own-base, not absolute PPL

**Files changed:**
- `[REDACTED_SECRET].md`

## cpt-plan-4b-flagship-tiering

Folded VRAM/tiering recommendation into PLAN_FABLE5_TO_IMPROVE_CPT.md: Qwen3.5-4B-Base is now the flagship (not just dev default); 9B demoted to concession-gated E3 with mandatory ~20-step VRAM probe (peak reserved < ~15 GB); T4×2 non-Unsloth escape hatch added to risk register. Updated TL;DR §0.6, M1 wording, E3, §4.1 table/verdict, target v2 config, checklist.

- Flagship CPT base = Qwen3.5-4B-Base on single T4 Unsloth path
- 9B requires empirical VRAM probe before multi-session; full recipe over-budget at seq 2048
- T4×2 + drop Unsloth generally not worth it vs 4B

## implement-cpt-v2-fable5

Implemented PLAN_FABLE5_TO_IMPROVE_CPT.md in code: mix builder v2 (7k chunking, G2 guard, dedup, share targeting, bible cap), token verify --mix, PD fetch helper, catechism MCQ builder, full A/B/C sota notebook regeneration for Qwen3.5-4B flagship with diagnostics and eval v2. Seeded Bunyan+KJV+WSC and Heidelberg holdout; rebuilt multi-bucket mix. Kaggle train/M1 still operator-side.

- G3: _gen_sota_notebooks.py is sole source of truth for *_sota notebooks
- Flagship model in notebooks/config: unsloth/Qwen3.5-4B-Base
- Bible capped at 4% share so KJV does not dominate thin Puritan sets
- Heidelberg curated holdout; WSC curated for training + MCQ

- `continued_pretrain/scripts/06_verify_tokens.py`
- `continued_pretrain/scripts/08_fetch_pd_sources.py`
- `continued_pretrain/scripts/09_build_catechism_mcq.py`

## fetch-puritan-corpus

Downloaded public-domain Puritan texts from Internet Archive (Owen, Watson, Sibbes, Brooks, Baxter, Flavel, Gurnall, Edwards) plus Bunyan extras into data/puritans/ (~18 MB). Added 10_fetch_puritans.py and PROVENANCE.md; rebuilt theology mix to ~22M chars with ~51% Puritan share.

- Prefer Archive.org /download/ DjVuTXT over /stream/ HTML shells
- Title-verify downloads; allow relaxed OCR match for Sibbes
- Remove duplicate Owen temptation file identical to mortification volume

- `data/puritans/`
- `data/puritans/PROVENANCE.md`
- `continued_pretrain/scripts/10_fetch_puritans.py`
- `continued_pretrain/data/theology_mix_train.txt`
- `continued_pretrain/data/theology_mix_manifest.json`

## fetch-confessions-institutes

Fetched WCF, Scottish WCF+catechisms edition, Calvin Institutes Beveridge vols 1–2, and curated 1689 LBCF into data/confessions/. Added 11_fetch_confessions.py and confession share cap (6%). Rebuilt mix: ~25M chars, confession ~5.6%, spurgeon 45%, puritan 45%, bible 4%.

- Prefer Archive.org DjVuTXT for WCF and Beveridge Institutes
- 1689 uses curated PD core chapters when IA lacks clean full text
- Cap confession share at 6% so Institutes does not swamp mix

- `data/confessions/`
- `continued_pretrain/scripts/11_fetch_confessions.py`

## cpt-v2-continue-kaggle-ready

Continued Fable5 plan to Kaggle-ready state: M1 gate (tied embeddings, hybrid qwen3_5, TRAIN_LM_HEAD=False), Belgic holdout, 10% PD general replay (~8.7M chars), full mix rebuild (~27M chars, shares on target), D3 verified_tokens (~8.2M tok), regenerated notebooks, Kaggle package script + KAGGLE_RUNBOOK_V2.md. Remaining work is operator upload/train on T4.

- M1: default TRAIN_LM_HEAD=False for Qwen3.5-4B-Base tied embeddings
- Offline Gutenberg classics as replay instead of FineWeb (no datasets required)
- Hybrid qwen3_5 architecture is a Kaggle risk — document fallback to Qwen2.5-3B

- `continued_pretrain/data/holdouts_manual/belgic_confession.txt`
- `continued_pretrain/data/replay/`
- `continued_pretrain/scripts/12_package_kaggle_corpus.py`
- `continued_pretrain/KAGGLE_RUNBOOK_V2.md`

## cpt-v2-preflight-max-steps

Added local preflight script (D1/D2-lite, G2, shares, holdouts) — PASS. Set MAX_STEPS=250 from D3 token math in B_sota/config. Regenerated notebooks, repackaged Kaggle zip. Plan checklist updated: all local gates done; remaining is Kaggle upload/train/eval only.

- MAX_STEPS=250 for ~1 epoch given ~8.2M tokens and 32768 tok/step
- Offline preflight required before Kaggle upload
- D4 decision locked to TRAIN_LM_HEAD=False from M1 config

- `continued_pretrain/scripts/13_local_preflight.py`
- `continued_pretrain/data/preflight_report.json`

<!-- memory-fabric:store/episodic/2026-07-14 -->
---
store_path: episodic/2026-07-14
title: "Episodic Journal — 2026-07-14"
summary: "Episodic Journal — 2026-07-14"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-07-13T21:12:31-04:00"
review_status: stale
---

## fn-sft-plan-fable5

Reviewed the SFT pipeline (fine_tuning/notebooks D/E/F + spurgeon_qa_train_final.jsonl + serving config) and wrote PLAN_FABLE5_TO_IMPROVE_FN.md, the SFT counterpart to PLAN_FABLE5_TO_IMPROVE_CPT.md. The plan chains SFT on the CPT v2 output (theology_cpt_v2_merged_hf, Qwen3.5-4B-Base) behind a GATE-0 dependency, with dev runs allowed on stock Qwen3.5-4B-Base in parallel. Audit found the pipeline never actually trained on Spurgeon data: E_qa_training.ipynb is the stock Unsloth Alpaca demo whose recorded run trained 60 steps on yahma/alpaca-cleaned (51,760 examples), with a three-way template mismatch (D=ChatML, E=Alpaca, F=ChatML), no completion-only masking, a vocab-resized <|PAD_TOKEN|> id 151665 (the known GGUF corruption trigger), and an ungated GGUF export that uploaded a broken model to HF.

**Key decisions:**
- SFT v2 base model = CPT v2 merged output (GATE-0: CPT §5 gate passed + Kaggle dataset theology-cpt-v2/theology_cpt_v2_merged_hf); never chain shippable work on spurgeon_phase1_merged_hf (Qwen2.5-3B, non-commercial license, truncation-tainted)
- One canonical ChatML template from the CPT-v2 tokenizer across data prep/training/eval/Modelfile; eos <|im_end|>; pad = existing token; never resize vocab
- Training data must be serve-shaped: real retriever output with [Sermon ...] headers, k=1-5 chunks, canonical persona system prompt in config.py; app side drops similarity_top_k from 6 to 4 for the fine-tuned path; MAX_SEQ_LENGTH=4096
- Data mix v2 ~5.5-6.5k examples: 60% serve-shaped grounded QA / 15% legacy refiltered / 12% refusals / 8% catechism QA / 3% persona redirects / 2-5% multi-turn; judge-filtered + deduped + manifest with empty-slice guard + frozen 100-question test set
- train_on_responses_only mandatory with an S3 masking audit; LoRA r=32 a=32 attn+MLP, lr 1e-4 cosine, 2 epochs, load_best_model_at_end
- GGUF/HF export gated on quantified eval (faithfulness >=4.0, refusal accuracy >=85%, echo rate <=2%, blind A/B >=60% vs Groq-70B path)

**Files changed:**
- `[REDACTED_SECRET].md`

<!-- memory-fabric:store/episodic/2026-08-12 -->
---
store_path: episodic/2026-08-12
title: "Episodic Journal — 2026-08-12"
summary: "Episodic Journal — 2026-08-12"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-12T09:00:43-04:00"
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

<!-- memory-fabric:store/episodic/2026-08-23 -->
---
store_path: episodic/2026-08-23
title: "Episodic Journal — 2026-08-23"
summary: "Upgraded and configured memory-fabric / ai-memory to v1.4.0 with field diary enabled (counts+queries)"
priority: low
tags: [episodic, session-journal]
schema_version: 1.3
last_updated: "2026-08-23T10:13:30-04:00"
---

## upgrade-memory-fabric-diary

Upgraded and configured memory-fabric / ai-memory to v1.4.0 with field diary enabled (counts+queries). Configured all MCP clients and synchronized agent instruction sets.

**Key decisions:**
- Upgraded memory-fabric via uv tool to v1.4.0
- Approved and enabled field diary at level counts+queries
- Configured all MCP clients to use direct binary execution
- Ran ai-memory sync-agents to synchronize agent instructions

**Files changed:**
- `IMPLEMENTATION_SUMMARY.md`

<!-- memory-fabric:local/debt -->
---
section: debt
summary: "Tracks technical debt (e.g., pure vector search, rate limiting) and roadmap items like multi-author support and automated ingestion."
priority: low
tags: [debt, risk]
schema_version: 1.3
last_updated: "2026-06-03T08:33:16-04:00"
summary_hash: 7afd302688cef326194440331d0c034f
review_status: stale
---

# Technical Debt & Roadmap

This section tracks outstanding technical debt, limitations, and future development opportunities.

## Known Technical Debt & Limits

- **Pure Vector Search Limitation**: The search currently relies entirely on semantic vector queries. This can occasionally miss exact bible reference keywords (e.g., searching for "Romans 8:28" might retrieve similar theological themes rather than the exact sermon). A hybrid search mechanism (BM25 + Vector) is needed to resolve this.
- **PDF Text Quality**: Ingestion from raw PDF sources yields lower text quality due to historical scans and OCR artifacts compared to the community markdown files. Ingestion should prioritize the markdown source.
- **Session-Based Rate Limiting**: The current query limit (8 queries/hour) is session-restricted in Streamlit memory, which can be bypassed by reloading the browser. A more robust server-side IP/token tracker is needed for production scaling.

## Roadmap & Pending Features

- **Multi-Author Interface**: While the data schema is author-aware, the application UI and prompt logic currently assume Charles Spurgeon is the single author. Support needs to be added for comparative queries (e.g., comparing Spurgeon and Jonathan Edwards on the same topic).
- **Weekly Automated Ingestion**: Set up automated pipelines to pull weekly updates from `lyteword/chspurgeon-sermons` to keep the vector database aligned with the community's latest transcriptions.
- **Mobile Styling**: Streamlit layouts require additional custom CSS injections to optimize readability and sidebar responsiveness on smaller mobile displays.
