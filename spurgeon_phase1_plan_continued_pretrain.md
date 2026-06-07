# Phase 1: Spurgeon Continued Pretraining
## Complete Plan for Kaggle Free Tier (Unsloth / QLoRA)

---

## Overview

**Goal:** Produce a LoRA adapter on top of **Qwen2.5-3B** that internalizes
Spurgeon's theological register, prose cadence, and rhetorical structure.

**Constraint:** Kaggle free tier — Single T4 GPU (16GB) is highly recommended. (A single T4 easily fits Qwen2.5-3B in 4-bit, and using 1x T4 instead of 2x T4 consumes your weekly Kaggle quota hours at half the rate, effectively doubling your weekly training limit to 30 hours of real session time. Set your notebook accelerator setting to "1x T4 GPU").

**Estimated sessions needed:** 3–4 total (1 for data prep, 2–3 for training)

**Strategy:** QLoRA (4-bit quantized base model) + LoRA adapter via Unsloth on a single T4.
Full fine-tuning is out of reach on free Kaggle; this approach gets you 90%+ of the
quality at a fraction of the memory cost.

---

## Step 1 — Data Collection

### Source: Local Markdown Files

You already have the corpus locally. No scraping or downloading needed.

```
.\data\chspurgeon-sermons\
    volume-1\          ← sermon-1.md, sermon-2.md  (hyphen, no zero-padding)
        sermon-1.md
        sermon-2.md
        ...
    volume-2\          ← sermon_NNNN.md  (underscore, no zero-padding)
        sermon_51.md
        sermon_52.md
        ...
    volume-N\
        ...
```

> **Note:** Volume-1 uses hyphens (`sermon-1.md`); volumes 2–63 use underscores
> (`sermon_NNNN.md`). Both are found by `rglob("*.md")` — no special handling needed.

This is a significant advantage — your `.md` files are already structured,
likely cleaner than raw OCR dumps, and organized by volume. Step 1 becomes
an **audit and inventory** pass, not a collection pass.

---

### 1.1 — Inventory Your Corpus (run locally)

Before touching any data, understand exactly what you have:

```python
import os
from pathlib import Path

corpus_root = Path(r".\data\chspurgeon-sermons")

volumes = sorted([d for d in corpus_root.iterdir() if d.is_dir()])
total_files = 0
total_chars = 0

print(f"{'Volume':<20} {'Files':>6} {'Avg size':>10}")
print("-" * 40)

for vol in volumes:
    md_files = sorted(vol.glob("*.md"))
    chars = sum(len(f.read_text(encoding="utf-8", errors="replace")) for f in md_files)
    avg = chars // len(md_files) if md_files else 0
    total_files += len(md_files)
    total_chars += chars
    print(f"{vol.name:<20} {len(md_files):>6} {avg:>9} ch")

print("-" * 40)
print(f"{'TOTAL':<20} {total_files:>6} {total_chars:>9} ch")
print(f"\nEstimated size: {total_chars / 1e6:.1f} MB")
```

This tells you: how many sermons you have, whether volumes are complete,
and if any files are suspiciously short (stubs, title pages, corrupt files).

---

### 1.2 — Inspect the Markdown Structure

Open a few `.md` files from different volumes to understand the format.
You need to know what a typical file looks like before writing the cleaner.

```python
# Sample 5 random files and print first 60 lines of each
import random

all_files = list(corpus_root.rglob("*.md"))
random.seed(42)
samples = random.sample(all_files, 5)

for path in samples:
    print(f"\n{'='*60}")
    print(f"FILE: {path}")
    print('='*60)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[:60]:
        print(line)
```

**Look for and note:**

| Element | Example | Action in Step 2 |
|---|---|---|
| Frontmatter block | *Not present in this corpus* | Stripper is a no-op — harmless |
| Sermon title header | `# The Blood of the Lamb` | Keep as plain text |
| Subheadings | `## I. The Nature of Faith` | Keep or strip `##` markers |
| Markdown emphasis | `**salvation**`, `*beloved*` | Strip markers, keep words |
| Horizontal rules | `---`, `***` | Remove |
| Volume/number lines | `No. 1234` or `Volume X` | Remove |
| Footnote markers | `[^1]`, `^1` | Remove |
| Blockquotes | `> Thus says the Lord` | Strip `>`, keep text |
| Scripture references | `(John 3:16)` | Keep — valuable signal |

---

### 1.3 — Flag Short or Anomalous Files

Files under ~3,000 characters are likely incomplete sermons, front matter,
title pages, or index files. Identify them before training:

```python
short_files = []
large_files = []

for path in corpus_root.rglob("*.md"):
    size = len(path.read_text(encoding="utf-8", errors="replace"))
    if size < 3000:
        short_files.append((path, size))
    elif size > 80_000:  # likely a multi-sermon concatenation
        large_files.append((path, size))

short_files.sort(key=lambda x: x[1])
print(f"Found {len(short_files)} short files (< 3,000 chars — stubs/index pages):")
for path, size in short_files[:20]:
    print(f"  {size:>6} ch  {path}")

large_files.sort(key=lambda x: -x[1])
print(f"\nFound {len(large_files)} oversized files (> 80,000 chars — possible multi-sermon):")
for path, size in large_files:
    print(f"  {size:>8} ch  {path}")
```

Open each short anomaly and decide: discard, or is it a legitimate short piece?
Open each large file and check if it contains two sermons concatenated — if so,
you can split it or train on it as-is (it will still be valid text).

---

### 1.4 — Hold-out Split (do this now, before any cleaning)

Randomly select 50 sermons across all volumes as a held-out evaluation set.
Copy them to a separate folder. To preserve your original corpus files completely untouched, do NOT delete them from the source folder. The cleaning script in Step 2 will dynamically skip these hold-out files when building the training corpus.

```python
import shutil, random
from pathlib import Path

random.seed(42)
corpus_root = Path(r".\data\chspurgeon-sermons")
holdout_dir = Path(r".\data\chspurgeon-holdout")
holdout_dir.mkdir(exist_ok=True)

all_files = list(corpus_root.rglob("*.md"))
holdout = random.sample(all_files, 50)

for src in holdout:
    # Preserve volume subfolder in holdout dir
    rel = src.relative_to(corpus_root)
    dst = holdout_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    # Note: We do NOT run src.unlink() to keep the source files intact.

print(f"Copied {len(holdout)} sermons to holdout → {holdout_dir}")
print("Original source files remain completely untouched.")
```
---

### What you need at the end of Step 1

- Local audit complete: you know your exact sermon count and any anomalies
- 50 hold-out sermons moved to a separate folder (never seen during training)
- Notes on the markdown structure (frontmatter? headers? footnote style?)
  — these notes directly feed into the cleaning decisions in Step 2

---

## Step 2 — Data Cleaning & Preparation

Since your source files are already `.md`, cleaning is faster than raw OCR.
The work here is **stripping markdown syntax** while preserving all theological content.
Budget half a day rather than 1–2 days.

### What to remove (Markdown-specific)

```
Markdown syntax:
  - Header markers:         #, ##, ###  (keep the text, remove the symbol)
  - Emphasis markers:       **bold**, *italic*, __bold__, _italic_
  - Horizontal rules:       ---, ***, ___  on their own lines  (rare in this corpus)
  - Blockquote markers:     >  at line start (keep the text after it)
  - Footnote references:    [^1], [^note]  (rare in this corpus)
  - Footnote definitions:   [^1]: full text of note
  - Markdown links:         [text](url) → keep "text", drop url
  - HTML tags:              <br>, <p>, <em>, etc.
  - HTML entities:          &mdash; → — , &amp; → & , &lt;&gt; → <>
  - Windows line endings:   \r\n → \n

Content metadata (corpus-specific footers present in volumes 11–62):
  - Volume/sermon numbers:  "No. 2456", "Volume LI", "SERMON NO. 1234"
  - Publication lines:      "London: Passmore & Alabaster, 1890"
  - Hymn list footers:      "HYMNS FROM OUR OWN HYMN BOOK — 18, 536, 586."
  - Scripture list footers: "PORTIONS OF SCRIPTURE READ BEFORE SERMON — Luke 7:36"
  - Collection credit:      "Adapted from The C. H. Spurgeon Collection, Version 1.0"
  - Editorial line:         "PRAY THE HOLY SPIRIT WILL USE THIS SERMON..."
  - Excessive blank lines:  3 or more consecutive blank lines

Note: Frontmatter (--- ... ---) does NOT exist in this corpus.
Note: "EXPOSITION BY C. H. SPURGEON:" blocks are valuable commentary — keep them.
```

### What to keep

- Sermon title (as plain text, `#` marker stripped)
- Scripture text line — `Text: John 3:16` — keep it, it's valuable signal
- Subheading text — strip `##` but preserve `I. The Nature of Faith` etc.
- Complete sermon body — every word
- Scripture references like `(John 3:16)` inline in the body

> **On subheadings:** Spurgeon's Roman-numeral outline structure
> (`I.`, `II.`, `III.`) is part of his rhetoric. Keeping the text without
> the `##` markers preserves that structure naturally.

### Cleaning script (Markdown-aware)

Run this **locally** before uploading to Kaggle.

```python
import re
import html
from pathlib import Path


def clean_md_sermon(raw_text: str) -> str:
    # 1. Normalise Windows line endings first
    text = raw_text.replace('\r\n', '\n')

    # 2. Decode HTML entities (&mdash; → —, &amp; → &, &lt; → <, etc.)
    #    Must happen before HTML tag stripping so &lt;&gt; → <> → stripped
    text = html.unescape(text)

    # 3. Truncate footer metadata at the end of the file
    # We look at the last 25 lines of the file for the start of the footer
    # to avoid falsely matching keywords (like "alabaster") inside the sermon body.
    lines = text.splitlines()
    total_lines = len(lines)
    scan_start = max(0, total_lines - 25)
    truncate_idx = None

    footer_patterns = [
        re.compile(r"portion\s+of\s+scripture\s+read", re.I),
        re.compile(r"portions\s+of\s+scripture\s+read", re.I),
        re.compile(r"hymns\s+from", re.I),
        re.compile(r"pray\s+the\s+holy\s+spirit", re.I),
        re.compile(r"adapted\s+from\s+the\s+c\.\s*h\.\s*spurgeon\s+collection", re.I),
        re.compile(r"the\s+tongue\s+of\s+the\s+wicked\s+has\s+assailed", re.I),
        re.compile(r"passmore\s*&\s*alabaster", re.I),
        re.compile(r"published\s+by\s+passmore", re.I),
        re.compile(r"london:\s+passmore", re.I),
    ]

    for i in range(scan_start, total_lines):
        line = lines[i]
        matched = False
        for pattern in footer_patterns:
            if pattern.search(line):
                matched = True
                break
        if matched:
            truncate_idx = i
            break

    if truncate_idx is not None:
        lines = lines[:truncate_idx]
        text = '\n'.join(lines)

    # 4. Strip heading markers, keep text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # 5. Strip bold/italic emphasis markers
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.+?)_{1,3}', r'\1', text)

    # 6. Strip blockquote markers, keep text
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)

    # 7. Remove horizontal rules (rare in this corpus but harmless)
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 8. Remove markdown links — keep display text
    text = re.sub(r'\[(.+?)\]\(.*?\)', r'\1', text)

    # 9. Remove footnote references: [^1] or [^note]
    text = re.sub(r'\[\^[^\]]+\]', '', text)

    # 10. Remove footnote definitions: [^1]: ...
    text = re.sub(r'^\[\^[^\]]+\]:.*$', '', text, flags=re.MULTILINE)

    # 11. Remove remaining HTML tags (after unescape so <> from &lt;&gt; are gone)
    text = re.sub(r'<[^>]+>', '', text)

    # 12. Remove sermon/volume number lines
    text = re.sub(r'^(SERMON\s+)?NO\.\s*\d+\.?\s*$', '',
                  text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^Volume\s+[IVXLCDM\d]+\.?\s*$', '',
                  text, flags=re.MULTILINE | re.IGNORECASE)

    # 13. Collapse 3+ blank lines to one
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def build_corpus(corpus_root: str, output_file: str, holdout_dir: str = None):
    root = Path(corpus_root)
    holdout_path = Path(holdout_dir) if holdout_dir else None
    seen = set()
    written, skipped = 0, 0

    with open(output_file, 'w', encoding='utf-8') as out:
        for md_file in sorted(root.glob("*.md")) + sorted(root.glob("*/*.md")):
            # If holdout_dir is provided, check if this file is a holdout and skip it
            if holdout_path:
                rel = md_file.relative_to(root)
                if (holdout_path / rel).exists():
                    skipped += 1
                    continue

            raw = md_file.read_text(encoding='utf-8', errors='replace')

            # Dedup by first 300 chars of raw content
            fingerprint = raw[:300].strip()
            if fingerprint in seen:
                skipped += 1
                continue
            seen.add(fingerprint)

            cleaned = clean_md_sermon(raw)

            if len(cleaned) < 500:  # skip stubs and index files
                skipped += 1
                continue

            out.write(cleaned)
            out.write('\n<|endoftext|>\n\n')
            written += 1

    print(f"Written: {written} sermons | Skipped/deduped: {skipped}")


# Run locally before uploading to Kaggle
build_corpus(
    corpus_root = r".\data\chspurgeon-sermons",
    output_file = r".\data\spurgeon_train.txt",
    holdout_dir = r".\data\chspurgeon-holdout"
)

# Clean and build the holdout corpus as well
build_corpus(
    corpus_root = r".\data\chspurgeon-holdout",
    output_file = r".\data\spurgeon_holdout.txt"
)
```
```

### Verify before uploading

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B")
with open(r".\data\spurgeon_train.txt", encoding="utf-8") as f:
    text = f.read()

# Tokenize a sample — full corpus may be slow
sample = text[:500_000]
tokens = tokenizer(sample)["input_ids"]
estimated_total = int(len(tokens) * len(text) / len(sample))
print(f"Estimated total tokens: {estimated_total:,}")
# Expect ~24M–26M tokens
```

### Final corpus files

| File | Content | Sermons | Est. Tokens |
|---|---|---|---|
| `spurgeon_train.txt` | Cleaned + concatenated, `<\|endoftext\|>` separated | ~3,450+ | ~25M |
| `spurgeon_holdout.txt` | Same cleaning, never used in training | 50 | ~350K |

---

### 2.4 — Upload to Kaggle

Once both files have been built and verified locally, you upload them directly as Kaggle datasets:

1. **Upload the training corpus:**
   - Go to `kaggle.com/datasets` → New Dataset
   - Upload `spurgeon_train.txt`
   - Name the dataset **`spurgeon-cpt-corpus`**
   - Set visibility to **Private**

2. **Upload the holdout corpus:**
   - Go to `kaggle.com/datasets` → New Dataset
   - Upload `spurgeon_holdout.txt`
   - Name the dataset **`spurgeon-cpt-holdout`**
   - Set visibility to **Private**

Once uploaded, both files are available in your Kaggle Notebook as:
```
/kaggle/input/spurgeon-cpt-corpus/spurgeon_train.txt
/kaggle/input/spurgeon-cpt-holdout/spurgeon_holdout.txt
```

---

## Step 3 — Kaggle Notebook Structure

Split work across **three separate Kaggle notebooks** to stay within session limits
and keep concerns isolated.

```
Notebook A: data_prep.ipynb
  → Upload cleaned .txt files → build HuggingFace Dataset → save to Kaggle output

Notebook B: training.ipynb (run multiple times, resuming each session)
  → Load dataset → train one epoch per session → save checkpoints

Notebook C: eval_and_merge.ipynb
  → Load best checkpoint → evaluate on holdout → merge LoRA → export
```

### Checkpoint persistence across sessions

Kaggle saves up to 20GB of output at session end. The workflow is:

1. At end of Session 1: checkpoints are in `/kaggle/working/checkpoints/` → saved automatically
2. For Session 2: add the Session 1 output notebook as an **Input Dataset**
3. Resume training from `/kaggle/input/<your-output-dataset>/checkpoints/checkpoint-XXXX`

Alternatively, connect Google Drive via Kaggle Secrets for direct cloud persistence.

---

## Step 4 — Model Choice

**Model: `unsloth/Qwen2.5-3B`**

Qwen2.5-3B is the chosen model for this project. It is a dense, text-first
architecture with an official Unsloth CPT notebook, predictable loss curves,
and a strong track record for exactly this kind of domain adaptation.

| Property | Value |
|---|---|
| Model ID | `unsloth/Qwen2.5-3B` |
| Parameters | 3B (dense) |
| VRAM (QLoRA 4-bit) | ~6GB |
| T4 headroom | ~10GB free — very comfortable |
| Context window | 32K (we use 2048 for training efficiency) |
| Unsloth CPT notebook | ✅ Official |
| Initial loss baseline | 2–4 (clean, easy to monitor) |
| License | Apache 2.0 |

The 10GB of headroom on a single T4 GPU means you can safely run context length 2048
with batch size 2 and gradient accumulation 8, with room to increase context
to 4096 if needed without OOM risk. Furthermore, training on a single T4 GPU is simpler to launch (requires no multi-GPU distributed launch commands) and uses Kaggle quota at half the rate of 2x T4.

---

## Step 5 — Environment Setup (Notebook A & B header)

> [!IMPORTANT]
> **Kaggle Settings:** You MUST toggle **Internet ON** in the settings sidebar on the right of your Kaggle notebook before executing these commands. Otherwise, pip installation and model fetching will fail.

```python
# Install (run once per session)
!pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git"
```

> [!WARNING]
> Do NOT run generic upgrades like `!pip install --upgrade trl transformers` right after installing Unsloth. Doing so can overwrite the specific, patched library versions compatible with Unsloth's optimized kernels and cause runtime import or CUDA memory errors. Let the official Unsloth installer handle the dependency tree.

Unsloth's Kaggle-specific install handles bitsandbytes and Flash Attention automatically.

---

## Step 6 — Dataset Preparation (Notebook A)

> **Kaggle dataset names used throughout this plan:**
> - Training corpus → uploaded as **`spurgeon-cpt-corpus`**
>   available at `/kaggle/input/spurgeon-cpt-corpus/`
> - Hold-out corpus → uploaded as **`spurgeon-cpt-holdout`**
>   available at `/kaggle/input/spurgeon-cpt-holdout/`
> - Saved HuggingFace dataset → written to `/kaggle/working/spurgeon_dataset/`
>   and linked in the next session as **`spurgeon-cpt-dataset`**

```python
from datasets import Dataset

# Load your cleaned corpus
with open("/kaggle/input/spurgeon-cpt-corpus/spurgeon_train.txt", "r") as f:
    full_text = f.read()

# Split into chunks at document boundaries for cleaner dataset structure
# (packing=True will re-pack these into full context windows during training)
documents = full_text.split('<|endoftext|>')
documents = [d.strip() for d in documents if len(d.strip()) > 200]

dataset = Dataset.from_dict({"text": documents})
dataset = dataset.train_test_split(test_size=0.01, seed=42)  # tiny val split for loss monitoring

# Save
dataset.save_to_disk("/kaggle/working/spurgeon_dataset")
print(f"Train: {len(dataset['train'])} documents")
print(f"Val:   {len(dataset['test'])} documents")
```

---

## Step 7 — Training Configuration (Notebook B)

### Model + LoRA setup

```python
from unsloth import FastLanguageModel
import torch

MAX_SEQ_LENGTH = 2048
LORA_RANK = 32

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name   = "unsloth/Qwen2.5-3B",
    max_seq_length = MAX_SEQ_LENGTH,
    dtype        = None,
    load_in_4bit = True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r = LORA_RANK,
    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha  = 64,
    lora_dropout = 0,             # Critical: Set to 0 to enable Unsloth's optimized kernels
    bias        = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 42,
)
# Expect initial loss of 2–4, falling to 1.5–2.5 after training.
```

### Training arguments

```python
from trl import SFTTrainer, SFTConfig
from datasets import load_from_disk

dataset = load_from_disk("/kaggle/input/spurgeon-cpt-dataset/spurgeon_dataset")

training_args = SFTConfig(
    # Batch
    per_device_train_batch_size  = 2,
    gradient_accumulation_steps  = 8,   # Effective batch size = 16
    # Schedule
    num_train_epochs             = 1,   # 1 epoch per Kaggle session
    warmup_steps                 = 100,
    learning_rate                = 2e-4,
    lr_scheduler_type            = "cosine",
    # Precision
    fp16 = not torch.cuda.is_bf16_supported(),
    bf16 = torch.cuda.is_bf16_supported(),
    # Optimizer
    optim        = "adamw_8bit",
    weight_decay = 0.01,
    # Logging
    logging_steps          = 50,
    eval_strategy          = "steps",
    eval_steps             = 500,
    # Checkpointing
    save_strategy          = "steps",
    save_steps             = 500,
    save_total_limit       = 3,         # Keep last 3 checkpoints
    output_dir             = "/kaggle/working/checkpoints",
    # Reproducibility
    seed = 42,
    # SFT Parameters
    dataset_text_field     = "text",
    max_seq_length         = MAX_SEQ_LENGTH,
    packing                = True,      # Critical: fills context windows for efficiency
)

trainer = SFTTrainer(
    model             = model,
    tokenizer         = tokenizer,
    train_dataset     = dataset["train"],
    eval_dataset      = dataset["test"],
    args              = training_args,
)
```

### Run training

> [!IMPORTANT]
> **Resuming Training Bug:** When resuming training in subsequent sessions (Session 2, etc.), you MUST increase `num_train_epochs` in the `TrainingArguments` (e.g. change it to `2` for Run 2, `3` for Run 3). If `num_train_epochs` remains equal to the number of completed epochs in the checkpoint (e.g. `1`), the trainer will assume training has completed and immediately exit without training anything.

```python
# Fix potential PicklingError with SFTConfig in Unsloth/TRL on Kaggle
import sys
import trl
if hasattr(trainer, "args") and trainer.args.__class__.__name__ == "SFTConfig":
    import trl.trainer.sft_config
    trl.trainer.sft_config.SFTConfig = trainer.args.__class__
    sys.modules["trl.trainer.sft_config"].SFTConfig = trainer.args.__class__
    trl.SFTConfig = trainer.args.__class__

# First session: train from scratch
trainer.train()

# Subsequent sessions: resume from checkpoint (make sure to set num_train_epochs to 2 in config!)
# trainer.train(resume_from_checkpoint="/kaggle/input/prev-run/checkpoints/checkpoint-2000")
```

### Save the adapter after each session

```python
# Always save at the end of a session, even if mid-epoch
model.save_pretrained("/kaggle/working/spurgeon_lora_epoch1")
tokenizer.save_pretrained("/kaggle/working/spurgeon_lora_epoch1")
```

---

## Step 8 — Session Schedule

| Session | Action | Duration |
|---|---|---|
| Pre-work | Data collection + cleaning (local or in a notebook) | 1–2 days |
| Notebook A | Build and save HuggingFace Dataset | ~1–2h |
| Notebook B — Run 1 | Epoch 1 (train from scratch) | ~7–9h |
| Notebook B — Run 2 | Epoch 2 (resume from checkpoint) | ~7–9h |
| Notebook B — Run 3 | Epoch 3 (optional, watch for overfitting) | ~7–9h |
| Notebook C | Evaluate + merge + export | ~2–3h |

> **Tip:** Start each training session early in the day so you can monitor the first
> few hundred steps before stepping away. Loss should drop meaningfully in the first
> 200–300 steps. If it plateaus immediately, check your data format.

---

## Step 9 — Evaluating Training (Notebook C)

### Loss monitoring (during training)

Training loss should decrease across epochs. A rough guide:

| Loss | Meaning |
|---|---|
| > 3.0 | Model barely learning; check data pipeline |
| 2.0–3.0 | Learning in progress; normal early training |
| 1.5–2.0 | Good adaptation |
| < 1.5 | Strong domain fit (watch for overfitting on holdout) |

### Perplexity on holdout set

```python
from unsloth import FastLanguageModel
import torch, math

FastLanguageModel.for_inference(model)

with open("/kaggle/input/spurgeon-cpt-holdout/spurgeon_holdout.txt") as f:
    holdout_text = f.read()

inputs = tokenizer(holdout_text, return_tensors="pt", truncation=True, max_length=2048)
inputs = {k: v.to("cuda") for k, v in inputs.items()}

with torch.no_grad():
    outputs = model(**inputs, labels=inputs["input_ids"])

perplexity = math.exp(outputs.loss.item())
print(f"Holdout perplexity: {perplexity:.2f}")
# Lower is better. Compare to base model's perplexity on same text.
```

### Qualitative tests

Always do these manually — numbers don't catch style drift:

```
Prompt 1 (completion style):
"The love of Christ is not a cold, speculative thing. It is —"

Prompt 2 (sermon opening):
"Text: Romans 8:28. 'And we know that all things work together for good
to them that love God.' My dear friends, —"

Prompt 3 (doctrinal treatment):
"What, then, is saving faith? Let us examine this question carefully, for —"
```

Good output: Spurgeon's characteristic rhythm — short punchy sentences, direct
address ("my dear friends", "I say to you"), rhetorical questions, vivid
illustration, pastoral urgency.

Bad output: Generic theological English, loss of directness, meandering prose.

---

## Step 10 — Merge & Export (Notebook C)

Once you're satisfied with the adapter:

```python
# Option A: Merge LoRA into base model (larger file, self-contained)
model.save_pretrained_merged(
    "/kaggle/working/spurgeon_merged",
    tokenizer,
    save_method = "merged_16bit",   # Full precision merged weights
)

# Option B: Save LoRA adapter only (small: ~100–300MB, requires base model to run)
model.save_pretrained("/kaggle/working/spurgeon_lora_final")
tokenizer.save_pretrained("/kaggle/working/spurgeon_lora_final")

# Option C: Push to Hugging Face Hub (for Phase 2 reuse)
model.push_to_hub("your-username/spurgeon-lora-phase1")
tokenizer.push_to_hub("your-username/spurgeon-lora-phase1")
```

**Recommendation for this stage:** Save Option B (LoRA only). It's small enough to
version, share, and load on top of the same base model in Phase 2 when you add Puritan texts.

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| OOM on T4 | Reduce batch size to 1, reduce context to 1024, or switch to 2B model |
| Session times out mid-epoch | Save every 250 steps instead of 500 |
| Loss not decreasing | Check `<\|endoftext\|>` separator is correct for your tokenizer; verify data loaded correctly |
| Overfitting on small corpus | Stop at 2 epochs; increase dropout to 0.1 |
| Checkpoints lost between sessions | Always download or link output before closing session |
| Poor qualitative style | Verify data cleaning — OCR artifacts destroy style signal (e.g. use footer truncation instead of broad search-and-replace keywords) |
| Trainer exits immediately on resume | Increase `num_train_epochs` to a higher number (e.g. `2` for Session 2) before calling `trainer.train(resume_from_checkpoint=...)` |
| Slower training speed | Ensure `lora_dropout` is set to `0` to enable Unsloth's optimized custom Triton kernels |
| Pip install fails / Cannot download model | Ensure the **Internet ON** toggle is enabled in the Kaggle notebook settings sidebar |

---

## What Success Looks Like

Phase 1 is complete when:

1. Training loss is stable and decreasing across 2 epochs
2. Holdout perplexity is measurably lower than base model perplexity on the same text
3. Qualitative completions have Spurgeon's sentence rhythm, pastoral directness,
   and characteristic vocabulary ("dear friends", "beloved", "I beseech you",
   vivid metaphors, doctrinal precision)
4. LoRA adapter is saved and versioned, ready for Phase 2

---

## Project Folder Structure

All continued-pretraining work lives under a dedicated `continued_pretrain/` folder,
kept separate from the instruction fine-tuning pipeline in `fine_tuning/`.

```
continued_pretrain/
├── README.md
├── scripts/
│   ├── 01_inventory.py          # Step 1.1 — count/audit corpus
│   ├── 02_inspect_samples.py    # Step 1.2 — sample random files
│   ├── 03_flag_anomalies.py     # Step 1.3 — short + large file detection
│   ├── 04_holdout_split.py      # Step 1.4 — create holdout set
│   └── 05_build_corpus.py       # Step 2  — clean + concat to .txt
├── notebooks/
│   ├── A_data_prep.ipynb        # Notebook A (Kaggle)
│   ├── B_training.ipynb         # Notebook B (Kaggle, run multiple times)
│   └── C_eval_and_merge.ipynb   # Notebook C (Kaggle)
├── configs/
│   └── train_config_cpt_qwen25.json
└── data/
    └── .gitkeep
```

### `.gitignore` additions required

The project `.gitignore` currently excludes `data/` and `*.ipynb` globally.
Add these exceptions so the new folder is tracked correctly:

```gitignore
# Allow continued_pretrain notebooks, scripts and configs
!continued_pretrain/
!continued_pretrain/**
!continued_pretrain/notebooks/*.ipynb
# But still exclude large generated corpus files
continued_pretrain/data/*.txt
continued_pretrain/data/*.bin
```

---

*Phase 2 will continue from this adapter, adding curated Puritan texts
(Sibbes, Watson, Owen, Bunyan, Brooks — estimated 30–50M curated tokens)
with Spurgeon oversampled 2–3× to preserve primary voice.*
