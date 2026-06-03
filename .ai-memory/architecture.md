---
section: architecture
summary: "Defines the system's core architectural context; consult for high-level design decisions."
priority: high
tags: [architecture]
schema_version: 1.3
last_updated: "2026-06-03T08:33:08-04:00"
summary_hash: d3946a64beefbe228f73fc781b7c1a44
---

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
