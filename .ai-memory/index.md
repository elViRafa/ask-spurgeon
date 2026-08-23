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
