# Phase 1: Spurgeon Continued Pretraining — Step 9: Evaluating Training (Notebook C) Plan

This document details the environment specifications, metric calculations, and code layout for **Step 9: Evaluating Training** of the continued pretraining pipeline. 

This step runs in Kaggle **Notebook C (`eval_and_merge.ipynb`)** to compute holdout perplexity, verify sermon register adaptation qualitatively, and export the final Phase 1 LoRA adapter weights.

---

## 1. Notebook C Environment Setup

* **Accelerator:** Select **1x T4 GPU**. Evaluation requires loading model weights and running inference. A T4 GPU provides plenty of compute capacity for this.
* **Internet Access:** Toggle **ON** (active). Required to download dependencies and tokenizer vocabularies.
* **Input Datasets:** Mount the following datasets:
  1. **`spurgeon-cpt-dataset`**: Contains the holdout split (`spurgeon_holdout_dataset`).
  2. **`spurgeon-training-run-1`** (ensure **Version 2** is active): Contains the output checkpoints from Notebook B Epoch 2 (including `checkpoint-432` or `spurgeon_lora_epoch2`).

---

## 2. Model & LoRA Loading Mechanics

Rather than loading the base model and Peft model separately and calling `model.load_state_dict()`, we leverage Unsloth's native `from_pretrained()` loading capabilities. 

When you pass a local path containing PEFT adapter configuration and weight files (such as `adapter_config.json` and `adapter_model.safetensors`), Unsloth automatically reads the base model ID, pulls it from Hugging Face Hub, instantiates the model in 4-bit, and attaches the adapter weights.

```python
from unsloth import FastLanguageModel
import torch

MAX_SEQ_LENGTH = 2048
LORA_PATH = "/kaggle/input/datasets/rafaelvieira1/spurgeon-training-run-1/checkpoints/checkpoint-432"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = LORA_PATH,
    max_seq_length = MAX_SEQ_LENGTH,
    dtype          = None,
    load_in_4bit   = True,
)
```

---

## 3. Quantitative Holdout Perplexity

We evaluate the language model's perplexity on the 50-sermon holdout dataset (`spurgeon_holdout_dataset`). Perplexity measures how well the model predicts the test text (lower perplexity indicates a better fit to Spurgeon's language).

### The Math:
$$\text{Perplexity} = \exp\left( \frac{\sum_{i} \text{Loss}_i \times N_i}{\sum_{i} N_i} \right)$$
Where $\text{Loss}_i$ is the average cross-entropy loss of sequence $i$, and $N_i$ is the token length of sequence $i$. This computes the correct length-weighted cross-entropy loss across the entire holdout set.

### Python Code:
```python
import math
from datasets import load_from_disk

# Set model to inference mode (enables faster forward passes)
FastLanguageModel.for_inference(model)

# Load the holdout dataset mounted from Notebook A outputs
holdout_dataset = load_from_disk("/kaggle/input/datasets/rafaelvieira1/spurgeon-cpt-dataset/spurgeon_holdout_dataset")

total_loss = 0.0
total_tokens = 0

print("Computing holdout perplexity...")
for idx, doc in enumerate(holdout_dataset):
    # Tokenize the sermon text
    inputs = tokenizer(doc["text"], return_tensors="pt")
    inputs = {k: v.to("cuda") for k, v in inputs.items()}
    
    num_tokens = inputs["input_ids"].size(1)
    
    # Safe truncation check to prevent out-of-bounds context index or VRAM spikes
    if num_tokens > MAX_SEQ_LENGTH:
        inputs = {k: v[:, :MAX_SEQ_LENGTH] for k, v in inputs.items()}
        num_tokens = MAX_SEQ_LENGTH
        
    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss.item()
        
    total_loss += loss * num_tokens
    total_tokens += num_tokens

average_loss = total_loss / total_tokens
perplexity = math.exp(average_loss)

print(f"\nEvaluation Results:")
print(f"  - Total Holdout Tokens: {total_tokens:,}")
print(f"  - Length-Weighted Loss: {average_loss:.4f}")
print(f"  - Holdout Perplexity: {perplexity:.2f}")
```

---

## 4. Qualitative style validation

Perplexity alone does not guarantee that the model is capturing Spurgeon's rhetorical pacing and theological idioms without collapsing into repetitive text loops. We test completions on three standard prompts.

### Prompts:
1. **Completion Test:** `"The love of Christ is not a cold, speculative thing. It is "`
2. **Sermon Opening Test:** `"Text: Romans 8:28. 'And we know that all things work together for good to them that love God.' My dear friends, "`
3. **Doctrinal Treatment Test:** `"What, then, is saving faith? Let us examine this question carefully, for "`

### Expectation & Style Metrics:
* **Theological Tone:** Solid Reformed/Baptist doctrine, highlighting grace, faith, Christ's atonement, and personal holiness.
* **Oratorical Rhythm:** Usage of characteristic rhetorical questions, direct audience addresses (e.g. *"my dear friends"*, *"beloved"*, *"sinner, hear this"*), and descriptive metaphors.
* **Termination Quality:** The model should generate a natural flow of thought and terminate when hitting the token limit without trailing off into gibberish.

---

## 5. Output Adapter Export

Finally, the adapter weights are saved to the local directory so they can be exported as your finalized Phase 1 LoRA model:

```python
output_path = "/kaggle/working/spurgeon_lora_final"

print(f"Saving final Phase 1 LoRA adapter weights to {output_path}...")
model.save_pretrained(output_path)
tokenizer.save_pretrained(output_path)
print("LoRA weights saved successfully.")
```
