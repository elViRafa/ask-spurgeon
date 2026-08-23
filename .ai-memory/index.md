---
section: index
summary: "Map of available project memory sections."
priority: high
tags: [index, memory]
schema_version: 1.3
last_updated: "2026-07-09T20:56:16-04:00"
consolidation_hash: dc4febef829d2344ced791190b2a66be
contradictions: []
consolidation_warnings: []
summary_hash: c81ed9efe309125e42b693ba950f4f04
---

# Project Memory Index

Updated by Memory Fabric Dreaming mode `light`.

| Section | Priority | Summary | Key Topics |
| --- | --- | --- | --- |
| `architecture` | high | Defines the RAG architecture for Spurgeon's sermons, detailing layers from Streamlit UI to Chroma/Qdrant vector DBs and LLM providers. | • Core Architecture Layers<br>• Key Subsystems |
| `bugs` | medium | Generated map of memory-store/bugs/ (6 entries). | • **Bug Fix: GGUF Vocab Shift and Alignment (具有战士/ _Parms)*...<br>• **Bug Fix: Unsloth Embedding Offload on Read-Only Filesys...<br>• **Gemma 4 Chat Template Processor Fix** (`bugs/gemma4-cha... |
| `debt` | low | Tracks technical debt (e.g., pure vector search, rate limiting) and roadmap items like multi-author support and automated ingestion. | • Known Technical Debt & Limits<br>• Roadmap & Pending Features |
| `decisions` | medium | Generated map of memory-store/decisions/ (3 entries). | • **Gemma 4 Fine-Tuning Transition** (`decisions/gemma4-fin...<br>• **Gemma 4 Local Ollama Deployment** (`decisions/gemma4-lo...<br>• **Decisions Map Notes (Pending Review)** (`decisions/map-... |
| `fine-tuning` | medium | Generated map of memory-store/fine-tuning/ (3 entries). | • **Gemma 4 Local Dataset Generation Analysis** (`fine-tuni...<br>• **Gemma 2 Fine-Tuning Support** (`fine-tuning/gemma-suppo...<br>• **Reverting Custom Model, Weight Copying, and ChatML in Q... |
| `framework-rules` | medium | Defines coding standards, required libraries (Streamlit, LlamaIndex), environment setup (.env), and database rules for the codebase. | • 1. Runtime Environment<br>• 2. Core Libraries & Packages<br>• 3. Vector Database Rules<br>• 4. Agent Memory Guidelines |
| `grok` | medium | Generated map of memory-store/grok/ (1 entries). | • **Grok Integration with Memory Fabric (MCP + Docs + Nativ... |
| `pretraining` | medium | Generated map of memory-store/pretraining/ (9 entries). | • **Pretraining Step 10 (Merge & Export to Hugging Face)** ...<br>• **Fixed SFTConfig Pickling Mismatch on Kaggle** (`pretrai...<br>• **Pretraining Step 1 — Data Collection Complete** (`pretr... |
| `schemas` | high | Defines data contracts, metadata schemas for ingested texts, and environment variable configurations. | • 1. Document & Chunk Metadata Schema<br>• 2. Ingestion Parameters<br>• 3. Environment Variables (Configuration Schema) |
| `ubiquitous-language` | medium | Defines consistent domain language used throughout the codebase for clarity and shared understanding. | None recorded |

## Memory Store

Please see the dedicated [Memory Store Index](memory-store/index.md) for a map of available semantic memory store files.
