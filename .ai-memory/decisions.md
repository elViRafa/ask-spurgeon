---
section: decisions
summary: "Details model fine-tuning, memory integration, performance fixes (FastAPI/OpenBLAS), and local execution options (Ollama/CUDA)."
priority: medium
tags: [decisions, adr]
schema_version: 1.3
last_updated: "2026-06-03T08:33:24-04:00"
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
