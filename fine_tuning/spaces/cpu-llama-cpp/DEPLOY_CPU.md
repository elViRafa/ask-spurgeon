# Deploying Your Fine-Tuned Spurgeon Model on Free CPU (llama.cpp)

This is currently the **most reliable free way** to run your 8B fine-tuned model on Hugging Face Spaces.

TGI on CPU basic is unstable for 8B models. `llama.cpp` is much better for CPU.

## Prerequisites

1. Your model must be converted to **GGUF** format (Q4_K_M or Q5_K_M recommended).
2. Upload the GGUF file to a Hugging Face repo (e.g. `rafaelvieirar1r/llama-3.1-8b-spurgeon-generator-gguf`).

If you want to use the same fine-tuned model in **Ollama** locally, download the GGUF from Hugging Face and import it with the Gemma 4 Modelfile.

## Step-by-Step Deployment

### 1. Convert your merged model to GGUF (do this once)

**Easiest way**: Use this Colab notebook:

https://colab.research.google.com/github/ggerganov/llama.cpp/blob/master/convert_hf_to_gguf.py

Or run locally:

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make
python convert_hf_to_gguf.py /path/to/your/merged/model --outfile Spurgeon-8B-Q4_K_M.gguf --outtype q4_k_m
```

Upload the resulting `.gguf` file to a new HF repo.

### 1b. Use the model locally in Ollama

If your GGUF is already on Hugging Face at `rafaelvieirar1r/gemma-4-12b-spurgeon-generator`, you can pull it down and create an Ollama model directly:

```bash
huggingface-cli download rafaelvieirar1r/gemma-4-12b-spurgeon-generator Spurgeon-Gemma4-12B-Q4_K_M.gguf --local-dir ..\..\models --local-dir-use-symlinks False
cd ..\..\models
ollama create spurgeon-gemma4 -f Modelfile.gemma4
ollama run spurgeon-gemma4
```

Then set your app to use the local Ollama endpoint:

```env
LLM_PROVIDER=openai
CUSTOM_LLM_BASE_URL=http://localhost:11434/v1
CUSTOM_LLM_API_KEY=ollama
CUSTOM_LLM_MODEL=spurgeon-gemma4
```

### 2. Create the Space

1. Go to https://huggingface.co/new-space
2. Set:
   - **Space name**: `spurgeon-generator-cpu` (example)
   - **SDK**: **Docker**
   - **Hardware**: **CPU basic**
3. Click Create Space

### 3. Add the files

Upload these three files from `fine_tuning/spaces/cpu-llama-cpp/`:

- `Dockerfile`
- `requirements.txt`
- `main.py`
- `README.md` (optional but recommended)

### 4. Configure model location using Space Variables (recommended)

Do **not** hardcode your repo in `main.py` (it gets overwritten on every push).

Instead, in your Space go to:

**Settings → Variables** (public) or **Secrets** (for tokens):

- `MODEL_REPO` = `your-username/llama-3.1-8b-spurgeon-generator-gguf`
- `MODEL_FILENAME` = `Spurgeon-8B-Q4_K_M.gguf`

If the GGUF repo is private, also add a **Secret**:

- `HF_TOKEN` = `hf_...` (token with read permission on the model repo)

The code already does `os.getenv("MODEL_REPO", ...)` so these will be picked up automatically.

### 5. Deploy

Upload / commit the files from `fine_tuning/spaces/cpu-llama-cpp/`.

**Important**: Building the `llama-cpp-python` wheel from source is heavy. 
On HF's build runners you will see for a long time:

```
Building wheel for llama-cpp-python (pyproject.toml): still running...
```

This is **normal** — it compiles llama.cpp + OpenBLAS and can take 10–30+ minutes. Do not cancel.

After the image builds, the container starts and will download + load your GGUF (several GB). This first startup is slow.

Once the Space shows **Running**, the endpoint is ready at:

```
https://<your-username>-<space-name>.hf.space/v1/chat/completions
```

**Note for browser users:** Opening the root URL in a browser will now return a JSON with links to `/docs` (Swagger UI), `/health`, and the API. This is normal — it's a pure API server (FastAPI), not a web app. Use the `/v1/chat/completions` from code or visit `/docs` in browser.

---

## Using in Your Main App

Set these secrets in your main RAG Space:

```toml
LLM_PROVIDER = "openai"
CUSTOM_LLM_BASE_URL = "https://your-username-spurgeon-generator-cpu.hf.space/v1"
CUSTOM_LLM_API_KEY = "hf_dummy"
CUSTOM_LLM_MODEL = "spurgeon-8b"
```

Then your app will call your fine-tuned model instead of Groq.

---

## Tips for Better Performance

- Use **Q4_K_M** or **Q5_K_M** quantization (best balance).
- Set `N_CTX=2048` or `3072` in `main.py` if you get memory issues.
- Increase `N_THREADS` if the Space has more CPU cores (check logs).

## Limitations (Free CPU)

- Speed: ~2–6 tokens/second
- Cold start: 30–90 seconds after sleeping
- Best used as a **style-specialized model** alongside Groq (hybrid setup)

This setup is currently the most stable free CPU solution for 8B models on HF Spaces.
