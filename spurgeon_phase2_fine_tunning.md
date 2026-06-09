# Phase 2: Instruction Fine-Tuning for QA + RAG
## Building a Spurgeon Q&A System on the Phase 1 Adapter

---

## Overview

**Goal:** Produce a LoRA adapter that turns the Phase 1 domain-adapted model into
an instruction-following Q&A system grounded in Spurgeon's sermons, paired with a
FAISS-backed RAG pipeline that retrieves relevant sermon passages before generation.

**Input:** Phase 1 LoRA adapter (`spurgeon_lora_phase1`) + base `unsloth/Qwen2.5-3B`

**Output:**
- Phase 2 LoRA adapter (`spurgeon_lora_qa`) — instruction-tuned for Q&A
- FAISS vector index of all ~3,500 sermons (`spurgeon_faiss.index`)
- A retriever + generator pipeline ready to serve queries

**Strategy:**
1. **Merge** Phase 1 LoRA into the base model → clean starting point for Phase 2
2. **Generate** synthetic QA pairs from the sermon corpus (locally, via Claude API)
3. **Fine-tune** a new LoRA for instruction following using SFTTrainer
4. **Build** a FAISS retrieval index from the same corpus
5. **Wire** retriever → fine-tuned model → answer

**Constraint:** Same Kaggle free tier — single T4. The fine-tuning load is
lighter than Phase 1 (smaller dataset, fewer epochs), so this fits comfortably.

---

## Architecture Diagram

```
User Query
    │
    ▼
┌──────────────────────────────────────┐
│  FAISS Retrieval (runs locally/CPU)  │
│  - Embed query with BGE-small        │
│  - Top-K sermon chunks retrieved     │
└──────────────────┬───────────────────┘
                   │  retrieved context (top 3–5 chunks)
                   ▼
┌──────────────────────────────────────┐
│  Prompt Assembly                     │
│  system + context + user question    │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Qwen2.5-3B                          │
│  + Phase 1 LoRA (domain style)       │
│  + Phase 2 LoRA (instruction/QA)     │
└──────────────────┬───────────────────┘
                   │
                   ▼
              Answer in Spurgeon's voice
```

---

## Two Sub-Tracks Running in Parallel

| Track | What it does | Where it runs |
|---|---|---|
| **2A — QA Fine-tuning** | Teaches the model to follow Q&A instructions | Kaggle (T4) |
| **2B — RAG Pipeline** | Retrieval index + query engine | Locally (CPU) or Kaggle |

Both use the same corpus. Track 2B does not require GPU — you can build the
FAISS index on a laptop while Track 2A trains on Kaggle.

---

## Track 2A — QA Fine-Tuning

---

### Step 1 — Synthetic QA Dataset Generation (run locally)

We generate the instruction-tuning dataset programmatically by feeding overlapping sermon chunks to a teacher model (e.g., Groq `llama-3.3-70b-versatile` or `llama-3.1-8b-instant` fallback) and asking it to write 1-2 realistic, specific Q&A pairs directly from the text. 

To teach the model to be honest without making it lazy, we also intentionally inject a controlled ratio of unanswerable questions (around 7% of the dataset) by pairing sermon chunks with mismatched queries and prompting the teacher LLM to generate a polite refusal in Spurgeon's pastoral voice.

This consolidated pipeline is implemented in the single script `fine_tuning/scripts/generate_qa_pairs.py`.

#### 1.1 — Generation Script (`generate_qa_pairs.py`)

Run this script locally to chunk the sermon markdown files, generate the Q&A pairs, and output a formatted dataset:

```bash
python fine_tuning/scripts/generate_qa_pairs.py --limit 1000 --output fine_tuning/data/spurgeon_train_1500.jsonl
```

The script performs the following steps:
1. Scans `data/chspurgeon-sermons` for sermon files, filtering out any files in `data/chspurgeon-holdout` to preserve evaluation integrity.
2. Cleans raw markdown and chunks the sermons into overlapping segments of ~1200 characters.
3. For ~93% of the samples, it calls the teacher LLM with a prompt instructing it to write natural, specific Q&A pairs grounded 100% in the chunk, adopting Spurgeon's warm, pastoral, 19th-century theological register.
4. For ~7% of the samples, it pairs the chunk with an out-of-scope query (e.g., about Charles Darwin's evolution theory or modern technology) and calls the LLM to write a grounded refusal in Spurgeon's voice (e.g., *"I see no mention of this in the text..."*).
5. Formats the outputs directly into ChatML format (compatible with Qwen2.5 / Unsloth) and writes them to a JSONL dataset.

---

### Step 2 — Upload to Kaggle

| File | Kaggle Dataset Name | Path |
|---|---|---|
| `qa_train.jsonl` | `spurgeon-qa-train` | `/kaggle/input/spurgeon-qa-train/qa_train.jsonl` |
| `qa_val.jsonl` | `spurgeon-qa-val` | `/kaggle/input/spurgeon-qa-val/qa_val.jsonl` |
| Phase 1 merged model | `spurgeon-phase1-merged` | `/kaggle/input/spurgeon-phase1-merged/` |

> **On using the Phase 1 adapter:** Before running Phase 2 training, merge the
> Phase 1 LoRA into the base model using Notebook C from Phase 1:
> ```python
> model.save_pretrained_merged(
>     "/kaggle/working/spurgeon_phase1_merged",
>     tokenizer,
>     save_method = "merged_16bit",
> )
> ```
> Then upload the merged model folder as the `spurgeon-phase1-merged` dataset.
> This avoids stacking two LoRAs, which complicates inference and checkpointing.

---

### Step 3 — Notebook Structure (Phase 2)

```
Notebook D: qa_data_prep.ipynb
  → Load JSONL files → build HuggingFace Dataset → apply ChatML template → save

Notebook E: qa_training.ipynb
  → Load Phase 1 merged model → new LoRA → instruction fine-tune → save adapter

Notebook F: qa_eval.ipynb
  → Load adapter → run qualitative tests + holdout perplexity → export
```

---

### Step 4 — QA Dataset Preparation (Notebook D)

```python
from datasets import Dataset
import json

def load_jsonl(path):
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records

train_records = load_jsonl("/kaggle/input/spurgeon-qa-train/qa_train.jsonl")
val_records   = load_jsonl("/kaggle/input/spurgeon-qa-val/qa_val.jsonl")

train_ds = Dataset.from_list(train_records)
val_ds   = Dataset.from_list(val_records)

# Apply Qwen2.5 ChatML template using the tokenizer
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = "/kaggle/input/spurgeon-phase1-merged",
    max_seq_length = 2048,
    dtype          = None,
    load_in_4bit   = True,
)

def format_chatML(example):
    """Convert conversations list to a single formatted string."""
    messages = example["conversations"]
    return {"text": tokenizer.apply_chat_template(
        messages,
        tokenize           = False,
        add_generation_prompt = False,
    )}

train_ds = train_ds.map(format_chatML)
val_ds   = val_ds.map(format_chatML)

train_ds.save_to_disk("/kaggle/working/qa_dataset_train")
val_ds.save_to_disk("/kaggle/working/qa_dataset_val")

print(f"Train: {len(train_ds):,} | Val: {len(val_ds):,}")
# Inspect a sample
print(train_ds[0]["text"][:800])
```

---

### Step 5 — QA Fine-Tuning Configuration (Notebook E)

Phase 2 is a lighter training run than Phase 1 — the dataset is smaller (~7K pairs)
and 2 epochs is sufficient. Total training time: **2–4 hours** on a single T4.

#### Model + LoRA setup

```python
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch

MAX_SEQ_LENGTH = 2048
LORA_RANK      = 16   # Smaller rank than Phase 1: QA adapter is an instruction layer, not deep domain shift

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = "/kaggle/input/spurgeon-phase1-merged",
    max_seq_length = MAX_SEQ_LENGTH,
    dtype          = None,
    load_in_4bit   = True,
)

# Apply the correct chat template for Qwen2.5
tokenizer = get_chat_template(tokenizer, chat_template="qwen-2.5")

model = FastLanguageModel.get_peft_model(
    model,
    r                          = LORA_RANK,
    target_modules             = ["q_proj", "k_proj", "v_proj", "o_proj",
                                  "gate_proj", "up_proj", "down_proj"],
    lora_alpha                 = 32,
    lora_dropout               = 0,
    bias                       = "none",
    use_gradient_checkpointing = "unsloth",
    random_state               = 42,
)
```

#### Training arguments

```python
from trl import SFTTrainer, SFTConfig
from datasets import load_from_disk

train_ds = load_from_disk("/kaggle/working/qa_dataset_train")
val_ds   = load_from_disk("/kaggle/working/qa_dataset_val")

training_args = SFTConfig(
    # Batch — QA pairs are short; we can afford a larger effective batch
    per_device_train_batch_size  = 4,
    gradient_accumulation_steps  = 4,    # Effective batch size = 16
    # Schedule
    num_train_epochs             = 3,    # 3 epochs on ~7K pairs is sufficient
    warmup_steps                 = 50,
    learning_rate                = 1e-4, # Lower than Phase 1 — fine-tuning, not pretraining
    lr_scheduler_type            = "cosine",
    # Precision
    fp16 = not torch.cuda.is_bf16_supported(),
    bf16 = torch.cuda.is_bf16_supported(),
    # Optimizer
    optim        = "adamw_8bit",
    weight_decay = 0.01,
    # Logging
    logging_steps          = 25,
    eval_strategy          = "steps",
    eval_steps             = 200,
    # Checkpointing
    save_strategy          = "steps",
    save_steps             = 200,
    save_total_limit       = 3,
    output_dir             = "/kaggle/working/qa_checkpoints",
    # SFT Parameters
    dataset_text_field     = "text",
    max_seq_length         = MAX_SEQ_LENGTH,
    packing                = False,   # OFF for QA: each pair is one clean training example
    seed                   = 42,
)

trainer = SFTTrainer(
    model         = model,
    tokenizer     = tokenizer,
    train_dataset = train_ds,
    eval_dataset  = val_ds,
    args          = training_args,
)

trainer.train()

model.save_pretrained("/kaggle/working/spurgeon_lora_qa")
tokenizer.save_pretrained("/kaggle/working/spurgeon_lora_qa")
```

> **Key difference from Phase 1:** `packing=False`. In Phase 1 (pretraining),
> you want every token to count, so packing fills context windows fully.
> In Phase 2 (instruction tuning), each QA pair must be one clean example with
> its own system prompt — packing would corrupt pair boundaries.

#### Expected loss trajectory

| Stage | Expected Loss |
|---|---|
| Start of Epoch 1 | 1.8–2.5 (inheriting Phase 1 domain knowledge) |
| End of Epoch 1 | 1.2–1.6 |
| End of Epoch 2 | 0.9–1.3 |
| End of Epoch 3 | 0.7–1.1 |

If loss is below 0.6 by Epoch 3, you are likely overfitting — stop early.

---

### Step 6 — QA Evaluation (Notebook F)

#### Automated: validation loss curve

The val loss plotted every 200 steps is your primary quantitative signal.
It should decrease across all 3 epochs with no uptick.

#### Qualitative test battery

These 6 prompts cover all five QA types. Run them after Epoch 2 and Epoch 3
and compare the outputs side by side:

```python
from unsloth import FastLanguageModel

FastLanguageModel.for_inference(model)

test_prompts = [
    # Doctrinal
    "What is Charles Spurgeon's understanding of the doctrine of election?",
    # Expository
    "How does Spurgeon interpret the phrase 'Come unto me, all ye that labour' in Matthew 11:28?",
    # Applicational
    "What counsel does Spurgeon give to a Christian who feels God is distant?",
    # Passage-based (paste an actual Spurgeon excerpt as context)
    "Based on this passage: 'The blood is the life of the covenant...'\nWhat theological point is Spurgeon making here?",
    # Biographical
    "How did Spurgeon describe the moment of his own conversion?",
    # Edge case — out of scope (should be honest, not hallucinate)
    "What did Spurgeon think about Charles Darwin's theory of evolution?",
]

messages_template = [
    {"role": "system",    "content": "You are a scholar of Charles Spurgeon's sermons. Answer questions accurately and faithfully based on Spurgeon's preaching, theology, and pastoral teaching."},
    {"role": "user",      "content": ""},  # filled per prompt
]

for prompt in test_prompts:
    messages = messages_template.copy()
    messages[1] = {"role": "user", "content": prompt}

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize              = True,
        add_generation_prompt = True,
        return_tensors        = "pt",
    ).to("cuda")

    with torch.no_grad():
        output = model.generate(
            inputs,
            max_new_tokens  = 300,
            temperature     = 0.3,
            top_p           = 0.9,
            repetition_penalty = 1.1,
        )

    decoded = tokenizer.decode(output[0][inputs.shape[-1]:], skip_special_tokens=True)
    print(f"\n{'='*60}")
    print(f"Q: {prompt}")
    print(f"A: {decoded}")
```

**What to look for:**
- Answers are grounded — no fabricated sermon titles or scripture references
- Tone is warm and scholarly, not generic chatbot English
- Spurgeon's vocabulary surfaces in the answers ("sovereign grace", "the precious blood", etc.)
- The edge case (Darwin) is answered cautiously, acknowledging limited evidence

---

## Track 2B — RAG Pipeline

Track 2B is entirely CPU-based and can run locally. No Kaggle GPU needed.

---

### Step 1 — Chunking for Retrieval

Retrieval chunks must be smaller than QA training chunks — they need to be
semantically self-contained so the embedding model can represent them accurately.

```python
# scripts/10_build_retrieval_chunks.py
import json
from pathlib import Path

corpus_root = Path(r".\data\chspurgeon-sermons")
output_file = Path(r".\data\retrieval_chunks.jsonl")

CHUNK_SIZE = 600    # characters — ~150 tokens: dense enough for FAISS but retrievable
CHUNK_STEP = 300    # 50% overlap

chunks = []
for md_file in sorted(corpus_root.rglob("*.md")):
    raw = md_file.read_text(encoding="utf-8", errors="replace")
    if len(raw) < 1000:
        continue

    # Extract volume + sermon ID from path
    parts  = md_file.parts
    volume = parts[-2] if len(parts) >= 2 else "unknown"
    stem   = md_file.stem

    # Clean inline (reuse your clean_md_sermon function from Phase 1)
    from build_corpus import clean_md_sermon
    text = clean_md_sermon(raw)

    for i, start in enumerate(range(0, len(text) - 100, CHUNK_STEP)):
        chunk = text[start : start + CHUNK_SIZE].strip()
        if len(chunk) < 100:
            continue
        chunks.append({
            "id":      f"{volume}/{stem}/chunk{i}",
            "source":  str(md_file),
            "volume":  volume,
            "sermon":  stem,
            "text":    chunk,
        })

with open(output_file, "w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"Total retrieval chunks: {len(chunks):,}")
# Expect ~200,000–300,000 chunks for the full corpus
```

---

### Step 2 — Build FAISS Index (run locally)

```bash
pip install faiss-cpu sentence-transformers
```

```python
# scripts/11_build_faiss_index.py
import json, faiss, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

CHUNKS_FILE   = Path(r".\data\retrieval_chunks.jsonl")
INDEX_FILE    = Path(r".\data\spurgeon_faiss.index")
META_FILE     = Path(r".\data\spurgeon_faiss_meta.jsonl")
EMBED_MODEL   = "BAAI/bge-small-en-v1.5"   # 33M params, fast on CPU, strong retrieval
BATCH_SIZE    = 512

# Load chunks
chunks = []
with open(CHUNKS_FILE, encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))
texts = [c["text"] for c in chunks]
print(f"Indexing {len(texts):,} chunks...")

# Embed
model = SentenceTransformer(EMBED_MODEL)
embeddings = model.encode(
    texts,
    batch_size         = BATCH_SIZE,
    show_progress_bar  = True,
    normalize_embeddings = True,   # Required for cosine similarity via inner product
)
embeddings = np.array(embeddings, dtype="float32")
print(f"Embeddings shape: {embeddings.shape}")

# Build FAISS index (Inner Product = cosine similarity when embeddings are L2-normalized)
dim   = embeddings.shape[1]   # 384 for bge-small
index = faiss.IndexFlatIP(dim)
index.add(embeddings)
faiss.write_index(index, str(INDEX_FILE))

# Save metadata separately (FAISS stores only vectors, not text)
with open(META_FILE, "w", encoding="utf-8") as f:
    for c in chunks:
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"Index saved: {INDEX_FILE} ({INDEX_FILE.stat().st_size / 1e6:.1f} MB)")
print(f"Meta saved:  {META_FILE}")
# Index file: ~200–500MB depending on corpus size
```

---

### Step 3 — RAG Query Pipeline

This is the final assembly: retriever + prompt builder + fine-tuned model.

```python
# rag_pipeline.py
import json, faiss, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch

# ─── Load retrieval components ───────────────────────────────────────────────

INDEX_FILE  = Path(r".\data\spurgeon_faiss.index")
META_FILE   = Path(r".\data\spurgeon_faiss_meta.jsonl")
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

index = faiss.read_index(str(INDEX_FILE))
meta  = []
with open(META_FILE, encoding="utf-8") as f:
    for line in f:
        meta.append(json.loads(line))

embedder = SentenceTransformer(EMBED_MODEL)

# ─── Load generation model ───────────────────────────────────────────────────

BASE_MODEL = "unsloth/Qwen2.5-3B"
PHASE1_MERGED = r".\models\spurgeon_phase1_merged"   # or use base + phase1 LoRA
PHASE2_LORA   = r".\models\spurgeon_lora_qa"

tokenizer = AutoTokenizer.from_pretrained(PHASE2_LORA)
base      = AutoModelForCausalLM.from_pretrained(
    PHASE1_MERGED,
    torch_dtype    = torch.float16,
    device_map     = "auto",
)
model = PeftModel.from_pretrained(base, PHASE2_LORA)
model.eval()

# ─── Retrieval function ───────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = 4) -> list[dict]:
    emb = embedder.encode(
        [query],
        normalize_embeddings = True,
    ).astype("float32")
    scores, indices = index.search(emb, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append({**meta[idx], "score": float(score)})
    return results

# ─── Prompt builder ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a scholar of Charles Spurgeon's sermons. "
    "Answer questions accurately and faithfully based on Spurgeon's preaching, "
    "theology, and pastoral teaching. "
    "Use the provided sermon excerpts to ground your answer. "
    "Cite the sermon source (volume and sermon name) when referencing a passage."
)

def build_rag_prompt(query: str, chunks: list[dict]) -> list[dict]:
    context_block = "\n\n---\n\n".join(
        f"[Source: {c['volume']} / {c['sermon']}]\n{c['text']}"
        for c in chunks
    )
    user_message = (
        f"Sermon excerpts for context:\n\n{context_block}\n\n"
        f"Question: {query}"
    )
    return [
        {"role": "system",    "content": SYSTEM_PROMPT},
        {"role": "user",      "content": user_message},
    ]

# ─── Full RAG answer function ─────────────────────────────────────────────────

def answer(query: str, top_k: int = 4, max_new_tokens: int = 400) -> str:
    chunks = retrieve(query, top_k=top_k)
    messages = build_rag_prompt(query, chunks)

    input_ids = tokenizer.apply_chat_template(
        messages,
        tokenize              = True,
        add_generation_prompt = True,
        return_tensors        = "pt",
    ).to(model.device)

    with torch.no_grad():
        output = model.generate(
            input_ids,
            max_new_tokens     = max_new_tokens,
            temperature        = 0.3,
            top_p              = 0.9,
            repetition_penalty = 1.15,
            do_sample          = True,
        )

    new_tokens = output[0][input_ids.shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)

# ─── Example usage ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    q = "What does Spurgeon teach about the perseverance of the saints?"
    print(f"Q: {q}\n")
    print(f"A: {answer(q)}")
```

---

### Step 4 — RAG Evaluation

RAG quality is evaluated on three dimensions:

#### 4.1 — Retrieval quality (offline)

```python
# Spot-check: for known questions, did the retriever surface the right sermon?
test_pairs = [
    ("What does Spurgeon say about the Blood of Christ?",         "blood"),
    ("How does Spurgeon describe the new birth?",                  "regeneration"),
    ("What is Spurgeon's view on the Lord's Supper?",             "supper"),
]

for query, keyword in test_pairs:
    results = retrieve(query, top_k=4)
    hits = sum(1 for r in results if keyword in r["text"].lower())
    print(f"Query: {query[:50]}")
    print(f"  Top-4 hits containing '{keyword}': {hits}/4")
    for r in results:
        print(f"  [{r['score']:.3f}] {r['volume']}/{r['sermon']}")
    print()
```

#### 4.2 — End-to-end faithfulness (manual)

For 20–30 held-out questions:
- Run `answer()` and record the output
- Open the cited sermon and verify the answer is grounded in it
- Flag: fabricated citations, wrong doctrine attribution, or generic non-answers

#### 4.3 — Groundedness vs. parametric split

Run the same questions with and without RAG:

```python
def answer_no_rag(query, max_new_tokens=400):
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "user",    "content": query},
    ]
    # identical generation, no context injected
    ...
```

Good results: RAG answers are more specific, cite real sermons, avoid vague
generalities that the parametric model alone would produce.

---

## Step-by-Step Session Schedule

| Session | Track | Action | Duration |
|---|---|---|---|
| Local pre-work | 2A | Chunk + generate QA pairs via Claude API | 2–4h |
| Local pre-work | 2A | Filter, format, upload to Kaggle | 1h |
| Local pre-work | 2B | Build FAISS index | 1–2h (CPU) |
| Notebook D | 2A | QA dataset prep + ChatML formatting | ~1h |
| Notebook E — Run 1 | 2A | Epochs 1–3 (full run, dataset is small) | ~2–4h |
| Notebook F | 2A | QA evaluation + export | ~1–2h |
| Local integration | 2B | Wire `rag_pipeline.py` end-to-end | 1–2h |

Total elapsed clock time: ~2–3 days (mostly waiting on generation + training).

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Generated QA pairs are too generic | Audit 100 random pairs before training; regenerate with a stricter system prompt if needed |
| Packing=True leaks across QA pairs | Always use `packing=False` for instruction tuning |
| Model ignores retrieved context | Increase `top_k`; check the context is within `max_seq_length`; reorder prompt to put context before instruction |
| Retrieval returns wrong-topic chunks | Try `top_k=6` and rerank by keyword match; or upgrade embedding model to `BAAI/bge-base-en-v1.5` |
| RAG prompt too long for 2048 context | Shorten chunks to 400 chars; or increase `MAX_SEQ_LENGTH` to 4096 (fits on T4 with 4-bit) |
| Model hallucinates sermon citations | Add an explicit instruction: "Only cite sermons if you are confident about the source." |
| Overfitting on small QA dataset | Monitor val loss; stop at Epoch 2 if val loss increases |
| Phase 1 merged model not loading | Ensure `save_method="merged_16bit"` was used in Phase 1 export; verify folder contains `config.json` |

---

## What Success Looks Like

Phase 2 is complete when:

1. **QA fine-tuning:** The model answers doctrinal and expository questions
   about Spurgeon with grounded, coherent, 2–5 sentence responses in a
   scholarly-but-warm register — not generic theological English.

2. **Retrieval:** Top-4 retrieved chunks for 80%+ of test queries are
   topically relevant to the question (manual audit of 30 queries).

3. **RAG end-to-end:** The `answer()` pipeline produces responses that cite
   identifiable sermons and are verifiably grounded in retrieved passages —
   not confabulated.

4. **Phase 2 adapter is saved and versioned**, ready for Phase 3 (multi-turn
   conversation, Puritan corpus expansion, or RLHF alignment).

---

## Project Folder Updates

```
continued_pretrain/
├── scripts/
│   ├── 06_chunk_for_qa.py
│   ├── 07_generate_qa.py
│   ├── 08_filter_qa.py
│   ├── 09_format_chatML.py
│   ├── 10_build_retrieval_chunks.py
│   └── 11_build_faiss_index.py
├── notebooks/
│   ├── D_qa_data_prep.ipynb
│   ├── E_qa_training.ipynb
│   └── F_qa_eval.ipynb
├── rag_pipeline.py              ← end-to-end retriever + generator
└── data/
    ├── qa_chunks.jsonl          ← chunks sent to Claude for generation
    ├── qa_pairs_raw.jsonl       ← raw generated pairs
    ├── qa_pairs_filtered.jsonl  ← after quality filter
    ├── qa_train.jsonl           ← ChatML-formatted training set
    ├── qa_val.jsonl             ← ChatML-formatted validation set
    ├── retrieval_chunks.jsonl   ← smaller chunks for FAISS
    ├── spurgeon_faiss.index     ← FAISS vector index (gitignored)
    └── spurgeon_faiss_meta.jsonl← chunk metadata for FAISS lookup
```

### `.gitignore` additions

```gitignore
# Large generated data and index files
continued_pretrain/data/*.jsonl
continued_pretrain/data/*.index
# Track only the scripts and notebooks
!continued_pretrain/scripts/
!continued_pretrain/notebooks/
!continued_pretrain/rag_pipeline.py
```

---

*Phase 3 possibilities: multi-turn dialogue tuning (conversation history),
RLHF/DPO alignment on theological accuracy ratings,
Puritan corpus expansion (Sibbes, Watson, Owen, Bunyan) with
Spurgeon oversampled 2–3× to preserve primary voice,
and serving via a lightweight FastAPI wrapper on the merged model.*
