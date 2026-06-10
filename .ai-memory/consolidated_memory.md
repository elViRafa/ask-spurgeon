<!-- memory-fabric:local/index -->
---
section: index
summary: "Map of available project memory sections."
priority: high
tags: [index, memory]
schema_version: 1.3
last_updated: "2026-06-09T18:50:28-04:00"
consolidation_hash: dc4febef829d2344ced791190b2a66be
contradictions: []
consolidation_warnings: []
summary_hash: c81ed9efe309125e42b693ba950f4f04
---

# Project Memory Index

Updated by Memory Fabric Dreaming mode `light` at 2026-06-09T18:50:28-04:00.

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

<!-- memory-fabric:local/architecture -->
---
section: architecture
summary: "Defines the RAG architecture for Spurgeon's sermons, detailing layers from Streamlit UI to Chroma/Qdrant vector DBs and LLM providers."
priority: high
tags: [architecture]
schema_version: 1.3
last_updated: "2026-06-03T08:33:08-04:00"
summary_hash: bfa6b46d9eb00a6552e658b497cc91ad
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

<!-- memory-fabric:local/decisions -->
---
section: decisions
summary: "Details model fine-tuning, memory integration, performance fixes (FastAPI/OpenBLAS), and local execution options (Ollama/CUDA)."
priority: medium
tags: [decisions, adr]
schema_version: 1.3
last_updated: "2026-06-05T10:06:40-04:00"
summary_hash: b3f7967650eea7bea2eee8fb73f743be
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

<!-- memory-fabric:local/framework-rules -->
---
section: framework-rules
summary: "Defines coding standards, required libraries (Streamlit, LlamaIndex), environment setup (.env), and database rules for the codebase."
priority: medium
tags: [framework, rules]
schema_version: 1.3
last_updated: "2026-06-03T08:33:33-04:00"
summary_hash: f0dd594251d74f0ce1c3d34410c1767e
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
summary: "Tracks technical debt (e.g., pure vector search, rate limiting) and roadmap items like multi-author support and automated ingestion."
priority: low
tags: [debt, risk]
schema_version: 1.3
last_updated: "2026-06-03T08:33:16-04:00"
summary_hash: 7afd302688cef326194440331d0c034f
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

<!-- memory-fabric:store/bugs/gemma4-chat-template-fix -->
---
store_path: bugs/gemma4-chat-template-fix
title: "Gemma 4 Chat Template Processor Fix"
summary: "Gemma 4 Chat Template Processor Fix"
priority: medium
tags: [gemma4, chat-template, bugfix, unsloth]
schema_version: 1.3
last_updated: "2026-06-05T12:50:30-04:00"
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

<!-- memory-fabric:store/bugs/unsloth-fast-patching-warnings -->
---
store_path: bugs/unsloth-fast-patching-warnings
title: "Unsloth Training Warnings & Fast Patching Resolution"
summary: "Unsloth Training Warnings & Fast Patching Resolution"
priority: medium
tags: [unsloth, lora, gemma4, bugfix]
schema_version: 1.3
last_updated: "2026-06-06T12:04:12-04:00"
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

<!-- memory-fabric:store/fine-tuning/data-generation-gemma4 -->
---
store_path: fine-tuning/data-generation-gemma4
title: "Gemma 4 Local Dataset Generation Analysis"
summary: "Gemma 4 Local Dataset Generation Analysis"
priority: medium
tags: [fine-tuning, gemma4, dataset, ollama]
schema_version: 1.3
last_updated: "2026-06-08T12:46:23-04:00"
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
---

# Gemma 2 Fine-Tuning Support

Parameterized scripts and config files to support fine-tuning Gemma 2 models (like unsloth/gemma-2-9b-it-bnb-4bit) matching local gemma4 configurations.

- Updated train_spurgeon_qlora.py to read base model and chat template (gemma2) via CLI args.
- Configured launch_training.py to pass parameters dynamically from configuration files.
- Added train_config_gemma.json configuration file.
- Created Spurgeon_Gemma2_Training_Colab.ipynb for Colab training and Modelfile.gemma for Ollama import.

<!-- memory-fabric:store/grok/integration -->
---
store_path: grok/integration
title: "Grok Integration with Memory Fabric (MCP + Docs + Native Layer)"
summary: "Grok Integration with Memory Fabric (MCP + Docs + Native Layer)"
priority: high
tags: [grok, mcp, memory-fabric, integration, docs, agents]
schema_version: 1.3
last_updated: "2026-06-05T09:41:35-04:00"
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

<!-- memory-fabric:store/pretraining/bugs/sftconfig-pickle -->
---
store_path: pretraining/bugs/sftconfig-pickle
title: "Fixed SFTConfig Pickling Mismatch on Kaggle"
summary: "Fixed SFTConfig Pickling Mismatch on Kaggle"
priority: medium
tags: [pretraining, unsloth, trl, sftconfig, pickle, bug-fix]
schema_version: 1.3
last_updated: "2026-06-07T06:33:34-04:00"
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

<!-- memory-fabric:store/pretraining/data-collection -->
---
store_path: pretraining/data-collection
title: "Pretraining Step 1 — Data Collection Complete"
summary: "Pretraining Step 1 — Data Collection Complete"
priority: medium
tags: [pretraining, dataset, sermons]
schema_version: 1.3
last_updated: "2026-06-06T18:50:44-04:00"
---

Domain audit complete: 3,536 sermons (129.60 MB, 129.6M chars) across 63 volumes. Created 50-sermon holdout split in data/chspurgeon-holdout. Flagged two oversized multi-sermon files in volumes 5 and 7.

<!-- memory-fabric:store/pretraining/dataset-preparation -->
---
store_path: pretraining/dataset-preparation
title: "Pretraining Step 6 — Dataset Preparation (Notebook A) Plan"
summary: "Pretraining Step 6 — Dataset Preparation (Notebook A) Plan"
priority: medium
tags: [pretraining, dataset, kaggle, huggingface]
schema_version: 1.3
last_updated: "2026-06-06T19:38:20-04:00"
---

Documents the environment settings, directory layout, code cells, and verification diagnostics for Step 6: Dataset Preparation of Phase 1 of the Charles Spurgeon continued pretraining pipeline.

### Details:
- **Notebook A (`data_prep.ipynb`)** runs on CPU-only (accelerator: None) with Internet ON to preserve GPU quota.
- Ingests the cleaned training set `spurgeon_train.txt` and holdout set `spurgeon_holdout.txt` from `/kaggle/input/`.
- Splits text documents on the `<|endoftext|>` marker, filtering out short segments (< 200 chars).
- Partitions the training corpus into a 99% train and 1% validation split (`train_test_split`).
- Saves the resulting binary datasets (`spurgeon_dataset` and `spurgeon_holdout_dataset`) to `/kaggle/working/` using `save_to_disk`.
- The output datasets are versioned as a private Kaggle dataset named `spurgeon-cpt-dataset` to be mounted as input for Notebook B (`training.ipynb`).

<!-- memory-fabric:store/pretraining/environment-setup -->
---
store_path: pretraining/environment-setup
title: "Pretraining Step 5 — Environment Setup & Configurations"
summary: "Pretraining Step 5 — Environment Setup & Configurations"
priority: medium
tags: [pretraining, environment, kaggle, config, secrets]
schema_version: 1.3
last_updated: "2026-06-06T19:35:50-04:00"
---

Execution configurations and dependency management rules for continued pretraining on Kaggle Free Tier. Guidelines specify toggling Internet ON, choosing None accelerator for Notebook A (Data Prep) to conserve quota, and selecting 1x T4 GPU for Notebook B/C. Installation relies solely on `unsloth[kaggle-new]` package pulling from GitHub, with a strict warning against manual upgrades of transformers/trl/peft to avoid breaking CUDA Triton kernels. Detailed setup includes programmatic Hugging Face token authentication via Kaggle Secrets (HF_TOKEN) and optional Weights & Biases training logs tracking (WANDB_API_KEY).

<!-- memory-fabric:store/pretraining/eval-and-export -->
---
store_path: pretraining/eval-and-export
title: "Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)"
summary: "Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)"
priority: medium
tags: [pretraining, schedule, evaluation, export, notebook-c, perplexity]
schema_version: 1.3
last_updated: "2026-06-08T07:34:40-04:00"
---

# Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export)

Following the successful execution of Notebook B (Epoch 1 & 2) up to step 432:
1. **Pretraining Schedule Updated:** Timeline has been updated to bypass Epoch 3 and proceed directly to evaluation and merge. v2 of the private Kaggle dataset `spurgeon-training-run-1` carries the `checkpoint-432` weights and files forward.
2. **Notebook C Plan created:** Step 9 details the evaluation requirements (1x T4 GPU, Internet ON), input dataset mounts, loading the adapter via Unsloth's native `FastLanguageModel.from_pretrained()`, computing length-weighted perplexity on the 50-sermon holdout dataset, executing qualitative prompts, and exporting the final Phase 1 LoRA adapter weights.
3. **Jupyter Notebook Template created:** The evaluation template has been created at `continued_pretrain/notebooks/C_eval_and_merge.ipynb`.

<!-- memory-fabric:store/pretraining/merge-and-export -->
---
store_path: pretraining/merge-and-export
title: "Pretraining Step 10 (Merge & Export to Hugging Face)"
summary: "Pretraining Step 10 (Merge & Export to Hugging Face)"
priority: high
tags: [pretraining, merge, export, gguf, huggingface, upload]
schema_version: 1.3
last_updated: "2026-06-08T10:18:26-04:00"
---

# Pretraining Step 10 (Merge & Export to Hugging Face)

Step 10 of the continued pretraining plan has been successfully completed:
1. **Model Weights Merged:** The trained Phase 1 LoRA adapter weights (from checkpoint-432) were merged back into the base Qwen2.5-3B model.
2. **GGUF Conversion (F16 Precision):** The merged model was converted to GGUF format with original 16-bit (`f16`) precision on Kaggle, preserving 100% of the pretraining model quality.
3. **Hugging Face Hub Upload:** The GGUF file (`qwen2.5-3b.F16.gguf` under `/kaggle/working/spurgeon_f16_gguf_gguf/`) was successfully uploaded to the Hugging Face model repository `rafaelvieirar1r/qwen2.5-3b-spurgeon-gguf-phase1` using the user's secure write token (`HF_TOKEN`) from Kaggle Secrets.
4. **Robustness Improvement:** Updated the local template notebook `continued_pretrain/notebooks/C_eval_and_merge.ipynb` to use dynamic glob-based GGUF file detection (`glob.glob("/kaggle/working/**/*.gguf", recursive=True)`) to gracefully handle folder and filename variations.

<!-- memory-fabric:store/pretraining/model-choice -->
---
store_path: pretraining/model-choice
title: "Pretraining Step 4 — Model Choice & Technical Rationale"
summary: "Pretraining Step 4 — Model Choice & Technical Rationale"
priority: medium
tags: [pretraining, model, qwen, vram]
schema_version: 1.3
last_updated: "2026-06-06T19:33:37-04:00"
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
---

Overview of Kaggle Notebooks layout for Spurgeon's Qwen2.5-3B continued pretraining. Work is split across three notebooks (A: data prep, B: training, C: evaluation/export) to circumvent Kaggle's 9-hour execution limits. Notebook B details PEFT QLoRA configuration, memory-saving parameters (lora_dropout=0, batch size 2, gradient accumulation 8, packing=True), and includes strict rules for trainer epoch incrementing when resuming checkpoints from input datasets. Notebook C handles holdout perplexity and qualitative style evaluation.

<!-- memory-fabric:store/pretraining/training-configuration -->
---
store_path: pretraining/training-configuration
title: "Pretraining Step 7 — Training Configuration (Notebook B) Plan"
summary: "Pretraining Step 7 — Training Configuration (Notebook B) Plan"
priority: medium
tags: [pretraining, training, lora, qlora, kaggle, unsloth]
schema_version: 1.3
last_updated: "2026-06-06T20:59:08-04:00"
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
