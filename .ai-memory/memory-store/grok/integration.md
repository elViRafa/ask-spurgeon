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
