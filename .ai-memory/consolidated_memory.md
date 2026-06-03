<!-- memory-fabric:local/index -->
---
section: index
summary: "Map of available project memory sections."
priority: high
tags: [index, memory]
schema_version: 1.3
last_updated: "2026-06-03T08:33:50-04:00"
consolidation_hash: eae938c84e51afe555b7f9cb6e0d2fb4
contradictions: []
consolidation_warnings: []
---

# Project Memory Index

Updated by Memory Fabric Dreaming mode `light` at 2026-06-03T08:33:50-04:00.

| Section | Priority | Summary | Key Topics |
| --- | --- | --- | --- |
| `architecture` | high | Defines the system's core architectural context; consult for high-level design decisions. | • Core Architecture Layers<br>• Key Subsystems |
| `debt` | low | Tracks technical debt, noting known risks and necessary code cleanup tasks for future reference. | • Known Technical Debt & Limits<br>• Roadmap & Pending Features |
| `decisions` | medium | Details model fine-tuning, memory integration, and local deployment strategies for LLM inference. | • 1. Custom Model Fine-Tuning & Quantization (2026-06-01)<br>• 2. Memory Systems Integration (2026-06-01 to 2026-06-02)<br>• 3. Deployment & Performance Optimization (2026-06-02)<br>• 4. Local Execution Options (2026-06-02) |
| `framework-rules` | medium | Defines project-wide coding standards, requiring Python 3.11+ and using pytest for all unit testing. | • 1. Runtime Environment<br>• 2. Core Libraries & Packages<br>• 3. Vector Database Rules<br>• 4. Agent Memory Guidelines |
| `schemas` | high | Defines critical data structures and contracts for consistent application-wide data handling. | • 1. Document & Chunk Metadata Schema<br>• 2. Ingestion Parameters<br>• 3. Environment Variables (Configuration Schema) |
| `ubiquitous-language` | medium | Defines consistent domain language used throughout the codebase for clarity and shared understanding. | None recorded |

<!-- memory-fabric:local/architecture -->
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

<!-- memory-fabric:local/schemas -->
---
section: schemas
summary: "Defines critical data structures and contracts for consistent application-wide data handling."
priority: high
tags: [schemas, contracts]
schema_version: 1.3
last_updated: "2026-06-03T08:33:40-04:00"
summary_hash: b3b07bd428a50a2feac2c6473b6abb02
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
LLM_PROVIDER=groq|openai
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

<!-- memory-fabric:local/decisions -->
---
section: decisions
summary: "Details model fine-tuning, memory integration, and local deployment strategies for LLM inference."
priority: medium
tags: [decisions, adr]
schema_version: 1.3
last_updated: "2026-06-03T08:33:24-04:00"
summary_hash: c9f68144d5138d88c179236ec40a6546
---

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

<!-- memory-fabric:local/framework-rules -->
---
section: framework-rules
summary: "Defines project-wide coding standards, requiring Python 3.11+ and using pytest for all unit testing."
priority: medium
tags: [framework, rules]
schema_version: 1.3
last_updated: "2026-06-03T08:33:33-04:00"
summary_hash: 558f00833027bc0a96a2d499ad428a31
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
---

# Ubiquitous Language

Record project terminology here.

<!-- memory-fabric:local/debt -->
---
section: debt
summary: "Tracks technical debt, noting known risks and necessary code cleanup tasks for future reference."
priority: low
tags: [debt, risk]
schema_version: 1.3
last_updated: "2026-06-03T08:33:16-04:00"
summary_hash: 35d09f7cc83f7a612e143ede7aed0ff4
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
