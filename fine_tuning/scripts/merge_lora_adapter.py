#!/usr/bin/env python3
"""
Merge LoRA adapter into base model for deployment.

Usage (example):
python fine_tuning/scripts/merge_lora_adapter.py \
    --base_model "unsloth/llama-3.1-8b-instruct" \
    --adapter_path "fine_tuning/models/Spurgeon_8B_QLoRA_1500-20260601T135127Z-3-001/Spurgeon_8B_QLoRA_1500" \
    --output_path "fine_tuning/models/Spurgeon-8B-Merged-16bit" \
    --save_4bit false
"""

import argparse
import os
from pathlib import Path
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, required=True)
    parser.add_argument("--adapter_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--save_4bit", type=str, default="false")
    parser.add_argument("--hf_repo_id", type=str, default=None, help="Optional Hugging Face repository ID to upload the merged model (e.g. username/repo-name)")
    parser.add_argument("--hf_token", type=str, default=None, help="Optional Hugging Face write token")
    args = parser.parse_args()

    save_4bit = args.save_4bit.lower() == "true"

    print(f"Loading base model: {args.base_model}")
    device_map = "auto" if torch.cuda.is_available() else None
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if not save_4bit else torch.bfloat16,
        device_map=device_map,
        trust_remote_code=True,
    )

    print(f"Loading LoRA adapter from: {args.adapter_path}")
    model = PeftModel.from_pretrained(base_model, args.adapter_path)

    print("Merging adapter weights into base model...")
    model = model.merge_and_unload()

    print(f"Saving merged model to: {args.output_path}")
    model.save_pretrained(args.output_path)

    print("Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    tokenizer.save_pretrained(args.output_path)

    print("\n[SUCCESS] Merge complete!")
    print(f"Merged model saved at: {args.output_path}")
    print("You can now upload this folder to Hugging Face and deploy with TGI.")

    if args.hf_repo_id:
        print(f"\nUploading merged model to Hugging Face repository: {args.hf_repo_id}...")
        from huggingface_hub import HfApi
        
        token = args.hf_token or os.environ.get("HF_TOKEN")
        if not token:
            print("WARNING: No --hf_token or HF_TOKEN env variable provided. Attempting to use cached Hugging Face credentials...")
            
        api = HfApi(token=token)
        try:
            api.create_repo(repo_id=args.hf_repo_id, repo_type="model", exist_ok=True)
            api.upload_folder(
                folder_path=args.output_path,
                repo_id=args.hf_repo_id,
                repo_type="model",
                commit_message="Upload merged Spurgeon fine-tuned model (1500 examples)"
            )
            print("\n[SUCCESS] Hugging Face upload complete!")
            print(f"Your model is now available at: https://huggingface.co/{args.hf_repo_id}")
        except Exception as e:
            print(f"\n❌ Error uploading to Hugging Face: {e}")


if __name__ == "__main__":
    main()
