---
section: index
summary: "Map of available project memory sections."
priority: high
tags: [index, memory]
schema_version: 1.3
last_updated: "2026-09-26T15:07:26-03:00"
consolidation_hash: acd058fab27bf79aa31f9bd2e3dc7172
contradictions: ["`fine-tuning/hf-spurgeon-qa-v2-gguf` and `fine-tuning/plans/ollama-merge-gguf` cover similar content but state different numbers (2.71 vs 07) - review for conflict [heuristic]", "`pretraining/cpt-b-eval-strategy` and `pretraining/cpt-eval-unify-vs-buckets` cover similar content but state different numbers (0 / 1650 / 17 vs 0.2 / 1.2 / 18) - review for conflict [heuristic]", "`pretraining/cpt-corpus-v3-s1-complete` and `pretraining/cpt-corpus-v3-s1-wave1` cover similar content but state different numbers (0.282874 / 0.658552 / 0.7 vs 0.10 / 0.164 / 0.45) - review for conflict [heuristic]", "`pretraining/cpt-phase-b-mix-a-output-v4` and `pretraining/cpt-phase-b-v5-reweight-ready` cover similar content but state different numbers (0.2848 / 251 / 38.4 vs 0.2701 / 029 / 096) - review for conflict [heuristic]", "`bugs/lora-frozen-embeddings-special-tokens` and `bugs/sft-tokenizer-mismatch-vinfos-spepacer` disagree about `im_start` (pos vs neg) - review for conflict [polarity]"]
consolidation_warnings: []
summary_hash: c81ed9efe309125e42b693ba950f4f04
contradiction_count: 50
---

# Project Memory Index

Updated by Memory Fabric Dreaming mode `light`.

| Section | Priority | Summary | Key Topics |
| --- | --- | --- | --- |
| `architecture` | high | Generated map of memory-store/architecture/ (1 entries). | • **Ask Spurgeon Rag** (`architecture/ask-spurgeon-rag`, me... |
| `bugs` | medium | Generated map of memory-store/bugs/ (7 entries). | • **Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)*...<br>• **Qwen3.5 processor text-as-image in C_eval** (`bugs/qwen...<br>• **Bug Fix: Unsloth Embedding Offload on Read-Only Filesys... |
| `debt` | low | App debt (hybrid search, rate limits) plus 2026-08-29 memory-fabric LLM/host hygiene notes. | • Known Technical Debt & Limits<br>• Roadmap & Pending Features |
| `decisions` | medium | Generated map of memory-store/decisions/ (2 entries). | • **Gemma 4 Fine-Tuning Transition** (`decisions/gemma4-fin...<br>• **Gemma 4 Local Ollama Deployment** (`decisions/gemma4-lo... |
| `episodic` | medium | Generated map of memory-store/episodic/ (30 entries). | • **Episodic Journal — 2026-07-11** (`episodic/2026-07-11`,...<br>• **Episodic Journal — 2026-07-12** (`episodic/2026-07-12`,...<br>• **Episodic Journal — 2026-07-13** (`episodic/2026-07-13`,... |
| `failures` | medium | Generated map of memory-store/failures/ (32 entries). | • **Vast official Unsloth image smoke blocked; LD_LIBRARY_P...<br>• **asyncua write_value BadTypeMismatch when writing int to...<br>• **B_training_sota: EarlyStopping disabled — metric_for_be... |
| `fine-tuning` | medium | Generated map of memory-store/fine-tuning/ (39 entries). | • **Fine-tuning next session handoff** (`fine-tuning/next-s...<br>• **SFT QA gold rewrite pilot (20 rows, merged)** (`fine-tu...<br>• **SFT/serve: knowledge assistant, not Spurgeon persona** ... |
| `framework-rules` | medium | Defines coding standards, required libraries (Streamlit, LlamaIndex), environment setup (.env), and database rules for the codebase. | • 1. Runtime Environment<br>• 2. Core Libraries & Packages<br>• 3. Vector Database Rules<br>• 4. Agent Memory Guidelines |
| `grok` | medium | Generated map of memory-store/grok/ (3 entries). | • **Grok Bot Forge for Vast/Runpod training** (`grok/forge-...<br>• **Grok Bot Foundry for train/export code** (`grok/foundry...<br>• **Grok Integration with Memory Fabric (MCP + Docs + Nativ... |
| `pretraining` | medium | Generated map of memory-store/pretraining/ (85 entries). | • **CPT B_training_sota known issues (P1 closed — log spam)...<br>• **Composite CPT early stop merges split HF eval events** ...<br>• **Confessions + Institutes corpus (WCF, 1689, Calvin)** (... |
| `schemas` | high | Defines data contracts, metadata schemas for ingested texts, and environment variable configurations. | • 1. Document & Chunk Metadata Schema<br>• 2. Ingestion Parameters<br>• 3. Environment Variables (Configuration Schema) |
| `ubiquitous-language` | medium | Defines consistent domain language used throughout the codebase for clarity and shared understanding. | None recorded |

## Memory Store

Please see the dedicated [Memory Store Index](memory-store/index.md) for a map of available semantic memory store files.
