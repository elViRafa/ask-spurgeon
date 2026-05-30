# Publishing Options Analysis – Ask Spurgeon RAG

**Date**: June 2026  
**Project**: Ask Spurgeon – Free public RAG over 3,500+ English sermons of Charles Haddon Spurgeon.

---

## Project Characteristics (Important for Hosting Decisions)

| Aspect                    | Current State                                      | Implications for Hosting |
|---------------------------|----------------------------------------------------|---------------------------|
| **Architecture**          | Monolithic Streamlit app                           | Hard to deploy on pure serverless platforms |
| **Backend Logic**         | LlamaIndex + Qdrant client + Groq                  | Needs reliable Python runtime |
| **Heavy Work at Runtime** | Vector search (offloaded to Qdrant Cloud) + LLM calls | Relatively lightweight after ingestion |
| **Data**                  | ~49,391 vectors in Qdrant Cloud                    | No need to host vectors yourself |
| **Multilingual**          | Query + Answer translation (Portuguese supported)  | Adds some latency and cost |
| **Tone**                  | Neutral modern AI (no role-play)                   | Simpler prompting |
| **Ingestion**             | Done separately (good)                             | No need to run heavy jobs on the hosting platform |
| **Traffic Expectation**   | Low to medium (personal / community project)       | Free tiers are viable |

**Key Insight**: Because the heavy lifting (embeddings + vector storage) lives in external services, the app is lighter than it appears. However, the current **Streamlit** framework makes deployment choices more restricted.

---

## Option Comparison

### Option 1: Hugging Face Spaces (Current Direction)

**Description**  
Deploy the existing Streamlit app directly on Hugging Face Spaces (CPU basic – free).

**Pros**
- Extremely easy for Streamlit apps (official support)
- Free tier available
- Persistent storage options (though not needed here)
- Good for public demos and sharing
- Simple secrets management
- Already has deployment notes in the repo

**Cons**
- Free tier has limited resources (CPU basic can be slow under load)
- Apps sleep after inactivity (cold start delay)
- Limited customization of infrastructure
- Not ideal if you want a very polished custom frontend later
- Rate limits and resource contention possible

**Cost (Free Tier)**: $0  
**Complexity**: Very Low  
**Suitability for this project**: High (for MVP / public demo)

**Recommendation**: Excellent choice while the app remains Streamlit-based.

---

### Option 2: Render.com (Free / Hobby Tier)

**Description**  
Deploy either the current Streamlit app or the emerging FastAPI backend on Render.

**Pros**
- Good free tier for web services (with limitations)
- Excellent Python support
- Easy deployment from GitHub
- Can run both Streamlit and FastAPI without issues
- Free tier includes automatic SSL and custom domains (on paid)
- Better performance and uptime than HF Spaces free tier in many cases

**Cons**
- Free web services spin down after 15 minutes of inactivity (cold starts)
- Limited hours on the free tier (can be restrictive for public apps)
- Hobby plan ($7/month) removes most limitations

**Cost (Free Tier)**: $0 (with spin-down)  
**Cost (Hobby)**: $7/month  
**Complexity**: Low–Medium  
**Suitability**: Very High

---

### Option 3: Railway (Hobby Plan)

**Description**  
Deploy on Railway.app (very popular among indie developers).

**Pros**
- Excellent developer experience
- Strong Python + Docker support
- Easy environment variable and secret management
- Good performance
- Hobby plan is reasonably priced ($5 + usage)

**Cons**
- Free tier is quite limited (mostly for testing)
- Can become expensive if traffic grows without optimization
- Less "set and forget" than some other platforms

**Cost (Free)**: Very limited  
**Cost (Hobby)**: Starts at ~$5 + usage  
**Complexity**: Low  
**Suitability**: High

---

### Option 4: Fly.io

**Description**  
Deploy as a Docker container on Fly.io's global edge network.

**Pros**
- Global deployment (low latency worldwide)
- Very generous free allowance (3 VMs + 3GB persistent storage)
- Excellent for Dockerized apps
- Good performance

**Cons**
- Steeper learning curve (Docker + fly.toml)
- Free VMs can be slow or limited in resources
- Requires more operational knowledge than Render or HF Spaces

**Cost (Free Tier)**: Very usable for low traffic  
**Complexity**: Medium  
**Suitability**: Medium-High (if you're comfortable with Docker)

---

### Option 5: Vercel (Frontend Only) + Separate Backend

**Description**  
Use Vercel only for a modern Next.js frontend, and host the Python backend (FastAPI) on Render/Railway/Fly.io.

**Pros**
- Best possible free frontend hosting (Vercel is excellent)
- Can build a much nicer, faster, more maintainable UI than Streamlit
- Full control over frontend tech (React, Tailwind, etc.)
- Separates concerns cleanly

**Cons**
- Requires significant refactor (extract API + build new frontend)
- More moving parts (two deployments to manage)
- Higher initial development cost

**Cost**: Free for frontend + backend on another free/hobby platform  
**Complexity**: High (initially)  
**Suitability**: High long-term

---

### Option 6: Self-Hosted VPS (Hetzner, Oracle Cloud, etc.)

**Description**  
Run the app on a cheap VPS (e.g. Hetzner Cloud ~€3–4/month, Oracle Always Free).

**Pros**
- Full control
- No cold starts
- Can run Streamlit or FastAPI + reverse proxy (Caddy/Nginx)
- Can host multiple projects cheaply
- Oracle Cloud Always Free tier is very powerful (if you can get it)

**Cons**
- You manage the server (security, updates, uptime)
- More operational overhead
- Not "serverless"

**Cost**: €3–6/month (or $0 on Oracle Always Free)  
**Complexity**: Medium–High  
**Suitability**: Good if you like managing servers

---

### Option 7: Streamlit Community Cloud

**Description**  
Official Streamlit hosting.

**Pros**
- Zero cost
- Extremely simple

**Cons**
- Very limited resources
- Apps frequently go to sleep
- Not suitable for public production apps with any real usage
- Limited features compared to other platforms

**Recommendation**: Only for internal testing.

---

## Recommendation Matrix

| Option                              | Ease of Deploy | Free Tier Quality | Performance | Long-term Maintainability | Best For |
|-------------------------------------|----------------|-------------------|-------------|---------------------------|----------|
| **Hugging Face Spaces**             | Excellent      | Good              | Medium      | Medium                    | Quick public demo |
| **Render.com**                      | Very Good      | Good              | Good        | High                      | **Best current choice** |
| **Railway**                         | Very Good      | Limited           | Good        | High                      | Good alternative |
| **Fly.io**                          | Medium         | Good              | Very Good   | High                      | Global low latency |
| **Vercel (Frontend) + Render**      | Hard           | Excellent         | Excellent   | Very High                 | Professional product |
| **Self-hosted VPS**                 | Medium         | Excellent         | Excellent   | Medium                    | Maximum control + lowest cost |
| Streamlit Community Cloud           | Excellent      | Poor              | Poor        | Low                       | Only testing |

---

## Final Recommendations

### Short-term / MVP (Next 1–2 months)
- **Primary**: Deploy to **Render.com** (Hobby plan or free with spin-down)
- **Alternative**: Keep using **Hugging Face Spaces** (easiest)

### Medium-term (When you want better UX)
- Move to **Vercel (Next.js frontend) + FastAPI backend on Render/Railway**
- This gives you the best of both worlds: beautiful frontend + proper backend

### Long-term / Lowest Cost
- Self-hosted on **Hetzner Cloud** (~€4/month) or **Oracle Cloud Always Free**

---

## Suggested Next Actions

1. Decide your priority: **Ease** vs **Professionalism** vs **Lowest Cost**
2. If Ease → Deploy current Streamlit to Render or HF Spaces
3. If Professionalism → Continue extracting the FastAPI backend and plan the Next.js frontend
4. Document secrets and environment variables clearly
5. Set up basic monitoring (UptimeRobot + error logging)

Would you like me to start preparing deployment files (e.g. `render.yaml`, improved FastAPI structure, or a Next.js frontend skeleton) based on your preferred direction?