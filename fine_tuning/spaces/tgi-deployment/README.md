---
title: Spurgeon Generator (TGI)
emoji: ✝️
colorFrom: yellow
colorTo: gray
sdk: docker
sdk_version: latest
app_port: 7860
---

# Spurgeon Generator - Text Generation Inference

This Space runs a fine-tuned **Llama-3.1-8B** model specialized in Charles Spurgeon's style using **Text Generation Inference (TGI)**.

## Endpoint

This Space exposes an **OpenAI-compatible API** at:

```
https://<your-space-name>.hf.space/v1/chat/completions
```

You can call it the same way you call Groq or OpenAI.

## Usage Example (Python)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://YOUR-SPACE-NAME.hf.space/v1",
    api_key="hf_xxxxxxxxxxxxxxxx"   # Can be any string when no auth is set
)

response = client.chat.completions.create(
    model="tgi",
    messages=[
        {"role": "system", "content": "You are Charles Haddon Spurgeon."},
        {"role": "user", "content": "What does the Bible say about suffering?"}
    ],
    max_tokens=512,
    temperature=0.7,
)

print(response.choices[0].message.content)
```

## Model

- Base: Llama-3.1-8B-Instruct
- Fine-tuned on Spurgeon sermons with high fidelity to the source texts.
- Trained with QLoRA on ~1500 grounded examples.

## Notes

- This is a free Space → GPU may go to sleep after inactivity.
- For production use, consider moving to paid HF Inference Endpoints.
- Combine with your RAG system for best results (retrieval + this generator).

## Source

Fine-tuning code and data generation available in the main repository.
