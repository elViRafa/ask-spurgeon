# Deploying Your Spurgeon Fine-Tuned Model with TGI on HF Spaces (Free)

This guide walks you through deploying `llama-3.1-8b-spurgeon-generator` using **Text Generation Inference (TGI)** on Hugging Face Spaces for free.

## Step 1: Merge Your LoRA Adapter (Important)

Your current model is a **LoRA adapter only**. For the simplest TGI deployment, you should first merge it with the base model.

Run this script locally or on Colab:

```bash
python fine_tuning/scripts/merge_lora_adapter.py \
  --base_model "unsloth/llama-3.1-8b-instruct" \
  --adapter_path "fine_tuning/models/Spurgeon_8B_QLoRA_1500-20260601T135127Z-3-001/Spurgeon_8B_QLoRA_1500" \
  --output_path "fine_tuning/models/Spurgeon-8B-Merged-16bit"
```

This will create a full model you can upload.

## Step 2: Upload the Merged Model to Hugging Face

1. Create a new model repo on Hugging Face (e.g. `your-username/llama-3.1-8b-spurgeon-generator`).
2. Upload the merged folder (or use the `huggingface_hub` Python library).

## Step 3: Create a TGI Space

1. Go to: https://huggingface.co/new-space
2. Choose:
   - **SDK**: Docker
   - **Hardware**: CPU basic (or GPU if you have quota)
   - **Visibility**: Public (recommended)
3. Connect it to your GitHub repo (or create files directly).

## Step 4: Add the Required Files

Copy the files from this folder into your Space:
- `Dockerfile`
- `README.md` (this becomes the Space card)

Edit the `Dockerfile` and replace `YOUR_USERNAME/llama-3.1-8b-spurgeon-generator` with your actual model repo.

## Step 5: (Recommended) Set Environment Variables

In your Space → **Settings → Variables and secrets**, add:

- `HF_HUB_ENABLE_HF_TRANSFER=1` (faster downloads)

## Accessing the API

Once the Space is running, your OpenAI-compatible endpoint will be:

```
https://<username>-<space-name>.hf.space/v1/chat/completions
```

You can now call this from your main RAG app instead of (or in addition to) Groq.

## Limitations of Free Tier

- GPU can sleep after inactivity.
- Cold starts can take 1–3 minutes.
- Limited concurrent requests.

For production, consider moving to paid **HF Inference Endpoints**.

## Next Steps

After deploying, update your main app to call this new endpoint when you want maximum Spurgeon style.
