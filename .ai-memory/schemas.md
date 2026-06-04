---
section: schemas
summary: "Defines data contracts, metadata schemas for ingested texts, and environment variable configurations."
priority: high
tags: [schemas, contracts]
schema_version: 1.3
last_updated: "2026-06-03T08:33:40-04:00"
summary_hash: e0fe7d0aa73fa2f3f2226b9a4b4b16f9
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
