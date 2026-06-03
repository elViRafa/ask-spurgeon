---
title: Spurgeon Generator (CPU - llama.cpp)
emoji: ✝️
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
---

# Spurgeon Generator - CPU Inference (llama.cpp)

This Space runs your fine-tuned **Llama-3.1-8B Spurgeon model** using **llama.cpp** for efficient CPU inference.

## Why this instead of TGI?

TGI on CPU Basic has very poor support for 8B models and often crashes.  
`llama.cpp` is currently the most reliable and performant way to run 8B models on free CPU Spaces.

## Endpoint

This Space exposes a **full OpenAI-compatible API**:

```
https://<your-space>.hf.space/v1/chat/completions
```

You can use it exactly like Groq or OpenAI in your main RAG app.

**Note:** Opening the root URL (`https://<your-space>.hf.space/`) in a browser will return a JSON with useful links (including `/docs` for Swagger UI to test the API). There is no full web UI — it's an API-only server.

You can also check health at `/health`.

## How to Use (from your main app)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-username-spurgeon-generator.hf.space/v1",
    api_key="hf_dummy"
)

response = client.chat.completions.create(
    model="spurgeon-8b",
    messages=[
        {"role": "system", "content": "You are Charles Haddon Spurgeon."},
        {"role": "user", "content": "What does the Bible say about suffering?"}
    ],
    max_tokens=400,
    temperature=0.7,
)

print(response.choices[0].message.content)
```

## Important: Model Format

This Space expects your model in **GGUF** format.

You must convert your merged 16-bit model to GGUF (Q4_K_M or Q5_K_M recommended for CPU) and upload it to a separate repo (e.g. `your-username/llama-3.1-8b-spurgeon-generator-gguf`).

Then set these as **Space Variables** (Settings → Variables) so you don't have to edit code:

- `MODEL_REPO` = `your-username/llama-3.1-8b-spurgeon-generator-gguf`
- `MODEL_FILENAME` = `Spurgeon-8B-Q4_K_M.gguf`

(If the repo is private, also add `HF_TOKEN` as a Secret.)

## Performance on Free CPU Basic

- Expect 2–6 tokens/second (depending on context length).
- First request after sleep can take 30–90 seconds (model loading).
- Suitable for low-traffic personal use or as a style-specialized fallback.

## How to Convert Your Model to GGUF

1. Go to this Colab: https://colab.research.google.com/github/ggerganov/llama.cpp/blob/master/convert_hf_to_gguf.py
2. Or use the official `llama.cpp` convert script.
3. Recommended quantization: `Q4_K_M` or `Q5_K_M` for best quality/speed on CPU.

## Running Locally (for testing)

You can run the generator on your own PC (useful while developing the main RAG app).

1. Make sure you have the GGUF file (e.g. `Spurgeon-8B-Q4_K_M.gguf`).

2. Run:
   ```bash
   cd fine_tuning/spaces/cpu-llama-cpp
   LOCAL_MODEL_PATH=/absolute/path/to/Spurgeon-8B-Q4_K_M.gguf python main.py
   ```

   The server will be available at `http://localhost:7860/v1`

3. In your main app's `.env` point to it:
   ```env
   LLM_PROVIDER=openai
   CUSTOM_LLM_BASE_URL=http://localhost:7860/v1
   CUSTOM_LLM_API_KEY=hf_dummy
   CUSTOM_LLM_MODEL=spurgeon-8b
   ```

4. Then `streamlit run app.py` (from project root).

**Note**: Requires ~6-10 GB RAM depending on quantization and context.

## Build Time Warning (HF Spaces)

When you first push, the build log will get stuck for a long time at:

```
Building wheel for llama-cpp-python (pyproject.toml): still running...
```

This is expected — `llama-cpp-python` compiles llama.cpp from source. It can take 10–30 minutes (or more) on HF's CPU builders. Leave the tab open and wait. The improved Dockerfile now uses OpenBLAS for both faster build success and better runtime performance.

## Source

Fine-tuning code: https://github.com/elViRafa/ask-spurgeon
