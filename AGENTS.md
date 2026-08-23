# Agent Instructions — Memory Fabric

This file is read automatically by Claude Code, Gemini CLI, Codex, Antigravity, and other MCP-aware AI agents.
GitHub Copilot reads `.github/copilot-instructions.md` instead.

---

## Memory Fabric — Semantic Store Agent Instructions

You must use the `memory-fabric` MCP tools for all project memory operations. Do not read or write `.ai-memory/` files using raw file-system tools.

### 1. Startup & Retrieval (The Active Memory Workflow)
Accessing the Memory Store is an active process driven by the agent using the following tools:

1. **Session Map:** At session start, you MUST call `read_combined_context_tool(cwd="<absolute project root path>")`. This serves as your index map to quickly grasp what is stored, load directives, and active session steering prompts.
2. **Search & Target:** To find specific information without reading everything, use `keyword_search_tool(cwd="...", query="<keyword>")` to look for relevant topics already documented in memory.
3. **Deep Dive:** After locating a reference via the index or keyword search, go straight to the necessary file by calling `read_memory_store_tool` (for semantic paths) or `read_section` (for legacy sections) to extract the full context needed for your answer.

### 2. Registering Memory in the Store
After completing a task (e.g., a design decision, a bug fix, schema creation, or refactoring), persist this knowledge.

Use `write_memory_store_tool` to register small, standalone memory files.

**Strict Semantic Store Rules:**
1. **`store_path` formatting:** Must be lowercase, alphanumeric segments separated by slashes. No spaces, no capital letters, and **no `.md` extension** (e.g., `architecture/decisions/jwt-auth` or `bugs/auth-redirect-fix`).
2. **Path Nesting:** Max 5 levels of directory nesting.
3. **Duplicate Prevention:** The tool automatically strips out duplicate bullet points or lines when appending.

**Tool Parameters:**
* `cwd`: Absolute path to project root.
* `store_path`: The semantic path (e.g., `architecture/decisions/auth-service`).
* `content`: The markdown text body of the memory.
* `title`: (Optional) Human-readable title.
* `tags`: (Optional) Comma-separated tags (e.g., `auth,security`).
* `priority`: (Optional) `high`, `medium`, or `low` (default: `medium`).
* `mode`: (Optional) `replace` to overwrite, or `append` to add to the end (default: `replace`).

### 3. Legacy Section Writes
If you are updating a legacy flat section file (e.g., updating a list of risks in `debt`), call `write_local_memory_tool(cwd="...", section="debt", content="...", mode="append")`. Prefer `write_memory_store_tool` for new standalone topics.

### 4. Security & Best Practices
* **Do NOT** store credentials, tokens, or passwords in memory — the server redacts them, but avoid writing them in the first place.

### 5. Memory Maintenance (Dreaming)
To consolidate memory, check for contradictions, or refresh the index, you can use the `dream_tool`. For detailed instructions on parameters (like `mode` and `apply`) and when to trigger a dream, refer to `.agents/rules/dreaming.md`.

<!-- >>> memory-fabric:project-directives (managed block; edit .ai-memory steering files instead) >>> -->
## Project Directives — Memory Fabric

Hand-curated development guidelines shared by every AI agent working on this repo.
Source of truth: the `role: steering` section files in `.ai-memory/`. Edit those
files (review via MR), then run `ai-memory sync-agents` — never edit this
generated copy in place.

<!-- directive: framework-rules -->
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

<!-- directive: ubiquitous-language -->
# Ubiquitous Language

Record project terminology here.
<!-- <<< memory-fabric:project-directives <<< -->
