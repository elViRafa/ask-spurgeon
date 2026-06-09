---
store_path: index
title: "Memory Store Index"
summary: "Index of all semantic memory store files."
priority: high
tags: [index, memory-store]
schema_version: 1.3
last_updated: "2026-06-09T14:02:05-04:00"
---

# Memory Store Index

Updated by Memory Fabric Dreaming mode `light` at 2026-06-09T14:02:05-04:00.

| Path | Priority | Summary | Key Topics | Tags |
| --- | --- | --- | --- | --- |
| `bugs/gemma4-chat-template-fix` | medium | Gemma 4 Chat Template Processor Fix | • Problem<br>• Solution | gemma4, chat-template, bugfix, unsloth |
| `bugs/unsloth-fast-patching-warnings` | medium | Unsloth Training Warnings & Fast Patching Resolution | • 1. LoRA Dropout Performance Warning<br>• 2. Gemma 4 Audio Tower Hook Registration Warning | unsloth, lora, gemma4, bugfix |
| `decisions/gemma4-finetuning` | medium | Guides the upgrade of fine-tuning pipelines from Gemma 2 to the efficient, newer Gemma 4 12B model. | • Rationale<br>• Configuration Details | gemma4, finetuning, decisions |
| `decisions/gemma4-local-ollama` | medium | Gemma 4 Local Ollama Deployment | • 1. Tokenizer List Parsing Bug Fix<br>• 2. Remote Streaming Conversion & Double Quantization<br>• 3. Importing into Ollama<br>• 4. Local Disk Cleanup (8B f16 Reclaim) | gemma4, ollama, gguf, quantization, cleanup |
| `fine-tuning/data-generation-gemma4` | medium | Gemma 4 Local Dataset Generation Analysis | • Evaluation Results<br>• Implementation | fine-tuning, gemma4, dataset, ollama |
| `fine-tuning/gemma-support` | medium | Gemma 2 fine-tuning support scripts and configs. | • Updated train_spurgeon_qlora.py to read base model and ch...<br>• Configured launch_training.py to pass parameters dynamica...<br>• Added train_config_gemma.json configuration file. | gemma2, fine-tuning, ollama |
| `grok/integration` | high | Grok Integration with Memory Fabric (MCP + Docs + Native Layer) | • Key Integration Points (as of 2026-06-04/05)<br>• Usage in Grok Sessions for this Project<br>• Windows / This Env Specifics<br>• Benefits for this Project | grok, mcp, memory-fabric, integration, docs, agents |
| `pretraining/bugs/sftconfig-pickle` | medium | Fixed SFTConfig Pickling Mismatch on Kaggle | None recorded | pretraining, unsloth, trl, sftconfig, pickle, bug-fix |
| `pretraining/data-collection` | medium | Pretraining Step 1 — Data Collection Complete | None recorded | pretraining, dataset, sermons |
| `pretraining/dataset-preparation` | medium | Pretraining Step 6 — Dataset Preparation (Notebook A) Plan | • **Notebook A (`data_prep.ipynb`)** runs on CPU-only (acce...<br>• Ingests the cleaned training set `spurgeon_train.txt` and...<br>• Splits text documents on the `<\|endoftext\|>` marker, filt... | pretraining, dataset, kaggle, huggingface |
| `pretraining/environment-setup` | medium | Pretraining Step 5 — Environment Setup & Configurations | None recorded | pretraining, environment, kaggle, config, secrets |
| `pretraining/eval-and-export` | medium | Pretraining Step 8 (Schedule) and Step 9 (Evaluation & Export) | None recorded | pretraining, schedule, evaluation, export, notebook-c, perplexity |
| `pretraining/merge-and-export` | high | Pretraining Step 10 (Merge & Export to Hugging Face) | None recorded | pretraining, merge, export, gguf, huggingface, upload |
| `pretraining/model-choice` | medium | Pretraining Step 4 — Model Choice & Technical Rationale | None recorded | pretraining, model, qwen, vram |
| `pretraining/notebook-structure` | medium | Pretraining Step 3 — Kaggle Notebook Structure | None recorded | pretraining, kaggle, notebook, setup |
| `pretraining/training-configuration` | medium | Pretraining Step 7 — Training Configuration (Notebook B) Plan | • **Notebook B (`training.ipynb`)** runs on 1x T4 GPU (16GB...<br>• VRAM is budgeted carefully (~7.55 GB usage, leaving ~8.45...<br>• Pinned installation of `unsloth[kaggle-new]` is used; man... | pretraining, training, lora, qlora, kaggle, unsloth |
