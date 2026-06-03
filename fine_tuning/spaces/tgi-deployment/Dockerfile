# Dockerfile for deploying your fine-tuned Spurgeon model with TGI on HF Spaces
FROM ghcr.io/huggingface/text-generation-inference:latest

# WARNING: 
# TGI on free "CPU Basic" tier has very limited support for 8B models.
# It frequently fails to start or is extremely slow (as you already saw with the Flash Attention + mamba errors).
# This Dockerfile is mainly useful if you later upgrade to a paid GPU Space.

# Your merged 16-bit model on the Hub
ENV MODEL_ID=rafaelvieirar1r/llama-3.1-8b-spurgeon-generator

# More conservative settings to reduce memory usage on CPU
CMD ["--model-id", "rafaelvieirar1r/llama-3.1-8b-spurgeon-generator", \
     "--port", "7860", \
     "--max-input-length", "2048", \
     "--max-total-tokens", "4096"]
