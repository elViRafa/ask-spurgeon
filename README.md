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

### Local Development Options

You can run the full stack locally using either ChromaDB or Qdrant.

#### 1. ChromaDB — Recommended for quick local development (default)

**Easiest (no Docker):**
```env
VECTOR_STORE=chroma
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=spurgeon_sermons_v1
```

Then:
```bash
python ingest.py --source markdown --limit 100
streamlit run app.py
```

**With Docker:**
```bash
docker compose up -d chromadb
```

#### 2. Qdrant — Recommended when you want realistic local testing

This is closer to what you will use in production/HF Spaces.

```bash
docker compose up -d qdrant
```

Then set in `.env`:
```env
VECTOR_STORE=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=spurgeon_sermons_local
```

Ingest and run as usual:
```bash
python ingest.py --source markdown --limit 100
streamlit run app.py
```

**Tip**: Use Chroma for fast iteration. Switch to local Qdrant when you want to test features that behave more like production (better filtering, etc.).

### Accessing the Qdrant Management UI (Dashboard)

When you have Qdrant running locally via Docker:

1. Make sure the container is up:
   ```bash
   docker compose up -d qdrant
   ```

2. Open your browser and go to:
   ```
   http://localhost:6333/dashboard
   ```

If you set an API key in `docker-compose.yml`, append it like this:
```
http://localhost:6333/dashboard?api_key=YOUR_API_KEY_HERE
```

The Dashboard lets you:
- Browse collections
- View and search vectors
- Inspect payload (metadata)
- Run raw queries
- Monitor cluster status

This is very useful for debugging during local development.

### Using Your Fine-Tuned Custom Model Locally

If you have built the Q4_K_M GGUF locally (in `fine_tuning/models/Spurgeon-8B-Q4_K_M.gguf`), you can test the full RAG + custom LLM pipeline locally.

1. Start the generator server (in one terminal):
   ```bash
   cd fine_tuning/spaces/cpu-llama-cpp
   # Use the local GGUF (adjust path if needed)
   LOCAL_MODEL_PATH=../../models/Spurgeon-8B-Q4_K_M.gguf python main.py
   ```
   It will listen on http://localhost:7860/v1 (OpenAI-compatible).

2. In your `.env` (for the main app), add/override:
   ```env
   LLM_PROVIDER=openai
   CUSTOM_LLM_BASE_URL=http://localhost:7860/v1
   CUSTOM_LLM_API_KEY=hf_dummy
   CUSTOM_LLM_MODEL=spurgeon-8b
   ```

3. Run the main app:
   ```bash
   streamlit run app.py
   ```

The sidebar will show "Using custom model: **spurgeon-8b**" and chat will use your local fine-tuned model.

**Note**: The generator loads the entire model into RAM (~5-8 GB for Q4 8B). Close it when not testing.

### Local Streamlit + Remote HF Generator Space (easiest way to test your fine-tuned model)

This is exactly your current setup: run the Streamlit RAG app on your local PC, but use the fine-tuned LLM running on a (free) Hugging Face Space.

**Step-by-step:**

1. Edit your `.env` (in the project root) with these lines (replace with your actual generator space name):

   ```env
   LLM_PROVIDER=openai
   CUSTOM_LLM_BASE_URL=https://<your-username>-<your-generator-space-name>.hf.space/v1
   CUSTOM_LLM_API_KEY=hf_dummy
   CUSTOM_LLM_MODEL=spurgeon-8b
   ```

   Leave your other settings (GROQ_API_KEY for fallback, VECTOR_STORE, etc.) as they are.

2. **Wake up the generator Space first** (critical on free tier):
   - Open `https://<your-username>-<your-generator-space-name>.hf.space` in your browser.
   - Wait until the status shows **Running** (it can take 30-90+ seconds the first time after sleeping; it may download the GGUF on cold start).
   - You can test it quickly by visiting the /health endpoint in browser or with curl.

3. Run Streamlit locally:

   ```bash
   streamlit run app.py
   ```

4. Look for these signs that it's using your custom model:
   - In the **sidebar**: "🤖 Using custom model: **spurgeon-8b**"
   - In the **terminal** where you ran streamlit: a line like  
     `Using custom OpenAI-compatible LLM at: https://...hf.space/v1 (model=spurgeon-8b)`

**Common gotchas on local + HF generator**:
- Free HF Spaces sleep after ~48h of no traffic. Always visit the generator URL first.
- First generation after wake-up will be slow (model load + download if needed).
- Make sure the generator Space has its own secrets set correctly (MODEL_REPO, MODEL_FILENAME pointing to your uploaded GGUF).
- If you see "Unknown model 'tgi'" it means your .env or deployed code still has the old default — use `spurgeon-8b` and make sure you pulled the latest code changes.

To go back to Groq only: set `LLM_PROVIDER=groq` in .env and restart Streamlit.

This setup lets you develop the UI locally while the heavy model runs on (free) HF infrastructure.

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
