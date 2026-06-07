# Phase 1: Spurgeon Continued Pretraining — Step 6: Dataset Preparation (Notebook A) Plan

This file documents the environment configs, directory layout, code cell implementations, and dataset verification steps for **Step 6: Dataset Preparation** of the continued pretraining pipeline.

This step runs in Kaggle **Notebook A (`data_prep.ipynb`)** to convert the cleaned plain-text files from Step 2 into Hugging Face `Dataset` binaries, create training/validation splits, and save the resulting directories so they can be mounted as inputs for training.

---

## 1. Kaggle Hardware & Environment Configuration

Since processing text and formatting datasets is a CPU-bound operation, we optimize resource utilization to avoid wasting precious GPU hours:

1. **Accelerator:** Select **None** (CPU-only). Hugging Face dataset processing operates entirely on the CPU. Setting the accelerator to CPU-only consumes 0 hours of your weekly GPU quota.
2. **Internet Access:** Toggle **ON** (active) in the Settings panel. This is required to install the Hugging Face `datasets` library from PyPI.
3. **Session Type:** Interactive (running cell-by-cell) is suitable since total execution time is under 3 minutes.

---

## 2. Directory Layout and File Paths

Kaggle mounts input datasets under `/kaggle/input/` and writes output artifacts to `/kaggle/working/`. The notebook must target these absolute paths:

| Path | Access Mode | Purpose / Contents |
| :--- | :--- | :--- |
| `/kaggle/input/datasets/rafaelvieira1/spurgeon-cpt-corpus/spurgeon_train.txt` | Read-Only | Cleaned training text file (~3,486 sermons, `<|endoftext|>` separated). |
| `/kaggle/input/datasets/rafaelvieira1/spurgeon-cpt-holdout/spurgeon_holdout.txt` | Read-Only | Cleaned holdout text file (50 sermons, `<|endoftext|>` separated). |
| `/kaggle/working/spurgeon_dataset/` | Read/Write | Output Hugging Face `DatasetDict` folder containing `train` and `test` (validation) splits. |
| `/kaggle/working/spurgeon_holdout_dataset/` | Read/Write | Output Hugging Face `Dataset` folder containing the holdout split for final perplexity evaluation. |

---

## 3. Python Code Cells for Notebook A (`data_prep.ipynb`)

Below are the exact code cells to be executed sequentially in **Notebook A**.

### Cell 1: Install Dependencies
Install the lightweight Hugging Face `datasets` library. We suppress verbose outputs to keep the log clean.
```python
# Cell 1: Environment Setup
!pip install datasets -q
```

### Cell 2: Import Libraries and Load Training Corpus
We load the raw training corpus file, split the text on the `<|endoftext|>` document boundary marker, filter out empty slices or short stubs under 200 characters, and convert the python list to a Hugging Face `Dataset`.
```python
# Cell 2: Load and Parse Training Corpus
import os
from pathlib import Path
from datasets import Dataset

train_corpus_path = "/kaggle/input/datasets/rafaelvieira1/spurgeon-cpt-corpus/spurgeon_train.txt"

if not os.path.exists(train_corpus_path):
    raise FileNotFoundError(f"Training corpus file not found at: {train_corpus_path}. "
                            "Please ensure the 'spurgeon-cpt-corpus' dataset is added to this notebook.")

print(f"Loading training corpus from {train_corpus_path}...")
with open(train_corpus_path, "r", encoding="utf-8") as f:
    train_text = f.read()

print(f"Corpus size: {len(train_text):,} characters.")

# Split into separate documents at sermon boundaries
raw_docs = train_text.split('<|endoftext|>')
# Filter out empty documents, trailing spaces, or stubs under 200 characters
train_docs = [doc.strip() for doc in raw_docs if len(doc.strip()) > 200]

print(f"Parsed {len(train_docs)} training documents (skipped {len(raw_docs) - len(train_docs)} short segments/stubs).")

# Instantiate Hugging Face Dataset
train_dataset = Dataset.from_dict({"text": train_docs})
print("Hugging Face Dataset successfully created:")
print(train_dataset)
```

### Cell 3: Create Train/Validation Splits
To monitor training loss and prevent overfitting, we split our training dataset into a **99% training set** and a **1% validation set**. We use a pinned seed for reproducibility.
```python
# Cell 3: Create Train-Validation Split
dataset_split = train_dataset.train_test_split(test_size=0.01, seed=42)

print("Split Results:")
print(f"  - Train split: {len(dataset_split['train'])} documents")
print(f"  - Validation split: {len(dataset_split['test'])} documents")
```

### Cell 4: Load and Format Holdout Corpus
We prepare the 50-sermon holdout dataset as a separate Hugging Face `Dataset`. This dataset will remain completely untouched during training and will only be used in Notebook C to calculate final perplexity.
```python
# Cell 4: Load and Parse Holdout Corpus
holdout_corpus_path = "/kaggle/input/datasets/rafaelvieira1/spurgeon-cpt-holdout/spurgeon_holdout.txt"

if not os.path.exists(holdout_corpus_path):
    raise FileNotFoundError(f"Holdout corpus file not found at: {holdout_corpus_path}. "
                            "Please ensure the 'spurgeon-cpt-holdout' dataset is added to this notebook.")

print(f"Loading holdout corpus from {holdout_corpus_path}...")
with open(holdout_corpus_path, "r", encoding="utf-8") as f:
    holdout_text = f.read()

print(f"Holdout corpus size: {len(holdout_text):,} characters.")

# Split into separate documents at sermon boundaries
raw_holdout_docs = holdout_text.split('<|endoftext|>')
holdout_docs = [doc.strip() for doc in raw_holdout_docs if len(doc.strip()) > 200]

print(f"Parsed {len(holdout_docs)} holdout documents (skipped {len(raw_holdout_docs) - len(holdout_docs)} segments).")

# Create holdout Hugging Face Dataset
holdout_dataset = Dataset.from_dict({"text": holdout_docs})
print(holdout_dataset)
```

### Cell 5: Save Datasets to Disk and Verify
Save the processed dataset directories to the Kaggle writable environment and verify the output paths.
```python
# Cell 5: Save Datasets to Writable Workspace
train_save_path = "/kaggle/working/spurgeon_dataset"
holdout_save_path = "/kaggle/working/spurgeon_holdout_dataset"

print(f"Saving training/validation dataset split to {train_save_path}...")
dataset_split.save_to_disk(train_save_path)

print(f"Saving holdout dataset to {holdout_save_path}...")
holdout_dataset.save_to_disk(holdout_save_path)

# Verify directory structures and file outputs on disk
print("\nVerifying files in /kaggle/working/:")
for root, dirs, files in os.walk("/kaggle/working/"):
    depth = root.replace("/kaggle/working/", "").count(os.sep)
    indent = "  " * depth
    print(f"{indent}[D] {os.path.basename(root) or 'working/'}")
    for file in files:
        file_path = os.path.join(root, file)
        size_kb = os.path.getsize(file_path) / 1024
        print(f"{indent}  - {file} ({size_kb:.2f} KB)")
        
print("\nDataset preparation completed successfully!")
```

---

## 4. Verification and Diagnostic Steps

Upon completing execution, check the following checklist in the notebook output cell:

1. **Document Counts Validation:**
   * **`dataset_split['train']`** must contain exactly **3,451 documents** (99% of 3,486).
   * **`dataset_split['test']`** must contain exactly **35 documents** (1% of 3,486).
   * **`holdout_dataset`** must contain exactly **50 documents**.
2. **Text Structure Inspection:**
   * Print a sample chunk using `print(dataset_split['train'][0]['text'][:300])`.
   * Verify that heading hashes (e.g. `#`, `##`) are stripped.
   * Verify that sermon numbers/publication info are absent from the start and end of the text.
3. **Directory Structure Verification:**
   * Ensure that `state.json`, `dataset_info.json`, and arrow-format shards (e.g., `data-00000-of-00001.arrow`) exist in both directories.

---

## 5. Kaggle Dataset Versioning and Export

To make these Hugging Face datasets available as inputs to Notebook B (`training.ipynb`) without needing to recreate them:

1. **Save Version:** Click on **"Save Version"** in the top-right menu of the Kaggle notebook editor.
2. **Select Run Type:** Select **"Save & Run All (Commit)"**. This runs the entire notebook from top to bottom on Kaggle's background servers.
3. **Wait for Completion:** Once the run completes successfully, click **"Open in Viewer"** on the completed run.
4. **Create Output Dataset:**
   * In the viewer, scroll to the **Output** section.
   * Click **"New Dataset"** or **"Create Dataset"** from the notebook output directory.
   * Name this dataset **`spurgeon-cpt-dataset`**.
   * Set the visibility to **Private**.
5. **Mount to Notebook B:**
   * In Notebook B (`training.ipynb`), click **"Add Input"** on the right sidebar.
   * Search for your private dataset **`spurgeon-cpt-dataset`** and mount it.
   * It will now be readable at: `/kaggle/input/spurgeon-cpt-dataset/spurgeon_dataset/` and `/kaggle/input/spurgeon-cpt-dataset/spurgeon_holdout_dataset/`.
