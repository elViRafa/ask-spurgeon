# Hugging Face Spaces Deployment Guide – Ask Spurgeon

This guide explains how to deploy the Ask Spurgeon RAG app to Hugging Face Spaces (free tier).

## Recommended Deployment Method: Docker

We strongly recommend using the **Dockerfile** method instead of the direct Streamlit SDK. It gives better control over the Python version and dependencies.

### Step 1: Create a New Space

1. Go to [https://huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose:
   - **SDK**: Docker
   - **Hardware**: CPU basic (free)
   - **Visibility**: Public (or Private)
3. Connect your GitHub repository (recommended) or upload files directly.

### Step 2: Required Secrets

Go to your Space → **Settings → Secrets** and add the following:

```toml
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
QDRANT_URL = "https://your-cluster-id.us-east-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "your_qdrant_api_key_here"
QDRANT_COLLECTION = "spurgeon_sermons"
```

### Step 3: Important Files for HF Spaces

These files are already prepared in the repository:

- `Dockerfile` – Optimized for HF Spaces (Python 3.13)
- `.dockerignore` – Keeps the image small and excludes local data
- `requirements.txt` – All dependencies
- `app.py` – Main Streamlit application
- `.streamlit/config.toml` – Forces the dark vintage Bible theme

### Step 4: Ingestion Strategy (Critical)

**Never run full ingestion inside the Space.**

The correct workflow is:

1. Run ingestion **locally** or in a GitHub Action:
   ```bash
   python ingest.py --source markdown --recreate-collection
   ```
2. The vectors are stored in **Qdrant Cloud** (permanent).
3. The Space only reads from Qdrant — no heavy computation needed at startup.

This is the reason we use Qdrant Cloud instead of local vector storage.

### Space Configuration

In your Space settings:

- **Hardware**: CPU basic (free)
- **Sleep time**: Can be left at default (Space will sleep after inactivity)
- **Persistent Storage**: Not needed (everything lives in Qdrant Cloud)

### Expected Behavior on HF Spaces

- First load after cold start will be slower (embedding model ~100MB download).
- The interface automatically detects browser language and switches to Portuguese (or English).
- All labels, filters, examples, disclaimers, and messages are fully bilingual.
- Subsequent requests are fast.
- Groq free tier rate limits still apply — the app has built-in fallback and rate limiting.

### Custom Domain (Optional)

You can assign a free `*.hf.space` subdomain or connect a custom domain in Space settings.

### Troubleshooting

| Issue                              | Solution |
|------------------------------------|----------|
| "QDRANT_URL not set"               | Add secrets in Space Settings |
| Slow first load                    | Normal on CPU basic after cold start |
| Groq rate limit errors             | Expected on free tier. App will fallback automatically |
| Collection not found               | Run `ingest.py` locally first against your Qdrant Cloud |
| Out of memory                      | Reduce traffic or upgrade hardware (paid) |

### Alternative: Direct Streamlit SDK (Not Recommended)

You *can* deploy without Docker by selecting **SDK = Streamlit**, but the Dockerfile method is more reliable for this project.

---

**Status**: Ready for deployment on Hugging Face Spaces using the provided `Dockerfile`.

The application includes full Portuguese language support (auto-detected from browser).

---

## Pre-Deployment Checklist (Do this before pushing)

- [ ] You have a Qdrant Cloud cluster with the collection already populated (`spurgeon_sermons` or your collection name)
- [ ] You have run ingestion **locally** at least once against your Qdrant cluster
- [ ] You have the three secrets ready:
  - `GROQ_API_KEY`
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
- [ ] (Optional but recommended) `QDRANT_COLLECTION` is set if different from default
- [ ] Your GitHub repo is clean (no `data/` folder, no `.env` file committed)
- [ ] You have tested the app locally with the same secrets (via `.env`)
- [ ] You are using the `Dockerfile` method (not the raw Streamlit SDK)

Once the Space is live:
1. Wait for the first cold start (embedding model download)
2. Test with both English and Portuguese browsers
3. Monitor the logs in the Space for any secret or connection errors

For the best experience, deploy via GitHub repository connection so updates are automatic.
