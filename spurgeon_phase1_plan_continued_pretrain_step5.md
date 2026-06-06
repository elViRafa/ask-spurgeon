# Phase 1: Spurgeon Continued Pretraining — Step 5: Environment Setup & Configurations

This file documents the dependencies, hardware switches, package installation rules, and authentication configurations required for **Step 5: Environment Setup** of the pretraining pipeline.

---

## 1. Kaggle Hardware & Session Constraints

Kaggle environment settings must be configured correctly in the right-hand panel before executing notebook cells:

1. **Accelerator Configuration:**
   - **Notebook A (Data Prep):** Select **None** (CPU-only). GPU resources are billed per hour; processing text datasets does not benefit from GPU acceleration, saving weekly quota hours.
   - **Notebook B (Training):** Select **1x T4 GPU** (16 GB VRAM).
   - **Notebook C (Evaluation):** Select **1x T4 GPU** (16 GB VRAM).
2. **Internet Access:**
   - **MUST be toggled ON** (active) for all sessions. By default, Kaggle notebooks disable external internet. Toggling it ON is required to fetch python packages from PyPI, install Unsloth from GitHub, and download base model weights from the Hugging Face Hub.
3. **Session Lifetimes:**
   - Interactive sessions automatically terminate after 9 hours (GPU) or 12 hours (CPU), or after 1 hour of user inactivity.
   - Background runs (using "Save Version" -> "Save & Run All") run up to 9 hours uninterrupted and are unaffected by browser disconnection.

---

## 2. Package Management and Installation Rules

Kaggle resets the python virtual environment whenever a session restarts. Therefore, package installation commands must be executed at the top of the notebook in every session.

### 2.1 — Pinned Installation Commands
```python
# Cell 1 in Notebook B and C
!pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git"
```

### 2.2 — CRITICAL: No Manual Dependency Upgrades
> [!WARNING]
> Do NOT execute manual upgrades of primary libraries, such as:
> `!pip install --upgrade transformers trl peft bitsandbytes`
> 
> **Why:** Unsloth depends on specific, pinned, and source-patched versions of these libraries to perform its custom memory-efficient Triton kernel operations. Upgrading them pulls PyPI versions that lack these patches, causing:
> 1. Failure to load compiled CUDA kernels, resulting in slow training speeds.
> 2. VRAM allocation overflows (OOM) due to unpatched memory leakages in standard PEFT classes.
> 3. Import errors due to deprecated signatures in the latest library releases.

### 2.3 — Optimized Compilation Helpers
The Kaggle Unsloth target (`unsloth[kaggle-new]`) automatically handles the setup of:
* **Flash Attention-2:** Speeds up attention computation by 2-4x and reduces activation memory quadratically.
* **8-bit bitsandbytes Optimizer:** Allocates model parameters in 4-bit while maintaining optimization states in 8-bit.

---

## 3. Directory Layout and File Paths

Kaggle mounts file systems in predictable directory structures. All scripts and notebooks must target these absolute paths:

| Path | Mode | Purpose |
| :--- | :--- | :--- |
| `/kaggle/working/` | Read/Write | Active workspace. Checkpoints, temporary datasets, and exported adapters are written here. Max storage capacity is 20 GB. |
| `/kaggle/input/` | Read-Only | Mounted input datasets. Contains uploaded corpora and checkpoints from previous sessions. |
| `/kaggle/input/spurgeon-cpt-corpus/` | Read-Only | Uploaded sermon training text `spurgeon_train.txt`. |
| `/kaggle/input/spurgeon-cpt-holdout/` | Read-Only | Uploaded holdout sermon text `spurgeon_holdout.txt`. |
| `/kaggle/input/spurgeon-cpt-dataset/` | Read-Only | Hugging Face dataset directories output from Notebook A. |

---

## 4. Hugging Face Authentication & Secrets

To download base models and programmatically upload trained adapters or weights to the Hugging Face Hub, notebooks must authenticate without interactive terminal prompting.

### 4.1 — Registering Kaggle Secrets
1. In the Kaggle notebook interface, navigate to the top menu: **Add-ons** -> **Secrets**.
2. Add a new secret:
   - **Label:** `HF_TOKEN`
   - **Value:** *[Your Hugging Face Write Token]*
3. Enable the checkbox to permit the notebook to access this secret.

### 4.2 — Programmatic Authentication Code
```python
import os
from kaggle_secrets import UserSecretsClient

try:
    user_secrets = UserSecretsClient()
    hf_token = user_secrets.get_secret("HF_TOKEN")
    
    # Set HF token environment variable for Hugging Face Hub APIs
    os.environ["HF_TOKEN"] = hf_token
    
    # Programmatic login
    from huggingface_hub import login
    login(token=hf_token, write=True)
    print("Hugging Face Hub successfully authenticated.")
except Exception as e:
    print(f"Hugging Face Secret not found or authentication failed: {e}")
    print("Continuing in offline/public access mode.")
```

---

## 5. Weights & Biases (W&B) Logging (Optional)

To track loss curves, GPU usage, and learning rate schedules dynamically across training epochs, configure W&B:

### 5.1 — Secrets Registration
Add another Kaggle Secret:
* **Label:** `WANDB_API_KEY`
* **Value:** *[Your W&B API Key]*

### 5.2 — Initialization Code
```python
try:
    wandb_key = user_secrets.get_secret("WANDB_API_KEY")
    os.environ["WANDB_API_KEY"] = wandb_key
    os.environ["WANDB_PROJECT"] = "spurgeon-continued-pretraining"
    os.environ["WANDB_LOG_MODEL"] = "false" # Prevent raw adapter uploading to wandb
    print("W&B tracking initialized.")
except Exception as e:
    os.environ["WANDB_DISABLED"] = "true"
    print("W&B Key not found. Training logs will fall back to stdout logging.")
```
