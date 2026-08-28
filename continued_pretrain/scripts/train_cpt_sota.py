#!/usr/bin/env python3
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

UNSLOTH_PIP_SPEC = "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"


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

"""Path / GPU / checkpoint helpers for CPT SOTA B+C (Kaggle + Runpod).

Inlined into generated notebooks by ``_gen_sota_notebooks.py`` (Kaggle kernels
cannot import this file). Keep this module stdlib-only and free of
``from __future__ import annotations`` so the source stays valid when pasted
after other imports.
"""

import hashlib
import math
import os
import re

KAGGLE_WORKING = "/kaggle/working"
KAGGLE_INPUT = "/kaggle/input"
DEFAULT_WORKSPACE = "/workspace"
SKIP_WALK_DIRS = {"hf_home", "unsloth_compiled_cache", ".cache", "hub", "__pycache__"}


def posix_path(path):
    return str(path).replace("\\", "/")


def sha256_file(path, chunk_size=1024 * 1024):
    """Hex digest of a file. Used to pin the C-eval adapter before from_pretrained."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def local_lora_dir(work_root):
    """Prefer $WORK_ROOT/theology_cpt_lora over a walk that can hit Kaggle 4-bit copies."""
    path = os.path.join(work_root, "theology_cpt_lora")
    if os.path.isfile(os.path.join(path, "adapter_config.json")):
        return path
    return None


def is_kaggle_work_root(work_root):
    path = posix_path(work_root).rstrip("/")
    return path == KAGGLE_WORKING or path.endswith("/kaggle/working")


def resolve_work_root(env=None):
    """CPT_WORK_ROOT, else /kaggle/working, else /workspace, else cwd."""
    env = os.environ if env is None else env
    explicit = (env.get("CPT_WORK_ROOT") or "").strip()
    if explicit:
        return os.path.abspath(explicit)
    if os.path.isdir(KAGGLE_WORKING):
        return KAGGLE_WORKING
    if os.path.isdir(DEFAULT_WORKSPACE):
        return DEFAULT_WORKSPACE
    return os.path.abspath(os.getcwd())


def layout_paths(work_root):
    return {
        "offload_dir": os.path.join(work_root, "unsloth_offload"),
        "hf_home": os.path.join(work_root, "hf_home"),
        "local_dataset": os.path.join(work_root, "theology_dataset"),
        "local_holdout": os.path.join(work_root, "theology_holdouts"),
        "output_dir": os.path.join(work_root, "checkpoints_sota"),
        "adapter_out": os.path.join(work_root, "theology_cpt_lora"),
        "run_config_out": os.path.join(work_root, "theology_cpt_run_config.json"),
        "requirements_lock": os.path.join(work_root, "requirements_lock.txt"),
        "out_lora_final": os.path.join(work_root, "theology_cpt_lora_final"),
        "out_merged": os.path.join(work_root, "theology_cpt_merged_hf"),
        "out_metrics": os.path.join(work_root, "theology_cpt_eval_metrics.json"),
    }


def first_existing(*candidates):
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def is_hf_dataset_root(path):
    return bool(path) and os.path.isfile(os.path.join(path, "dataset_dict.json"))


def is_hf_holdout_root(path):
    if not path or not os.path.isdir(path):
        return False
    spurgeon = os.path.join(path, "spurgeon")
    return os.path.isfile(os.path.join(spurgeon, "dataset_info.json")) or os.path.isfile(
        os.path.join(spurgeon, "state.json")
    )


def pruned_walk(root, max_depth=6):
    if not root or not os.path.isdir(root):
        return
    root_norm = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root_norm):
        dirnames[:] = [d for d in dirnames if d not in SKIP_WALK_DIRS and not d.startswith(".")]
        rel = os.path.relpath(dirpath, root_norm)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > max_depth:
            dirnames[:] = []
            continue
        yield dirpath, dirnames, filenames


def dataset_search_roots(work_root, env=None, kaggle_input=None, cwd=None):
    env = os.environ if env is None else env
    kaggle_input = KAGGLE_INPUT if kaggle_input is None else kaggle_input
    cwd = os.getcwd() if cwd is None else cwd
    roots = []
    data = (env.get("CPT_DATA_ROOT") or "").strip()
    if data:
        roots.append(data)
    roots.extend(
        [
            os.path.join(work_root, "theology_dataset"),
            os.path.join(work_root, "theology-cpt-dataset"),
            os.path.join(work_root, "a_output"),
            os.path.join(work_root, "a_output_v3"),
            os.path.join(work_root, "kaggle", "a_output"),
            os.path.join(work_root, "kaggle", "a_output_v3"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v3"),
            os.path.join(cwd, "kaggle", "a_output"),
            os.path.join(cwd, "kaggle", "a_output_v3"),
        ]
    )
    if kaggle_input and os.path.isdir(kaggle_input):
        roots.extend(
            [
                os.path.join(kaggle_input, "theology-cpt-dataset"),
                os.path.join(kaggle_input, "datasets", "rafaelvieira1", "theology-cpt-dataset"),
            ]
        )
    return roots


def find_hf_dataset_root(search_roots):
    for base in search_roots:
        if not base or not os.path.exists(base):
            continue
        nested = os.path.join(base, "theology_dataset")
        for cand in (nested, base):
            if is_hf_dataset_root(cand):
                return cand
    return None


def holdout_search_roots(work_root, dataset_root=None, env=None, kaggle_input=None):
    env = os.environ if env is None else env
    kaggle_input = KAGGLE_INPUT if kaggle_input is None else kaggle_input
    roots = []
    explicit = (env.get("CPT_HOLDOUT_PATH") or "").strip()
    if explicit:
        roots.append(explicit)
    roots.append(os.path.join(work_root, "theology_holdouts"))
    if dataset_root:
        parent = os.path.dirname(dataset_root)
        roots.extend(
            [
                os.path.join(parent, "theology_holdouts"),
                os.path.join(dataset_root, "theology_holdouts"),
            ]
        )
    if kaggle_input and os.path.isdir(kaggle_input):
        roots.extend(
            [
                os.path.join(kaggle_input, "theology-cpt-dataset", "theology_holdouts"),
                os.path.join(
                    kaggle_input,
                    "datasets",
                    "rafaelvieira1",
                    "theology-cpt-dataset",
                    "theology_holdouts",
                ),
            ]
        )
    return roots


def find_hf_holdout_root(search_roots, walk_roots=None):
    for cand in search_roots:
        if is_hf_holdout_root(cand):
            return cand
    for root in walk_roots or []:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, dirnames, _files in pruned_walk(root, max_depth=6):
            if "theology_holdouts" in dirnames:
                cand = os.path.join(dirpath, "theology_holdouts")
                if is_hf_holdout_root(cand):
                    return cand
            if os.path.basename(dirpath) == "theology_holdouts" and is_hf_holdout_root(dirpath):
                return dirpath
    return None


def corpus_search_roots(work_root, env=None, kaggle_input=None, cwd=None):
    env = os.environ if env is None else env
    kaggle_input = KAGGLE_INPUT if kaggle_input is None else kaggle_input
    cwd = os.getcwd() if cwd is None else cwd
    roots = []
    data = (env.get("CPT_DATA_ROOT") or "").strip()
    if data:
        roots.append(data)
    roots.extend(
        [
            os.path.join(work_root, "theology-cpt-corpus"),
            os.path.join(cwd, "continued_pretrain", "data"),
            os.path.join(cwd, "data"),
        ]
    )
    if kaggle_input and os.path.isdir(kaggle_input):
        roots.extend(
            [
                os.path.join(kaggle_input, "theology-cpt-corpus"),
                os.path.join(kaggle_input, "datasets", "rafaelvieira1", "theology-cpt-corpus"),
            ]
        )
    return roots


def find_corpus_root(search_roots):
    for cand in search_roots:
        if not cand or not os.path.isdir(cand):
            continue
        if os.path.isfile(os.path.join(cand, "theology_mix_manifest.json")):
            return cand
    return None


def find_highest_checkpoint(root):
    """Highest checkpoint-* directory that contains trainer_state.json."""
    if not root or not os.path.isdir(root):
        return None
    best = None
    best_step = -1
    for name in os.listdir(root):
        match = re.match(r"checkpoint-(\d+)$", name)
        if not match:
            continue
        ckpt = os.path.join(root, name)
        if os.path.isfile(os.path.join(ckpt, "trainer_state.json")):
            step = int(match.group(1))
            if step > best_step:
                best_step = step
                best = ckpt
    return best


def collect_checkpoint_roots(work_root, kaggle_input=None):
    kaggle_input = KAGGLE_INPUT if kaggle_input is None else kaggle_input
    roots = []
    local = os.path.join(work_root, "checkpoints_sota")
    if os.path.isdir(local):
        roots.append(local)
    if kaggle_input and os.path.isdir(kaggle_input):
        for cand in (
            os.path.join(
                kaggle_input,
                "notebooks",
                "rafaelvieira1",
                "theology-cpt-v2-b-training-sota",
                "checkpoints_sota",
            ),
            os.path.join(kaggle_input, "theology-cpt-v2-b-training-sota", "checkpoints_sota"),
        ):
            if os.path.isdir(cand) and cand not in roots:
                roots.append(cand)
        for dirpath, dirnames, _files in pruned_walk(kaggle_input, max_depth=6):
            if os.path.basename(dirpath) == "checkpoints_sota" and dirpath not in roots:
                roots.append(dirpath)
            if "checkpoints_sota" in dirnames:
                cand = os.path.join(dirpath, "checkpoints_sota")
                if cand not in roots:
                    roots.append(cand)
    return roots


def resolve_prev_checkpoint(work_root, env=None, kaggle_input=None):
    """Explicit PREV_RUN_CHECKPOINT wins; empty string forces a fresh run."""
    env = os.environ if env is None else env
    kaggle_input = KAGGLE_INPUT if kaggle_input is None else kaggle_input
    if "PREV_RUN_CHECKPOINT" in env:
        val = (env.get("PREV_RUN_CHECKPOINT") or "").strip()
        if not val:
            return None
        return val
    best = None
    best_step = -1
    for root in collect_checkpoint_roots(work_root, kaggle_input=kaggle_input):
        found = find_highest_checkpoint(root)
        if not found:
            continue
        match = re.search(r"checkpoint-(\d+)$", os.path.basename(found))
        step = int(match.group(1)) if match else -1
        if step > best_step:
            best_step = step
            best = found
    return best


def resolve_gpu_profile(cc_major=None, env=None):
    """GPU_PROFILE env override, else ampere if sm_80+, else t4."""
    env = os.environ if env is None else env
    explicit = (env.get("GPU_PROFILE") or "").strip().lower()
    if explicit in ("t4", "ampere"):
        return explicit
    if cc_major is None:
        return "t4"
    try:
        major = int(cc_major)
    except (TypeError, ValueError):
        return "t4"
    return "ampere" if major >= 8 else "t4"


def trainer_mixed_precision(train_embeddings, bf16_supported):
    """Return (fp16, bf16). Ampere bf16 stays on even with embed LoRA.

    T4 (no bf16) + embed LoRA must stay float32: fp16 autocast vs fp32 embeds
    crashes eval. T4 without embeds uses fp16.
    """
    if bf16_supported:
        return False, True
    if train_embeddings:
        return False, False
    return True, False


def checkpoint_save_policy(work_root):
    """Kaggle 20 GB disk vs Runpod volume resume."""
    if is_kaggle_work_root(work_root):
        return {"save_total_limit": 1, "save_only_model": True}
    return {"save_total_limit": 3, "save_only_model": False}


def loss_at_step(log_history, step, metric_key):
    """Latest ``metric_key`` recorded at exactly ``step``, or None."""
    if not log_history:
        return None
    found = None
    want = int(step)
    for entry in log_history:
        if not isinstance(entry, dict):
            continue
        try:
            entry_step = int(entry.get("step", -1))
        except (TypeError, ValueError):
            continue
        if entry_step != want:
            continue
        if metric_key not in entry or entry[metric_key] is None:
            continue
        try:
            found = float(entry[metric_key])
        except (TypeError, ValueError):
            continue
    return found


def spurgeon_loss_at_step(log_history, step):
    """Latest ``eval_spurgeon_loss`` recorded at exactly ``step``, or None."""
    return loss_at_step(log_history, step, "eval_spurgeon_loss")


def spurgeon_rose_by_step(log_history, now_step=50, ref_step=25):
    """True iff eval_spurgeon_loss at now_step is strictly worse than at ref_step.

    Missing either value → False (do not abort; caller should warn).
    Equal / flat / improved → False.
    """
    now = spurgeon_loss_at_step(log_history, now_step)
    ref = spurgeon_loss_at_step(log_history, ref_step)
    if now is None or ref is None:
        return False
    return now > ref


def find_adapter(search_roots):
    """Prefer theology_cpt_lora (best-at-end) over checkpoint-* dirs."""
    markers = []
    for root in search_roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in pruned_walk(root, max_depth=10):
            if "adapter_config.json" not in filenames:
                continue
            name = posix_path(dirpath)
            if "theology_cpt_lora" in name or "checkpoints_sota" in name:
                markers.append(dirpath)
    ranked = []
    for path in markers:
        name = posix_path(path)
        score = 0
        if name.endswith("/theology_cpt_lora") or "/theology_cpt_lora/" in name:
            score += 100
        if "checkpoint-" in name:
            score += 5
        ranked.append((score, path))
    ranked.sort(reverse=True)
    return ranked[0][1] if ranked else None


def adapter_search_roots(work_root, kaggle_input=None):
    kaggle_input = KAGGLE_INPUT if kaggle_input is None else kaggle_input
    roots = [work_root]
    if kaggle_input and os.path.isdir(kaggle_input):
        roots.append(kaggle_input)
    return roots


def resolve_run_mode(env=None):
    """``continue`` when CPT_RUN_MODE=continue; otherwise ``fresh``."""
    env = os.environ if env is None else env
    mode = (env.get("CPT_RUN_MODE") or "fresh").strip().lower()
    return "continue" if mode == "continue" else "fresh"


def _env_float(env, key, default):
    val = (env.get(key) or "").strip()
    if not val:
        return default
    return float(val)


def _env_int(env, key, default):
    val = (env.get(key) or "").strip()
    if not val:
        return default
    return int(val)


def resolve_continue_training_config(env=None, packed_epoch_steps=None):
    """Overrides for CPT_RUN_MODE=continue. Empty dict when not in continue mode."""
    env = os.environ if env is None else env
    if resolve_run_mode(env) != "continue":
        return {}

    packed = int(packed_epoch_steps or 0)
    min_steps = 0
    if packed > 0:
        min_steps = max(1, math.ceil(0.4 * packed))
    explicit_min = (env.get("EARLY_STOP_MIN_STEPS") or "").strip()
    if explicit_min:
        min_steps = int(explicit_min)

    buckets_raw = (env.get("EVAL_BUCKETS_DURING_TRAIN") or "").strip()
    if buckets_raw:
        buckets = [part.strip() for part in buckets_raw.split(",") if part.strip()]
    else:
        buckets = ["spurgeon", "puritan", "confession"]

    return {
        "run_mode": "continue",
        "learning_rate": _env_float(env, "LEARNING_RATE", 4e-6),
        "embedding_learning_rate": _env_float(env, "EMBEDDING_LEARNING_RATE", 1.5e-6),
        "warmup_ratio": _env_float(env, "WARMUP_RATIO", 0.01),
        "eval_docs_per_bucket": _env_int(env, "EVAL_DOCS_PER_BUCKET", 16),
        "eval_buckets_during_train": buckets,
        "abort_spurgeon_step": _env_int(env, "ABORT_SPURGEON_STEP", 0),
        "early_stop_min_steps": min_steps,
        "early_stop_epsilon": _env_float(env, "EARLY_STOP_EPSILON", 0.005),
        "early_stop_patience": _env_int(env, "EARLY_STOPPING_PATIENCE", 2),
        "composite_early_stop_metrics": ["eval_spurgeon_loss", "eval_mix_loss"],
        "use_composite_early_stop": True,
    }


def metric_improved(current, best, epsilon):
    """True when lower loss improved vs best by more than epsilon."""
    return float(current) < float(best) - float(epsilon)


def update_composite_flat_state(bests, flat_streak, metrics, metric_keys, epsilon):
    """Update running bests / flat streak after one eval dict.

    Returns ``(new_bests, new_streak, any_improved)``. Missing metric keys do not
    count as flat (``any_improved=True`` so streak resets).
    """
    new_bests = dict(bests or {})
    streak = int(flat_streak or 0)
    if not metrics:
        return new_bests, streak, True

    for key in metric_keys:
        if key not in metrics or metrics[key] is None:
            return new_bests, streak, True

    any_improved = False
    for key in metric_keys:
        current = float(metrics[key])
        best = new_bests.get(key)
        if best is None:
            new_bests[key] = current
            any_improved = True
            continue
        if metric_improved(current, best, epsilon):
            new_bests[key] = current
            any_improved = True

    if any_improved:
        return new_bests, 0, True
    return new_bests, streak + 1, False


def composite_should_halt(flat_streak, patience):
    """True when flat streak reached patience."""
    return int(flat_streak) >= int(patience)


def resolve_init_adapter(work_root, env=None, kaggle_input=None):
    """Adapter path for continue mode (CPT_INIT_ADAPTER, local LoRA, or find_adapter)."""
    env = os.environ if env is None else env
    explicit = (env.get("CPT_INIT_ADAPTER") or "").strip()
    if explicit:
        return explicit
    if resolve_run_mode(env) != "continue":
        return None
    local = local_lora_dir(work_root)
    if local:
        return local
    return find_adapter(adapter_search_roots(work_root, kaggle_input=kaggle_input))


def find_file(filename, search_roots, prefer_substrings=()):
    hits = []
    for root in search_roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in pruned_walk(root, max_depth=10):
            if filename in filenames:
                hits.append(os.path.join(dirpath, filename))
            elif filename in dirnames:
                hits.append(os.path.join(dirpath, filename))
    if not hits:
        return None
    for sub in prefer_substrings:
        for hit in hits:
            if sub in posix_path(hit):
                return hit
    return hits[0]

# skipped notebook magic: !pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git"

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

import torch

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

import os
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
MODEL_NAME = "unsloth/Qwen3.5-4B-Base"  # M1 fail → "unsloth/Mistral-7B-v0.3"
# MODEL_NAME = "unsloth/Qwen3.5-9B-Base"  # E3 only after VRAM probe passes
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
    print(f"Continue mode: init_adapter={INIT_ADAPTER_PATH}")

PREV_RUN_CHECKPOINT = resolve_prev_checkpoint(WORK_ROOT, kaggle_input=_kaggle_input)
if CPT_RUN_MODE == "continue" and PREV_RUN_CHECKPOINT:
    print(
        "WARNING: PREV_RUN_CHECKPOINT ignored in continue mode — "
        "adapter-only load + fresh Adam (not HF resume)"
    )
    PREV_RUN_CHECKPOINT = None
if PREV_RUN_CHECKPOINT:
    print(f"Auto-resume: PREV_RUN_CHECKPOINT={PREV_RUN_CHECKPOINT}")
else:
    print("No prior checkpoint found — fresh training run.")
    print("  (empty PREV_RUN_CHECKPOINT env forces fresh; do not resume Kaggle 4-bit ckpts on Ampere bf16)")
SEED = 42
APPEND_EOS = True              # D2 fix if packed rows lack EOS

print("Config ready.")
print(f"  work_root={WORK_ROOT} save_total_limit={SAVE_TOTAL_LIMIT} save_only_model={SAVE_ONLY_MODEL}")
print(f"  model={MODEL_NAME} seq={MAX_SEQ_LENGTH} r={LORA_RANK} rslora={USE_RSLORA}")
print(f"  gpu_profile={GPU_PROFILE} load_in_4bit={LOAD_IN_4BIT} lora_gdn={LORA_GDN}")
print(f"  packing_mode={PACKING_MODE} pad_to_max={PAD_TO_MAX} manual_pack={MANUAL_PACK}")
print(f"  lr={LEARNING_RATE} emb_lr={EMBEDDING_LEARNING_RATE} warmup_ratio={WARMUP_RATIO}")
print(f"  max_steps={MAX_STEPS} eval_steps={EVAL_STEPS} metric={METRIC_FOR_BEST}")
print(f"  abort_spurgeon_step={ABORT_SPURGEON_STEP} ref_step={ABORT_SPURGEON_REF_STEP}")
print(f"  batch={PER_DEVICE_BATCH}x{GRAD_ACCUM} train_embed={TRAIN_EMBEDDINGS} train_lm_head={TRAIN_LM_HEAD}")
print(f"  eval_docs={EVAL_DOCS_PER_BUCKET} eval_buckets={EVAL_BUCKETS_DURING_TRAIN}")
print(f"  cpt_run_mode={CPT_RUN_MODE} init_adapter={INIT_ADAPTER_PATH} composite_stop={USE_COMPOSITE_EARLY_STOP}")
print(f"  offload_dir={OFFLOAD_DIR}")
print(f"  CORPUS_ROOT={CORPUS_ROOT}")
print(f"  SRC_DATASET_PATH={SRC_DATASET_PATH}")
print(f"  SRC_HOLDOUT_PATH={SRC_HOLDOUT_PATH}")
print(f"  MANIFEST_PATH={MANIFEST_PATH}")
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

from unsloth import FastLanguageModel
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

from unsloth import UnslothTrainer, UnslothTrainingArguments
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
print(f"  load_best_model_at_end={training_args.load_best_model_at_end}")

import numpy as np

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

# Run only when MODEL_NAME is the 9B experiment. Pass if peak reserved < ~15 GB.
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
    print("VRAM probe skipped (flagship 4B path).")

import sys
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
        )

def _sha256_file(p):
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
print("Checkpoints:", OUTPUT_DIR)

