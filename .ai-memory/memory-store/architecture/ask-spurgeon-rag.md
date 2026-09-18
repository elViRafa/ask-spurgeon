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
