#!/usr/bin/env python3
"""
Generator for SOTA CPT notebooks (v2 / Fable 5).

**G3 source of truth:** edit THIS file, then regenerate notebooks. Do not hand-edit
`*_sota.ipynb` and this generator in parallel.

  python continued_pretrain/scripts/_gen_sota_notebooks.py
"""

from __future__ import annotations

import json
from pathlib import Path

# Pin once verified on T4 (G1). Leave empty string to use floating HEAD (not recommended).
UNSLOTH_GIT_REF = ""  # e.g. "abc1234deadbeef" — set after first good Kaggle session
UNSLOTH_INSTALL = (
    f'!pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git@{UNSLOTH_GIT_REF}"'
    if UNSLOTH_GIT_REF
    else '!pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git"'
)

# Flagship base (plan §4.1). Unsloth 4-bit build preferred when available.
FLAGSHIP_MODEL = "unsloth/Qwen3.5-4B-Base"
FALLBACK_MODEL = "unsloth/Qwen2.5-3B"
EXPERIMENT_9B = "unsloth/Qwen3.5-9B-Base"


def lines(s: str) -> list[str]:
    parts = s.split("\n")
    out: list[str] = []
    for i, p in enumerate(parts):
        if i < len(parts) - 1:
            out.append(p + "\n")
        elif p:
            out.append(p)
    return out


def md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": lines(src)}


def code(src: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": lines(src),
    }


def write_nb(path: Path, cells: list[dict]) -> None:
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path}")


def gen_b_training_sota(path: Path) -> None:
    cells = [
        md(
            f"""# SOTA CPT Training v2 — Spurgeon / Puritans / Theology (Notebook B_sota)

**Does not replace** `B_training.ipynb` (Phase-1 Spurgeon-only baseline).

Plan: `continued_pretrain/PLAN_FABLE5_TO_IMPROVE_CPT.md`

### Flagship recipe (v2)
- Base: **`{FLAGSHIP_MODEL}`** (Apache 2.0). Fallback: `{FALLBACK_MODEL}` if M1 fails.
- QLoRA r=64 + rsLoRA; targets attn+MLP+`embed_tokens`(+`lm_head` per D4)
- **`UnslothTrainer`** dual LR: body `5e-5`, embeddings `1e-5` (fallback `5e-6` on fp16 spikes)
- `warmup_ratio=0.03`, packing @ 2048, `max_steps` multi-session resume
- Per-bucket eval dict; `load_best_model_at_end` on `eval_mix_loss`
- Diagnostics D1/D2/D4; run config records manifest SHA + pip freeze

### 9B (E3 — not flagship)
Only after VRAM probe (~20 steps, `max_memory_reserved` < ~15 GB). Full dual-LR at seq 2048
is over-budget on single T4.

### VRAM escape hatches (T4 16GB)
1. `TRAIN_LM_HEAD = False` if D4 shows tied embeddings or OOM
2. `TRAIN_EMBEDDINGS = False`
3. `LORA_RANK = 32`
4. `PER_DEVICE_BATCH = 1`, raise `GRAD_ACCUM`
"""
        ),
        md("## 1. Install Dependencies (G1 — pin after first good run)"),
        code(
            UNSLOTH_INSTALL
            + "\n"
            + """
# Record environment lock for multi-session resume (G1)
import subprocess, pathlib
lock = pathlib.Path("/kaggle/working/requirements_lock.txt")
try:
    freeze = subprocess.check_output(["pip", "freeze"], text=True)
    lock.write_text(freeze, encoding="utf-8")
    print("Wrote", lock, "lines=", freeze.count(chr(10)))
except Exception as e:
    print("pip freeze skipped:", e)
"""
        ),
        md("## 2. Config (edit this cell only)"),
        code(
            f'''import os
import json
import hashlib
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
# Unsloth may offload embeddings to disk when training them — must be writable (not /kaggle/input)
os.environ.setdefault("UNSLOTH_COMPILE_DISABLE", "0")
OFFLOAD_DIR = "/kaggle/working/unsloth_offload"
os.makedirs(OFFLOAD_DIR, exist_ok=True)
os.environ["HF_HOME"] = "/kaggle/working/hf_home"
os.makedirs(os.environ["HF_HOME"], exist_ok=True)

# ---- Model / LoRA (flagship §4.1 + M1 gate) ----
# M1 risk: Qwen3.5 is hybrid (linear_attention + full_attention + vision_config).
# If from_pretrained / train fails on T4, set MODEL_NAME to fallback immediately.
MODEL_NAME = "{FLAGSHIP_MODEL}"  # M1 fail → "{FALLBACK_MODEL}"
# MODEL_NAME = "{EXPERIMENT_9B}"  # E3 only after VRAM probe passes
MAX_SEQ_LENGTH = 2048
LORA_RANK = 64
LORA_ALPHA = 64
USE_RSLORA = True
TRAIN_EMBEDDINGS = True
# M1 (2026-07-13): Qwen3.5-4B-Base has tie_word_embeddings=true → default lm_head OFF.
# Flip to True only if D4 shows clean separate head training + VRAM holds.
TRAIN_LM_HEAD = False
LORA_DROPOUT = 0

# ---- Dual LR (Unsloth CPT; v2 emb LR) ----
LEARNING_RATE = 5e-5
EMBEDDING_LEARNING_RATE = 1e-5  # fallback 5e-6 on fp16 spikes
WARMUP_RATIO = 0.03             # v2: was fixed warmup_steps=100
WEIGHT_DECAY = 0.01
LR_SCHEDULER = "cosine"

# ---- Batch / steps ----
PER_DEVICE_BATCH = 2
GRAD_ACCUM = 8
# D3 (2026-07-13): ~8.2M train tokens / 32768 tok/step ≈ 250 steps/epoch.
# Reconfirm with D1 packed tokens_per_epoch on Kaggle, then lock for multi-session resume.
MAX_STEPS = 250
NUM_TRAIN_EPOCHS = 1.0         # ignored when MAX_STEPS is set
LOGGING_STEPS = 10
EVAL_STEPS = 50                # shorter epoch → more frequent eval
SAVE_STEPS = 50
SAVE_TOTAL_LIMIT = 2           # v2: was 3
LOAD_BEST_MODEL_AT_END = True
METRIC_FOR_BEST = "eval_mix_loss"
REPORT_TO = "none"             # or "wandb" with Kaggle secret

# ---- Paths (Kaggle) ----
SRC_DATASET_PATH = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-dataset/theology_dataset"
SRC_HOLDOUT_PATH = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-dataset/theology_holdouts"
LOCAL_DATASET_PATH = "/kaggle/working/theology_dataset"
LOCAL_HOLDOUT_PATH = "/kaggle/working/theology_holdouts"
OUTPUT_DIR = "/kaggle/working/checkpoints_sota"
ADAPTER_OUT = "/kaggle/working/theology_cpt_lora"
RUN_CONFIG_OUT = "/kaggle/working/theology_cpt_run_config.json"
MANIFEST_PATH = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-corpus/theology_mix_manifest.json"
# Optional local/corpus mount for manifest hash:
# MANIFEST_PATH = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-corpus/theology_mix_manifest.json"

PREV_RUN_CHECKPOINT = None
SEED = 42
APPEND_EOS = True              # D2 fix if packed rows lack EOS
EVAL_DOCS_PER_BUCKET = 8

print("Config ready.")
print(f"  model={{MODEL_NAME}} seq={{MAX_SEQ_LENGTH}} r={{LORA_RANK}} rslora={{USE_RSLORA}}")
print(f"  lr={{LEARNING_RATE}} emb_lr={{EMBEDDING_LEARNING_RATE}} warmup_ratio={{WARMUP_RATIO}}")
print(f"  train_embed={{TRAIN_EMBEDDINGS}} train_lm_head={{TRAIN_LM_HEAD}}")
print(f"  offload_dir={{OFFLOAD_DIR}}")'''
        ),
        md("## 3. Model & PEFT (CPT targets) + D4 tied-embeddings check"),
        code(
            '''from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)

target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]
if TRAIN_LM_HEAD:
    target_modules.append("lm_head")
if TRAIN_EMBEDDINGS:
    target_modules.append("embed_tokens")

model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=target_modules,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=SEED,
    use_rslora=USE_RSLORA,
)

# ---- D4: tied embeddings ----
d4 = {
    "tie_word_embeddings": getattr(model.config, "tie_word_embeddings", None),
    "same_storage": None,
    "trainable_embed_or_head": [],
}
try:
    emb = model.get_input_embeddings().weight
    head = model.get_output_embeddings().weight
    d4["same_storage"] = int(emb.data_ptr() == head.data_ptr())
except Exception as e:
    d4["error"] = str(e)
for n, p in model.named_parameters():
    if ("embed_tokens" in n or "lm_head" in n) and p.requires_grad:
        d4["trainable_embed_or_head"].append({"name": n, "shape": list(p.shape)})

print("D4 tied embeddings:", json.dumps(d4, indent=2))
if d4.get("same_storage") and TRAIN_LM_HEAD:
    print(
        "WARNING: base weights share storage (tied). "
        "If lm_head is not truly trainable separately, set TRAIN_LM_HEAD=False and re-run PEFT cell."
    )
print("Target modules:", target_modules)
try:
    model.print_trainable_parameters()
except Exception:
    pass'''
        ),
        md("## 4. Dataset + per-bucket eval + UnslothTrainer"),
        code(
            '''from unsloth import UnslothTrainer, UnslothTrainingArguments
from datasets import load_from_disk
import shutil

if not os.path.exists(LOCAL_DATASET_PATH):
    if not os.path.exists(SRC_DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found at {SRC_DATASET_PATH}. "
            "Run A_data_prep_sota.ipynb and mount theology-cpt-dataset."
        )
    print(f"Copying dataset {SRC_DATASET_PATH} -> {LOCAL_DATASET_PATH} ...")
    shutil.copytree(SRC_DATASET_PATH, LOCAL_DATASET_PATH)
else:
    print(f"Using writable dataset at {LOCAL_DATASET_PATH}")

dataset = load_from_disk(LOCAL_DATASET_PATH)
print(dataset)

# Ensure EOS on each doc (D2) so packing preserves document boundaries
train_ds = dataset["train"]
if APPEND_EOS and tokenizer.eos_token:
    def _add_eos(batch):
        eos = tokenizer.eos_token
        texts = []
        for t in batch["text"]:
            t = t if t.endswith(eos) else (t + eos)
            texts.append(t)
        return {"text": texts}
    train_ds = train_ds.map(_add_eos, batched=True, desc="append EOS")

# Per-bucket eval dict (v2)
eval_sets = {}
mix_eval = dataset.get("test") or dataset.get("validation")
if mix_eval is not None:
    eval_sets["mix"] = mix_eval.select(range(min(EVAL_DOCS_PER_BUCKET * 2, len(mix_eval))))

holdout_src = SRC_HOLDOUT_PATH if os.path.exists(SRC_HOLDOUT_PATH) else LOCAL_HOLDOUT_PATH
if os.path.exists(holdout_src):
    if holdout_src != LOCAL_HOLDOUT_PATH and not os.path.exists(LOCAL_HOLDOUT_PATH):
        shutil.copytree(holdout_src, LOCAL_HOLDOUT_PATH)
        holdout_src = LOCAL_HOLDOUT_PATH
    for name in ["spurgeon", "puritan", "confession", "general"]:
        p = os.path.join(holdout_src, name)
        if os.path.exists(p):
            ds = load_from_disk(p)
            if APPEND_EOS and tokenizer.eos_token and "text" in ds.column_names:
                eos = tokenizer.eos_token
                ds = ds.map(
                    lambda batch: {
                        "text": [t if t.endswith(eos) else t + eos for t in batch["text"]]
                    },
                    batched=True,
                )
            eval_sets[name] = ds.select(range(min(EVAL_DOCS_PER_BUCKET, len(ds))))
            print(f"  eval[{name}]={len(eval_sets[name])}")
else:
    print("NOTE: no multi-holdouts found; eval will use mix split only.")

if not eval_sets and mix_eval is not None:
    eval_sets = mix_eval

training_args = UnslothTrainingArguments(
    per_device_train_batch_size=PER_DEVICE_BATCH,
    gradient_accumulation_steps=GRAD_ACCUM,
    warmup_ratio=WARMUP_RATIO,
    learning_rate=LEARNING_RATE,
    embedding_learning_rate=EMBEDDING_LEARNING_RATE,
    lr_scheduler_type=LR_SCHEDULER,
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    optim="adamw_8bit",
    weight_decay=WEIGHT_DECAY,
    logging_steps=LOGGING_STEPS,
    eval_strategy="steps",
    eval_steps=EVAL_STEPS,
    save_strategy="steps",
    save_steps=SAVE_STEPS,
    save_total_limit=SAVE_TOTAL_LIMIT,
    load_best_model_at_end=LOAD_BEST_MODEL_AT_END and isinstance(eval_sets, dict) and "mix" in eval_sets,
    metric_for_best_model=METRIC_FOR_BEST if LOAD_BEST_MODEL_AT_END else None,
    greater_is_better=False,
    output_dir=OUTPUT_DIR,
    seed=SEED,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    packing=True,
    report_to=REPORT_TO,
)

if MAX_STEPS is not None:
    training_args.max_steps = int(MAX_STEPS)
else:
    training_args.num_train_epochs = float(NUM_TRAIN_EPOCHS)

trainer = UnslothTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_ds,
    eval_dataset=eval_sets if eval_sets else None,
    args=training_args,
)

print("Trainer ready:", type(trainer).__name__)
print(f"  train size={len(train_ds)}")
print(f"  eval keys={list(eval_sets) if isinstance(eval_sets, dict) else type(eval_sets)}")'''
        ),
        md("## 5. Diagnostics D1 (truncation) + D2 (EOS)"),
        code(
            '''import numpy as np

# D1 — where did my tokens go?
tds = trainer.train_dataset
n = len(tds)
# Packed datasets may expose input_ids only after collator; try both
def _row_len(i):
    row = tds[i]
    if "input_ids" in row:
        return len(row["input_ids"])
    if "text" in row:
        return len(tokenizer(row["text"], add_special_tokens=False)["input_ids"])
    return -1

step = max(1, n // 200)
lens = [_row_len(i) for i in range(0, n, step)]
lens = [x for x in lens if x > 0]
d1 = {
    "packed_or_raw_rows": n,
    "sampled": len(lens),
    "row_token_len_min": int(min(lens)) if lens else None,
    "row_token_len_p50": int(np.median(lens)) if lens else None,
    "row_token_len_max": int(max(lens)) if lens else None,
    "tokens_per_epoch_est": int(n * float(np.mean(lens))) if lens else None,
}
print("D1 truncation diagnostic:", json.dumps(d1, indent=2))
if d1["row_token_len_max"] and d1["row_token_len_max"] <= MAX_SEQ_LENGTH and n < 5000:
    print(
        "NOTE: If tokens_per_epoch_est << corpus tokens and max≈2048 with ~1 row/doc, "
        "truncation is still present — rebuild mix with max_chunk_chars=7000."
    )

# D2 — EOS boundaries (first 5 rows)
eos = tokenizer.eos_token_id
d2_counts = []
for i in range(min(5, n)):
    row = tds[i]
    if "input_ids" in row:
        ids = list(row["input_ids"])
    else:
        ids = tokenizer(row["text"], add_special_tokens=False)["input_ids"]
    d2_counts.append(ids.count(eos))
print("D2 EOS counts (first 5):", d2_counts)
if d2_counts and max(d2_counts) == 0:
    print("WARNING: no EOS found — ensure APPEND_EOS=True and re-run dataset cell.")'''
        ),
        md("## 6. Optional: 9B VRAM probe (E3 gate — skip for 4B flagship)"),
        code(
            '''# Run only when MODEL_NAME is the 9B experiment. Pass if peak reserved < ~15 GB.
RUN_VRAM_PROBE = False  # set True for E3
PROBE_STEPS = 20
VRAM_PROBE_LIMIT_GB = 15.0

if RUN_VRAM_PROBE:
    import time
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.empty_cache()
    t0 = time.time()
    # Short train run
    old_max = getattr(trainer.args, "max_steps", None)
    trainer.args.max_steps = PROBE_STEPS
    trainer.train()
    peak_gb = torch.cuda.max_memory_reserved() / (1024 ** 3)
    dt = time.time() - t0
    print(f"VRAM probe: peak_reserved={peak_gb:.2f} GB over {PROBE_STEPS} steps in {dt:.1f}s")
    if peak_gb < VRAM_PROBE_LIMIT_GB:
        print("PASS — multi-session 9B may proceed with this locked config.")
    else:
        print("FAIL — stay on 4B flagship or re-probe with concessions (embed-only / seq 1024 / batch 1).")
    # Do not continue long training from probe state without restart
else:
    print("VRAM probe skipped (flagship 4B path).")'''
        ),
        md("## 7. Train"),
        code(
            '''import sys
import trl
import time

# Pickle guard (Phase-1 / v1)
if hasattr(trainer, "args"):
    cls_name = trainer.args.__class__.__name__
    if cls_name in ("SFTConfig", "UnslothTrainingArguments"):
        try:
            import trl.trainer.sft_config as sft_config_mod
            sft_config_mod.SFTConfig = trainer.args.__class__
            sys.modules["trl.trainer.sft_config"].SFTConfig = trainer.args.__class__
            trl.SFTConfig = trainer.args.__class__
        except Exception as e:
            print("Pickle guard skipped:", e)

# Measure s/step over first steps if MAX_STEPS not set (guidance for multi-session)
print("Starting SOTA CPT v2...")
t0 = time.time()
if PREV_RUN_CHECKPOINT:
    if not os.path.exists(PREV_RUN_CHECKPOINT):
        raise FileNotFoundError(f"Checkpoint not found: {PREV_RUN_CHECKPOINT}")
    print(f"Resuming from {PREV_RUN_CHECKPOINT}")
    train_result = trainer.train(resume_from_checkpoint=PREV_RUN_CHECKPOINT)
else:
    train_result = trainer.train()
elapsed = time.time() - t0
print(train_result)
print(f"Wall time: {elapsed/3600:.2f} h")'''
        ),
        md("## 8. Save adapter + run config (manifest hash, D1–D4, freeze)"),
        code(
            '''def _sha256_file(p):
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

manifest_meta = None
if os.path.exists(MANIFEST_PATH):
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            manifest_meta = json.load(f)
    except Exception as e:
        print("manifest load failed:", e)

run_config = {
    "plan": "PLAN_FABLE5_TO_IMPROVE_CPT v2",
    "model_name": MODEL_NAME,
    "flagship": MODEL_NAME,
    "max_seq_length": MAX_SEQ_LENGTH,
    "lora_rank": LORA_RANK,
    "lora_alpha": LORA_ALPHA,
    "use_rslora": USE_RSLORA,
    "target_modules": target_modules,
    "learning_rate": LEARNING_RATE,
    "embedding_learning_rate": EMBEDDING_LEARNING_RATE,
    "warmup_ratio": WARMUP_RATIO,
    "per_device_batch": PER_DEVICE_BATCH,
    "grad_accum": GRAD_ACCUM,
    "max_steps": MAX_STEPS,
    "num_train_epochs": NUM_TRAIN_EPOCHS,
    "seed": SEED,
    "dataset_src": SRC_DATASET_PATH,
    "prev_checkpoint": PREV_RUN_CHECKPOINT,
    "manifest_path": MANIFEST_PATH,
    "manifest_sha256": _sha256_file(MANIFEST_PATH) if os.path.exists(MANIFEST_PATH) else None,
    "manifest_created_at": (manifest_meta or {}).get("created_at"),
    "manifest_buckets": (manifest_meta or {}).get("buckets"),
    "d4_tied_embeddings": d4,
    "d1_truncation": d1 if "d1" in dir() else None,
    "d2_eos_counts": d2_counts if "d2_counts" in dir() else None,
    "requirements_lock": "/kaggle/working/requirements_lock.txt",
    "offload_dir": OFFLOAD_DIR,
    "notes": "SOTA CPT v2 — dual LR, per-bucket eval, Qwen3.5-4B flagship. Baseline B_training.ipynb frozen.",
}

print(f"Saving adapter to {ADAPTER_OUT} ...")
model.save_pretrained(ADAPTER_OUT)
tokenizer.save_pretrained(ADAPTER_OUT)

with open(RUN_CONFIG_OUT, "w", encoding="utf-8") as f:
    json.dump(run_config, f, indent=2)

print("Saved:")
print(" ", ADAPTER_OUT)
print(" ", RUN_CONFIG_OUT)
print("Checkpoints:", OUTPUT_DIR)'''
        ),
    ]
    write_nb(path, cells)


def gen_a_data_prep_sota(path: Path) -> None:
    cells = [
        md(
            """# SOTA CPT Dataset Prep v2 (Notebook A_sota)

Builds Hugging Face datasets from the multi-source theology mix:

```bash
python continued_pretrain/scripts/07_build_theology_mix.py
python continued_pretrain/scripts/06_verify_tokens.py --mix
```

**Does not replace** `A_data_prep.ipynb` (Spurgeon-only).

### Guards (G2)
Refuses to build if the mix is Spurgeon-only (single domain bucket) unless
`ALLOW_SPURGEON_ONLY = True` (diagnostics only).

### Outputs
- `/kaggle/working/theology_dataset` (train/test)
- `/kaggle/working/theology_holdouts/{spurgeon,puritan,confession,general}`
"""
        ),
        md("## 1. Install"),
        code("!pip install datasets -q"),
        md("## 2. Config"),
        code(
            '''import os
import json
from pathlib import Path
from datasets import Dataset, DatasetDict

CORPUS_ROOT = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-corpus"
TRAIN_TXT = os.path.join(CORPUS_ROOT, "theology_mix_train.txt")
HOLDOUT_DIR = os.path.join(CORPUS_ROOT, "holdouts")
MANIFEST_PATH = os.path.join(CORPUS_ROOT, "theology_mix_manifest.json")

OUT_TRAIN = "/kaggle/working/theology_dataset"
OUT_HOLDOUTS = "/kaggle/working/theology_holdouts"
DOC_SEP = "<|endoftext|>"
MIN_CHARS = 200
VAL_FRACTION = 0.01
SEED = 42
ALLOW_SPURGEON_ONLY = False  # G2: True only for diagnostics

print("Config OK")'''
        ),
        md("## 3. G2 multi-bucket guard + parse training mix"),
        code(
            '''def parse_concat_txt(path, min_chars=MIN_CHARS):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    text = Path(path).read_text(encoding="utf-8")
    docs = [d.strip() for d in text.split(DOC_SEP) if len(d.strip()) > min_chars]
    print(f"{path}: {len(text):,} chars -> {len(docs)} docs")
    max_doc = max((len(d) for d in docs), default=0)
    over = sum(1 for d in docs if len(d) > 8000)
    print(f"  max_doc_chars={max_doc}  docs>8k={over}")
    return docs

# G2: refuse Spurgeon-only "SOTA" mixes
if os.path.exists(MANIFEST_PATH):
    manifest = json.loads(Path(MANIFEST_PATH).read_text(encoding="utf-8"))
    buckets = manifest.get("buckets") or {}
    domain = [b for b in buckets if b in ("spurgeon", "puritan", "confession", "bible")]
    non_empty = [b for b in domain if (buckets.get(b) or {}).get("chars", 0) > 0]
    print("Manifest domain buckets with chars:", non_empty)
    print("Bucket shares:", {b: buckets[b].get("char_share") for b in buckets})
    if len(non_empty) < 2 and not ALLOW_SPURGEON_ONLY:
        raise RuntimeError(
            "G2: theology mix has <2 domain buckets "
            f"{non_empty}. Add Puritans/confessions/Bible and rebuild with "
            "07_build_theology_mix.py (omit --allow-spurgeon-only). "
            "Set ALLOW_SPURGEON_ONLY=True only for diagnostics."
        )
else:
    print("WARNING: no manifest found; cannot enforce multi-bucket guard.")

train_docs = parse_concat_txt(TRAIN_TXT)
train_ds = Dataset.from_dict({"text": train_docs})
split = train_ds.train_test_split(test_size=VAL_FRACTION, seed=SEED)
print(split)
print(f"train={len(split['train'])} val={len(split['test'])}")'''
        ),
        md("## 4. Parse multi-holdouts"),
        code(
            '''holdout_names = ["spurgeon", "puritan", "confession", "general"]
holdouts = {}

for name in holdout_names:
    p = os.path.join(HOLDOUT_DIR, f"{name}_holdout.txt")
    if os.path.exists(p):
        docs = parse_concat_txt(p)
        if docs:
            holdouts[name] = Dataset.from_dict({"text": docs, "bucket": [name] * len(docs)})
        else:
            print(f"NOTE: empty holdout: {p}")
    else:
        print(f"NOTE: missing holdout (skip): {p}")

print("Holdout buckets:", {k: len(v) for k, v in holdouts.items()})
if "puritan" not in holdouts and not ALLOW_SPURGEON_ONLY:
    print("WARNING: puritan holdout empty — domain eval will be weak until data v2 is complete.")'''
        ),
        md("## 5. Save to disk"),
        code(
            '''import shutil

if os.path.exists(OUT_TRAIN):
    shutil.rmtree(OUT_TRAIN)
split.save_to_disk(OUT_TRAIN)
print("Saved", OUT_TRAIN)

os.makedirs(OUT_HOLDOUTS, exist_ok=True)
for name, ds in holdouts.items():
    out = os.path.join(OUT_HOLDOUTS, name)
    if os.path.exists(out):
        shutil.rmtree(out)
    ds.save_to_disk(out)
    print("Saved", out)

print("\\nDone. Version /kaggle/working as Kaggle dataset: theology-cpt-dataset")
print("Mount that dataset into B_training_sota.ipynb")'''
        ),
    ]
    write_nb(path, cells)


def gen_c_eval_sota(path: Path) -> None:
    cells = [
        md(
            f"""# SOTA CPT Eval + Merge v2 (Notebook C_sota)

Evaluates the SOTA adapter with decision-grade metrics (plan Phase 3):

1. Multi-bucket PPL for **base / Phase-1 adapter / v2 adapter** (`EVAL_BASE=True` default)
2. Deterministic **greedy** style/doctrine/forgetting probes (+ optional sampled flavor)
3. **Catechism MCQ** log-likelihood (WSC absorption + Heidelberg generalization)
4. Merge/GGUF only after success criteria pass (`RUN_MERGE = False` until then)

Flagship base: `{FLAGSHIP_MODEL}`

**Does not replace** `C_eval_and_merge.ipynb`.
"""
        ),
        md("## 1. Install"),
        code(UNSLOTH_INSTALL),
        md("## 2. Config"),
        code(
            f'''import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

MODEL_NAME = "{FLAGSHIP_MODEL}"  # must match training base
MAX_SEQ_LENGTH = 2048
LOAD_IN_4BIT = True

ADAPTER_PATH = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-lora/theology_cpt_lora"
# Optional Phase-1 adapter for honest comparison (same base only — else use %Δ vs own base)
PHASE1_ADAPTER_PATH = None  # e.g. "/kaggle/input/.../spurgeon_phase1_lora"
HOLDOUT_ROOT = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-dataset/theology_holdouts"
MCQ_PATH = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-corpus/catechism_mcq.json"

EVAL_BASE = True
EVAL_PHASE1 = False  # set True if PHASE1_ADAPTER_PATH is same base family
MAX_DOCS_PER_BUCKET = 50
PROBE_SEED = 42
RUN_MERGE = False  # set True only after §5 success criteria pass

OUT_LORA = "/kaggle/working/theology_cpt_lora_final"
OUT_MERGED = "/kaggle/working/theology_cpt_merged_hf"
OUT_METRICS = "/kaggle/working/theology_cpt_eval_metrics.json"

print("Config OK")'''
        ),
        md("## 3. Load v2 adapter"),
        code(
            '''from unsloth import FastLanguageModel
import torch
import json
import math
from datasets import load_from_disk

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=ADAPTER_PATH,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=LOAD_IN_4BIT,
)
FastLanguageModel.for_inference(model)
print("Loaded adapter from", ADAPTER_PATH)'''
        ),
        md("## 4. Multi-holdout PPL + Δ table"),
        code(
            '''def eval_ppl(model, tokenizer, dataset, max_docs=None, max_seq=MAX_SEQ_LENGTH):
    total_loss = 0.0
    total_tokens = 0
    n = len(dataset) if max_docs is None else min(len(dataset), max_docs)
    for i in range(n):
        text = dataset[i]["text"]
        inputs = tokenizer(text, return_tensors="pt", add_special_tokens=False)
        inputs = {k: v.to("cuda") for k, v in inputs.items()}
        num_tokens = inputs["input_ids"].size(1)
        if num_tokens > max_seq:
            inputs = {k: v[:, :max_seq] for k, v in inputs.items()}
            num_tokens = max_seq
        if num_tokens < 2:
            continue
        with torch.no_grad():
            out = model(**inputs, labels=inputs["input_ids"])
            loss = out.loss.item()
        total_loss += loss * num_tokens
        total_tokens += num_tokens
    if total_tokens == 0:
        return {"tokens": 0, "loss": None, "ppl": None, "docs": 0}
    avg = total_loss / total_tokens
    return {"tokens": total_tokens, "loss": avg, "ppl": math.exp(avg), "docs": n}

buckets = ["spurgeon", "puritan", "confession", "general"]
metrics = {"v2": {}, "base": {}, "phase1": {}, "delta_vs_base_pct": {}}

for name in buckets:
    path = os.path.join(HOLDOUT_ROOT, name)
    if not os.path.exists(path):
        print("skip missing", path)
        continue
    ds = load_from_disk(path)
    print(f"Evaluating v2 PPL on {name} ({len(ds)} docs)...")
    metrics["v2"][name] = eval_ppl(model, tokenizer, ds, max_docs=MAX_DOCS_PER_BUCKET)
    m = metrics["v2"][name]
    if m["ppl"] is not None:
        print(f"  v2 {name}: ppl={m['ppl']:.2f} loss={m['loss']:.4f} tokens={m['tokens']:,}")

def score_model(label, model_name_or_path):
    print(f"Loading {label} from {model_name_or_path}...")
    m, t = FastLanguageModel.from_pretrained(
        model_name=model_name_or_path,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=LOAD_IN_4BIT,
    )
    FastLanguageModel.for_inference(m)
    out = {}
    for name in buckets:
        path = os.path.join(HOLDOUT_ROOT, name)
        if not os.path.exists(path):
            continue
        ds = load_from_disk(path)
        out[name] = eval_ppl(m, t, ds, max_docs=MAX_DOCS_PER_BUCKET)
        if out[name]["ppl"] is not None:
            print(f"  {label} {name}: ppl={out[name]['ppl']:.2f}")
    del m
    torch.cuda.empty_cache()
    return out

if EVAL_BASE:
    metrics["base"] = score_model("base", MODEL_NAME)
if EVAL_PHASE1 and PHASE1_ADAPTER_PATH:
    metrics["phase1"] = score_model("phase1", PHASE1_ADAPTER_PATH)

# Δ table vs base
print("\\n=== Δ PPL vs base (% lower is better absorption for domain buckets) ===")
print(f"{'bucket':12s}  {'base':>8s}  {'v2':>8s}  {'%Δ':>8s}")
for name in buckets:
    b = (metrics["base"].get(name) or {}).get("ppl")
    v = (metrics["v2"].get(name) or {}).get("ppl")
    if b and v:
        pct = 100.0 * (v - b) / b
        metrics["delta_vs_base_pct"][name] = round(pct, 2)
        print(f"{name:12s}  {b:8.2f}  {v:8.2f}  {pct:7.1f}%")

with open(OUT_METRICS, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
print("Wrote", OUT_METRICS)'''
        ),
        md("## 5. Probes (greedy = comparable; sample = flavor)"),
        code(
            '''style_prompts = [
    "The love of Christ is not a cold, speculative thing. It is",
    "Text: Romans 8:28. 'And we know that all things work together for good to them that love God.' My dear friends,",
    "What, then, is saving faith? Let us examine this question carefully, for",
]
doctrine_prompts = [
    "The Westminster Confession teaches that God from all eternity did,",
    "Justification is an act of God's free grace wherein He",
    "True saving faith rests upon Christ alone, for",
]
forgetting_prompts = [
    "The capital of France is",
    "Photosynthesis in green plants converts light energy into",
    "In the nineteenth century, the Industrial Revolution",
]

def generate(prompt, max_new_tokens=150, greedy=True):
    torch.manual_seed(PROBE_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(PROBE_SEED)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    gen_kwargs = dict(max_new_tokens=max_new_tokens)
    if greedy:
        gen_kwargs.update(dict(do_sample=False))
    else:
        gen_kwargs.update(dict(do_sample=True, temperature=0.7, top_p=0.9))
    with torch.no_grad():
        out = model.generate(**inputs, **gen_kwargs)
    return tokenizer.decode(out[0], skip_special_tokens=True)

probe_log = {"greedy": {}, "sampled": {}}
for label, prompts in [
    ("style", style_prompts),
    ("doctrine", doctrine_prompts),
    ("forgetting", forgetting_prompts),
]:
    probe_log["greedy"][label] = []
    print(f"\\n=== {label.upper()} (greedy, seed={PROBE_SEED}) ===")
    for p in prompts:
        text = generate(p, greedy=True, max_new_tokens=120 if label != "forgetting" else 40)
        print("\\n---\\n", text[:800])
        probe_log["greedy"][label].append({"prompt": p, "completion": text})

# Optional flavor (non-comparable)
print("\\n=== Style (sampled, flavor only) ===")
probe_log["sampled"]["style"] = []
for p in style_prompts[:1]:
    text = generate(p, greedy=False)
    print(text[:500])
    probe_log["sampled"]["style"].append({"prompt": p, "completion": text})

metrics["probes"] = probe_log
with open(OUT_METRICS, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)'''
        ),
        md("## 6. Catechism MCQ log-likelihood (WSC + Heidelberg)"),
        code(
            '''def option_logprob(model, tok, prompt, option):
    full = tok(prompt + " " + option, return_tensors="pt").to("cuda")
    p_len = tok(prompt, return_tensors="pt")["input_ids"].size(1)
    with torch.no_grad():
        logits = model(**full).logits[:, :-1].float()
    ids = full["input_ids"][:, 1:]
    lp = torch.log_softmax(logits, -1).gather(-1, ids.unsqueeze(-1)).squeeze(-1)
    # mean logprob of option tokens only
    start = max(0, p_len - 1)
    if start >= lp.size(1):
        return float("-inf")
    return lp[0, start:].mean().item()

def mcq_accuracy(model, tok, items):
    if not items:
        return None
    hits = 0
    for it in items:
        opts = [it["a"], *it.get("distractors", [])]
        scores = [option_logprob(model, tok, f"Q. {it['q']}\\nA.", o) for o in opts]
        hits += int(scores.index(max(scores)) == 0)
    return hits / len(items)

mcq_metrics = {}
if os.path.exists(MCQ_PATH):
    mcq = json.loads(open(MCQ_PATH, encoding="utf-8").read())
    sets = mcq.get("sets") or mcq
    for set_name, items in sets.items():
        if not items:
            continue
        acc = mcq_accuracy(model, tokenizer, items)
        mcq_metrics[f"v2_{set_name}"] = acc
        print(f"MCQ v2 {set_name}: {acc:.1%} (n={len(items)})")
    if EVAL_BASE and any(sets.values()):
        base_m, base_t = FastLanguageModel.from_pretrained(
            model_name=MODEL_NAME,
            max_seq_length=MAX_SEQ_LENGTH,
            dtype=None,
            load_in_4bit=LOAD_IN_4BIT,
        )
        FastLanguageModel.for_inference(base_m)
        for set_name, items in sets.items():
            if not items:
                continue
            acc = mcq_accuracy(base_m, base_t, items)
            mcq_metrics[f"base_{set_name}"] = acc
            print(f"MCQ base {set_name}: {acc:.1%}")
        del base_m
        torch.cuda.empty_cache()
else:
    print(
        f"NOTE: no MCQ file at {MCQ_PATH}. Build with "
        "scripts/09_build_catechism_mcq.py and upload to corpus dataset."
    )

metrics["mcq"] = mcq_metrics
with open(OUT_METRICS, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
print("Updated", OUT_METRICS)'''
        ),
        md("## 7. Save LoRA + optional merge (gated)"),
        code(
            '''print("Saving final LoRA to", OUT_LORA)
model.save_pretrained(OUT_LORA)
tokenizer.save_pretrained(OUT_LORA)

if not RUN_MERGE:
    print("RUN_MERGE=False — skip merge/GGUF until §5 success criteria pass.")
else:
    try:
        print("Merging 16-bit HF weights to", OUT_MERGED)
        model.save_pretrained_merged(OUT_MERGED, tokenizer, save_method="merged_16bit")
        print("Merge complete")
        print(
            "GGUF note: if exporting to Ollama, load tokenizer FROM the merged folder "
            "(vocab-shift fix — see project memory bugs/ollama-tokenizer-corruption-fix)."
        )
    except Exception as e:
        print("Merge skipped/failed:", e)

print("Done. Metrics at", OUT_METRICS)'''
        ),
        md(
            """## Success criteria (checklist)

| Probe | Target |
|-------|--------|
| Manifest | ≥4 buckets, shares in range, holdouts non-empty, `verified_tokens` present |
| Spurgeon PPL | Better than base; after base swap use %Δ-vs-own-base + probes (not raw PPL vs Phase-1) |
| Puritan / confession PPL | ≥15% better than base |
| General PPL | ≤10% worse than base |
| Heidelberg MCQ | ≥ +10 points absolute vs base |
| WSC MCQ | Near-ceiling (absorption) |
| Greedy style | Preferable Spurgeon-ness vs base |
"""
        ),
    ]
    write_nb(path, cells)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    nb_dir = root / "notebooks"
    gen_b_training_sota(nb_dir / "B_training_sota.ipynb")
    gen_a_data_prep_sota(nb_dir / "A_data_prep_sota.ipynb")
    gen_c_eval_sota(nb_dir / "C_eval_sota.ipynb")
    # G3 marker
    marker = root / "scripts" / "NOTE_SOURCE_OF_TRUTH.txt"
    marker.write_text(
        "G3: scripts/_gen_sota_notebooks.py is the source of truth for *_sota.ipynb.\n"
        "Edit the generator, then run: python continued_pretrain/scripts/_gen_sota_notebooks.py\n"
        "Do not hand-edit notebooks and generator in parallel.\n",
        encoding="utf-8",
    )
    print(f"Wrote {marker}")


if __name__ == "__main__":
    main()
