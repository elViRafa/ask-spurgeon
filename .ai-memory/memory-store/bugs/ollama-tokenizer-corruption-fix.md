---
store_path: bugs/ollama-tokenizer-corruption-fix
title: "Bug Fix: Ollama Runaway Generation and Tokenizer Corruption"
summary: "Bug Fix: Ollama Runaway Generation and Tokenizer Corruption"
priority: medium
tags: [bugs, tokenizer, gguf, ollama]
schema_version: 1.3
last_updated: "2026-06-10T15:18:59-04:00"
---

# Bug Fix: Ollama Runaway Generation and Tokenizer Corruption (vinfos/spep/quotelev)

## Context
When exporting a merged model to GGUF format using Unsloth (Phase 1 pretraining), the special token mappings (like `<|im_end|>` and `<|im_start|>`) inside the tokenizer can get corrupted. When reloading the GGUF model or its converted Hugging Face folder as the base model for Phase 2 fine-tuning:
1. Special control tokens split into ordinary subwords (e.g., `<|im_end|>` tokenizes to the subwords of `\"vinfos\"` or is mapped to the token ID of `\"quotelev\"`).
2. SFT training on this dataset teaches the model to end its turn by literally generating the ordinary subwords for `\"vinfos\"` or `\"quotelev\"`.
3. In Ollama, the model outputs `\"vinfos\"` or `\"quotelev\"` at the end of its turn, and since Ollama does not recognize it as a stop token, generation continues indefinitely in a loop simulating both user and assistant turns.
4. **Base Model vs. Fine-Tuned Model Confusion:** The user loaded `./spurgeon_f16_gguf.F16.gguf` (the Phase 1 base model) in their local Ollama `Modelfile`. This base model lacks instruction tuning (SFT), causing it to refuse theological questions and claim to be a STEM assistant developed by Alibaba Cloud.

## Solution
1. **Patched Notebooks (Re-training):** Updated [D_qa_data_prep.ipynb](file:///c:/Users/rafael/Projetos/search-sermons/fine_tuning/notebooks/D_qa_data_prep.ipynb), [E_qa_training.ipynb](file:///c:/Users/rafael/Projetos/search-sermons/fine_tuning/notebooks/E_qa_training.ipynb), and [F_qa_eval.ipynb](file:///c:/Users/rafael/Projetos/search-sermons/fine_tuning/notebooks/F_qa_eval.ipynb) to load clean tokenizer configurations directly from Hugging Face's `\"unsloth/Qwen2.5-3B-Instruct\"` repository instead of the corrupted local folder, ensuring proper atomic tokenization to ID `151645`.
2. **Download Fine-Tuned GGUF Model:** Instructed the user to re-run the patched notebooks D, E, F on Kaggle to produce the clean fine-tuned GGUF file (`spurgeon_qa_f16_gguf.F16.gguf`), download it, and place it in the local `fine_tuning/models/` directory.
3. **Local Modelfile Configuration:** Updated the local [Modelfile](file:///c:/Users/rafael/Projetos/search-sermons/fine_tuning/models/Modelfile) to load the fine-tuned model and use standard stop parameters, removing the temporary mitigations for `"vinfos"`, `"spep"`, and `"+lsi"`.
