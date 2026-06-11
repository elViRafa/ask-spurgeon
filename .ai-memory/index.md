---
section: index
summary: "Map of available project memory sections."
priority: high
tags: [index, memory]
schema_version: 1.3
last_updated: "2026-06-11T10:46:51-04:00"
consolidation_hash: dc4febef829d2344ced791190b2a66be
contradictions: []
consolidation_warnings: []
summary_hash: c81ed9efe309125e42b693ba950f4f04
---

# Project Memory Index

Updated by Memory Fabric Dreaming mode `light` at 2026-06-11T10:46:51-04:00.

| Section | Priority | Summary | Key Topics |
| --- | --- | --- | --- |
| `architecture` | high | Defines the RAG architecture for Spurgeon's sermons, detailing layers from Streamlit UI to Chroma/Qdrant vector DBs and LLM providers. | • Core Architecture Layers<br>• Key Subsystems |
| `debt` | low | Tracks technical debt (e.g., pure vector search, rate limiting) and roadmap items like multi-author support and automated ingestion. | • Known Technical Debt & Limits<br>• Roadmap & Pending Features |
| `decisions` | medium | Details model fine-tuning, memory integration, performance fixes (FastAPI/OpenBLAS), and local execution options (Ollama/CUDA). | • 1. Custom Model Fine-Tuning & Quantization (2026-06-01)<br>• 2. Memory Systems Integration (2026-06-01 to 2026-06-02)<br>• 3. Deployment & Performance Optimization (2026-06-02)<br>• 4. Local Execution Options (2026-06-02)<br>• 5. Grok + Memory Fabric Docs & Full Integration (2026-06-05)<br>• 6. Kaggle Model Saving Support (2026-06-05) |
| `framework-rules` | medium | Defines coding standards, required libraries (Streamlit, LlamaIndex), environment setup (.env), and database rules for the codebase. | • 1. Runtime Environment<br>• 2. Core Libraries & Packages<br>• 3. Vector Database Rules<br>• 4. Agent Memory Guidelines |
| `schemas` | high | Defines data contracts, metadata schemas for ingested texts, and environment variable configurations. | • 1. Document & Chunk Metadata Schema<br>• 2. Ingestion Parameters<br>• 3. Environment Variables (Configuration Schema) |
| `ubiquitous-language` | medium | Defines consistent domain language used throughout the codebase for clarity and shared understanding. | None recorded |

## Memory Store

Please see the dedicated [Memory Store Index](memory-store/index.md) for a map of available semantic memory store files.
