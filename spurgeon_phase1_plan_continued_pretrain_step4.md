# Phase 1: Spurgeon Continued Pretraining — Step 4: Model Choice & Technical Rationale

This file documents the technical specs, architectural decisions, VRAM budgeting, and tokenizer compatibility for **Step 4: Model Choice** of the continued pretraining pipeline.

The model selected for this phase is **`unsloth/Qwen2.5-3B`** (the base model variant).

---

## 1. Model Specifications & Architecture

Qwen2.5-3B is a state-of-the-art, dense, decoder-only language model developed by the Qwen team, pre-quantized and packaged by Unsloth for optimized training.

| Specification | Value | Technical Context |
| :--- | :--- | :--- |
| **Model ID** | `unsloth/Qwen2.5-3B` | Base model (non-instruct), ideal for continued pretraining. |
| **Parameters** | 3.09 Billion (dense) | Optimal capacity for style transfer without high computational cost. |
| **Quantization** | 4-bit (NF4) | NF4 (NormalFloat4) quantization via `bitsandbytes` to minimize VRAM. |
| **Context Length** | 32,768 tokens | Trained at 2,048 tokens context window for GPU efficiency. |
| **Vocab Size** | 151,643 tokens | Large BPE-based vocabulary, minimizes subword fragmentation. |
| **Attention Mechanism** | Grouped-Query Attention | Reduces KV cache memory usage, speeding up packed sequence training. |
| **License** | Apache 2.0 | Permissive commercial and research usage. |

---

## 2. Rationale for Selecting Qwen2.5-3B

The selection of Qwen2.5-3B is based on three primary factors: performance-to-size ratio, vocab structure, and hardware compatibility.

### 2.1 — Archaic English Handling (19th-Century Prose)
Spurgeon's sermons are written in 19th-century English, featuring biblical registers, archaic pronouns (`thou`, `thee`, `ye`), and verbs (`hast`, `doth`, `save`). 
* Models with smaller vocabularies (e.g., LLaMA 3's 128k or older LLaMA 2's 32k) fragment these archaic tokens into multiple subword pieces, increasing the average sequence length and diluting the style representation.
* Qwen2.5's **151,643 token vocabulary** natively represents many of these theological and archaic words as single tokens, resulting in higher training throughput and more robust token-level statistical adaptation.

### 2.2 — Dense vs. Mixture of Experts (MoE)
On Kaggle's free tier, training MoE models (like Mixtral or Qwen2.5-Plus variants) is impossible due to routing overhead and parameter VRAM footprints. Dense architectures have predictable memory bounds and stable loss curves, making Qwen2.5-3B the most capable dense model under the 8B parameter threshold.

### 2.3 — Comparison with Alternative Models

| Feature | Qwen2.5-3B (Chosen) | Llama-3.2-3B | Gemma-2-2B |
| :--- | :--- | :--- | :--- |
| **Parameter Size** | 3.09B | 3.21B | 2.50B |
| **Vocab Size** | 151,643 | 128,256 | 256,000 |
| **CPT Stability** | Excellent (low loss variance) | Moderate | High loss spikes reported |
| **Unsloth Support** | Native CPT Notebooks | Native CPT Notebooks | Lacks stable packing recipes |
| **T4 VRAM Headroom** | **~10.2 GB** | ~9.8 GB | ~11.5 GB |

---

## 3. LoRA Hyperparameter Configurations

For continued pretraining (CPT), the goal is to shift the style and vocabulary distribution of the model without overwriting its core knowledge. 

### 3.1 — Target Modules
We target both attention projection matrices and MLP gate modules:
* `q_proj`, `k_proj`, `v_proj`, `o_proj` (Attention)
* `gate_proj`, `up_proj`, `down_proj` (Feed-Forward Network)

This covers all linear layers in the transformer block, maximizing the expressive power of the LoRA adapter.

### 3.2 — No Embeddings or LM Head Training
* **Decision:** We do **NOT** train the input embeddings or the output language modeling head (`lm_head`).
* **Rationale:** Training embeddings and the LM head increases the trainable parameters by hundreds of millions, requiring them to be kept in full 16-bit precision. This causes a major VRAM spike (~3-4 GB extra) and risks gradient instability during training. Since we are not adding new special vocabulary tokens (we are repurposing the existing vocabulary to model Spurgeon's dialect), frozen embeddings are sufficient and highly stable.

### 3.3 — Hyperparameter Settings
* **Rank ($r$) = 32:** Large enough to capture complex prose cadences and structural style choices, while keeping adapter size small (~100-300 MB).
* **Alpha ($\alpha$) = 64:** Following the rule of thumb $\alpha = 2 \times r$, this scales the LoRA weights appropriately, allowing the style shifts to influence the activations.
* **LoRA Dropout = 0:** Critically set to `0` to enable Unsloth's custom CUDA/Triton fast-patching kernels. Setting a non-zero dropout disables kernel fusion, increasing training time by 20-50%.

---

## 4. Hardware VRAM & Compute Budget (1x T4 GPU)

Training on Kaggle's single T4 GPU provides **16 GB of GDDR6 VRAM**. We budget our memory layout to prevent Out-Of-Memory (OOM) crashes:

### 4.1 — VRAM Budget Breakdown
1. **Model Weights (4-bit NF4):** ~2.15 GB
2. **Optimizer States (AdamW 8-bit):** ~0.25 GB (only stored for the trainable LoRA adapter parameters)
3. **KV Cache (Batch Size = 2, Length = 2048):** ~0.45 GB
4. **Activations & Gradients:** ~3.5 GB (managed via gradient checkpointing)
5. **System Overhead & CUDA Context:** ~1.2 GB
* **Total Estimated VRAM Usage:** **~7.55 GB**
* **Available Headroom:** **~8.45 GB** (Extremely safe, zero risk of OOM under normal training runs)

### 4.2 — Compute Quota Budgeting
Using a single T4 GPU on Kaggle consumes your weekly GPU quota hours at **1.0x rate** (compared to 2.0x for 2x T4).
* **Weekly Limit:** 30 hours.
* **Epoch Time:** ~7-9 hours.
* **Total Training Time (2 Epochs):** ~14-18 hours.
* **Quota Consumed:** ~14-18 hours (Leaving ~12-16 hours free for evaluations and other runs).

---

## 5. Tokenizer Special Tokens and Separators

The tokenizer for `unsloth/Qwen2.5-3B` utilizes the `<|endoftext|>` special token to represent document boundaries. 

* **Ingestion Mapping:** In Step 2, we separated individual sermons using `<|endoftext|>`. During training, the SFTTrainer's `packing=True` parameter concatenates documents together, placing the `<|endoftext|>` token between them, and splits them into clean `2048` token context windows.
* **Prompting Separator:** When prompting the pre-trained model in Notebook C, appending `<|endoftext|>` resets the model's contextual state, signalling the start of a fresh sermon output.
