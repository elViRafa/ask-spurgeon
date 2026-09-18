---
section: debt
summary: "App debt (hybrid search, rate limits) plus 2026-08-29 memory-fabric LLM/host hygiene notes."
priority: low
tags: [debt, risk]
schema_version: 1.3
last_updated: "2026-08-29T11:07:00-04:00"
summary_hash: 089c37fc31054b93e50d68038bbf1c4d
review_status: stale
---

# Technical Debt & Roadmap

This section tracks outstanding technical debt, limitations, and future development opportunities.

## Known Technical Debt & Limits

- **Pure Vector Search Limitation**: Search relies on semantic vector queries and can miss exact bible-reference keywords (e.g. "Romans 8:28"). Hybrid BM25 + vector is needed.
- **PDF Text Quality**: Raw PDF/OCR is worse than community markdown; prefer markdown sources for ingest.
- **Session-Based Rate Limiting**: 8 queries/hour in Streamlit session memory is bypassable by reload; production needs server-side IP/token limits.
- **Memory fabric hygiene (2026-08-29)**: Many store files were missing from `memory-store/index.md` until deep dream; `OLLAMA_HOST` in `.env` had an inline `#` comment breaking the URL; `MEMORY_FABRIC_LLM_PROVIDER=ollama` pointed at missing `gemma4` while only `spurgeon-cpt` was pulled. Prefer Gemini free or Cursor split-tool for Dreaming.

## Roadmap & Pending Features

- **Multi-Author Interface**: Schema is author-aware; UI/prompts still assume Spurgeon-only.
- **Weekly Automated Ingestion**: Pull updates from `lyteword/chspurgeon-sermons` on a schedule.
- **Mobile Styling**: Extra CSS for Streamlit sidebar/readability on small screens.
