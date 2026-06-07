# Phase 1: Spurgeon Continued Pretraining — Step 7: Training Configuration (Notebook B) Plan

This file documents the technical configurations, hyperparameters, library constraints, and cross-session checkpoint resumption logic for **Step 7: Training Configuration** of the continued pretraining pipeline.

This step runs in Kaggle **Notebook B (`training.ipynb`)** to train a PEFT LoRA adapter on top of `unsloth/Qwen2.5-3B` using the dataset prepared in Notebook A.

---

## 1. Kaggle Hardware & VRAM Allocation

Training a large language model requires GPU acceleration. We optimize the VRAM footprint on Kaggle's single T4 GPU (16 GB GDDR6) to guarantee fast training speed and eliminate Out-Of-Memory (OOM) risks:

1. **Accelerator:** Select **1x T4 GPU**. This allocates a single T4 GPU. A single T4 GPU is simpler to initialize and consumes your weekly Kaggle quota hours at a **1.0x rate** (compared to a 2.0x rate for 2x T4), doubling your weekly training allowance to 30 session hours.
2. **Internet Access:** Toggle **ON** (active) in the Settings sidebar. This is required to download Python dependencies from PyPI, the Unsloth installer from GitHub, and the Qwen base weights from the Hugging Face Hub.
3. **VRAM Budgeting (Qwen2.5-3B in 4-bit NF4):**
   * **Base Model weights:** ~2.15 GB
   * **Optimizer States (AdamW 8-bit):** ~0.25 GB
   * **KV Cache (Batch Size = 2, Length = 2048):** ~0.45 GB
   * **Activations & Gradients:** ~3.50 GB (managed via gradient checkpointing)
   * **System/CUDA Context Overhead:** ~1.20 GB
   * **Total VRAM Consumption:** **~7.55 GB**
   * **Available Headroom:** **~8.45 GB** (Extremely safe; zero risk of OOM under normal execution).

---

## 2. Dependency Management and Installation Rules

Because Kaggle resets the execution environment on session start, installation commands must run at the top of Notebook B in every session.

### 2.1 — Pinned Installation
```python
# Install Unsloth and specific patched versions for Kaggle environment
!pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git"
```

### 2.2 — CRITICAL: No Manual Upgrades
> [!WARNING]
> Do NOT execute manual upgrades of primary libraries, such as:
> `!pip install --upgrade transformers trl peft bitsandbytes`
> 
> **Why:** Unsloth depends on specific, pinned, and source-patched versions of these libraries to perform its custom memory-efficient Triton kernel operations. Upgrading them pulls PyPI versions that lack these patches, causing:
> 1. Failure to load compiled CUDA kernels, resulting in slow training speeds.
> 2. VRAM allocation overflows (OOM) due to unpatched memory leakages in standard PEFT classes.
> 3. Import errors due to deprecated signatures in the latest library releases.

---

## 3. Model & PEFT Setup Code

We load the base model in 4-bit quantization and define the LoRA adapter. We target both attention projection matrices and MLP layers to maximize adaptation capability.

```python
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

from unsloth import FastLanguageModel
import torch

MAX_SEQ_LENGTH = 2048
LORA_RANK = 32

# 1. Load base model in 4-bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name   = "unsloth/Qwen2.5-3B",
    max_seq_length = MAX_SEQ_LENGTH,
    dtype        = None,
    load_in_4bit = True,
)

# 2. Apply the PEFT LoRA adapter
model = FastLanguageModel.get_peft_model(
    model,
    r = LORA_RANK,
    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha   = 64,
    lora_dropout = 0, # Critical: set to 0 to enable fast custom Triton kernels
    bias         = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 42,
)
```

---

## 4. Trainer Configuration (SFTTrainer)

We configure the Hugging Face `SFTTrainer` with sequence packing enabled. Packing is crucial for pretraining: it concatenates multiple short texts (separated by `<|endoftext|>`) into a single 2048-token sequence, preventing wasted compute on padding tokens and speeding up training by 3-5x.

```python
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_from_disk
import os
import shutil

# Kaggle mounts input datasets as read-only. SFTTrainer's internal dataset.map()
# attempts to write temporary cached files in the dataset folder, causing an OSError.
# To prevent this, we copy the dataset from /kaggle/input/ to the writable /kaggle/working/ first.
src_dataset_path = "/kaggle/input/datasets/rafaelvieira1/spurgeon-cpt-dataset/spurgeon_dataset"
local_dataset_path = "/kaggle/working/spurgeon_dataset"

if not os.path.exists(local_dataset_path):
    print(f"Copying dataset from {src_dataset_path} to writable path {local_dataset_path}...")
    shutil.copytree(src_dataset_path, local_dataset_path)
else:
    print(f"Dataset already exists at writable path: {local_dataset_path}")

# Load the dataset from the writable local directory
dataset = load_from_disk(local_dataset_path)

# Define target output directory
output_dir = "/kaggle/working/checkpoints"
```

### 4.1 — Training Hyperparameters and Rationale

* **Batch Size per Device = 2 / Gradient Accumulation Steps = 8:** This results in an **effective batch size of 16** (2 * 8), which provides stable gradient updates without exceeding the VRAM limit.
* **Learning Rate = 2e-4 with Cosine Scheduler:** The standard rate for LoRA domain adaptation, decaying smoothly to zero over the course of training.
* **Optimizer = `adamw_8bit`:** Saves ~2 GB of VRAM by storing optimizer momentum states in 8-bit precision instead of 32-bit float.
* **`save_total_limit = 3`:** Keeps only the last 3 checkpoints. This is critical to prevent running out of Kaggle's **20 GB writeable disk quota** (each checkpoint is ~300-500MB).
* **`packing = True`:** Packs documents together using the tokenizer's `<|endoftext|>` token as a boundary.

---

## 5. Checkpoint Resumption & Epoch-Incrementing Logic

Due to Kaggle's **9-hour session limit** for background runs, training our ~30.28M tokens (which takes roughly 15-18 hours total for 2 full epochs) must be split into two sessions. 

### 5.1 — The SFTTrainer Auto-Exit Bug
> [!IMPORTANT]
> When resuming training, the trainer reads the completed training progress from the checkpoint directory. If you set `num_train_epochs = 1` in Session 1, and resume in Session 2 with `num_train_epochs = 1`, the trainer will see that 1 epoch has already been completed and will **immediately exit** without training anything.
> 
> **Mitigation:** You MUST increment the `num_train_epochs` parameter to match the total target epochs (e.g. set it to `2` for Run 2, and `3` for Run 3).

### 5.2 — Programmatic Resumption Code
We implement a robust check that automatically detects if previous checkpoints exist, dynamically increments the epoch targets, and passes the folder path to `trainer.train()`:

```python
# RESUMPTION CONFIGURATION
# To resume: mount the output dataset of your previous run (e.g., Run 1) as an Input Dataset
RUN_NUMBER = 1 # Update to 2, 3, etc. for subsequent runs

# If resuming from a previous run output mounted as an input, specify the path here:
# Example: "/kaggle/input/datasets/rafaelvieira1/spurgeon-training-run-1/checkpoints/checkpoint-1500"
PREV_RUN_CHECKPOINT = None 

# Define total target epochs (must be equal to the current run number)
TOTAL_TARGET_EPOCHS = RUN_NUMBER

training_args = TrainingArguments(
    per_device_train_batch_size = 2,
    gradient_accumulation_steps = 8,
    num_train_epochs            = TOTAL_TARGET_EPOCHS,
    warmup_steps                = 100,
    learning_rate               = 2e-4,
    lr_scheduler_type           = "cosine",
    fp16                        = not torch.cuda.is_bf16_supported(),
    bf16                        = torch.cuda.is_bf16_supported(),
    optim                       = "adamw_8bit",
    weight_decay                = 0.01,
    logging_steps               = 50,
    eval_strategy               = "steps",
    eval_steps                  = 500,
    save_strategy               = "steps",
    save_steps                  = 500,
    save_total_limit            = 3,
    output_dir                  = output_dir,
    seed                        = 42,
)

trainer = SFTTrainer(
    model              = model,
    tokenizer          = tokenizer,
    train_dataset      = dataset["train"],
    eval_dataset       = dataset["test"],
    dataset_text_field = "text",
    max_seq_length     = MAX_SEQ_LENGTH,
    packing            = True,
    args               = training_args,
)

# Execute training
if PREV_RUN_CHECKPOINT:
    if os.path.exists(PREV_RUN_CHECKPOINT):
        print(f"Resuming training from checkpoint: {PREV_RUN_CHECKPOINT}")
        trainer.train(resume_from_checkpoint=PREV_RUN_CHECKPOINT)
    else:
        raise FileNotFoundError(f"Checkpoint not found at: {PREV_RUN_CHECKPOINT}. "
                                "Please check the path or ensure the previous run's dataset is mounted.")
else:
    print("Starting training from scratch...")
    trainer.train()
```

---

## 6. Output Adapter Export

At the end of each session, we explicitly save the trained LoRA adapter weights (which are small, ~100-300MB, compared to the 16-bit merged weights) so they can be exported easily and loaded for evaluation in Notebook C:

```python
output_path = f"/kaggle/working/spurgeon_lora_epoch{RUN_NUMBER}"

print(f"Saving PEFT LoRA adapter weights to {output_path}...")
model.save_pretrained(output_path)
tokenizer.save_pretrained(output_path)

print("Weights saved successfully. Notebook B execution completed.")
```

---

## 7. Operational Checklist for Training Run 1 & 2

### Session 1: Training Run 1 (Epoch 1)
1. Launch **Notebook B (`training.ipynb`)** on a T4 GPU. Toggle **Internet ON**.
2. Mount **`spurgeon-cpt-dataset`** as an Input Dataset.
3. In the code cell:
   * Set `RUN_NUMBER = 1`
   * Set `PREV_RUN_CHECKPOINT = None`
4. Run the notebook. At completion, it outputs `/kaggle/working/spurgeon_lora_epoch1` and `/kaggle/working/checkpoints/`.
5. Click **"Save Version"** -> **"Save & Run All (Commit)"**.
6. When the run finishes, create a private output dataset from the version viewer named **`spurgeon-training-run-1`**.

### Session 2: Training Run 2 (Epoch 2)
1. Open **Notebook B** in edit mode.
2. Under "Input", click "Add Input". Search for and mount **`spurgeon-training-run-1`**.
3. In the configuration cell:
   * Set `RUN_NUMBER = 2`
   * Set `PREV_RUN_CHECKPOINT = "/kaggle/input/datasets/rafaelvieira1/spurgeon-training-run-1/checkpoints/checkpoint-XXXX"` (pointing to the last checkpoint folder in the mounted Run 1 output, e.g. `checkpoint-1500`).
4. Run the notebook. SFTTrainer will load the weights and resume training from the exact step of epoch 1.
5. Click **"Save Version"** -> **"Save & Run All (Commit)"**.
6. Create a private output dataset from the viewer named **`spurgeon-training-run-2`** (containing `spurgeon_lora_epoch2`).
