---
store_path: fine-tuning/data-generation-gemma4
title: "Gemma 4 Local Dataset Generation Analysis"
summary: "Gemma 4 Local Dataset Generation Analysis"
priority: medium
tags: [fine-tuning, gemma4, dataset, ollama]
schema_version: 1.3
last_updated: "2026-06-08T12:46:23-04:00"
---

# Gemma 4 Local Dataset Generation Analysis

We evaluated the feasibility of using Google's Gemma 4 (12B) model locally via Ollama to generate the synthetic Q&A instruction fine-tuning dataset for the Charles Spurgeon Q&A assistant.

## Evaluation Results
- **groundedness & Fidelity:** The model successfully followed strict instructions to ground its answers 100% in the provided context chunk, avoiding external extrapolations or hallucinations.
- **Stylistic Persona:** The model successfully adopted Charles Spurgeon's theological style, register, and vocabulary (e.g., using markers like "My brethren," and "doth").
- **Question Quality:** Rather than using generic templates, Gemma 4 generated specific, detail-oriented questions directly derived from the passage text.
- **Speed & Feasibility:** Once loaded into local memory in Ollama, generation takes approximately 3.5 seconds per request. Running locally avoids rate limit errors (such as Groq's 30 RPM limit on free tiers) and has zero API costs.

## Implementation
- Created `generate_qa_pairs_ollama.py` to target local Ollama instances (with JSON mode enabled).
- Created `generate_qa_pairs_openrouter.py` to support OpenRouter free model endpoints.
- Launched a parallel background run of 1,000 examples using the local `gemma4:latest` model, writing to `spurgeon_train_ollama.jsonl`.
- Created `merge_datasets.py` to consolidate, deduplicate, shuffle, and split all generated outputs.
