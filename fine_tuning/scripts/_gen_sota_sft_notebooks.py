#!/usr/bin/env python3
"""
Generator for SOTA SFT notebooks (v2 / Fable 5 FN plan).

**G3 source of truth:** edit THIS file, then regenerate notebooks.

  python fine_tuning/scripts/_gen_sota_sft_notebooks.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from config import SPURGEON_SFT_SYSTEM_PROMPT  # noqa: E402

UNSLOTH_GIT_REF = ""
UNSLOTH_INSTALL = (
    f'!pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git@{UNSLOTH_GIT_REF}"'
    if UNSLOTH_GIT_REF
    else '!pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git"'
)

STOCK_MODEL = "unsloth/Qwen3.5-4B-Base"
KAGGLE_GATE0_MERGED = (
    "/kaggle/input/datasets/rafaelvieira1/theology-cpt-v2/theology_cpt_v2_merged_hf"
)
RUNPOD_GATE0_MERGED = "/workspace/theology_cpt_v2_merged_hf"
# Notebooks default to Kaggle path; RunPod/train_sft_sota.py use SFT_GATE0_MERGED env.
GATE0_MERGED = KAGGLE_GATE0_MERGED

CANONICAL_SYSTEM = SPURGEON_SFT_SYSTEM_PROMPT

# Plain ChatML for Base (HF Base tokenizer has no chat_template). No thinking/vision/tools.
QWEN35_SFT_CHATML = (
    "{%- for message in messages %}"
    "{%- if message['role'] == 'system' %}"
    "{{- '<|im_start|>system\\n' + message['content'] + '<|im_end|>\\n' }}"
    "{%- elif message['role'] == 'user' %}"
    "{{- '<|im_start|>user\\n' + message['content'] + '<|im_end|>\\n' }}"
    "{%- elif message['role'] == 'assistant' %}"
    "{{- '<|im_start|>assistant\\n' + message['content'] + '<|im_end|>\\n' }}"
    "{%- endif %}"
    "{%- endfor %}"
    "{%- if add_generation_prompt %}"
    "{{- '<|im_start|>assistant\\n' }}"
    "{%- endif %}"
)

S2_HELPER = f'''
def text_tokenizer(tok):
    """Unwrap VL Processor → inner tokenizer (Qwen3.5 is multimodal)."""
    inner = tok
    for _ in range(4):
        nxt = getattr(inner, "tokenizer", None)
        if nxt is None or nxt is inner:
            break
        inner = nxt
    return inner

IM_START, IM_END, EOT = "<|im_start|>", "<|im_end|>", "<|endoftext|>"
QWEN35_SFT_CHATML = {QWEN35_SFT_CHATML!r}

def apply_sft_special_token_contract(tok):
    tok = text_tokenizer(tok)
    n0 = len(tok)
    tok.padding_side = "right"
    if tok.pad_token is None or tok.pad_token == IM_END:
        tok.pad_token = EOT
    tok.pad_token_id = tok.convert_tokens_to_ids(tok.pad_token)
    if not getattr(tok, "chat_template", None):
        tok.chat_template = QWEN35_SFT_CHATML
    for t in (IM_START, IM_END, EOT):
        ids = tok(t, add_special_tokens=False)["input_ids"]
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], (list, tuple)):
            ids = list(ids[0])
        assert len(ids) == 1, f"{{t}} not atomic: {{ids}}"
        print(t, "->", ids[0], "(atomic)")
    im_end_id = tok.convert_tokens_to_ids(IM_END)
    eot_id = tok.convert_tokens_to_ids(EOT)
    assert tok.pad_token_id != im_end_id, "pad must not be <|im_end|>"
    assert 0 <= tok.pad_token_id < len(tok)
    assert len(tok) == n0, "vocab resize during S2 — abort"
    print("eos (native, do not reassign):", tok.eos_token, tok.eos_token_id)
    print("pad:", tok.pad_token, tok.pad_token_id)
    print("im_end_id:", im_end_id, "eot_id:", eot_id, "len:", len(tok), "vocab_size:", tok.vocab_size)
    demo = tok.apply_chat_template(
        [{{"role": "system", "content": "S"}}, {{"role": "user", "content": "U"}},
         {{"role": "assistant", "content": "A"}}],
        tokenize=False, add_generation_prompt=False,
    )
    print(demo)
    assert IM_END in demo and IM_START in demo
    return tok, im_end_id, eot_id
'''.lstrip()


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


def gen_d_qa_data_prep_sota(path: Path) -> None:
    cells = [
        md(
            f"""# SOTA SFT Data Prep v2 — Spurgeon Q&A (Notebook D_sota)

Plan: `fine_tuning/notebooks/PLAN_FABLE5_TO_IMPROVE_FN.md`

- Input: `qa_mix_train.jsonl` / `qa_mix_val.jsonl` from `build_qa_mix.py`
- Template: plain ChatML (`<|im_end|>` turn stop). Base has no `chat_template` — we inject one (no thinking/vision).
- **No vocab resize** — keep stock specials; pad = existing token, never `<|im_end|>`
- Outputs `qa_dataset_train/` + `qa_dataset_val/` via `save_to_disk`
"""
        ),
        md("## 1. Config"),
        code(
            f'''import json
from pathlib import Path

# Kaggle: mount qa-mix dataset; local: repo fine_tuning/data/
DATA_ROOT = Path("/kaggle/input/datasets/spurgeon-qa-mix-v1")
if not DATA_ROOT.exists():
    DATA_ROOT = Path("../../data")  # local from notebooks/

TRAIN_JSONL = DATA_ROOT / "qa_mix_train.jsonl"
VAL_JSONL = DATA_ROOT / "qa_mix_val.jsonl"
MANIFEST = DATA_ROOT / "qa_mix_manifest.json"
OUT_TRAIN = Path("/kaggle/working/qa_dataset_train") if Path("/kaggle/working").exists() else Path("../../data/qa_dataset_train")
OUT_VAL = Path("/kaggle/working/qa_dataset_val") if Path("/kaggle/working").exists() else Path("../../data/qa_dataset_val")
MAX_SEQ_LENGTH = 4096

CANONICAL_SYSTEM = {CANONICAL_SYSTEM!r}
'''
        ),
        md("## 2. Load tokenizer (stock Qwen3.5 for dev; same family as CPT merge)"),
        code(
            f'''import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Tokenizer-only: FastLanguageModel.get_tokenizer is not a public Unsloth API.
# D is data-prep — do not load the model / GPU weights here.
from transformers import AutoTokenizer

{S2_HELPER}

MODEL_NAME = "{STOCK_MODEL}"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer, im_end_id, eot_id = apply_sft_special_token_contract(tokenizer)
'''
        ),
        md("## 3. Build ChatML dataset + S1 token audit"),
        code(
            '''import numpy as np
from datasets import Dataset

def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def to_chatml_text(messages):
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)

def build_ds(jsonl_path):
    rows = load_jsonl(jsonl_path)
    texts = []
    for ex in rows:
        msgs = ex["messages"]
        if msgs[0]["content"] != CANONICAL_SYSTEM:
            msgs = [{"role": "system", "content": CANONICAL_SYSTEM}] + msgs[1:]
        texts.append({"text": to_chatml_text(msgs), "messages": msgs})
    return Dataset.from_list(texts)

train_ds = build_ds(TRAIN_JSONL)
val_ds = build_ds(VAL_JSONL)
print("train/val:", len(train_ds), len(val_ds))

lens = [len(tokenizer(x["text"])["input_ids"]) for x in train_ds]
print("S1 p50/p90/p99/max:", np.percentile(lens, [50, 90, 99]).astype(int), max(lens))
over = sum(l > MAX_SEQ_LENGTH for l in lens)
print(f"over {{MAX_SEQ_LENGTH}}:", over, f"({100*over/max(1,len(lens)):.1f}%)")
if over > len(lens) * 0.02:
    print("WARNING: >2% examples exceed MAX_SEQ_LENGTH — trim data or lower k before training")
'''
        ),
        md("## 4. Save to disk (consumed by E_sota)"),
        code(
            '''OUT_TRAIN.mkdir(parents=True, exist_ok=True)
OUT_VAL.mkdir(parents=True, exist_ok=True)
train_ds.save_to_disk(str(OUT_TRAIN))
val_ds.save_to_disk(str(OUT_VAL))
print("Saved", OUT_TRAIN, OUT_VAL)
if MANIFEST.exists():
    print("Manifest:", json.loads(MANIFEST.read_text(encoding="utf-8"))["counts"])
'''
        ),
    ]
    write_nb(path, cells)


def gen_e_qa_training_sota(path: Path) -> None:
    cells = [
        md(
            f"""# SOTA SFT Training v2 — Spurgeon Q&A (Notebook E_sota)

Plan: `fine_tuning/notebooks/PLAN_FABLE5_TO_IMPROVE_FN.md`

- **Dev:** `{STOCK_MODEL}` + D_sota `save_to_disk` output
- **Final (GATE-0):** set `USE_CPT_MERGE=True` → `{GATE0_MERGED}`
- ChatML + `train_on_responses_only` + no vocab resize
"""
        ),
        md("## 1. Environment (CUDA before Unsloth)"),
        code(
            '''import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ.setdefault("HF_HOME", "/kaggle/working/hf_home")
os.makedirs(os.environ["HF_HOME"], exist_ok=True)
OFFLOAD_DIR = "/kaggle/working/unsloth_offload"
os.makedirs(OFFLOAD_DIR, exist_ok=True)
'''
        ),
        md("## 2. Install Unsloth (G1 — pin after first good run)"),
        code(UNSLOTH_INSTALL),
        md("## 3. Config"),
        code(
            f'''import json, hashlib, os
from pathlib import Path
from datetime import datetime, timezone

USE_CPT_MERGE = False  # GATE-0: set True for final run on CPT merged HF
STOCK_MODEL = "{STOCK_MODEL}"
GATE0_PATH = os.environ.get("SFT_GATE0_MERGED", "{GATE0_MERGED}")
BASE_MODEL = GATE0_PATH if USE_CPT_MERGE else STOCK_MODEL

DATA_TRAIN = Path("/kaggle/working/qa_dataset_train")
DATA_VAL = Path("/kaggle/working/qa_dataset_val")
if not DATA_TRAIN.exists():
    DATA_TRAIN = Path("../../data/qa_dataset_train")
    DATA_VAL = Path("../../data/qa_dataset_val")

MAX_SEQ_LENGTH = 4096
LORA_RANK = 32
LORA_ALPHA = 32
LORA_DROPOUT = 0
PER_DEVICE_BATCH = 2
GRAD_ACCUM = 8
NUM_EPOCHS = 2
LEARNING_RATE = 1e-4
WARMUP_RATIO = 0.03
SEED = 3407
OUT_DIR = Path("/kaggle/working/spurgeon_qa_lora_v2")
RUN_CONFIG = Path("/kaggle/working/sft_run_config.json")

print("BASE_MODEL:", BASE_MODEL)
print("USE_CPT_MERGE:", USE_CPT_MERGE)
'''
        ),
        md("## 4. Load model + S2 special-token audit"),
        code(
            f'''from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from datasets import load_from_disk
from trl import SFTTrainer, SFTConfig
from transformers import DataCollatorForSeq2Seq

{S2_HELPER}

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)
tokenizer, im_end_id, eot_id = apply_sft_special_token_contract(tokenizer)

model = FastLanguageModel.get_peft_model(
    model,
    r=LORA_RANK,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=SEED,
)

train_ds = load_from_disk(str(DATA_TRAIN))
val_ds = load_from_disk(str(DATA_VAL))
print("Loaded", len(train_ds), len(val_ds))
'''
        ),
        md("## 5. Trainer + S3 masking audit"),
        code(
            '''# TRL >=0.18: dataset_text_field lives on SFTConfig only (not SFTTrainer kwargs).
trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    args=SFTConfig(
        per_device_train_batch_size=PER_DEVICE_BATCH,
        gradient_accumulation_steps=GRAD_ACCUM,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        lr_scheduler_type="cosine",
        optim="adamw_8bit",
        weight_decay=0.01,
        fp16=not hasattr(__import__("torch").cuda, "is_bf16_supported") or not __import__("torch").cuda.is_bf16_supported(),
        bf16=hasattr(__import__("torch").cuda, "is_bf16_supported") and __import__("torch").cuda.is_bf16_supported(),
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=max(20, len(train_ds) // (PER_DEVICE_BATCH * GRAD_ACCUM * 10)),
        save_steps=max(50, len(train_ds) // (PER_DEVICE_BATCH * GRAD_ACCUM * 5)),
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        seed=SEED,
        report_to="none",
        output_dir=str(OUT_DIR / "checkpoints"),
        dataset_text_field="text",
        packing=False,
        max_length=MAX_SEQ_LENGTH,
        eos_token="<|endoftext|>",
        pad_token="<|endoftext|>",
    ),
)

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\\n",
    response_part="<|im_start|>assistant\\n",
)

# pad==eot must not clone labels / zero stop-token CE
trainer.data_collator = DataCollatorForSeq2Seq(
    tokenizer, padding=True, label_pad_token_id=-100,
)

# S3 — supervised tokens must be assistant + <|im_end|> only
row = trainer.train_dataset[0]
ids, labs = row["input_ids"], row["labels"]
if hasattr(ids, "tolist"):
    ids, labs = ids.tolist(), labs.tolist()
kept = [t for t, l in zip(ids, labs) if l != -100]
decoded = tokenizer.decode(kept)
print(decoded)
frac = len(kept) / max(1, len(ids))
print(f"supervised fraction: {frac:.1%}")
assert im_end_id in kept, "S3 FAIL: <|im_end|> not in supervised labels"
assert "<|im_start|>user" not in decoded, "S3 FAIL: user turn leaked into labels"
'''
        ),
        md("## 6. Train + save run config"),
        code(
            '''import subprocess, torch

trainer_stats = trainer.train()
print(trainer_stats)

OUT_DIR.mkdir(parents=True, exist_ok=True)
model.save_pretrained(str(OUT_DIR / "lora"))
tokenizer.save_pretrained(str(OUT_DIR / "lora"))

run_cfg = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "base_model": BASE_MODEL,
    "use_cpt_merge": USE_CPT_MERGE,
    "max_seq_length": MAX_SEQ_LENGTH,
    "lora_rank": LORA_RANK,
    "epochs": NUM_EPOCHS,
    "train_rows": len(train_ds),
    "val_rows": len(val_ds),
    "peak_vram_gb": round(torch.cuda.max_memory_reserved() / 1e9, 2) if torch.cuda.is_available() else None,
}
try:
    run_cfg["pip_freeze"] = subprocess.check_output(["pip", "freeze"], text=True)[:8000]
except Exception:
    pass
RUN_CONFIG.write_text(json.dumps(run_cfg, indent=2), encoding="utf-8")
print("Saved adapter to", OUT_DIR / "lora")
print("Run config:", RUN_CONFIG)
'''
        ),
    ]
    write_nb(path, cells)


def gen_f_qa_eval_sota(path: Path) -> None:
    cells = [
        md(
            f"""# SOTA SFT Eval + Gated Export v2 (Notebook F_sota)

Plan: `fine_tuning/notebooks/PLAN_FABLE5_TO_IMPROVE_FN.md`

- Greedy eval on frozen `qa_test_frozen.jsonl`
- **EXPORT=False** until §5 gates pass
- GGUF/HF/Ollama only when `EXPORT=True`
"""
        ),
        md("## 1. Config"),
        code(
            f'''import os, json, re
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

USE_CPT_MERGE = False
STOCK_MODEL = "{STOCK_MODEL}"
GATE0_PATH = os.environ.get("SFT_GATE0_MERGED", "{GATE0_MERGED}")
BASE_MODEL = GATE0_PATH if USE_CPT_MERGE else STOCK_MODEL

LORA_DIR = Path("/kaggle/working/spurgeon_qa_lora_v2/lora")
TEST_JSONL = Path("/kaggle/input/datasets/spurgeon-qa-mix-v1/qa_test_frozen.jsonl")
if not TEST_JSONL.exists():
    TEST_JSONL = Path("../../data/qa_test_frozen.jsonl")

OUT_METRICS = Path("/kaggle/working/sft_eval_metrics.json")
OUT_MERGED = Path("/kaggle/working/spurgeon_qa_v2_merged_hf")
HF_REPO = "rafaelvieirar1r/qwen3.5-4b-spurgeon-qa"

# Gate: set True only after §5 criteria pass manually
EXPORT = False
MAX_SEQ_LENGTH = 4096

REFUSAL_RE = re.compile(r"does not contain|could not find|insufficient|cannot answer", re.I)
CORRUPT_RE = re.compile(r"pist|spep|RGAR|据", re.I)
'''
        ),
        md("## 2. Load model for inference"),
        code(
            f'''from unsloth import FastLanguageModel
from datasets import Dataset

{S2_HELPER}

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)
tokenizer, im_end_id, eot_id = apply_sft_special_token_contract(tokenizer)
if LORA_DIR.exists():
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, str(LORA_DIR))
FastLanguageModel.for_inference(model)

def generate(messages, max_new_tokens=400):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text=prompt, return_tensors="pt")
    inputs = {{k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}}
    out = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        temperature=0.0,
        eos_token_id=[im_end_id, eot_id],
        pad_token_id=tokenizer.pad_token_id,
    )
    text = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=False)
    if IM_END in text:
        text = text.split(IM_END)[0]
    return text.strip()
'''
        ),
        md("## 3. Frozen battery metrics"),
        code(
            '''def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def is_refusal(text):
    return bool(REFUSAL_RE.search(text))

items = load_jsonl(TEST_JSONL)
metrics = {"n": len(items), "format_ok": 0, "echo": 0, "corrupt": 0, "refusal_hits": 0, "refusal_total": 0}
samples = []

for ex in items[: min(50, len(items))]:
    msgs = ex["messages"]
    gold_refusal = is_refusal(msgs[-1]["content"])
    pred = generate(msgs[:-1])
    samples.append({"q": msgs[1]["content"][:200], "pred": pred[:400]})

    if CORRUPT_RE.search(pred):
        metrics["corrupt"] += 1
    if "CONTEXT:" in pred and pred.count("CONTEXT:") > 1:
        metrics["echo"] += 1
    if not CORRUPT_RE.search(pred) and len(pred) > 20:
        metrics["format_ok"] += 1
    if gold_refusal:
        metrics["refusal_total"] += 1
        if is_refusal(pred):
            metrics["refusal_hits"] += 1

metrics["refusal_accuracy"] = (
    metrics["refusal_hits"] / metrics["refusal_total"] if metrics["refusal_total"] else None
)
metrics["corrupt_rate"] = metrics["corrupt"] / max(1, len(samples))
OUT_METRICS.write_text(json.dumps({"metrics": metrics, "samples": samples}, indent=2), encoding="utf-8")
print(json.dumps(metrics, indent=2))
print("Samples written to", OUT_METRICS)
'''
        ),
        md("## 4. Gated merge + GGUF export"),
        code(
            '''if not EXPORT:
    print("EXPORT=False — skip merge/GGUF/HF upload until §5 gates pass.")
else:
    print("Merging 16-bit to", OUT_MERGED)
    model.save_pretrained_merged(str(OUT_MERGED), tokenizer, save_method="merged_16bit")
    tokenizer.save_pretrained(str(OUT_MERGED))
    print(
        "Next: convert to GGUF (f16 + Q4_K_M), upload to", HF_REPO,
        "\\nFiles: spurgeon-qa-v2.F16.gguf / spurgeon-qa-v2.Q4_K_M.gguf",
        "\\nOllama: fine_tuning/models/Modelfile.qwen35-spurgeon-qa-v2",
        "\\nSmoke: python fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2",
    )
'''
        ),
    ]
    write_nb(path, cells)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    nb_dir = root / "notebooks"
    gen_d_qa_data_prep_sota(nb_dir / "D_qa_data_prep_sota.ipynb")
    gen_e_qa_training_sota(nb_dir / "E_qa_training_sota.ipynb")
    gen_f_qa_eval_sota(nb_dir / "F_qa_eval_sota.ipynb")
    marker = root / "scripts" / "NOTE_SFT_SOURCE_OF_TRUTH.txt"
    marker.write_text(
        "G3: fine_tuning/scripts/_gen_sota_sft_notebooks.py is the source of truth for *_sota SFT notebooks.\n"
        "Edit the generator, then run: python fine_tuning/scripts/_gen_sota_sft_notebooks.py\n",
        encoding="utf-8",
    )
    print(f"Wrote {marker}")


if __name__ == "__main__":
    main()
