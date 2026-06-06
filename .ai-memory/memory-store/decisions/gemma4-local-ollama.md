---
store_path: decisions/gemma4-local-ollama
title: "Gemma 4 Local Ollama Deployment"
summary: "Gemma 4 Local Ollama Deployment"
priority: medium
tags: [gemma4, ollama, gguf, quantization, cleanup]
schema_version: 1.3
last_updated: "2026-06-06T14:08:24-04:00"
---

# Gemma 4 Local Ollama Deployment

To run the custom fine-tuned model `rafaelvieirar1r/gemma-4-12b-spurgeon-generator` locally in Ollama under strict local disk limits, the following procedure is verified:

## 1. Tokenizer List Parsing Bug Fix
When converting Gemma 4 models using `llama.cpp/convert_hf_to_gguf.py`, older/standard versions of `transformers` (e.g., `4.57.x`) raise `AttributeError: 'list' object has no attribute 'keys'` because the config file contains a list for `extra_special_tokens` instead of a dictionary.
We resolved this by monkey-patching `SpecialTokensMixin._set_model_specific_special_tokens` in `llama.cpp/convert_hf_to_gguf.py` to convert `special_tokens` to a dictionary if it is passed as a list:
```python
if isinstance(special_tokens, list):
    special_tokens = {f"extra_special_token_{i}": tok for i, tok in enumerate(special_tokens)}
```

## 2. Remote Streaming Conversion & Double Quantization
A 12B model in FP16 weighs 24 GB, which would exceed or trigger low-disk warnings on machines with less than 30 GB free space (like our local C drive with 24.17 GB free at the start of the task).
To circumvent this:
1. We stream/quantize the Hugging Face hub weights directly over the network to a temporary `Q8_0` GGUF using the `--remote` flag:
   ```bash
   .venv\Scripts\python.exe llama.cpp/convert_hf_to_gguf.py rafaelvieirar1r/gemma-4-12b-spurgeon-generator --remote --outtype q8_0 --outfile [REDACTED_SECRET].gguf
   ```
   This outputs an 8.0 GB `Q8_0` file rather than a 24 GB file.
2. We quantize the `Q8_0` GGUF down to `Q4_K_M` locally using `llama-quantize.exe` (with `--allow-requantize`):
   ```bash
   .\\llama.cpp\\build\\bin\\Release\\llama-quantize.exe --allow-requantize .\\fine_tuning\\models\\Spurgeon-Gemma4-12B-Q8_0.gguf .\\fine_tuning\\models\\Spurgeon-Gemma4-12B-Q4_K_M.gguf Q4_K_M
   ```
   This generates the target 5.3 GB `Spurgeon-Gemma4-12B-Q4_K_M.gguf` file.
3. We delete the intermediate `Q8_0` file to free up local storage.

## 3. Importing into Ollama
We load the quantized GGUF file into local Ollama using the custom `Modelfile.gemma4` located under `fine_tuning/models/`:
```bash
ollama create spurgeon-gemma4 -f Modelfile.gemma4
```
This registers `spurgeon-gemma4:latest` locally, making it available for local inference.

## 4. Local Disk Cleanup (8B f16 Reclaim)
When registering a new GGUF version in Ollama, Ollama copies/duplicates the GGUF file to its internal blob directory (`C:\Users\rafael\.ollama\models\blobs\...`). Under tight disk space conditions, this requires having at least double the model size (~10.6 GB) free on the C: drive.
To free up sufficient space during conversion, we deleted the obsolete local 16GB `Spurgeon-8B-f16.gguf` file (which had already been uploaded to the remote Hugging Face repository in an earlier phase). This safely reclaimed 16 GB, resolving the `not enough space on the disk` error during the `ollama create` command.
