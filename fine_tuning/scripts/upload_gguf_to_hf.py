import os
import sys
from pathlib import Path
from huggingface_hub import HfApi

def load_token_from_env():
    # Attempt to load HF_TOKEN from local .env
    for env_path in [Path(".env"), Path("../.env"), Path("../../.env"), Path("fine_tuning/models/../../.env")]:
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    # Check both uncommented and commented out token as a fallback
                    if stripped.startswith("HF_TOKEN="):
                        token = stripped.split("=", 1)[1].strip("'\" ")
                        if token:
                            return token
                    elif stripped.startswith("# HF_TOKEN="):
                        token = stripped.split("=", 1)[1].strip("'\" ")
                        if token:
                            return token
    return None

def main():
    gguf_path = Path("fine_tuning/models/Spurgeon-8B-f16.gguf")
    if not gguf_path.exists():
        print(f"[ERROR] Local GGUF file not found at: {gguf_path.absolute()}")
        print("Please ensure you have converted the model to GGUF format first!")
        sys.exit(1)

    print(f"[FOUND] Local GGUF model at: {gguf_path.absolute()}")
    print(f"[INFO] File size: {gguf_path.stat().st_size / (1024**3):.2f} GB")

    # Retrieve HF Token
    hf_token = load_token_from_env() or os.environ.get("HF_TOKEN")
    if not hf_token:
        print("\nHugging Face Write Token not found in .env or environment variables.")
        hf_token = input("Please paste your Hugging Face write token here: ").strip()
        if not hf_token:
            print("[ERROR] A valid Hugging Face token is required to upload.")
            sys.exit(1)

    repo_id = "rafaelvieirar1r/llama-3.1-8b-spurgeon-generator-gguf"
    print(f"\n[START] Starting upload of {gguf_path.name} to Hugging Face repository: {repo_id}...")

    api = HfApi(token=hf_token)
    try:
        # Create repository if it doesn't exist
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
        
        # Upload the single GGUF file
        api.upload_file(
            path_or_fileobj=str(gguf_path),
            path_in_repo=gguf_path.name,
            repo_id=repo_id,
            repo_type="model",
            commit_message=f"Upload {gguf_path.name} (float16 GGUF)"
        )
        print("\n[SUCCESS] Hugging Face GGUF upload complete!")
        print(f"URL: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"\n[ERROR] Error uploading to Hugging Face: {e}")
        print("Please verify that your write token is correct and has repository creation/write permissions.")

if __name__ == "__main__":
    main()
