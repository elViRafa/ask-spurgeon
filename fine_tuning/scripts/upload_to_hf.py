import os
import sys
from pathlib import Path
from huggingface_hub import HfApi

def load_token_from_env():
    # Attempt to load HF_TOKEN from local .env
    for env_path in [Path(".env"), Path("../.env"), Path("../../.env")]:
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("HF_TOKEN="):
                        token = line.strip().split("=", 1)[1].strip("'\" ")
                        if token:
                            return token
    return None

def main():
    merged_path = Path("fine_tuning/models/Spurgeon-8B-Merged-16bit")
    if not merged_path.exists():
        print(f"❌ Error: Local merged model folder not found at: {merged_path.absolute()}")
        print("Please ensure you have completed the local model merge step first!")
        sys.exit(1)

    print(f"✅ Found local merged model at: {merged_path.absolute()}")

    # Retrieve HF Token
    hf_token = load_token_from_env() or os.environ.get("HF_TOKEN")
    if not hf_token:
        print("\n🔑 Hugging Face Write Token not found in .env or environment variables.")
        hf_token = input("Please paste your Hugging Face write token here: ").strip()
        if not hf_token:
            print("❌ Error: A valid Hugging Face token is required to upload.")
            sys.exit(1)

    repo_id = "rafaelvieirar1r/llama-3.1-8b-spurgeon-generator"
    print(f"\n🚀 Starting upload of local folder to Hugging Face repository: {repo_id}...")

    api = HfApi(token=hf_token)
    try:
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
        api.upload_folder(
            folder_path=str(merged_path),
            repo_id=repo_id,
            repo_type="model",
            commit_message="Upload merged Spurgeon fine-tuned model (1500 examples)"
        )
        print("\n🎉 [SUCCESS] Hugging Face upload complete!")
        print(f"🔗 Your model is now available at: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"\n❌ Error uploading to Hugging Face: {e}")
        print("Please verify that your write token is correct and has repository creation/write permissions.")

if __name__ == "__main__":
    main()
