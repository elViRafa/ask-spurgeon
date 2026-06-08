---
store_path: pretraining/merge-and-export
title: "Pretraining Step 10 (Merge & Export to Hugging Face)"
summary: "Pretraining Step 10 (Merge & Export to Hugging Face)"
priority: high
tags: [pretraining, merge, export, gguf, huggingface, upload]
schema_version: 1.3
last_updated: "2026-06-08T10:18:26-04:00"
---

# Pretraining Step 10 (Merge & Export to Hugging Face)

Step 10 of the continued pretraining plan has been successfully completed:
1. **Model Weights Merged:** The trained Phase 1 LoRA adapter weights (from checkpoint-432) were merged back into the base Qwen2.5-3B model.
2. **GGUF Conversion (F16 Precision):** The merged model was converted to GGUF format with original 16-bit (`f16`) precision on Kaggle, preserving 100% of the pretraining model quality.
3. **Hugging Face Hub Upload:** The GGUF file (`qwen2.5-3b.F16.gguf` under `/kaggle/working/spurgeon_f16_gguf_gguf/`) was successfully uploaded to the Hugging Face model repository `rafaelvieirar1r/qwen2.5-3b-spurgeon-gguf-phase1` using the user's secure write token (`HF_TOKEN`) from Kaggle Secrets.
4. **Robustness Improvement:** Updated the local template notebook `continued_pretrain/notebooks/C_eval_and_merge.ipynb` to use dynamic glob-based GGUF file detection (`glob.glob("/kaggle/working/**/*.gguf", recursive=True)`) to gracefully handle folder and filename variations.
