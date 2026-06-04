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
