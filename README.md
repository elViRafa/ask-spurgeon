---
title: Ask Spurgeon
emoji: 📖
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---

# ✝️ Ask Spurgeon — Free Public RAG App

> A beautiful, completely free, publicly accessible web application where anyone can chat with or search the full collection of Charles Haddon Spurgeon’s sermons (~3,500 sermons, 63 volumes — all public domain).

**Live philosophy**: Talk to Spurgeon. Search his wisdom on faith, prayer, suffering, grace, election, the cross, and the Christian life.

---

## Features

- **Semantic search + conversational interface** powered by LlamaIndex + Groq
- **Rich metadata filtering**: by author, volume, year, Bible book, sermon number
- **Bible reference aware**: extract and filter on references found in the sermons
- **Source transparency**: every answer shows the exact sermons used with excerpts
- Answers are grounded in Spurgeon's actual sermons with clear citations (the AI does not role-play as Spurgeon)
- **Author-aware architecture**: ready for future authors (Edwards, Lloyd-Jones, Calvin, etc.)
- **Free-tier friendly**: careful rate limiting + model fallback for Groq

---

## Recommended Tech Stack (2026)

| Layer            | Choice                              | Reason |
|------------------|-------------------------------------|--------|
| UI               | Streamlit                           | Fastest beautiful public apps |
| RAG Framework    | LlamaIndex                          | Better than LangChain for this use case |
| Embeddings       | `BAAI/bge-small-en-v1.5` (fastembed)| Excellent quality + CPU friendly |
| LLM              | Groq `llama-3.3-70b-versatile` + fallback | Best free tier in 2026 |
| Vector DB        | **Qdrant Cloud (free tier)**        | 1GB RAM / 4GB disk, permanent, no card |
| Hosting          | Hugging Face Spaces (Docker)        | Zero cost, recommended |

---

## Quick Start (Local Development)

### 1. Clone & Install

**Recommended Python version**: 3.11, 3.12 or 3.13 (Python 3.14 may have compatibility issues with some RAG packages as of mid-2026).

```bash
git clone https://github.com/YOUR_USERNAME/ask-spurgeon.git
cd ask-spurgeon

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Get API Keys (Free)

1. **Groq** (required for chat): https://console.groq.com/keys
2. **Qdrant Cloud** (recommended): https://cloud.qdrant.io → Create free cluster

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys
```

### 4. Ingest Data (Most Important Step)

**Best option (recommended)** — clean Markdown from the community:

```bash
# Clone the full sermon collection (CC0)
git clone https://github.com/lyteword/chspurgeon-sermons.git data/chspurgeon-sermons

# Start small (MVP)
python ingest.py --source markdown --limit 80 --recreate-collection

# Later: full collection (can take 30–90 min depending on machine)
python ingest.py --source markdown
```

**Alternative** (original PDFs — lower quality text):

```bash
python scripts/download_sermons.py --count 50
python ingest.py --source pdf --limit 50
```

### 5. Run the App

```bash
streamlit run app.py
```

Visit http://localhost:8501

---

### Alternative: Local Development with ChromaDB (Recommended for local testing)

If you want to run everything locally without Qdrant Cloud:

**Easiest option (no Docker required):**

1. Set in your `.env`:
   ```env
   VECTOR_STORE=chroma
   CHROMA_PERSIST_DIR=./chroma_db
   ```

2. Ingest data locally:
   ```bash
   python ingest.py --source markdown --limit 100
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

**Docker option** (if you prefer running Chroma in Docker):
- Use `docker compose up -d`
- Set `CHROMA_HOST` and `CHROMA_PORT` instead of `CHROMA_PERSIST_DIR`

---

## Deployment to Hugging Face Spaces (Free)

1. Create a new Space → **Streamlit** SDK
2. Push this repository (or connect via GitHub)
3. In **Settings → Secrets**, add:

```toml
GROQ_API_KEY = "gsk_..."
QDRANT_URL = "https://your-cluster.us-east-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "your_qdrant_key"
QDRANT_COLLECTION = "spurgeon_sermons_v1"
```

4. (Optional but recommended) Set **Hardware** to CPU basic or upgrade if you get traffic.

5. The app will automatically use the remote Qdrant collection. No need to store vectors on HF.

**Important**: Ingestion is best done locally or on a temporary powerful machine, then the collection lives forever in Qdrant Cloud.

---

## Project Structure

```
ask-spurgeon/
├── app.py                  # Main Streamlit application
├── ingest.py               # Data ingestion pipeline (Markdown + PDF)
├── config.py               # All settings, models, prompts, constants
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── utils/
│   ├── __init__.py
│   ├── bible_refs.py       # Robust Bible reference extractor + normalizer
│   ├── metadata.py         # Parsers for Markdown and PDF sources
│   └── prompts.py          # Spurgeon-style system prompts
├── scripts/
│   └── download_sermons.py # Optional PDF downloader
└── data/                   # .gitignore'd — put sermons here
    ├── chspurgeon-sermons/ # Recommended: clone of lyteword repo
    └── sermons/            # PDFs (chs1.pdf, chs2.pdf, ...)
```

---

## Key Design Decisions

### Author-Aware RAG (Future-Proof)

Every document and chunk stores `author`. Future queries like:

- "What did Spurgeon and Lloyd-Jones say about sanctification?"
- "Only show sermons by Jonathan Edwards"

...will work with minimal code changes.

### Bible Reference Handling

- Sermons are indexed with **both** sermon-level and chunk-level Bible references
- Filters support "Show only sermons referencing Romans 8"
- Primary scripture (the text preached on) is extracted with heuristics

### Rate Limiting & Cost Control

- Hard per-session limit (default 8 queries/hour)
- Automatic fallback from `llama-3.3-70b-versatile` → `llama-3.1-8b-instant`
- Response caching via Streamlit primitives
- Clear UI messaging when limits are hit

### Chunking Strategy

- 768 tokens with 128 overlap (good balance for long 19th-century sermons)
- All metadata (author, sermon #, volume, year, references) is copied to every chunk

### Evaluation Framework

The project includes a proper RAG evaluation suite:

```bash
# Quick evaluation with LLM-as-Judge
python eval.py --limit 5

# Compare two different prompts
python eval.py --compare default strict
```

See [tests/README.md](tests/README.md) for details on the 20 curated test questions (inspired by GotQuestions.org) and the LLM judge scoring system.

---

## Data Sources

| Source | Quality | Recommendation |
|--------|---------|----------------|
| [lyteword/chspurgeon-sermons](https://github.com/lyteword/chspurgeon-sermons) | Excellent (clean Markdown) | **Strongly preferred** |
| spurgeongems.org PDFs (`chs*.pdf`) | Good (modernized text) | Acceptable fallback |
| Monergism EPUBs | Very good | Alternative bulk source |
| Archive.org scans | Variable (OCR) | Only for historical fidelity |

---

## Legal & Ethical

- All sermons by Charles Haddon Spurgeon (1834–1892) are **public domain**.
- This project is **not officially affiliated** with any Spurgeon society, publisher, or the Metropolitan Tabernacle.
- AI answers can hallucinate. Always verify important quotes against original published volumes.
- Strong disclaimer is shown on every page.

---

## Roadmap / Future Work

- [ ] Add support for second author (e.g. Jonathan Edwards)
- [ ] Hybrid search (BM25 + vector) for exact Bible verse queries
- [ ] "Compare Spurgeon and X on topic Y" multi-author mode
- [ ] Export answers as nicely formatted study notes
- [ ] Weekly automated ingestion of any new community transcriptions
- [ ] Mobile-friendly layout improvements

---

## Contributing

Pull requests are welcome, especially:

- Better Bible reference parsing
- Improved prompt engineering for Spurgeon's voice
- Additional high-quality public domain authors

---

## Deployment to Production

This project is designed for **zero-cost deployment** on Hugging Face Spaces.

[![Deploy on HF Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/deploy-on-spaces-lg.svg)](https://huggingface.co/new-space?template=)

### Quick Deploy (Hugging Face Spaces)

1. Go to [https://huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose **Docker** as the SDK + **CPU basic** (free)
3. Connect your GitHub repo (recommended for auto-updates)
4. Add the 3 required secrets (see [hf_spaces/DEPLOYMENT.md](hf_spaces/DEPLOYMENT.md))
5. Deploy

> **Critical**: The Space does **not** contain the sermon data.  
> You must run ingestion **locally first** against your Qdrant Cloud cluster before deploying.

Full guide: [hf_spaces/DEPLOYMENT.md](hf_spaces/DEPLOYMENT.md)

### Alternative Deployment Options

See [publish_options.md](publish_options.md) for a full comparison of hosting platforms (Render, Railway, Fly.io, Vercel + backend, self-hosted VPS, etc.).

## Acknowledgments

- The volunteers who created the beautiful Markdown edition at [lyteword/chspurgeon-sermons](https://github.com/lyteword/chspurgeon-sermons)
- spurgeongems.org for making the sermons freely available online for decades
- The LlamaIndex, Qdrant, Groq, and Streamlit teams

> "Visit many good books, but live in the Bible."  
> — Charles Haddon Spurgeon

---

**Built with love for the church and the glory of God.**

*This is free software. Use it to know Christ better.*
