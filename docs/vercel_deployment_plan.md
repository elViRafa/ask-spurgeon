# Vercel Free Tier Deployment Plan – Ask Spurgeon RAG

## Current Situation (May 2026)

- **Frontend + Backend**: Single Streamlit application (`app.py`)
- **Heavy dependencies**: LlamaIndex, HuggingFace embeddings (at runtime in some paths), Qdrant client
- **External services**:
  - Qdrant Cloud (vector DB) – already good
  - Groq API (LLM + translations) – already good
- Full index: ~49,391 points (complete sermon collection)

## Major Problem

**Streamlit does not run well on Vercel Free Tier.**

Vercel is optimized for:
- Static sites
- Next.js / React / frontend frameworks
- Serverless / Edge Functions (Node.js, limited Python support)

**Why Streamlit fails on Vercel**:
- Streamlit runs its own long-lived server process (Uvicorn)
- Vercel serverless functions have strict limits (10s execution on Hobby, cold starts)
- Heavy Python packages + model loading will timeout or exceed memory
- No good support for persistent WebSocket connections that Streamlit relies on

## Recommended Architecture for Vercel

### Best Practical Path: **Decoupled Frontend + Backend**

```
┌─────────────────────┐
│   Vercel (Free)     │   ← Next.js frontend (excellent free tier)
│   - Nice UI         │
│   - Language switch │
│   - Source cards    │
└──────────┬──────────┘
           │ HTTPS calls
           ↓
┌─────────────────────┐
│  Backend (Render /  │   ← FastAPI or Flask (Python)
│  Railway / Fly.io)  │     - /api/query endpoint
│  Hobby/Free tier    │     - Handles retrieval + Groq calls
└──────────┬──────────┘     - Translation logic
           │
           ↓
   External Services (already in use)
   - Qdrant Cloud
   - Groq API
```

### Why This Works on Vercel Free Tier

- Vercel only hosts the **frontend** (Next.js) → perfect fit, generous free limits.
- The Python backend runs on a platform that actually supports long-running Python processes.
- Much better DX, performance, and scalability.

## Step-by-Step Migration Plan

### Phase 1: Backend Extraction (FastAPI)

1. Create a new `backend/` folder.
2. Convert the core logic from Streamlit into a FastAPI app:
   - `/api/query` endpoint
   - Accept: `{ question: string, language?: string, filters?: object }`
   - Return: `{ answer: string, sources: [...], english_answer?: string }`
3. Move reusable logic:
   - `generate_response()` logic
   - Translation functions
   - Prompt building
4. Use environment variables properly (never hardcode keys).

**Recommended hosting for backend (Free/Hobby tiers)**:
- **Render.com** (easiest for Python, good free tier)
- **Railway.app** (very developer friendly)
- **Fly.io** (global edge, generous free allowance)

### Phase 2: Frontend on Vercel (Next.js)

1. Create `frontend/` with Next.js + TypeScript + Tailwind.
2. Beautiful UI inspired by current dark/gold aesthetic.
3. Features:
   - Language selector (English / Português + future)
   - Chat interface
   - Source cards (always show English original + link)
   - Optional "View English answer" toggle
   - Example questions
4. Call the backend API (use environment variable for backend URL).

### Phase 3: Deployment

**Vercel (Frontend)**:
- Connect GitHub repo
- Set `frontend/` as root directory
- Environment variables: `NEXT_PUBLIC_API_URL`

**Backend (Render/Railway)**:
- Deploy the FastAPI app
- Set environment variables:
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `GROQ_API_KEY`
  - `EMBEDDING_MODEL` (if still needed)

### Phase 4: Optimizations for Free Tiers

- Add caching for repeated questions (Redis on Upstash – free tier available)
- Rate limiting on the backend
- Lazy loading of heavy components
- Consider using Groq's faster model for translations

## Alternative: Keep Everything Python (Not on Vercel)

If you want to stay with a pure Python stack:

**Best free/paid-friendly options**:
- **Hugging Face Spaces** (original recommendation in the project) – works great with Streamlit
- **Render.com** (deploy Streamlit or FastAPI)
- **Railway**
- **Fly.io**

These are much more suitable than Vercel for this type of application.

## Quick Decision Matrix

| Option                        | Ease of Deploy | Cost (Free Tier) | Performance | Recommendation |
|-------------------------------|----------------|------------------|-------------|----------------|
| Streamlit on Vercel           | Very Hard      | Will break       | Poor        | Avoid |
| Next.js (Vercel) + FastAPI    | Medium         | Good             | Good        | **Best for Vercel** |
| Full app on Render/Railway    | Easy           | Good             | Very Good   | **Recommended overall** |
| Hugging Face Spaces           | Easy           | Good             | Good        | Very good choice |

## Immediate Action Items (This Week)

1. Decide: Do you *really* want Vercel, or is "free production hosting" the real goal?
2. If Vercel → Start Phase 1 (extract FastAPI backend).
3. If flexible → Deploy current Streamlit app to **Render.com** or **Hugging Face Spaces** (much faster path to production).

Would you like me to:
- Start creating the FastAPI backend structure right now?
- Create a `render.yaml` for easy deployment to Render?
- Or prepare a full Next.js + FastAPI skeleton?

Let me know your preference and I'll start executing the chosen path immediately.