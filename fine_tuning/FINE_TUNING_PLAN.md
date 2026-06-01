# Fine-Tuning Plan: Spurgeon Generator with High Textual Fidelity

**Project**: Ask Spurgeon RAG  
**Goal**: Create a fine-tuned model that generates answers in Spurgeon's voice while maintaining **high fidelity** to the retrieved source text.  
**Date**: 2026-05-31  
**Status**: Implementation in progress

---

## 1. Core Philosophy & Design Decisions

### Why Fine-Tuning (and Why Not)

- **Current system strength**: Strong retrieval + Groq 70B gives good factual grounding.
- **Problem**: Even with good retrieval, the generator (Groq) does not speak in Spurgeon's distinctive voice.
- **Risk of naive fine-tuning**: The model can learn to *sound* like Spurgeon while saying things he never said (style without substance).

**Our Approach**: Grounded Style Transfer
- Keep the existing RAG retrieval system (the source of truth).
- Fine-tune only the **generator** to answer *strictly from the provided context* in Spurgeon's style.
- This is fundamentally different from training a standalone Spurgeon chatbot.

### Key Principle: "Fidelity First"

Every training example must follow this contract:
> "Given this exact retrieved context, generate an answer in Spurgeon's voice that uses *only* information present in the context."

This is enforced during:
- Synthetic data generation (teacher model prompt)
- Training data formatting (context is always visible)
- Evaluation (we measure faithfulness to context)

---

## 2. Recommended Technical Stack

| Component              | Choice                                      | Reason |
|------------------------|---------------------------------------------|--------|
| Base Model             | `meta-llama/Llama-3.1-8B-Instruct`          | Best quality/size tradeoff for fine-tuning |
| Method                 | QLoRA + Unsloth                             | Fastest + lowest VRAM (critical for 8B+) |
| Data Format            | Llama-3 ChatML (with explicit context)      | Native for the base model |
| Training Environment   | Google Colab Pro (A100) or RunPod/Vast      | Realistic free/cheap path |
| Data Generation        | Groq `llama-3.3-70B-versatile` (or Claude)  | Strong teacher for high-quality synthetic data |

**Why not 70B for training initially?**
- 8B is much more practical to iterate on.
- We can later distill or train a 70B adapter once we validate the approach.

---

## 3. Data Creation Strategy (Most Critical Part)

### 3.1 Data Generation Pipeline

We use the existing RAG system to create high-fidelity training data:

1. Sample real questions (from `tests/rag_test_questions.py` + new ones).
2. Retrieve top-k relevant chunks using current Chroma/Qdrant index.
3. Send to strong teacher model with this strict prompt:

```text
You are Charles Haddon Spurgeon (1834–1892).

You must answer the user's question **using only the information in the "CONTEXT" section below**.
- Do not add external knowledge.
- Do not invent quotes or stories.
- If the context does not contain the answer, clearly say so.
- Speak in your natural 19th-century voice: direct, pastoral, vivid, full of biblical imagery, and warm toward the listener.

CONTEXT:
{retrieved_chunks}

QUESTION:
{question}

Answer:
```

4. Save as ChatML format with:
   - System message containing the context + instructions
   - User message = original question
   - Assistant message = the generated Spurgeon-style answer

### 3.2 Target Dataset

- **Minimum viable**: 3,000–5,000 high-quality examples
- **Good target**: 8,000–15,000 examples
- Mix of:
  - Short doctrinal questions
  - Practical pastoral questions
  - "Explain this passage" questions
  - Questions where context is insufficient (teaches honesty)

---

## 4. Training Configuration (QLoRA + Unsloth)

**Target for first serious run**:
- Model: Llama-3.1-8B-Instruct
- Quantization: 4-bit (NF4)
- LoRA rank: 64
- LoRA alpha: 128
- Target modules: All linear layers
- Sequence length: 4096–8192 (sermons are long)
- Epochs: 1.5–2
- Learning rate: 1e-4 with cosine decay
- Optimizer: AdamW 8-bit

**Expected training time**:
- On A100 40GB: ~3–6 hours for 8k examples
- On T4 (Colab free): Possible but slow (~15–25 hours) — only for very small experiments

---

## 5. Evaluation Strategy

We will not trust "it sounds good" subjective judgment.

### Automated Metrics
- **Faithfulness**: LLM-as-Judge scores how much of the answer is supported by the retrieved context (0–5)
- **Style Score**: Compare against a small set of real Spurgeon quotes (embedding similarity or another judge)
- **Helpfulness**: Standard helpfulness judge

### Human Evaluation (Gold Standard)
- 50–100 blind comparisons:
  - Current RAG + Groq 70B
  - RAG + Fine-tuned 8B
- Criteria: Faithfulness + Voice + Overall preference

---

## 6. Deployment Strategy

After training:
1. Merge LoRA weights into base model.
2. Upload merged model to Hugging Face (e.g. `rafaelvieirar1r/llama-3.1-8b-spurgeon-generator`).
3. Inference options (in order of recommendation):
   - **Best**: Keep using Groq 70B for most traffic + route difficult/style-sensitive queries to fine-tuned model.
   - Use the fine-tuned model via Hugging Face Inference Endpoints (paid but cheap).
   - Run locally with vLLM or Ollama for personal use.

---

## 7. Current Implementation Status (as of 2026-05-31)

### Completed (Autonomous Implementation)
- Full directory structure (`fine_tuning/`)
- This comprehensive plan document (`FINE_TUNING_PLAN.md`)
- Quick-start guide (`README.md`)
- **Ready-to-run Google Colab notebook** (`notebooks/Spurgeon_Fine_Tuning_Pipeline.ipynb`)
- Production-ready synthetic data generator (`scripts/generate_synthetic_data.py`)
- Complete Unsloth QLoRA training script (`scripts/train_spurgeon_qlora.py`)
- Evaluation script skeleton (`scripts/evaluate.py`)

### Current Status (Ready for Training)
- **Training dataset prepared**: `fine_tuning/data/spurgeon_train_1500.jsonl` (exactly 1500 examples)
- Training configuration: `fine_tuning/train_config.json`
- Easy launcher: `python fine_tuning/scripts/launch_training.py`

### Next Steps
1. Run training with the 1500 examples (use the launcher or Colab notebook).
2. Test training on Google Colab (even a small run is very valuable).
3. Build proper LLM-as-Judge evaluation for faithfulness + style.
4. Create one-click Colab notebook (already exists in `notebooks/`).

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Synthetic data not faithful | Very strict teacher prompt + post-filtering with LLM judge |
| Model forgets to use context | Always include context in every training example + system prompt |
| Overfitting to synthetic patterns | Mix in some real Spurgeon quotes as "continue this passage" tasks |
| 8B too weak for good style | Accept it as v1; plan 70B distillation later if promising |

---

## 9. How to Run (Once Scripts Are Ready)

See the individual scripts in `fine_tuning/scripts/` for detailed instructions.

Typical flow:
```bash
# 1. Generate synthetic data (requires Groq key)
python fine_tuning/scripts/generate_synthetic_data.py --limit 5000

# 2. Format for training
python fine_tuning/scripts/prepare_dataset.py

# 3. Train (on Colab or strong GPU)
python fine_tuning/scripts/train_spurgeon_qlora.py

# 4. Evaluate
python fine_tuning/scripts/evaluate.py
```

---

**Document Owner**: Grok (autonomous implementation)  
**Last Updated**: 2026-05-31
