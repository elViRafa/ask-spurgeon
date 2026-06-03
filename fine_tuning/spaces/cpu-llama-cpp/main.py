import os
import sys
import faulthandler
# Enable faulthandler to print C++ tracebacks in case of segmentation faults / crashes
faulthandler.enable()

# On Windows, add CUDA DLL directory to path if present so llama-cpp-python can load its CUDA dependencies
if sys.platform == "win32":
    cuda_path = os.getenv("CUDA_PATH")
    if cuda_path and os.path.exists(os.path.join(cuda_path, "bin")):
        try:
            os.add_dll_directory(os.path.join(cuda_path, "bin"))
        except Exception as e:
            print(f"Warning: Could not add CUDA DLL directory: {e}")

# Set OpenBLAS to use a single thread BEFORE importing any library that might load it,
# to prevent CPU oversubscription and deadlocks in the container.
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

app = FastAPI(title="Spurgeon Generator - llama.cpp CPU")

@app.get("/", include_in_schema=False)
async def root():
    """Root handler for browser visits. Returns info + links to docs and health."""
    return {
        "message": "Spurgeon Generator (llama.cpp CPU) is running!",
        "docs": "/docs",
        "health": "/health",
        "api": "/v1/chat/completions",
        "note": "This is an API-only service. Use /docs for interactive testing."
    }

# Configuration - prefer Space Variables / Secrets over the defaults
MODEL_REPO = os.getenv("MODEL_REPO", "rafaelvieirar1r/llama-3.1-8b-spurgeon-generator-gguf")
MODEL_FILENAME = os.getenv("MODEL_FILENAME", "Spurgeon-8B-Q4_K_M.gguf")
N_CTX = int(os.getenv("N_CTX", "4096"))
N_THREADS = int(os.getenv("N_THREADS", "2"))
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "0"))
LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH")  # For local development: full path to .gguf

print(f"Loading GGUF model: {MODEL_FILENAME} from repo {MODEL_REPO}")
if LOCAL_MODEL_PATH:
    print(f"  (Using LOCAL_MODEL_PATH={LOCAL_MODEL_PATH})")
else:
    print("  (Set MODEL_REPO and MODEL_FILENAME as Space Variables/Secrets to override)")

try:
    if LOCAL_MODEL_PATH:
        model_path = LOCAL_MODEL_PATH
        print(f"Using local model file: {model_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"LOCAL_MODEL_PATH file not found: {model_path}")
    else:
        # Download model from HF (happens on every cold start)
        model_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILENAME,
            token=os.getenv("HF_TOKEN"),  # optional, needed if repo is private
        )
        print(f"Model downloaded/cached to: {model_path}")

    # Load llama.cpp model
    llm = Llama(
        model_path=model_path,
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=True,
    )

    print("Model loaded successfully! Ready to serve /v1/chat/completions")

except Exception as e:
    print("\n" + "="*80)
    print("FATAL ERROR: Could not download or load the GGUF model.")
    print("="*80)
    print(f"Repo:    {MODEL_REPO}")
    print(f"File:    {MODEL_FILENAME}")
    print(f"Error:   {e}")
    print()
    print("Troubleshooting steps:")
    print("For HF Space:")
    print("1. Go to your HF Space → Settings and add these Variables/Secrets:")
    print("     MODEL_REPO      = rafaelvieirar1r/llama-3.1-8b-spurgeon-generator-gguf")
    print("     MODEL_FILENAME  = Spurgeon-8B-Q4_K_M.gguf   (or your exact filename)")
    print("2. If the GGUF repo is private, also add a Secret:")
    print("     HF_TOKEN        = hf_xxxxxxxxxxxxxxxxxxxx   (with read access)")
    print("3. Make sure you have UPLOADED the quantized .gguf file to the root of the MODEL_REPO")
    print("   on the 'main' branch (not in a folder).")
    print("4. Common filename: Spurgeon-8B-Q4_K_M.gguf  (from f16.gguf + quantize q4_k_m)")
    print("5. After changing secrets/variables, restart the Space.")
    print()
    print("For local development (on your PC):")
    print("1. Set env var: LOCAL_MODEL_PATH=/full/path/to/Spurgeon-8B-Q4_K_M.gguf")
    print("2. Run: python main.py   (it will load the local GGUF directly, no HF download needed)")
    print("3. The server will listen on http://localhost:7860/v1")
    print("4. Then in another terminal, run your main Streamlit app with matching CUSTOM_LLM_BASE_URL=http://localhost:7860/v1")
    print("="*80 + "\n")
    raise  # re-raise so the container fails clearly with the message above in logs

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "spurgeon-8b"
    messages: List[Message]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    stream: Optional[bool] = False

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # Convert messages to prompt (basic chat template)
        prompt = ""
        for msg in request.messages:
            if msg.role == "system":
                prompt += f"<|system|>\n{msg.content}\n"
            elif msg.role == "user":
                prompt += f"<|user|>\n{msg.content}\n"
            elif msg.role == "assistant":
                prompt += f"<|assistant|>\n{msg.content}\n"
        prompt += "<|assistant|>\n"

        if request.stream:
            # Streaming response
            def generate():
                for chunk in llm(
                    prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    stream=True,
                ):
                    delta = chunk["choices"][0]["text"]
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': delta}}]})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Non-streaming - run in separate thread to prevent event-loop blocking
            output = await asyncio.to_thread(
                llm,
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
            )
            response_text = output["choices"][0]["text"]

            return JSONResponse({
                "id": "chatcmpl-local",
                "object": "chat.completion",
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text.strip()
                    },
                    "finish_reason": "stop"
                }]
            })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
