#!/usr/bin/env python3
"""
Generator for SOTA CPT notebooks (v2 / Fable 5).

**G3 source of truth:** edit THIS file, then regenerate notebooks. Do not hand-edit
`*_sota.ipynb` and this generator in parallel.

  python continued_pretrain/scripts/_gen_sota_notebooks.py
"""

from __future__ import annotations

import inspect
import json
import shutil
import sys
from pathlib import Path

# Pin once verified on T4 (G1). Leave empty string to use floating HEAD (not recommended).
UNSLOTH_GIT_REF = ""  # e.g. "abc1234deadbeef" — set after first good Kaggle session
_UNSLOTH_GIT = (
    f"git+https://github.com/unslothai/unsloth.git@{UNSLOTH_GIT_REF}"
    if UNSLOTH_GIT_REF
    else "git+https://github.com/unslothai/unsloth.git"
)
UNSLOTH_PIP_SPEC_KAGGLE = f"unsloth[kaggle-new] @ {_UNSLOTH_GIT}"
UNSLOTH_PIP_SPEC_RUNPOD = f"unsloth[colab-new] @ {_UNSLOTH_GIT}"
UNSLOTH_INSTALL = f'!pip install "{UNSLOTH_PIP_SPEC_KAGGLE}"'

# Flagship base (plan §4.1). Unsloth 4-bit build preferred when available.
FLAGSHIP_MODEL = "unsloth/Qwen3.5-4B-Base"
FALLBACK_MODEL = "unsloth/Mistral-7B-v0.3"
EXPERIMENT_9B = "unsloth/Qwen3.5-9B-Base"
# Runpod B best LoRA (ckpt-400). eval_cpt_sota.py pins this; notebooks leave env empty (Kaggle).
RUNPOD_CPT_ADAPTER_SHA256 = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"


def _cpt_runtime_source() -> str:
    """Full cpt_runtime.py source for inlining into notebooks (Kaggle has no extra files)."""
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import cpt_runtime

    src = inspect.getsource(cpt_runtime)
    if src.startswith("#!"):
        src = src.split("\n", 1)[1]
    return src


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


def pack_document_isolated(
    doc_token_ids,
    max_seq_len,
    eos_token_id,
    ignore_index=-100,
    continuation_ignore=1,
):
    """Pack tokenized documents into rows of at most ``max_seq_len`` tokens.

    Isolation rules (CPT train vs C prefix-PPL):
    - Never splice leftover-of-A onto the start of B (old ``manual_stream`` cut).
    - Multiple *complete* documents share a row only when each fits in the remaining
      space. A split-doc tail is flushed before the next document starts.
    - Docs longer than ``max_seq_len`` are split into consecutive windows; the first
      ``continuation_ignore + 1`` labels of a continuation window are ``ignore_index``
      (HF causal LM already skips ``labels[0]``; this also drops the first real
      cold-start CE term). Each window is its own row.
    - The first token of every later document in a multi-doc row is ``ignore_index``
      so CE does not train "predict B given A" across EOS.
    - Attention mask is all-ones on content. GatedDeltaNet cannot use 2D segment
      masks; native Unsloth/varlen packing stays off (``packing=False``).

    Each document should already include a trailing EOS when ``eos_token_id`` is set.
    """
    if max_seq_len < 1:
        raise ValueError(f"max_seq_len must be >= 1, got {max_seq_len}")

    rows = []
    cur_ids = []
    cur_labs = []

    def flush():
        if not cur_ids:
            return
        rows.append({
            "input_ids": list(cur_ids),
            "attention_mask": [1] * len(cur_ids),
            "labels": list(cur_labs),
        })
        cur_ids.clear()
        cur_labs.clear()

    def append_chunk(chunk, *, continuation):
        if not chunk:
            return
        start = len(cur_ids)
        labs = list(chunk)
        if continuation:
            n_ign = min(max(1, int(continuation_ignore) + 1), len(labs))
            for j in range(n_ign):
                labs[j] = ignore_index
        elif start > 0:
            labs[0] = ignore_index
        cur_ids.extend(chunk)
        cur_labs.extend(labs)

    for raw in doc_token_ids:
        if not raw:
            continue
        ids = list(raw)
        if len(ids) <= max_seq_len:
            if len(cur_ids) + len(ids) > max_seq_len:
                flush()
            append_chunk(ids, continuation=False)
            continue

        # Split-doc windows never share a row with another document (that was
        # leftover-A + start-of-B). Flush any short leftover, then one row per window.
        flush()
        for i in range(0, len(ids), max_seq_len):
            append_chunk(ids[i : i + max_seq_len], continuation=(i > 0))
            flush()

    flush()
    return rows


def pack_one_doc_padded(
    doc_token_ids,
    max_seq_len,
    eos_token_id,
    pad_token_id=None,
    ignore_index=-100,
    continuation_ignore=1,
    pad_to_max=False,
):
    """One document (or one ``max_seq_len`` window) per row. Never concatenates docs.

    Fail-closed vs GatedDeltaNet: Unsloth packing and multi-doc concat leak recurrent
    state even when later-doc labels are ``ignore_index``. Optional ``pad_to_max``
    fills to ``max_seq_len`` with ``attention_mask=0`` and ``labels=ignore_index``.
    Default ``pad_to_max=False`` so batch-1 training does not feed pad tokens if GDN
    ignores the mask; ``DataCollatorForSeq2Seq`` still pads within a batch > 1.

    Long docs split into consecutive windows; continuation windows mask the first
    ``continuation_ignore + 1`` labels (same as ``pack_document_isolated``).
    """
    if max_seq_len < 1:
        raise ValueError(f"max_seq_len must be >= 1, got {max_seq_len}")
    if pad_to_max and pad_token_id is None:
        raise ValueError("pad_to_max=True requires pad_token_id")

    rows = []

    def emit(chunk, continuation):
        if not chunk:
            return
        if len(chunk) > max_seq_len:
            raise ValueError(f"chunk length {len(chunk)} > max_seq_len={max_seq_len}")
        labs = list(chunk)
        if continuation:
            n_ign = min(max(1, int(continuation_ignore) + 1), len(labs))
            for j in range(n_ign):
                labs[j] = ignore_index
        ids = list(chunk)
        attn = [1] * len(chunk)
        if pad_to_max:
            n_pad = max_seq_len - len(ids)
            ids = ids + [pad_token_id] * n_pad
            attn = attn + [0] * n_pad
            labs = labs + [ignore_index] * n_pad
        rows.append({
            "input_ids": ids,
            "attention_mask": attn,
            "labels": labs,
        })

    for raw in doc_token_ids:
        if not raw:
            continue
        ids = list(raw)
        if len(ids) <= max_seq_len:
            emit(ids, continuation=False)
            continue
        for i in range(0, len(ids), max_seq_len):
            emit(ids[i : i + max_seq_len], continuation=(i > 0))
    return rows


def build_b_training_cells() -> list[dict]:
    cells = [
        md(
            f"""# SOTA CPT Training v2 — Spurgeon / Puritans / Theology (Notebook B_sota)

**Does not replace** `B_training.ipynb` (Phase-1 Spurgeon-only baseline).

Plan: `continued_pretrain/PLAN_FABLE5_TO_IMPROVE_CPT.md`

### Flagship recipe (after B v12 eval rose at 1e-5)
- Base: **`{FLAGSHIP_MODEL}`** (Apache 2.0). Fallback: `{FALLBACK_MODEL}` if M1 fails.
- LoRA **r=32** + rsLoRA; attn+MLP+**`embed_tokens`** (`TRAIN_LM_HEAD=False` — tied)
- **`UnslothTrainer`** dual LR: body `1e-5`, embeddings `5e-6` (v11/v12 eval rose — do not cut LR again)
- After pack, **`MAX_STEPS` = one padded epoch** (`ceil(rows / 16)`; ~674 on B v13 10779 rows). Abort if `eval_spurgeon` rises by step 50.
- `warmup_ratio=0.03`, **one-doc padded rows @ 2048** (never concat two docs; GDN packing leaks)
- T4: `GPU_PROFILE="t4"` QLoRA 4-bit (unofficial). sm_80+ (4090/L4/A100): `"ampere"` bf16 LoRA ~10 GB. Default is **auto** from compute capability.
- Optional GDN LoRA: `in_proj_qkv` / `in_proj_z` / `out_proj` (never `in_proj_a`/`in_proj_b`)
- Per-bucket HF holdouts (2 docs, spurgeon-only during train); quiet early-stop on **`eval_spurgeon_loss`**
- Diagnostics D1/D2/D4; run config records manifest SHA + pip freeze
- C v4 scored B v6 **checkpoint-25**. Do **not** C v11/v12. Do **not** merge.

### Qwen3.5 constraints (RC1/RC4)
- VL Processor → Unsloth ignores `packing=True`; use one-doc padded rows + inner tokenizer
- GatedDeltaNet: native packing **silently leaks**; isolated concat of two complete short docs still leaks
- Unsloth may force float32 on T4; official 4B path is bf16 LoRA (Ampere+)
- Tied embeddings → do not train `lm_head` separately

### 9B (E3 — not flagship)
Only after VRAM probe (~20 steps, `max_memory_reserved` < ~15 GB). Full dual-LR at seq 2048
is over-budget on single T4.

### VRAM escape hatches (T4 16GB)
1. `TRAIN_LM_HEAD = False` if D4 shows tied embeddings or OOM
2. Drop `EVAL_DOCS_PER_BUCKET` to 2 and/or `EVAL_BUCKETS_DURING_TRAIN = ["spurgeon"]`
3. `TRAIN_EMBEDDINGS = False` only if batch-1 embed LoRA still OOMs (B v6 fallback — will not hit −15% PPL)
4. `LORA_RANK = 16`; `PER_DEVICE_BATCH = 1`, raise `GRAD_ACCUM`
"""
        ),
        md("## 0. Runtime helpers (Kaggle + Runpod)"),
        code(_cpt_runtime_source()),
        md("## 1. Install Dependencies (G1 — pin after first good run)"),
        code(
            UNSLOTH_INSTALL
            + "\n"
            + """
# Record environment lock for multi-session resume (G1)
import subprocess, pathlib, os
_lock_root = resolve_work_root()
os.makedirs(_lock_root, exist_ok=True)
lock = pathlib.Path(_lock_root) / "requirements_lock.txt"
try:
    freeze = subprocess.check_output(["pip", "freeze"], text=True)
    lock.write_text(freeze, encoding="utf-8")
    print("Wrote", lock, "lines=", freeze.count(chr(10)))
except Exception as e:
    print("pip freeze skipped:", e)
"""
        ),
        md("## 1b. GPU sanity check (fail fast on Pascal / P100)"),
        code(
            '''import torch

assert torch.cuda.is_available(), "CUDA not available — enable GPU accelerator"
name = torch.cuda.get_device_name(0)
major, minor = torch.cuda.get_device_capability(0)
cc = f"{major}.{minor}"
print("GPU:", name, "| capability:", cc, "| torch:", torch.__version__, "| cuda:", torch.version.cuda)
print("arch list:", torch.cuda.get_arch_list())
# Kaggle torch cu128 dropped Pascal (sm_60 / P100). T4 is sm_75. 4090/L4/A100 are sm_80+.
if major < 7:
    raise RuntimeError(
        f"Incompatible GPU {name} (sm_{major}{minor}). "
        "Need sm_70+ (T4) or sm_80+ (RTX 4090 / L4 / A100). "
        "Kaggle: set machine_shape=NvidiaTeslaT4 in kernel-metadata.json "
        "(enable_gpu alone may assign P100). Runpod: pick 4090/L4/A100, not T4."
    )
# Smoke a tiny CUDA op so we fail here, not mid-model-load
x = torch.zeros(1, device="cuda")
x.fill_(1.0)
print("CUDA smoke OK:", float(x.item()))
'''
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

WORK_ROOT = resolve_work_root()
os.makedirs(WORK_ROOT, exist_ok=True)
_layout = layout_paths(WORK_ROOT)
OFFLOAD_DIR = _layout["offload_dir"]
os.makedirs(OFFLOAD_DIR, exist_ok=True)
os.environ["HF_HOME"] = _layout["hf_home"]
os.makedirs(os.environ["HF_HOME"], exist_ok=True)

# ---- Model / LoRA (flagship §4.1 + M1 gate) ----
# M1 risk: Qwen3.5 is hybrid (linear_attention + full_attention + vision_config).
# ProcessorMixin → packing ignored; GatedDeltaNet → packing=False + one-doc padded rows.
# Unsloth may switch to float32 training on T4 (no bf16). Ampere/Ada: official bf16 LoRA.
# If from_pretrained / train fails on T4, set MODEL_NAME to fallback immediately.
MODEL_NAME = "{FLAGSHIP_MODEL}"  # M1 fail → "{FALLBACK_MODEL}"
# MODEL_NAME = "{EXPERIMENT_9B}"  # E3 only after VRAM probe passes
MAX_SEQ_LENGTH = 2048
# t4 = Tesla T4 (sm_75, 4-bit). ampere = sm_80+ (4090/L4/A100, bf16 LoRA ~10GB).
# Default auto from compute capability; override with env GPU_PROFILE=t4|ampere.
_cc_major = None
try:
    import torch as _torch_cfg
    if _torch_cfg.cuda.is_available():
        _cc_major = _torch_cfg.cuda.get_device_capability(0)[0]
except Exception:
    _cc_major = None
GPU_PROFILE = resolve_gpu_profile(_cc_major)
LOAD_IN_4BIT = GPU_PROFILE == "t4"
# RC2: lighter LoRA than v3 r=64/LR 5e-5 (that overfit after step 50 on *unpacked* data)
LORA_RANK = 32
LORA_ALPHA = 32
USE_RSLORA = True
# v5 OOM = embed LoRA + batch 2. v6 completed 1×16 with embeds off (C v4 still missed §5).
# v7: same 1×16 shape WITH embed LoRA (actual Unsloth CPT). If OOM, see EVAL_* fallbacks first.
TRAIN_EMBEDDINGS = True
# M1 (2026-07-13): Qwen3.5-4B-Base has tie_word_embeddings=true → default lm_head OFF.
# Flip to True only if D4 shows clean separate head training + VRAM holds.
TRAIN_LM_HEAD = False
LORA_DROPOUT = 0
# Cookbook GDN LoRA on the padded path only. Never LoRA in_proj_a / in_proj_b (NaNs if packing).
LORA_GDN = True

# ---- Dual LR (Unsloth CPT) ----
# v11 (2e-5): eval_spurgeon rose 2.349→2.363→2.383; early-stop 75; best=ckpt-25.
# v12 (1e-5): same rise 2.340→2.345→2.361. Keep 1e-5; next B is one-doc padded, not another LR cut.
LEARNING_RATE = 1e-5
EMBEDDING_LEARNING_RATE = 5e-6
WARMUP_RATIO = 0.03
WEIGHT_DECAY = 0.01
LR_SCHEDULER = "cosine"

# ---- Packing (GatedDeltaNet fail-closed) ----
MANUAL_PACK = True
PACKING_MODE = "one_doc_padded"  # "one_doc_padded" | "manual_isolated"
# pad_to_max=True fills every row to 2048. GDN may ignore attention_mask — keep False on T4.
PAD_TO_MAX = False

# ---- Batch / steps (one padded epoch; abort if eval_spurgeon rises by step 50) ----
PER_DEVICE_BATCH = 1
GRAD_ACCUM = 16
# Placeholder until pack: then MAX_STEPS is set to ceil(packed_rows / 16) (one epoch).
# B v13: 10779 rows → 674 steps. Do NOT keep the v4/v6 cap of 100.
MAX_STEPS = 476
NUM_TRAIN_EPOCHS = 1.0         # ignored when MAX_STEPS is set
LOGGING_STEPS = 10
EVAL_STEPS = 25
SAVE_STEPS = 25
# Operator rule encoded: stop if eval_spurgeon_loss at 50 is worse than at 25.
ABORT_SPURGEON_STEP = 50
ABORT_SPURGEON_REF_STEP = 25
_save_policy = checkpoint_save_policy(WORK_ROOT)
SAVE_TOTAL_LIMIT = _save_policy["save_total_limit"]
SAVE_ONLY_MODEL = _save_policy["save_only_model"]
LOAD_BEST_MODEL_AT_END = True
# RC3: align with §5 spurgeon holdout — not mix val (45 docs)
METRIC_FOR_BEST = "eval_spurgeon_loss"
EARLY_STOPPING_PATIENCE = 2
REPORT_TO = "none"             # or "wandb" with Kaggle secret
EVAL_DOCS_PER_BUCKET = 2       # v7 OOM at first eval with 8 docs/bucket + mix*2
# mix is always kept if present; v7 eval OOM: spurgeon-only besides mix
EVAL_BUCKETS_DURING_TRAIN = ["spurgeon"]

# ---- Continue-from-LoRA (CPT_RUN_MODE=continue) ----
CPT_RUN_MODE = resolve_run_mode()
EARLY_STOP_MIN_STEPS = 0
EARLY_STOP_EPSILON = 0.005
USE_COMPOSITE_EARLY_STOP = False
COMPOSITE_EARLY_STOP_METRICS = ["eval_spurgeon_loss", "eval_mix_loss"]
INIT_ADAPTER_PATH = None

# ---- Paths: env CPT_WORK_ROOT / CPT_DATA_ROOT / PREV_RUN_CHECKPOINT; Kaggle mounts still work ----
_kaggle_input = KAGGLE_INPUT if os.path.isdir(KAGGLE_INPUT) else None
SRC_DATASET_PATH = find_hf_dataset_root(
    dataset_search_roots(WORK_ROOT, kaggle_input=_kaggle_input)
)
SRC_HOLDOUT_PATH = find_hf_holdout_root(
    holdout_search_roots(WORK_ROOT, dataset_root=SRC_DATASET_PATH, kaggle_input=_kaggle_input),
    walk_roots=[p for p in (WORK_ROOT, _kaggle_input) if p],
)
CORPUS_ROOT = find_corpus_root(corpus_search_roots(WORK_ROOT, kaggle_input=_kaggle_input))
LOCAL_DATASET_PATH = _layout["local_dataset"]
LOCAL_HOLDOUT_PATH = _layout["local_holdout"]
OUTPUT_DIR = _layout["output_dir"]
ADAPTER_OUT = _layout["adapter_out"]
RUN_CONFIG_OUT = _layout["run_config_out"]
MANIFEST_PATH = first_existing(
    os.path.join(CORPUS_ROOT, "theology_mix_manifest.json") if CORPUS_ROOT else None,
    os.path.join(WORK_ROOT, "theology_mix_manifest.json"),
)

if CPT_RUN_MODE == "continue":
    INIT_ADAPTER_PATH = resolve_init_adapter(WORK_ROOT, kaggle_input=_kaggle_input)
    if not INIT_ADAPTER_PATH:
        raise RuntimeError(
            "CPT_RUN_MODE=continue requires CPT_INIT_ADAPTER or theology_cpt_lora under WORK_ROOT"
        )
    _cont_cfg = resolve_continue_training_config(packed_epoch_steps=None)
    LEARNING_RATE = _cont_cfg["learning_rate"]
    EMBEDDING_LEARNING_RATE = _cont_cfg["embedding_learning_rate"]
    WARMUP_RATIO = _cont_cfg["warmup_ratio"]
    EVAL_DOCS_PER_BUCKET = _cont_cfg["eval_docs_per_bucket"]
    EVAL_BUCKETS_DURING_TRAIN = _cont_cfg["eval_buckets_during_train"]
    ABORT_SPURGEON_STEP = _cont_cfg["abort_spurgeon_step"]
    EARLY_STOP_EPSILON = _cont_cfg["early_stop_epsilon"]
    EARLY_STOPPING_PATIENCE = _cont_cfg["early_stop_patience"]
    USE_COMPOSITE_EARLY_STOP = _cont_cfg["use_composite_early_stop"]
    COMPOSITE_EARLY_STOP_METRICS = _cont_cfg["composite_early_stop_metrics"]
    print(f"Continue mode: init_adapter={{INIT_ADAPTER_PATH}}")

PREV_RUN_CHECKPOINT = resolve_prev_checkpoint(WORK_ROOT, kaggle_input=_kaggle_input)
if CPT_RUN_MODE == "continue" and PREV_RUN_CHECKPOINT:
    print(
        "WARNING: PREV_RUN_CHECKPOINT ignored in continue mode — "
        "adapter-only load + fresh Adam (not HF resume)"
    )
    PREV_RUN_CHECKPOINT = None
if PREV_RUN_CHECKPOINT:
    print(f"Auto-resume: PREV_RUN_CHECKPOINT={{PREV_RUN_CHECKPOINT}}")
else:
    print("No prior checkpoint found — fresh training run.")
    print("  (empty PREV_RUN_CHECKPOINT env forces fresh; do not resume Kaggle 4-bit ckpts on Ampere bf16)")
SEED = 42
APPEND_EOS = True              # D2 fix if packed rows lack EOS

print("Config ready.")
print(f"  work_root={{WORK_ROOT}} save_total_limit={{SAVE_TOTAL_LIMIT}} save_only_model={{SAVE_ONLY_MODEL}}")
print(f"  model={{MODEL_NAME}} seq={{MAX_SEQ_LENGTH}} r={{LORA_RANK}} rslora={{USE_RSLORA}}")
print(f"  gpu_profile={{GPU_PROFILE}} load_in_4bit={{LOAD_IN_4BIT}} lora_gdn={{LORA_GDN}}")
print(f"  packing_mode={{PACKING_MODE}} pad_to_max={{PAD_TO_MAX}} manual_pack={{MANUAL_PACK}}")
print(f"  lr={{LEARNING_RATE}} emb_lr={{EMBEDDING_LEARNING_RATE}} warmup_ratio={{WARMUP_RATIO}}")
print(f"  max_steps={{MAX_STEPS}} eval_steps={{EVAL_STEPS}} metric={{METRIC_FOR_BEST}}")
print(f"  abort_spurgeon_step={{ABORT_SPURGEON_STEP}} ref_step={{ABORT_SPURGEON_REF_STEP}}")
print(f"  batch={{PER_DEVICE_BATCH}}x{{GRAD_ACCUM}} train_embed={{TRAIN_EMBEDDINGS}} train_lm_head={{TRAIN_LM_HEAD}}")
print(f"  eval_docs={{EVAL_DOCS_PER_BUCKET}} eval_buckets={{EVAL_BUCKETS_DURING_TRAIN}}")
print(f"  cpt_run_mode={{CPT_RUN_MODE}} init_adapter={{INIT_ADAPTER_PATH}} composite_stop={{USE_COMPOSITE_EARLY_STOP}}")
print(f"  offload_dir={{OFFLOAD_DIR}}")
print(f"  CORPUS_ROOT={{CORPUS_ROOT}}")
print(f"  SRC_DATASET_PATH={{SRC_DATASET_PATH}}")
print(f"  SRC_HOLDOUT_PATH={{SRC_HOLDOUT_PATH}}")
print(f"  MANIFEST_PATH={{MANIFEST_PATH}}")
# Fail early with a clear listing if mounts are wrong
if SRC_DATASET_PATH is None:
    print("ERROR: theology dataset not found.")
    print("  Set CPT_DATA_ROOT to a dir with theology_dataset/dataset_dict.json")
    print("  or copy continued_pretrain/kaggle/a_output to WORK_ROOT.")
    _scan = _kaggle_input or WORK_ROOT
    if os.path.isdir(_scan):
        print("Scanned:", _scan)
        for root, dirs, files in os.walk(_scan):
            depth = root.count(os.sep) - _scan.count(os.sep)
            if depth <= 2:
                print(" ", root, "dirs=", dirs[:12], "files=", files[:8])
    raise FileNotFoundError(
        "HF theology dataset not found (need dataset_dict.json). "
        "Kaggle: mount rafaelvieira1/theology-cpt-dataset. "
        "Runpod: copy kaggle/a_output/theology_dataset under CPT_WORK_ROOT or CPT_DATA_ROOT."
    )
if SRC_HOLDOUT_PATH is None and LOAD_BEST_MODEL_AT_END:
    print("ERROR: HF theology_holdouts not found (need spurgeon/ as HF dataset).")
    print("  Do NOT use corpus holdouts/*.txt.")
    raise FileNotFoundError(
        "RC3: theology_holdouts/spurgeon required (HF dataset). "
        "Kaggle: mount theology-cpt-dataset. Runpod: copy a_output/theology_holdouts."
    )
'''
        ),
        md("## 3. Model & PEFT (CPT targets) + D4 tied-embeddings check"),
        code(
            '''from unsloth import FastLanguageModel
import torch

_cc_major, _cc_minor = torch.cuda.get_device_capability(0)
if GPU_PROFILE == "ampere" and _cc_major < 8:
    raise RuntimeError(
        f"GPU_PROFILE=ampere requires sm_80+ (RTX 4090 / L4 / A100). "
        f"Got {torch.cuda.get_device_name(0)} sm_{_cc_major}{_cc_minor}."
    )
if GPU_PROFILE == "t4" and _cc_major >= 8:
    print(
        "NOTE: sm_80+ GPU with GPU_PROFILE=t4 (4-bit). "
        "Set GPU_PROFILE='ampere' (or unset to auto) for official bf16 LoRA (~10 GB)."
    )
if GPU_PROFILE == "ampere" and LOAD_IN_4BIT:
    print("WARNING: GPU_PROFILE=ampere but LOAD_IN_4BIT=True — Unsloth does not recommend QLoRA on Qwen3.5.")

_expected_adapter_sha = (os.environ.get("EXPECTED_ADAPTER_SHA256") or "").strip()
if INIT_ADAPTER_PATH:
    if _expected_adapter_sha.lower() not in ("", "none", "skip"):
        _adapter_weights = os.path.join(INIT_ADAPTER_PATH, "adapter_model.safetensors")
        _got_sha = sha256_file(_adapter_weights)
        if _got_sha.lower() != _expected_adapter_sha.lower():
            raise RuntimeError(
                f"adapter SHA256 mismatch: got {{_got_sha}} want {{_expected_adapter_sha}}"
            )
        print(f"INIT_ADAPTER SHA256 OK: {{_got_sha}}")
    _flm_kwargs = dict(
        model_name=INIT_ADAPTER_PATH,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=LOAD_IN_4BIT,
    )
else:
    _flm_kwargs = dict(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=LOAD_IN_4BIT,
    )
if not LOAD_IN_4BIT:
    _flm_kwargs["load_in_16bit"] = True
try:
    model, tokenizer = FastLanguageModel.from_pretrained(**_flm_kwargs)
except TypeError:
    _flm_kwargs.pop("load_in_16bit", None)
    model, tokenizer = FastLanguageModel.from_pretrained(**_flm_kwargs)

target_modules = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]
if LORA_GDN:
    if PACKING_MODE != "one_doc_padded":
        print(
            f"WARNING: LORA_GDN ignored (PACKING_MODE={{PACKING_MODE!r}}). "
            "GDN in_proj_* only on the padded path; do not LoRA in_proj_a/b if packing."
        )
    else:
        target_modules.extend(["in_proj_qkv", "in_proj_z", "out_proj"])
if TRAIN_LM_HEAD:
    target_modules.append("lm_head")
if TRAIN_EMBEDDINGS:
    target_modules.append("embed_tokens")

if INIT_ADAPTER_PATH:
    print(f"Loaded continue adapter from {{INIT_ADAPTER_PATH}} (skip get_peft_model)")
else:
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
if TRAIN_EMBEDDINGS and not d4.get("trainable_embed_or_head"):
    print(
        "WARNING (RC4): TRAIN_EMBEDDINGS=True but no trainable embed_tokens/lm_head params found. "
        "Embedding LoRA may be inactive on this Unsloth/PEFT build — check print_trainable_parameters."
    )
print("Target modules:", target_modules)
try:
    model.print_trainable_parameters()
except Exception:
    pass

# Unsloth upcasts embed_tokens to fp32 (modules_to_save) and unties lm_head (D4 same_storage=0).
# Train compiled loss survives; eval calls self.lm_head(hidden_fp32) vs weight_fp16 →
# RuntimeError: float != c10::Half. Align lm_head inputs to its weight dtype (no extra VRAM).
if TRAIN_EMBEDDINGS:
    _head = model.get_output_embeddings()
    if _head is not None and hasattr(_head, "weight"):
        def _lm_head_align_dtype(mod, args):
            x = args[0]
            wdt = mod.weight.dtype
            if x is not None and hasattr(x, "dtype") and x.dtype != wdt:
                x = x.to(wdt)
            return (x,) + args[1:]
        _head.register_forward_pre_hook(_lm_head_align_dtype)
        print(f"lm_head dtype-align hook registered (weight dtype={_head.weight.dtype})")
    else:
        print("NOTE: could not register lm_head dtype-align hook")
'''
        ),
        md("## 4. Dataset + manual pack + per-bucket eval + UnslothTrainer"),
        code(
            '''from unsloth import UnslothTrainer, UnslothTrainingArguments
from transformers import DataCollatorForSeq2Seq, EarlyStoppingCallback, TrainerCallback
from datasets import Dataset, load_from_disk
import shutil
import math

# Qwen3.5 loads a VL Processor — Unsloth ignores packing=True on ProcessorMixin models.
# GatedDeltaNet packing silently leaks. PACKING_MODE / PAD_TO_MAX come from the config cell.
# Do NOT set packing=True (Processor ignores it; GDN varlen is unsafe).
if "MANUAL_PACK" not in dir():
    MANUAL_PACK = True
if "PACKING_MODE" not in dir():
    PACKING_MODE = "one_doc_padded"
if "PAD_TO_MAX" not in dir():
    PAD_TO_MAX = False
if "ABORT_SPURGEON_STEP" not in dir():
    ABORT_SPURGEON_STEP = 50
if "ABORT_SPURGEON_REF_STEP" not in dir():
    ABORT_SPURGEON_REF_STEP = 25


def text_tokenizer(tok):
    """Unwrap VL Processor → inner PreTrainedTokenizer."""
    inner = tok
    for _ in range(4):
        nxt = getattr(inner, "tokenizer", None)
        if nxt is None or nxt is inner:
            break
        inner = nxt
    return inner


def ids_for_text(tok, text, add_special_tokens=False):
    """Tokenize text only — never pass a positional string into a VL Processor."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    t = text_tokenizer(tok)
    if hasattr(t, "encode") and getattr(t, "image_processor", None) is None:
        ids = t.encode(text, add_special_tokens=add_special_tokens)
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], (list, tuple)):
            ids = list(ids[0])
        return [int(x) for x in ids]
    try:
        out = t(text=text, add_special_tokens=add_special_tokens)
    except TypeError:
        out = t(text, add_special_tokens=add_special_tokens)
    ids = out["input_ids"]
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], (list, tuple)):
        ids = list(ids[0])
    return [int(x) for x in ids]


'''
            + inspect.getsource(pack_document_isolated)
            + "\n"
            + inspect.getsource(pack_one_doc_padded)
            + '''

def build_manual_packed_dataset(texts, tok, max_seq_len, eos_token_id):
    """Tokenize docs then emit rows for PACKING_MODE (one_doc_padded | manual_isolated)."""
    docs = []
    for text in texts:
        ids = ids_for_text(tok, text, add_special_tokens=False)
        if eos_token_id is not None and (not ids or ids[-1] != eos_token_id):
            ids = ids + [eos_token_id]
        if ids:
            docs.append(ids)
    pad_id = getattr(tok, "pad_token_id", None)
    if pad_id is None:
        pad_id = eos_token_id
    mode = PACKING_MODE
    if mode == "one_doc_padded":
        rows = pack_one_doc_padded(
            docs,
            max_seq_len,
            eos_token_id,
            pad_token_id=pad_id,
            pad_to_max=PAD_TO_MAX,
        )
    elif mode == "manual_isolated":
        rows = pack_document_isolated(docs, max_seq_len, eos_token_id)
    else:
        raise ValueError(f"Unknown PACKING_MODE={mode!r}")
    return Dataset.from_list(rows)


train_tok = text_tokenizer(tokenizer)
print("train_tok", type(train_tok).__name__, "eos_id=", train_tok.eos_token_id)

if not os.path.exists(LOCAL_DATASET_PATH):
    if not SRC_DATASET_PATH or not os.path.exists(SRC_DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found (SRC_DATASET_PATH={SRC_DATASET_PATH!r}). "
            "Mount rafaelvieira1/theology-cpt-dataset and ensure dataset_dict.json is present."
        )
    print(f"Copying dataset {SRC_DATASET_PATH} -> {LOCAL_DATASET_PATH} ...")
    shutil.copytree(SRC_DATASET_PATH, LOCAL_DATASET_PATH)
else:
    print(f"Using writable dataset at {LOCAL_DATASET_PATH}")

assert os.path.isfile(os.path.join(LOCAL_DATASET_PATH, "dataset_dict.json")), (
    f"Missing dataset_dict.json under {LOCAL_DATASET_PATH}"
)
dataset = load_from_disk(LOCAL_DATASET_PATH)
print(dataset)
print("train rows:", len(dataset["train"]))

train_ds = dataset["train"]
raw_doc_count = len(train_ds)

if MANUAL_PACK:
    print(
        f"Manual pack mode={PACKING_MODE} pad_to_max={PAD_TO_MAX}: "
        f"{raw_doc_count} docs -> <=2048-token rows (one doc/window per row if one_doc_padded) ..."
    )
    train_ds = build_manual_packed_dataset(
        train_ds["text"],
        train_tok,
        MAX_SEQ_LENGTH,
        train_tok.eos_token_id,
    )
    print(
        f"  packed rows={len(train_ds)}  raw_docs={raw_doc_count}  "
        f"(one_doc_padded: rows >= docs; isolated: rows ≈ docs; long docs add windows)"
    )
    _eff_batch = PER_DEVICE_BATCH * GRAD_ACCUM
    PACKED_EPOCH_STEPS = max(1, math.ceil(len(train_ds) / float(_eff_batch)))
    # One padded epoch (raise or clamp). Abort-at-50 / early-stop still cut short if eval rises.
    if MAX_STEPS is None or int(MAX_STEPS) != PACKED_EPOCH_STEPS:
        print(f"Setting MAX_STEPS {MAX_STEPS} -> {PACKED_EPOCH_STEPS} (one packed epoch)")
        MAX_STEPS = PACKED_EPOCH_STEPS
    print(
        f"packed_epoch_steps={PACKED_EPOCH_STEPS}  MAX_STEPS={MAX_STEPS}  "
        f"(one padded epoch; abort if eval_spurgeon rises by step {ABORT_SPURGEON_STEP})"
    )
    if CPT_RUN_MODE == "continue":
        _cont_cfg = resolve_continue_training_config(packed_epoch_steps=PACKED_EPOCH_STEPS)
        EARLY_STOP_MIN_STEPS = _cont_cfg.get("early_stop_min_steps", EARLY_STOP_MIN_STEPS)
        print(
            f"  continue early_stop_min_steps={EARLY_STOP_MIN_STEPS} "
            f"epsilon={EARLY_STOP_EPSILON} composite={USE_COMPOSITE_EARLY_STOP}"
        )
elif APPEND_EOS and train_tok.eos_token:
    def _add_eos(batch):
        eos = train_tok.eos_token
        return {"text": [t if t.endswith(eos) else (t + eos) for t in batch["text"]]}
    train_ds = train_ds.map(_add_eos, batched=True, desc="append EOS")

# Per-bucket eval dict — HF holdouts only (RC3)
eval_sets = {}
mix_eval = dataset.get("test") or dataset.get("validation")
if mix_eval is not None:
    eval_sets["mix"] = mix_eval.select(range(min(EVAL_DOCS_PER_BUCKET * 2, len(mix_eval))))

holdout_src = SRC_HOLDOUT_PATH
if holdout_src and os.path.exists(holdout_src):
    if holdout_src != LOCAL_HOLDOUT_PATH and not os.path.exists(LOCAL_HOLDOUT_PATH):
        shutil.copytree(holdout_src, LOCAL_HOLDOUT_PATH)
        holdout_src = LOCAL_HOLDOUT_PATH
    elif os.path.exists(LOCAL_HOLDOUT_PATH) and is_hf_holdout_root(LOCAL_HOLDOUT_PATH):
        holdout_src = LOCAL_HOLDOUT_PATH
    for name in ["spurgeon", "puritan", "confession", "general"]:
        p = os.path.join(holdout_src, name)
        if os.path.exists(p) and (
            os.path.isfile(os.path.join(p, "dataset_info.json"))
            or os.path.isfile(os.path.join(p, "state.json"))
        ):
            ds = load_from_disk(p)
            if APPEND_EOS and train_tok.eos_token and "text" in ds.column_names:
                eos = train_tok.eos_token
                ds = ds.map(
                    lambda batch: {
                        "text": [t if t.endswith(eos) else t + eos for t in batch["text"]]
                    },
                    batched=True,
                )
            eval_sets[name] = ds.select(range(min(EVAL_DOCS_PER_BUCKET, len(ds))))
            print(f"  eval[{name}]={len(eval_sets[name])}")
        else:
            print(f"  NOTE: skip holdout bucket {name!r} (not HF dataset at {p})")
else:
    print("NOTE: no HF multi-holdouts found.")

if not eval_sets and mix_eval is not None:
    eval_sets = mix_eval

_best_bucket = None
if isinstance(METRIC_FOR_BEST, str) and METRIC_FOR_BEST.startswith("eval_") and METRIC_FOR_BEST.endswith("_loss"):
    _best_bucket = METRIC_FOR_BEST[len("eval_") : -len("_loss")]

if isinstance(eval_sets, dict):
    _keep = set(EVAL_BUCKETS_DURING_TRAIN) | {"mix"}
    if _best_bucket:
        _keep.add(_best_bucket)
    dropped = [k for k in eval_sets if k not in _keep]
    if dropped:
        print("Dropping eval buckets (EVAL_BUCKETS_DURING_TRAIN):", dropped)
        eval_sets = {k: v for k, v in eval_sets.items() if k in _keep}

# When train is pre-tokenized (manual pack), eval must be too — Unsloth otherwise
# requires formatting_func on text eval dicts (RC1 follow-up).
def _tokenize_eval_ds(ds):
    rows = []
    for text in ds["text"]:
        ids = ids_for_text(train_tok, text, add_special_tokens=False)[:MAX_SEQ_LENGTH]
        if not ids:
            continue
        rows.append({
            "input_ids": ids,
            "attention_mask": [1] * len(ids),
            "labels": ids.copy(),
        })
    return Dataset.from_list(rows)

if MANUAL_PACK and isinstance(eval_sets, dict):
    eval_sets = {k: _tokenize_eval_ds(v) for k, v in eval_sets.items()}
    print("Tokenized eval buckets for manual-pack trainer:", {k: len(v) for k, v in eval_sets.items()})
elif MANUAL_PACK and eval_sets is not None and not isinstance(eval_sets, dict):
    eval_sets = _tokenize_eval_ds(eval_sets)
    print("Tokenized mix eval for manual-pack trainer:", len(eval_sets))

# RC3 gate: early-stop metric bucket must exist
if LOAD_BEST_MODEL_AT_END:
    if not isinstance(eval_sets, dict) or (_best_bucket and _best_bucket not in eval_sets):
        raise RuntimeError(
            f"RC3: METRIC_FOR_BEST={METRIC_FOR_BEST!r} requires eval_sets[{_best_bucket!r}]. "
            f"Got keys={list(eval_sets) if isinstance(eval_sets, dict) else type(eval_sets)}. "
            "Mount theology-cpt-dataset with theology_holdouts/spurgeon (HF), not corpus .txt."
        )

if USE_COMPOSITE_EARLY_STOP and isinstance(eval_sets, dict):
    for _metric in COMPOSITE_EARLY_STOP_METRICS:
        if not (_metric.startswith("eval_") and _metric.endswith("_loss")):
            raise RuntimeError(f"Composite metric must be eval_*_loss, got {_metric!r}")
        _bucket = _metric[len("eval_") : -len("_loss")]
        if _bucket not in eval_sets:
            raise RuntimeError(
                f"Composite early-stop requires eval_sets[{_bucket!r}] for {_metric!r}. "
                f"Got keys={list(eval_sets)}"
            )

# Embed LoRA upcasts embed_tokens to fp32. fp16 autocast then crashes eval
# (Linear float32 vs float16). bf16 on sm_80+ is the official path and stays ON
# even with TRAIN_EMBEDDINGS. T4 + embeds → both False (float32).
_bf16_ok = torch.cuda.is_bf16_supported()
_use_fp16, _use_bf16 = trainer_mixed_precision(TRAIN_EMBEDDINGS, _bf16_ok)
training_args = UnslothTrainingArguments(
    per_device_train_batch_size=PER_DEVICE_BATCH,
    gradient_accumulation_steps=GRAD_ACCUM,
    warmup_ratio=WARMUP_RATIO,
    learning_rate=LEARNING_RATE,
    embedding_learning_rate=EMBEDDING_LEARNING_RATE,
    lr_scheduler_type=LR_SCHEDULER,
    fp16=_use_fp16,
    bf16=_use_bf16,
    optim="adamw_8bit",
    weight_decay=WEIGHT_DECAY,
    logging_steps=LOGGING_STEPS,
    eval_strategy="steps",
    eval_steps=EVAL_STEPS,
    per_device_eval_batch_size=1,
    prediction_loss_only=True,  # 248k-vocab logits at eval OOMed T4 (~6.8 GiB)
    save_strategy="steps",
    save_steps=SAVE_STEPS,
    save_total_limit=SAVE_TOTAL_LIMIT,
    save_only_model=SAVE_ONLY_MODEL,
    load_best_model_at_end=LOAD_BEST_MODEL_AT_END and isinstance(eval_sets, dict) and (
        _best_bucket in eval_sets if _best_bucket else "spurgeon" in eval_sets
    ),
    metric_for_best_model=METRIC_FOR_BEST if LOAD_BEST_MODEL_AT_END else None,
    greater_is_better=False,
    output_dir=OUTPUT_DIR,
    seed=SEED,
    max_seq_length=MAX_SEQ_LENGTH,
    packing=False,  # Qwen3.5 Processor + GatedDeltaNet — native packing unsupported
    report_to=REPORT_TO,
)

if MAX_STEPS is not None:
    training_args.max_steps = int(MAX_STEPS)
else:
    training_args.num_train_epochs = float(NUM_TRAIN_EPOCHS)
print(f"  trainer_fp16={training_args.fp16} trainer_bf16={training_args.bf16} train_embed={TRAIN_EMBEDDINGS}")


class QuietEarlyStoppingCallback(EarlyStoppingCallback):
    """HF EarlyStoppingCallback warns on every non-Spurgeon eval dict (P1 log spam).
    Same patience logic; silent when the current logs lack metric_for_best_model."""

    def on_evaluate(self, args, state, control, metrics, **kwargs):
        metric_to_check = args.metric_for_best_model
        if not metric_to_check.startswith("eval_"):
            metric_to_check = f"eval_{metric_to_check}"
        metric_value = metrics.get(metric_to_check) if metrics else None
        if metric_value is None:
            return
        self.check_metric_value(args, state, control, metric_value)
        if self.early_stopping_patience_counter >= self.early_stopping_patience:
            control.should_training_stop = True


class _PrintEvalKeysOnce(TrainerCallback):
    def __init__(self):
        self._printed = False

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if self._printed or not metrics:
            return
        keys = sorted(k for k in metrics if str(k).startswith("eval_"))
        print(f"Eval metric keys step={state.global_step}: {keys}")
        if args.metric_for_best_model in (metrics or {}):
            print(f"  {args.metric_for_best_model}={metrics[args.metric_for_best_model]!r} (early-stop key present)")
            self._printed = True


class AbortIfSpurgeonRisesCallback(TrainerCallback):
    """Stop at step 50 if eval_spurgeon_loss rose vs step 25 (credit guard)."""

    def __init__(self, abort_step=50, ref_step=25):
        self.abort_step = int(abort_step)
        self.ref_step = int(ref_step)

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if self.abort_step <= 0:
            return
        step = int(getattr(state, "global_step", 0) or 0)
        if step != self.abort_step:
            return
        history = list(getattr(state, "log_history", None) or [])
        if metrics and metrics.get("eval_spurgeon_loss") is not None:
            history = history + [
                {"step": step, "eval_spurgeon_loss": metrics["eval_spurgeon_loss"]}
            ]
        now = spurgeon_loss_at_step(history, self.abort_step)
        ref = spurgeon_loss_at_step(history, self.ref_step)
        if now is None or ref is None:
            print(
                f"WARNING: abort-at-{{self.abort_step}} skipped "
                f"(eval_spurgeon_loss missing at step {{self.ref_step}} or {{self.abort_step}}; "
                f"ref={{ref}} now={{now}})"
            )
            return
        if spurgeon_rose_by_step(history, now_step=self.abort_step, ref_step=self.ref_step):
            print(
                f"ABORT: eval_spurgeon rose by step {{self.abort_step}} "
                f"({{ref:.6f}} @ {{self.ref_step}} -> {{now:.6f}} @ {{self.abort_step}})"
            )
            control.should_training_stop = True
        else:
            print(
                f"abort-at-{{self.abort_step}}: eval_spurgeon did not rise "
                f"({{ref:.6f}} @ {{self.ref_step}} -> {{now:.6f}} @ {{self.abort_step}})"
            )


class CompositeFlatEarlyStoppingCallback(TrainerCallback):
    """Halt when all composite metrics are flat within epsilon for patience evals."""

    def __init__(self, metric_keys, patience=2, epsilon=0.005, min_steps=0):
        self.metric_keys = list(metric_keys)
        self.patience = int(patience)
        self.epsilon = float(epsilon)
        self.min_steps = int(min_steps)
        self.bests = {}
        self.flat_streak = 0

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        step = int(getattr(state, "global_step", 0) or 0)
        if step < self.min_steps:
            return
        if not metrics:
            return
        self.bests, self.flat_streak, any_improved = update_composite_flat_state(
            self.bests,
            self.flat_streak,
            metrics,
            self.metric_keys,
            self.epsilon,
        )
        if any_improved:
            return
        if composite_should_halt(self.flat_streak, self.patience):
            print(
                f"COMPOSITE EARLY-STOP @ step {{step}}: "
                f"metrics={{self.metric_keys}} flat streak={{self.flat_streak}} "
                f"epsilon={{self.epsilon}} bests={{self.bests}}"
            )
            control.should_training_stop = True


_callbacks = [_PrintEvalKeysOnce()]
if USE_COMPOSITE_EARLY_STOP:
    _callbacks.append(
        CompositeFlatEarlyStoppingCallback(
            metric_keys=COMPOSITE_EARLY_STOP_METRICS,
            patience=int(EARLY_STOPPING_PATIENCE),
            epsilon=float(EARLY_STOP_EPSILON),
            min_steps=int(EARLY_STOP_MIN_STEPS),
        )
    )
elif LOAD_BEST_MODEL_AT_END and EARLY_STOPPING_PATIENCE:
    _callbacks.append(QuietEarlyStoppingCallback(early_stopping_patience=int(EARLY_STOPPING_PATIENCE)))
if ABORT_SPURGEON_STEP:
    _callbacks.append(
        AbortIfSpurgeonRisesCallback(
            abort_step=ABORT_SPURGEON_STEP,
            ref_step=ABORT_SPURGEON_REF_STEP,
        )
    )

# Seq2Seq collator preserves precomputed labels (incl. post-EOS -100).
# Transformers DataCollatorForLanguageModeling clones input_ids → labels and,
# when pad_token_id == eos_token_id (Qwen), also zeros EOS CE. Do not use it.
_pack_collator = None
if MANUAL_PACK:
    _pack_collator = DataCollatorForSeq2Seq(
        train_tok,
        padding=True,
        label_pad_token_id=-100,
    )

trainer = UnslothTrainer(
    model=model,
    tokenizer=train_tok,
    train_dataset=train_ds,
    eval_dataset=eval_sets if eval_sets else None,
    args=training_args,
    dataset_text_field="text" if not MANUAL_PACK else None,
    data_collator=_pack_collator,
    callbacks=_callbacks or None,
)

print("Trainer ready:", type(trainer).__name__)
print(f"  manual_pack={MANUAL_PACK}  packing=False  packing_mode={PACKING_MODE}")
print(f"  data_collator={type(trainer.data_collator).__name__}")
print(f"  train size={len(train_ds)}  raw_docs={raw_doc_count}")
print(f"  eval keys={list(eval_sets) if isinstance(eval_sets, dict) else type(eval_sets)}")
print(f"  metric_for_best={METRIC_FOR_BEST}  early_stopping_patience={EARLY_STOPPING_PATIENCE}")
print(f"  abort_spurgeon_step={ABORT_SPURGEON_STEP} ref_step={ABORT_SPURGEON_REF_STEP}")
print(f"  early_stop_min_steps={EARLY_STOP_MIN_STEPS} composite_stop={USE_COMPOSITE_EARLY_STOP}")
print(f"  load_best_model_at_end={training_args.load_best_model_at_end}")'''
        ),
        md("## 5. Diagnostics D1 (pack gate) + D2 (EOS)"),
        code(
            '''import numpy as np

# D1 — where did my tokens go?
tds = trainer.train_dataset
n = len(tds)

def _row_len(i):
    row = tds[i]
    if "input_ids" in row:
        return len(row["input_ids"])
    if "text" in row:
        return len(ids_for_text(train_tok, row["text"], add_special_tokens=False))
    return -1

step = max(1, n // 200)
lens = [_row_len(i) for i in range(0, n, step)]
lens = [x for x in lens if x > 0]
d1 = {
    "manual_pack": MANUAL_PACK,
    "packing_mode": PACKING_MODE if MANUAL_PACK else "native_or_text",
    "raw_doc_count": raw_doc_count,
    "packed_or_raw_rows": n,
    "sampled": len(lens),
    "row_token_len_min": int(min(lens)) if lens else None,
    "row_token_len_p50": int(np.median(lens)) if lens else None,
    "row_token_len_max": int(max(lens)) if lens else None,
    "tokens_per_epoch_est": int(n * float(np.mean(lens))) if lens else None,
}
print("D1 truncation diagnostic:", json.dumps(d1, indent=2))
if raw_doc_count:
    print(f"D1 row ratio packed/raw={n / float(raw_doc_count):.3f}  ({n} rows / {raw_doc_count} docs)")

# D1 gates: one_doc_padded has n ≈ docs (or more if long docs split). Isolated may concat.
# Still catch "packing never tokenized" and a broken splitter.
if MANUAL_PACK:
    first = tds[0] if n else {}
    if "input_ids" not in first or "labels" not in first:
        raise RuntimeError(
            "D1 GATE FAIL: packed train rows missing input_ids/labels — manual pack did not tokenize."
        )
    if lens and max(lens) > MAX_SEQ_LENGTH:
        raise RuntimeError(
            f"D1 GATE FAIL: packed row length {max(lens)} > MAX_SEQ_LENGTH={MAX_SEQ_LENGTH}."
        )
    if raw_doc_count and n > raw_doc_count * 3:
        raise RuntimeError(
            f"D1 GATE FAIL: {n} packed rows from {raw_doc_count} docs — splitter exploded."
        )
    if PACKING_MODE == "one_doc_padded" and raw_doc_count and n < raw_doc_count * 0.90:
        raise RuntimeError(
            f"D1 GATE FAIL: one_doc_padded produced {n} rows from {raw_doc_count} docs "
            "(expected rows >= nonempty docs — concat or drop?)."
        )
    if raw_doc_count and n >= raw_doc_count * 0.95:
        print(
            f"D1 NOTE: packed rows ≈ raw docs (mode={PACKING_MODE}) — expected for "
            "one_doc_padded / isolated pack (stream pack used to drop ~11% by splicing). "
            "Native packing=True skip is already caught by missing input_ids/labels."
        )

manifest_tokens = None
if os.path.exists(MANIFEST_PATH):
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as _mf:
            _mm = json.load(_mf)
        vt = (_mm.get("verified_tokens") or {}).get("estimated_tokens")
        manifest_tokens = vt or _mm.get("train_approx_tokens")
    except Exception:
        pass
if manifest_tokens and d1["tokens_per_epoch_est"]:
    ratio = d1["tokens_per_epoch_est"] / float(manifest_tokens)
    print(f"D1 corpus coverage: {ratio:.2%} of manifest tokens ({manifest_tokens:,})")
    if ratio < 0.85:
        print("WARNING: tokens_per_epoch_est << manifest — check chunking or tokenization path.")

# D2 — EOS boundaries (first 5 rows)
eos = train_tok.eos_token_id
d2_counts = []
for i in range(min(5, n)):
    row = tds[i]
    if "input_ids" in row:
        ids = list(row["input_ids"])
    else:
        ids = ids_for_text(train_tok, row["text"], add_special_tokens=False)
    d2_counts.append(ids.count(eos))
print("D2 EOS counts (first 5):", d2_counts)
if d2_counts and max(d2_counts) == 0:
    print("WARNING: no EOS found in packed rows — check build_manual_packed_dataset.")

def _post_eos_mask_stats(ids, labs, eos_id, ignore, pad_id=None, attn=None):
    n_bound = n_masked = 0
    for j in range(1, min(len(ids), len(labs))):
        if ids[j - 1] != eos_id:
            continue
        if attn is not None and j < len(attn) and not attn[j]:
            continue
        if pad_id is not None and ids[j] == pad_id:
            continue
        n_bound += 1
        if labs[j] == ignore:
            n_masked += 1
    return n_bound, n_masked

def _content_eos_count(ids, attn, eos_id):
    if attn is None or len(attn) != len(ids):
        attn = [1] * len(ids)
    return sum(1 for t, m in zip(ids, attn) if m and t == eos_id)

# D2 isolation — one_doc_padded must not concat; isolated post-EOS must be ignore_index
_ignore = -100
_n_bound = 0
_n_bound_masked = 0
_n_multi = 0
_probe_multi = None
_probe_ignore = None
if MANUAL_PACK and eos is not None:
    for i in range(n):
        row = tds[i]
        if "input_ids" not in row or "labels" not in row:
            continue
        ids = list(row["input_ids"])
        labs = list(row["labels"])
        attn = list(row.get("attention_mask") or [1] * len(ids))
        if _content_eos_count(ids, attn, eos) >= 2:
            _n_multi += 1
            if _probe_multi is None:
                _probe_multi = {
                    "input_ids": ids,
                    "attention_mask": attn,
                    "labels": labs,
                }
        if _probe_ignore is None and any(l == _ignore for l in labs):
            _probe_ignore = {
                "input_ids": ids,
                "attention_mask": attn,
                "labels": labs,
            }
        b, m = _post_eos_mask_stats(ids, labs, eos, _ignore, attn=attn)
        _n_bound += b
        _n_bound_masked += m
    print(
        f"D2 isolation (all {n} rows): mode={PACKING_MODE} multi_doc_rows={_n_multi} "
        f"post_eos_labels_masked={_n_bound_masked}/{_n_bound}"
    )
    if PACKING_MODE == "one_doc_padded" and _n_multi:
        raise RuntimeError(
            f"D2 GATE FAIL: one_doc_padded still has {_n_multi} multi-doc rows "
            "(two content EOS in one row) — GDN leak."
        )
    if _n_bound == 0:
        print(
            "D2 NOTE: no post-EOS token in packed rows — isolation gate did not fire "
            "(single-doc rows / EOS only at row end). Expected for one_doc_padded."
        )
    if _n_bound and _n_bound_masked < _n_bound:
        raise RuntimeError(
            f"D2 GATE FAIL: {_n_bound - _n_bound_masked}/{_n_bound} post-EOS labels "
            "are not ignore_index — cross-document CE is still on."
        )
    # Collator must not clone input_ids over labels (would undo ignore_index).
    _probe = _probe_multi if _probe_multi is not None else _probe_ignore
    if _probe is not None:
        try:
            batch = trainer.data_collator([_probe])
            _c_ids = batch["input_ids"][0].tolist()
            _c_labs = batch["labels"][0].tolist()
            _pad = getattr(train_tok, "pad_token_id", None)
            orig_ignore = sum(1 for l in _probe["labels"] if l == _ignore)
            coll_ignore = sum(1 for l in _c_labs if l == _ignore)
            print(
                f"D2 collator ignore_index: orig={orig_ignore} collated={coll_ignore} "
                f"collator={type(trainer.data_collator).__name__}"
            )
            if _probe_multi is not None:
                _cb, _cm = _post_eos_mask_stats(_c_ids, _c_labs, eos, _ignore, pad_id=_pad)
                print(f"D2 collator isolation: post_eos_masked={_cm}/{_cb}")
                if _cb and _cm < _cb:
                    raise RuntimeError(
                        f"D2 GATE FAIL: collator {type(trainer.data_collator).__name__} "
                        f"wiped {_cb - _cm}/{_cb} post-EOS ignore_index labels."
                    )
            if coll_ignore < orig_ignore:
                raise RuntimeError(
                    f"D2 GATE FAIL: collator {type(trainer.data_collator).__name__} "
                    f"dropped ignore_index labels ({coll_ignore} < {orig_ignore})."
                )
        except RuntimeError:
            raise
        except Exception as e:
            print("D2 NOTE: collator isolation check skipped:", type(e).__name__, e)
'''
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
_du = shutil.disk_usage(WORK_ROOT)
print(f"disk {WORK_ROOT} free={_du.free/1e9:.2f} GB used={_du.used/1e9:.2f} GB")
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
print(f"Wall time: {elapsed/3600:.2f} h")
# Operator gate: if eval_spurgeon rose after first eval, do not just raise MAX_STEPS — halve LR next run.
_sp = []
for row in getattr(trainer.state, "log_history", []) or []:
    if "eval_spurgeon_loss" in row:
        _sp.append((row.get("step"), row["eval_spurgeon_loss"]))
if _sp:
    print("eval_spurgeon_loss by step:", _sp)
    if len(_sp) >= 2 and _sp[-1][1] > _sp[0][1]:
        print(
            f"NOTE: eval_spurgeon_loss rose vs first eval (lr={LEARNING_RATE}). "
            "Stop. Do not C. Do not another LR-only B. Next is still one-doc padded / Ampere bf16."
        )'''
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
    "manual_pack": MANUAL_PACK if "MANUAL_PACK" in dir() else None,
    "packing_mode": PACKING_MODE if ("MANUAL_PACK" in dir() and MANUAL_PACK) else "native_or_text",
    "pad_to_max": PAD_TO_MAX if "PAD_TO_MAX" in dir() else None,
    "gpu_profile": GPU_PROFILE if "GPU_PROFILE" in dir() else None,
    "load_in_4bit": LOAD_IN_4BIT if "LOAD_IN_4BIT" in dir() else None,
    "lora_gdn": LORA_GDN if "LORA_GDN" in dir() else None,
    "raw_doc_count": raw_doc_count if "raw_doc_count" in dir() else None,
    "metric_for_best": METRIC_FOR_BEST,
    "early_stopping_patience": EARLY_STOPPING_PATIENCE,
    "requirements_lock": _layout["requirements_lock"],
    "offload_dir": OFFLOAD_DIR,
    "work_root": WORK_ROOT,
    "notes": "SOTA CPT — one_doc_padded rows, GDN LoRA on padded path. GPU_PROFILE auto (t4 4-bit / ampere bf16 sm_80+). Do not C/merge until §5 PPL. Do not resume Kaggle 4-bit ckpts on Ampere.",
}

print(f"Saving adapter to {ADAPTER_OUT} ...")
model.save_pretrained(ADAPTER_OUT)
tokenizer.save_pretrained(ADAPTER_OUT)

best_ckpt = getattr(trainer.state, "best_model_checkpoint", None)
print("trainer.state.best_global_step", getattr(trainer.state, "best_global_step", None))
print("trainer.state.best_model_checkpoint", best_ckpt)
print("trainer.state.best_metric", getattr(trainer.state, "best_metric", None))
_lora_w = os.path.join(ADAPTER_OUT, "adapter_model.safetensors")
_lora_hash = _sha256_file(_lora_w)
print("theology_cpt_lora sha256", _lora_hash)
if best_ckpt:
    _best_w = os.path.join(best_ckpt, "adapter_model.safetensors")
    _best_hash = _sha256_file(_best_w)
    print("best_ckpt sha256", _best_hash)
    if _lora_hash and _best_hash and _lora_hash != _best_hash:
        print("WARNING: saved LoRA SHA256 != best checkpoint — C may score the wrong file")
    elif _lora_hash and _best_hash:
        print("OK: saved LoRA matches best_model_checkpoint")

run_config["best_global_step"] = getattr(trainer.state, "best_global_step", None)
run_config["best_model_checkpoint"] = best_ckpt
run_config["best_metric"] = getattr(trainer.state, "best_metric", None)
run_config["adapter_sha256"] = _lora_hash
run_config["best_ckpt_sha256"] = _sha256_file(os.path.join(best_ckpt, "adapter_model.safetensors")) if best_ckpt else None
run_config["train_embeddings"] = TRAIN_EMBEDDINGS
run_config["eval_docs_per_bucket"] = EVAL_DOCS_PER_BUCKET
run_config["packed_epoch_steps"] = PACKED_EPOCH_STEPS if "PACKED_EPOCH_STEPS" in dir() else None
run_config["abort_spurgeon_step"] = ABORT_SPURGEON_STEP if "ABORT_SPURGEON_STEP" in dir() else 50
run_config["abort_spurgeon_ref_step"] = ABORT_SPURGEON_REF_STEP if "ABORT_SPURGEON_REF_STEP" in dir() else 25
run_config["cpt_run_mode"] = CPT_RUN_MODE if "CPT_RUN_MODE" in dir() else "fresh"
run_config["init_adapter_path"] = INIT_ADAPTER_PATH if "INIT_ADAPTER_PATH" in dir() else None
run_config["early_stop_min_steps"] = EARLY_STOP_MIN_STEPS if "EARLY_STOP_MIN_STEPS" in dir() else 0
run_config["early_stop_epsilon"] = EARLY_STOP_EPSILON if "EARLY_STOP_EPSILON" in dir() else None
run_config["use_composite_early_stop"] = USE_COMPOSITE_EARLY_STOP if "USE_COMPOSITE_EARLY_STOP" in dir() else False
run_config["composite_early_stop_metrics"] = (
    COMPOSITE_EARLY_STOP_METRICS if "COMPOSITE_EARLY_STOP_METRICS" in dir() else None
)
run_config["eval_buckets_during_train"] = (
    EVAL_BUCKETS_DURING_TRAIN if "EVAL_BUCKETS_DURING_TRAIN" in dir() else None
)

with open(RUN_CONFIG_OUT, "w", encoding="utf-8") as f:
    json.dump(run_config, f, indent=2)

print("Saved:")
print(" ", ADAPTER_OUT)
print(" ", RUN_CONFIG_OUT)
print("Checkpoints:", OUTPUT_DIR)'''
        ),
    ]
    return cells


def _strip_ipython_magics(src: str) -> str:
    out = []
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("!") or stripped.startswith("%"):
            out.append("# skipped notebook magic: " + stripped)
            continue
        out.append(line)
    return "\n".join(out)


def emit_train_cpt_sota(path: Path, cells: list[dict]) -> None:
    header = f'''#!/usr/bin/env python3
"""SOTA CPT B training — generated from _gen_sota_notebooks.py. Do not hand-edit.

Run on a GPU pod (Runpod RTX 4090 / L4) after copying the HF dataset:

    export CPT_WORK_ROOT=/workspace
    export CPT_DATA_ROOT=/workspace
    python continued_pretrain/scripts/train_cpt_sota.py --install   # first boot
    python continued_pretrain/scripts/train_cpt_sota.py

Do not resume Kaggle T4 4-bit checkpoints onto Ampere bf16.
Empty PREV_RUN_CHECKPOINT= forces a fresh run.
See continued_pretrain/RUNPOD_RUNBOOK.md.
"""
import argparse
import subprocess
import sys

UNSLOTH_PIP_SPEC = "{UNSLOTH_PIP_SPEC_RUNPOD}"


def _parse_and_maybe_install():
    parser = argparse.ArgumentParser(description="SOTA CPT training (B)")
    parser.add_argument(
        "--install",
        action="store_true",
        help="pip install Unsloth (non-Kaggle extra; skip if already on the pod)",
    )
    args, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    if args.install:
        print("Installing", UNSLOTH_PIP_SPEC)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "--break-system-packages",
                UNSLOTH_PIP_SPEC,
            ]
        )
        print("Install done. Re-run without --install to train.")
        raise SystemExit(0)


_parse_and_maybe_install()

# --- generated B cells (source of truth: _gen_sota_notebooks.py) ---
'''
    chunks = [header.rstrip(), ""]
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source") or [])
        chunks.append(_strip_ipython_magics(src))
        chunks.append("")
    path.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def _is_unsloth_install_cell(src: str) -> bool:
    if "pip" not in src:
        return False
    return "_KAGGLE_SPEC" in src or "_RUNPOD_SPEC" in src or "unsloth[" in src


def emit_eval_cpt_sota(path: Path, cells: list[dict]) -> None:
    header = f'''#!/usr/bin/env python3
"""SOTA CPT C eval — generated from _gen_sota_notebooks.py. Do not hand-edit.

Run on a GPU pod (Runpod RTX 4090) after copying LoRA + holdouts + MCQ:

    export CPT_WORK_ROOT=/workspace
    export CPT_DATA_ROOT=/workspace
    export HF_HOME=/workspace/hf_home
    export PYTHONUNBUFFERED=1
    export EXPECTED_ADAPTER_SHA256={RUNPOD_CPT_ADAPTER_SHA256}
    python3 -u continued_pretrain/scripts/eval_cpt_sota.py --preflight
    python3 -u continued_pretrain/scripts/eval_cpt_sota.py --install
    python3 -u continued_pretrain/scripts/eval_cpt_sota.py

Ampere bf16 only for the Runpod embed-FT adapter. Do not C this LoRA on T4 4-bit.
See continued_pretrain/RUNPOD_RUNBOOK.md.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

UNSLOTH_PIP_SPEC = "{UNSLOTH_PIP_SPEC_RUNPOD}"
EXPECTED_ADAPTER_SHA256_DEFAULT = "{RUNPOD_CPT_ADAPTER_SHA256}"


def _sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _preflight():
    """Fail before pip/HF download. Uses stdlib + image torch (no Unsloth)."""
    os.environ.setdefault("EXPECTED_ADAPTER_SHA256", EXPECTED_ADAPTER_SHA256_DEFAULT)
    os.environ.setdefault("REQUIRE_AMPERE", "1")
    work = (os.environ.get("CPT_WORK_ROOT") or "").strip()
    if not work:
        work = "/workspace" if os.path.isdir("/workspace") else os.getcwd()
    work = os.path.abspath(work)
    hf_home = (os.environ.get("HF_HOME") or "").strip() or os.path.join(work, "hf_home")
    os.makedirs(hf_home, exist_ok=True)
    adapter = os.path.join(work, "theology_cpt_lora")
    weights = os.path.join(adapter, "adapter_model.safetensors")
    cfg_path = os.path.join(adapter, "adapter_config.json")
    holdouts = os.path.join(work, "theology_holdouts")
    print("preflight WORK_ROOT", work)
    print("preflight HF_HOME", hf_home)
    if not os.path.isfile(cfg_path) or not os.path.isfile(weights):
        raise SystemExit(
            "preflight FAIL: expected "
            + adapter
            + "/adapter_config.json and adapter_model.safetensors"
        )
    want = (os.environ.get("EXPECTED_ADAPTER_SHA256") or EXPECTED_ADAPTER_SHA256_DEFAULT).strip()
    got = _sha256_file(weights)
    print("preflight adapter SHA256", got)
    if want.lower() not in ("", "none", "skip") and got.lower() != want.lower():
        raise SystemExit("preflight FAIL: SHA256 mismatch want " + want)
    with open(cfg_path, encoding="utf-8") as handle:
        cfg = json.load(handle)
    mts = cfg.get("modules_to_save") or []
    print("preflight modules_to_save", mts)
    for name in ("spurgeon", "puritan", "confession", "general"):
        bucket = os.path.join(holdouts, name)
        if not (
            os.path.isfile(os.path.join(bucket, "dataset_info.json"))
            or os.path.isfile(os.path.join(bucket, "state.json"))
        ):
            raise SystemExit("preflight FAIL: missing holdout " + bucket)
    print("preflight holdouts OK", holdouts)
    mcq = os.path.join(work, "catechism_mcq.json")
    if not os.path.isfile(mcq):
        print("preflight NOTE: no catechism_mcq.json at", mcq, "(MCQ will skip)")
    else:
        print("preflight MCQ", mcq)
    free = shutil.disk_usage(hf_home).free
    print("preflight disk_free_gb", round(free / (1024 ** 3), 1))
    if free < 20 * 1024 ** 3:
        raise SystemExit("preflight FAIL: need >=20 GB free on HF_HOME")
    try:
        import torch
    except ImportError as exc:
        raise SystemExit("preflight FAIL: torch missing (use official PyTorch image)") from exc
    if not torch.cuda.is_available():
        raise SystemExit("preflight FAIL: CUDA not available")
    name = torch.cuda.get_device_name(0)
    major, minor = torch.cuda.get_device_capability(0)
    print("preflight GPU", name, "sm", f"{{major}}.{{minor}}")
    if major < 8:
        raise SystemExit(
            "preflight FAIL: need sm_80+ Ampere/Ada for this embed-FT adapter, got "
            + name
        )
    x = torch.zeros(1, device="cuda")
    x.fill_(1.0)
    print("preflight CUDA smoke", float(x.item()))
    print("Preflight OK")


def _parse_and_maybe_install():
    os.environ.setdefault("EXPECTED_ADAPTER_SHA256", EXPECTED_ADAPTER_SHA256_DEFAULT)
    os.environ.setdefault("REQUIRE_AMPERE", "1")
    parser = argparse.ArgumentParser(description="SOTA CPT eval (C)")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="check GPU/SHA256/holdouts/disk then exit (no Unsloth)",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="pip install Unsloth (non-Kaggle extra; skip if already on the pod)",
    )
    args, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    if args.preflight:
        _preflight()
        if not args.install:
            print("Preflight OK. Re-run without --preflight to eval (or pass --install).")
            raise SystemExit(0)
    if args.install:
        print("Installing", UNSLOTH_PIP_SPEC)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "--break-system-packages",
                UNSLOTH_PIP_SPEC,
            ]
        )
        print("Install done. Re-run without --install to eval.")
        raise SystemExit(0)


_parse_and_maybe_install()

# --- generated C cells (source of truth: _gen_sota_notebooks.py) ---
'''
    chunks = [header.rstrip(), ""]
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source") or [])
        if _is_unsloth_install_cell(src):
            chunks.append("# skipped notebook Unsloth install cell (use --install)")
            chunks.append("")
            continue
        chunks.append(_strip_ipython_magics(src))
        chunks.append("")
    path.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def gen_b_training_sota(path: Path) -> None:
    cells = build_b_training_cells()
    write_nb(path, cells)
    emit_train_cpt_sota(Path(__file__).resolve().parent / "train_cpt_sota.py", cells)


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

CORPUS_ROOT = "/kaggle/input/theology-cpt-corpus"
if not os.path.exists(CORPUS_ROOT):
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

**C v4 already scored B v6 `checkpoint-25`** (SHA256 match with that run's `theology_cpt_lora`). Do **not**
set `ADAPTER_OVERRIDE` to that path. Leave override `None` so C loads `$WORK_ROOT/theology_cpt_lora`.
`SCORE_LAST_CHECKPOINT=False` unless `checkpoints_sota/checkpoint-*` is on the box.

Runpod Ampere bf16 + embed-FT adapter SHA256 `{RUNPOD_CPT_ADAPTER_SHA256}`. Do not C that LoRA in 4-bit.

**Does not replace** `C_eval_and_merge.ipynb`.
"""
        ),
        md("## 0. Runtime helpers (Kaggle + Runpod)"),
        code(_cpt_runtime_source()),
        md("## 1. Install"),
        code(
            "import os, subprocess, sys\n"
            f"_KAGGLE_SPEC = {UNSLOTH_PIP_SPEC_KAGGLE!r}\n"
            f"_RUNPOD_SPEC = {UNSLOTH_PIP_SPEC_RUNPOD!r}\n"
            "_spec = _KAGGLE_SPEC if os.path.isdir('/kaggle/working') else _RUNPOD_SPEC\n"
            "print('Installing', _spec)\n"
            "_cmd = [sys.executable, '-m', 'pip', 'install', '-q']\n"
            "if not os.path.isdir('/kaggle/working'):\n"
            "    _cmd.append('--break-system-packages')\n"
            "_cmd.append(_spec)\n"
            "subprocess.check_call(_cmd)\n"
        ),
        md("## 1b. GPU sanity"),
        code(
            '''import torch
assert torch.cuda.is_available(), "Enable GPU accelerator"
name = torch.cuda.get_device_name(0)
major, minor = torch.cuda.get_device_capability(0)
print("GPU:", name, "| capability:", f"{major}.{minor}", "| torch:", torch.__version__)
if major < 7:
    raise RuntimeError(
        f"Incompatible GPU {name} (sm_{major}{minor}). "
        "Need sm_70+ (T4) or sm_80+ (RTX 4090 / L4 / A100)."
    )
x = torch.zeros(1, device="cuda"); x.fill_(1.0)
print("CUDA smoke OK:", float(x.item()))
'''
        ),
        md("## 2. Config"),
        code(
            '''import os
import json
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

MODEL_NAME = "'''
            + FLAGSHIP_MODEL
            + '''"  # must match training base
MAX_SEQ_LENGTH = 2048
_cc_major = None
try:
    import torch as _torch_cfg
    if _torch_cfg.cuda.is_available():
        _cc_major = _torch_cfg.cuda.get_device_capability(0)[0]
except Exception:
    _cc_major = None
GPU_PROFILE = resolve_gpu_profile(_cc_major)
LOAD_IN_4BIT = GPU_PROFILE == "t4"

WORK_ROOT = resolve_work_root()
os.makedirs(WORK_ROOT, exist_ok=True)
_layout = layout_paths(WORK_ROOT)
os.environ["HF_HOME"] = _layout["hf_home"]
os.makedirs(os.environ["HF_HOME"], exist_ok=True)
print("HF_HOME", os.environ["HF_HOME"])
_kaggle_input = KAGGLE_INPUT if os.path.isdir(KAGGLE_INPUT) else None

ADAPTER_OVERRIDE = None  # after a complete B only; do NOT set to B v6 checkpoint-25 (C v4 already scored it)
_preferred = local_lora_dir(WORK_ROOT)
ADAPTER_PATH = ADAPTER_OVERRIDE or _preferred or find_adapter(adapter_search_roots(WORK_ROOT, kaggle_input=_kaggle_input))
if ADAPTER_PATH is None:
    print("ERROR: CPT adapter not found under WORK_ROOT or Kaggle input.")
    print("  Set CPT_WORK_ROOT to the B output dir (contains theology_cpt_lora/).")
    _scan = WORK_ROOT if os.path.isdir(WORK_ROOT) else _kaggle_input
    if _scan and os.path.isdir(_scan):
        print("Scanned:", _scan)
        for root, dirs, files in os.walk(_scan):
            if "hf_home" in root or "unsloth_compiled_cache" in root:
                continue
            depth = root.count(os.sep) - _scan.count(os.sep)
            if depth <= 4:
                print(" ", root, "dirs=", dirs[:10], "files=", files[:8])
    raise FileNotFoundError(
        "CPT adapter not found. Kaggle: mount theology-cpt-v2-b-training-sota. "
        "Runpod: set CPT_WORK_ROOT to the volume with theology_cpt_lora/."
    )
print("Using ADAPTER_PATH", ADAPTER_PATH, "(override)" if ADAPTER_OVERRIDE else "(auto)")
if ADAPTER_OVERRIDE and "checkpoint-25" in str(ADAPTER_OVERRIDE).replace("\\\\", "/"):
    print("WARNING: C v4 already scored B v6 checkpoint-25. Override is wasted unless this is a new B run.")

_acfg_path = os.path.join(ADAPTER_PATH, "adapter_config.json")
_acfg = json.load(open(_acfg_path, encoding="utf-8")) if os.path.isfile(_acfg_path) else {}
_mts = _acfg.get("modules_to_save") or []
print("adapter modules_to_save", _mts)
_require_ampere = (os.environ.get("REQUIRE_AMPERE") or "").strip().lower() in ("1", "true", "yes")
if _require_ampere and (GPU_PROFILE != "ampere" or LOAD_IN_4BIT):
    raise RuntimeError(
        f"REQUIRE_AMPERE=1 but gpu_profile={GPU_PROFILE} load_in_4bit={LOAD_IN_4BIT}. "
        "This Runpod embed-FT adapter must be scored Ampere bf16."
    )
if _mts and LOAD_IN_4BIT:
    raise RuntimeError(
        "embed-FT adapter (modules_to_save) cannot be scored in 4-bit. Use Ampere bf16."
    )
_weights = os.path.join(ADAPTER_PATH, "adapter_model.safetensors")
EXPECTED_ADAPTER_SHA256 = (os.environ.get("EXPECTED_ADAPTER_SHA256") or "").strip()
if os.path.isfile(_weights):
    _got_sha = sha256_file(_weights)
    print("adapter SHA256", _got_sha)
    if EXPECTED_ADAPTER_SHA256.lower() not in ("", "none", "skip") and _got_sha.lower() != EXPECTED_ADAPTER_SHA256.lower():
        raise RuntimeError(
            f"adapter SHA256 mismatch: got {_got_sha} want {EXPECTED_ADAPTER_SHA256}"
        )
elif EXPECTED_ADAPTER_SHA256.lower() not in ("", "none", "skip"):
    raise FileNotFoundError("adapter_model.safetensors missing at " + _weights)

PHASE1_ADAPTER_PATH = None  # e.g. path to spurgeon_phase1_lora

HOLDOUT_ROOT = find_hf_holdout_root(
    holdout_search_roots(WORK_ROOT, kaggle_input=_kaggle_input),
    walk_roots=[p for p in (WORK_ROOT, _kaggle_input) if p],
)
_mcq_roots = [WORK_ROOT]
if _kaggle_input:
    _mcq_roots.append(_kaggle_input)
MCQ_PATH = find_file("catechism_mcq.json", _mcq_roots, prefer_substrings=("theology-cpt-corpus", "data"))
print("Using HOLDOUT_ROOT", HOLDOUT_ROOT)
print("Using MCQ_PATH", MCQ_PATH)
print("WORK_ROOT", WORK_ROOT, "gpu_profile", GPU_PROFILE, "load_in_4bit", LOAD_IN_4BIT)

if HOLDOUT_ROOT is None:
    raise FileNotFoundError(
        "theology_holdouts not found. Copy kaggle/a_output/theology_holdouts to $CPT_WORK_ROOT."
    )
for _bucket in ("spurgeon", "puritan", "confession", "general"):
    _bp = os.path.join(HOLDOUT_ROOT, _bucket)
    if not (
        os.path.isfile(os.path.join(_bp, "dataset_info.json"))
        or os.path.isfile(os.path.join(_bp, "state.json"))
    ):
        raise FileNotFoundError("missing holdout bucket " + _bp)

EVAL_BASE = True
EVAL_PHASE1 = False  # set True if PHASE1_ADAPTER_PATH is same base family
MAX_DOCS_PER_BUCKET = 50
PROBE_SEED = 42
RUN_MERGE = False  # set True only after §5 holdout PPL passes (MCQ alone is not enough)
SCORE_LAST_CHECKPOINT = False  # no checkpoints_sota in the Runpod LoRA-only copy

OUT_LORA = _layout["out_lora_final"]
OUT_MERGED = _layout["out_merged"]
OUT_METRICS = _layout["out_metrics"]

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
print("Loaded adapter from", ADAPTER_PATH)
print("tokenizer", type(tokenizer).__name__)


def text_tokenizer(tok):
    """Unwrap VL Processor → inner PreTrainedTokenizer (Qwen3.5 is multimodal)."""
    inner = tok
    for _ in range(4):
        nxt = getattr(inner, "tokenizer", None)
        if nxt is None or nxt is inner:
            break
        inner = nxt
    return inner


def ids_for_text(tok, text, add_special_tokens=False):
    """Tokenize text only. Never pass a positional string into a VL Processor
    (__call__ first arg is images → 'Incorrect image source' on sermons)."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    t = text_tokenizer(tok)
    if hasattr(t, "encode") and getattr(t, "image_processor", None) is None:
        ids = t.encode(text, add_special_tokens=add_special_tokens)
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], (list, tuple)):
            ids = list(ids[0])
        return [int(x) for x in ids]
    try:
        out = t(text=text, add_special_tokens=add_special_tokens)
    except TypeError:
        out = t(text, add_special_tokens=add_special_tokens)
    ids = out["input_ids"]
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], (list, tuple)):
        ids = list(ids[0])
    return [int(x) for x in ids]


def tokenize_text(tok, text, max_seq=None, add_special_tokens=False, device="cuda"):
    ids = ids_for_text(tok, text, add_special_tokens=add_special_tokens)
    if max_seq is not None:
        ids = ids[:max_seq]
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    return {"input_ids": input_ids, "attention_mask": torch.ones_like(input_ids)}


_tt = text_tokenizer(tokenizer)
print("text_tokenizer", type(_tt).__name__)
_smoke = ids_for_text(tokenizer, "Sermon 32 | The Necessity of Increased Faith")
print("text tokenize smoke n=", len(_smoke), "head=", _smoke[:8])
if len(_smoke) < 2:
    raise RuntimeError("text tokenize smoke failed")'''
        ),
        md("## 4. Multi-holdout PPL + Δ table"),
        code(
            '''def eval_ppl(model, tokenizer, dataset, max_docs=None, max_seq=MAX_SEQ_LENGTH):
    total_loss = 0.0
    total_tokens = 0
    n = len(dataset) if max_docs is None else min(len(dataset), max_docs)
    for i in range(n):
        text = dataset[i]["text"]
        inputs = tokenize_text(tokenizer, text, max_seq=max_seq, add_special_tokens=False)
        num_tokens = inputs["input_ids"].size(1)
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

def load_holdout(name):
    hf = os.path.join(HOLDOUT_ROOT, name)
    if os.path.isdir(hf) and (
        os.path.isfile(os.path.join(hf, "dataset_info.json"))
        or os.path.isfile(os.path.join(hf, "state.json"))
    ):
        return load_from_disk(hf)
    txt_candidates = [
        os.path.join(HOLDOUT_ROOT or "", f"{name}_holdout.txt") if HOLDOUT_ROOT else None,
        os.path.join(WORK_ROOT, "holdouts", f"{name}_holdout.txt"),
        f"/kaggle/input/datasets/rafaelvieira1/theology-cpt-corpus/holdouts/{name}_holdout.txt",
        f"/kaggle/input/theology-cpt-corpus/holdouts/{name}_holdout.txt",
    ]
    for txt in txt_candidates:
        if txt and os.path.isfile(txt):
            from datasets import Dataset
            text = open(txt, encoding="utf-8").read()
            docs = [d.strip() for d in text.split("<|endoftext|>") if len(d.strip()) > 200]
            if not docs and text.strip():
                docs = [text.strip()]
            print("holdout fallback txt", txt, "docs", len(docs))
            return Dataset.from_dict({"text": docs, "bucket": [name] * len(docs)})
    return None

for name in buckets:
    ds = load_holdout(name)
    if ds is None:
        print("skip missing", name)
        continue
    print(f"Evaluating v2 PPL on {name} ({len(ds)} docs)...")
    metrics["v2"][name] = eval_ppl(model, tokenizer, ds, max_docs=MAX_DOCS_PER_BUCKET)
    m = metrics["v2"][name]
    if m["ppl"] is not None:
        print(f"  v2 {name}: ppl={m['ppl']:.2f} loss={m['loss']:.4f} tokens={m['tokens']:,}")

def option_logprob(model, tok, prompt, option):
    full = tokenize_text(tok, prompt + " " + option, add_special_tokens=True)
    p_len = len(ids_for_text(tok, prompt, add_special_tokens=True))
    with torch.no_grad():
        logits = model(**full).logits[:, :-1].float()
    ids = full["input_ids"][:, 1:]
    lp = torch.log_softmax(logits, -1).gather(-1, ids.unsqueeze(-1)).squeeze(-1)
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

def load_mcq_sets():
    if not MCQ_PATH or not os.path.isfile(MCQ_PATH):
        return {}
    mcq = json.loads(open(MCQ_PATH, encoding="utf-8").read())
    return mcq.get("sets") or mcq

def score_model(label, model_name_or_path, also_mcq=False):
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
        ds = load_holdout(name)
        if ds is None:
            continue
        out[name] = eval_ppl(m, t, ds, max_docs=MAX_DOCS_PER_BUCKET)
        if out[name]["ppl"] is not None:
            print(f"  {label} {name}: ppl={out[name]['ppl']:.2f}")
    mcq_out = {}
    if also_mcq:
        sets = load_mcq_sets()
        for set_name, items in (sets or {}).items():
            if not items:
                continue
            acc = mcq_accuracy(m, t, items)
            mcq_out[f"{label}_{set_name}"] = acc
            print(f"MCQ {label} {set_name}: {acc:.1%} (n={len(items)})")
    del m
    torch.cuda.empty_cache()
    return out, mcq_out

metrics["mcq"] = {}
if EVAL_BASE:
    metrics["base"], _base_mcq = score_model("base", MODEL_NAME, also_mcq=True)
    metrics["mcq"].update(_base_mcq)
if EVAL_PHASE1 and PHASE1_ADAPTER_PATH:
    metrics["phase1"], _ = score_model("phase1", PHASE1_ADAPTER_PATH, also_mcq=False)

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

# Confirm load_best_model_at_end: PPL on highest checkpoint-* vs scored adapter (best LoRA).
metrics["last_ckpt"] = {}
metrics["delta_last_ckpt_vs_base_pct"] = {}

def _find_last_checkpoint(adapter_path):
    import re
    if not adapter_path:
        return None
    root = os.path.dirname(adapter_path)
    ckpt_root = os.path.join(root, "checkpoints_sota")
    if not os.path.isdir(ckpt_root):
        ckpt_root = os.path.join(os.path.dirname(root), "checkpoints_sota")
    if not os.path.isdir(ckpt_root):
        return None
    best_n, best_p = -1, None
    for name in os.listdir(ckpt_root):
        m = re.match(r"checkpoint-(\\d+)$", name)
        if not m:
            continue
        n = int(m.group(1))
        p = os.path.join(ckpt_root, name)
        if os.path.isfile(os.path.join(p, "adapter_config.json")) and n >= best_n:
            best_n, best_p = n, p
    if not best_p:
        return None
    if os.path.normpath(os.path.abspath(best_p)) == os.path.normpath(os.path.abspath(adapter_path)):
        print("Last checkpoint path equals scored adapter; skip duplicate PPL")
        return None
    return best_p

if SCORE_LAST_CHECKPOINT:
    last_p = _find_last_checkpoint(ADAPTER_PATH)
    print("SCORE_LAST_CHECKPOINT path:", last_p)
    if last_p:
        metrics["last_ckpt_path"] = last_p
        metrics["last_ckpt"], _ = score_model("last_ckpt", last_p)
        print("\\n=== last ckpt Δ PPL vs base ===")
        for name in buckets:
            b = (metrics["base"].get(name) or {}).get("ppl")
            v = (metrics["last_ckpt"].get(name) or {}).get("ppl")
            vb = (metrics["v2"].get(name) or {}).get("ppl")
            if b and v:
                pct = 100.0 * (v - b) / b
                metrics["delta_last_ckpt_vs_base_pct"][name] = round(pct, 2)
                note = ""
                if vb:
                    note = f"  (best LoRA {100.0 * (vb - b) / b:+.1f}%)"
                print(f"{name:12s}  last {pct:+7.1f}%{note}")
        print("Ship on best LoRA (v2) holdout PPL, not last ckpt, not MCQ.")

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
    inputs = tokenize_text(tokenizer, prompt, add_special_tokens=True)
    gen_kwargs = dict(max_new_tokens=max_new_tokens)
    if greedy:
        gen_kwargs.update(dict(do_sample=False))
    else:
        gen_kwargs.update(dict(do_sample=True, temperature=0.7, top_p=0.9))
    with torch.no_grad():
        out = model.generate(**inputs, **gen_kwargs)
    return text_tokenizer(tokenizer).decode(out[0], skip_special_tokens=True)


def _trigram_repeat_ratio(text):
    """Fraction of consecutive trigrams that repeat a prior trigram (RC6 signal)."""
    toks = text.split()
    if len(toks) < 12:
        return 0.0
    tris = [tuple(toks[i : i + 3]) for i in range(len(toks) - 2)]
    seen = set()
    repeats = 0
    for t in tris:
        if t in seen:
            repeats += 1
        else:
            seen.add(t)
    return repeats / max(len(tris), 1)


probe_log = {"greedy": {}, "sampled": {}, "repetition_warnings": []}
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
        entry = {"prompt": p, "completion": text}
        ratio = _trigram_repeat_ratio(text)
        if ratio >= 0.25:
            msg = f"PROBE WARNING: repetition loop ({label}, trigram_repeat={ratio:.2f})"
            print(msg)
            entry["repetition_ratio"] = round(ratio, 3)
            probe_log["repetition_warnings"].append({"label": label, "ratio": round(ratio, 3), "prompt": p[:80]})
        probe_log["greedy"][label].append(entry)

# Optional flavor (non-comparable)
print("\\n=== Style (sampled, flavor only) ===")
probe_log["sampled"]["style"] = []
for p in style_prompts[:1]:
    text = generate(p, greedy=False)
    print(text[:500])
    probe_log["sampled"]["style"].append({"prompt": p, "completion": text})

if probe_log["repetition_warnings"]:
    print(f"\\nRC6: {len(probe_log['repetition_warnings'])} greedy probe(s) showed repetition loops (informational).")

metrics["probes"] = probe_log
with open(OUT_METRICS, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)'''
        ),
        md("## 6. Catechism MCQ log-likelihood (WSC + Heidelberg)"),
        code(
            '''mcq_metrics = dict(metrics.get("mcq") or {})
sets = load_mcq_sets()
if sets:
    for set_name, items in sets.items():
        if not items:
            continue
        acc = mcq_accuracy(model, tokenizer, items)
        mcq_metrics[f"v2_{set_name}"] = acc
        print(f"MCQ v2 {set_name}: {acc:.1%} (n={len(items)})")
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
            '''if RUN_MERGE:
    print("Saving final LoRA to", OUT_LORA)
    model.save_pretrained(OUT_LORA)
    tokenizer.save_pretrained(OUT_LORA)
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
else:
    print("RUN_MERGE=False — skip LoRA resave and merge/GGUF (adapter already at", ADAPTER_PATH, ")")

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

**Ship on holdout PPL first.** MCQ / probes do not override a PPL FAIL. `RUN_MERGE=False` until §5 PPL passes.
Do not `ADAPTER_OVERRIDE` B v6 `checkpoint-25`. Run this notebook only after **B v7**.
"""
        ),
    ]
    write_nb(path, cells)
    emit_eval_cpt_sota(Path(__file__).resolve().parent / "eval_cpt_sota.py", cells)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    nb_dir = root / "notebooks"
    gen_b_training_sota(nb_dir / "B_training_sota.ipynb")
    gen_a_data_prep_sota(nb_dir / "A_data_prep_sota.ipynb")
    gen_c_eval_sota(nb_dir / "C_eval_sota.ipynb")
    for name in ("A_data_prep_sota.ipynb", "B_training_sota.ipynb", "C_eval_sota.ipynb"):
        src = nb_dir / name
        dest_dir = root / "kaggle" / name.replace(".ipynb", "")
        if dest_dir.is_dir() and src.is_file():
            shutil.copy2(src, dest_dir / name)
            print(f"Copied {src} -> {dest_dir / name}")
    # G3 marker
    marker = root / "scripts" / "NOTE_SOURCE_OF_TRUTH.txt"
    marker.write_text(
        "G3: scripts/_gen_sota_notebooks.py is the source of truth for *_sota.ipynb\n"
        "and scripts/train_cpt_sota.py / scripts/eval_cpt_sota.py.\n"
        "Edit the generator, then run: python continued_pretrain/scripts/_gen_sota_notebooks.py\n"
        "Do not hand-edit notebooks/train_cpt_sota.py/eval_cpt_sota.py and generator in parallel.\n",
        encoding="utf-8",
    )
    print(f"Wrote {marker}")


if __name__ == "__main__":
    main()
