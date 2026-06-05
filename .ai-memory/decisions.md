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
