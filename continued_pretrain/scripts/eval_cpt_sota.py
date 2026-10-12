#!/usr/bin/env python3
"""SOTA CPT C eval — generated from _gen_sota_notebooks.py. Do not hand-edit.

Run on a GPU pod (Runpod RTX 4090) after copying LoRA + holdouts + MCQ:

    export CPT_WORK_ROOT=/workspace
    export CPT_DATA_ROOT=/workspace
    export HF_HOME=/workspace/hf_home
    export PYTHONUNBUFFERED=1
    export EXPECTED_ADAPTER_SHA256=06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432
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

_DEFAULT_UNSLOTH_PIP_SPEC = "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
# Override for stack isolation (e.g. UNSLOTH_PIP_SPEC='unsloth[colab-new]==2026.8.22').
UNSLOTH_PIP_SPEC = (os.environ.get("UNSLOTH_PIP_SPEC") or "").strip() or _DEFAULT_UNSLOTH_PIP_SPEC
EXPECTED_ADAPTER_SHA256_DEFAULT = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
TORCH_CU126_INDEX = "https://download.pytorch.org/whl/cu126"


def _maybe_upgrade_torch_for_cu124():
    try:
        import torch
    except ImportError:
        return
    ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
    if ver >= (2, 8):
        return
    print(f"Upgrading torch from {torch.__version__} -> 2.8.0+cu126 (cu124 image compat)")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "--break-system-packages",
            "torch==2.8.0",
            "torchvision",
            "torchaudio",
            "--index-url",
            TORCH_CU126_INDEX,
        ]
    )


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
    # new_authors is monitor-only: report if present, never a preflight / §5 gate.
    _na = os.path.join(holdouts, "new_authors")
    if os.path.isfile(os.path.join(_na, "dataset_info.json")) or os.path.isfile(
        os.path.join(_na, "state.json")
    ):
        print("preflight note: new_authors diagnostic holdout present (monitor-only)")
    else:
        print("preflight note: new_authors diagnostic holdout absent (optional)")
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
    print("preflight GPU", name, "sm", f"{major}.{minor}")
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
        _maybe_upgrade_torch_for_cu124()
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

"""Path / GPU / checkpoint helpers for CPT SOTA B+C (Kaggle + Runpod).

Inlined into generated notebooks by ``_gen_sota_notebooks.py`` (Kaggle kernels
cannot import this file). Keep this module stdlib-only and free of
``from __future__ import annotations`` so the source stays valid when pasted
after other imports.
"""

import hashlib
import json
import math
import os
import random
import re

KAGGLE_WORKING = "/kaggle/working"
KAGGLE_INPUT = "/kaggle/input"
DEFAULT_WORKSPACE = "/workspace"
SKIP_WALK_DIRS = {"hf_home", "unsloth_compiled_cache", ".cache", "hub", "__pycache__"}

# S7 Phase A: seed composite halt from S6 in-train values at ckpt-2050
# (EVAL_DOCS_PER_BUCKET=16). Do NOT replace with isolation-C full-holdout CE
# (puritan 20 / confession 10 docs) — those are a different measurement and
# make the seed unreachable on the in-train eval set.
# Holdout seeds stay (pinned v3 probes). Do not seed eval_mix_loss — mix-val
# is a different split and is not the §5 gate. Replay halt is holdouts only.
S7_DEFAULT_COMPOSITE_SEED_BESTS = {
    "eval_spurgeon_loss": 2.4987,
    "eval_puritan_loss": 1.751,
    "eval_confession_loss": 1.668,
}
# Continue budget: 955 steps (one packed epoch of v5; ~0.67 epoch of v6).
S7_DEFAULT_CONTINUE_MAX_STEPS = 955
S7_DEFAULT_EARLY_STOP_MIN_STEPS = 400
S7_DEFAULT_ABORT_SPURGEON_DELTA = 0.12
S7_DEFAULT_S5_SPURGEON_GUARDRAIL = 0.01
S7_DEFAULT_GENERAL_WARN_DELTA = 0.15

# S8 rewarm: higher LR / rank than the 2e-6 plateau. Composite seeds stay empty so the
# first in-train eval sets the bests (do not reuse the S6 constants 2.4987/1.751/1.668).
S8_DEFAULT_LEARNING_RATE = 3e-5
S8_DEFAULT_EMBEDDING_LEARNING_RATE = 3e-6
S8_DEFAULT_WARMUP_RATIO = 0.05
S8_DEFAULT_CONTINUE_MAX_STEPS = 400
FLAGSHIP_BASE_MODEL = "unsloth/Qwen3.5-4B-Base"
# Diagnostic only. Pinned holdout bytes stay the gate. Indices are <|endoftext|> docs.
CLEAN_HOLDOUT_EXCLUDE = {
    "puritan": (7, 10, 11),
    "confession": (3,),
}

# S7 eval buckets: gate metrics stay spurgeon/puritan/confession (composite + §5/Hub).
# general + new_authors are monitor-only (loaded/reported; not in COMPOSITE_EARLY_STOP_METRICS).
S7_GATE_EVAL_BUCKETS = ["spurgeon", "puritan", "confession"]
S7_MONITOR_EVAL_BUCKETS = ["general", "new_authors"]
S7_DEFAULT_EVAL_BUCKETS = S7_GATE_EVAL_BUCKETS + S7_MONITOR_EVAL_BUCKETS
# Isolation C preflight requires these HF buckets; new_authors stays optional (report if present).
C_REQUIRED_HOLDOUT_BUCKETS = ["spurgeon", "puritan", "confession", "general"]
C_MONITOR_HOLDOUT_BUCKETS = ["new_authors"]
# Train/eval discovery tries these HF subdirs under theology_holdouts/.
HOLDOUT_EVAL_CANDIDATES = C_REQUIRED_HOLDOUT_BUCKETS + C_MONITOR_HOLDOUT_BUCKETS


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


def resolve_continue_profile(env=None):
    """``s7`` or ``s8`` when CPT_CONTINUE_PROFILE is set; otherwise empty (S6 defaults)."""
    env = os.environ if env is None else env
    profile = (env.get("CPT_CONTINUE_PROFILE") or "").strip().lower()
    if profile in ("s7", "s8"):
        return profile
    return ""


def continue_checkpoint_profile(env=None):
    """``s7``/``s8`` when continue mode writes its own checkpoint dir; else empty."""
    env = os.environ if env is None else env
    if resolve_run_mode(env) != "continue":
        return ""
    return resolve_continue_profile(env)


def layout_paths(work_root, env=None):
    """Resolve work-root layout. S7 continue writes to checkpoints_s7, not sota."""
    env = os.environ if env is None else env
    explicit = (env.get("CPT_OUTPUT_DIR") or "").strip()
    if explicit:
        output_dir = explicit
    elif continue_checkpoint_profile(env):
        output_dir = os.path.join(work_root, "checkpoints_" + continue_checkpoint_profile(env))
    else:
        output_dir = os.path.join(work_root, "checkpoints_sota")
    return {
        "offload_dir": os.path.join(work_root, "unsloth_offload"),
        "hf_home": os.path.join(work_root, "hf_home"),
        "local_dataset": os.path.join(work_root, "theology_dataset"),
        "local_holdout": os.path.join(work_root, "theology_holdouts"),
        "output_dir": output_dir,
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
            os.path.join(work_root, "a_output_v6_p0"),
        os.path.join(work_root, "a_output_v6"),
            os.path.join(work_root, "a_output_v5"),
            os.path.join(work_root, "a_output_v4"),
            os.path.join(work_root, "a_output_v3"),
            os.path.join(work_root, "kaggle", "a_output"),
            os.path.join(work_root, "kaggle", "a_output_v6_p0"),
        os.path.join(work_root, "kaggle", "a_output_v6"),
            os.path.join(work_root, "kaggle", "a_output_v5"),
            os.path.join(work_root, "kaggle", "a_output_v4"),
            os.path.join(work_root, "kaggle", "a_output_v3"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v6_p0"),
        os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v6"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v5"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v4"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v3"),
            os.path.join(cwd, "kaggle", "a_output"),
            os.path.join(cwd, "kaggle", "a_output_v6_p0"),
        os.path.join(cwd, "kaggle", "a_output_v6"),
            os.path.join(cwd, "kaggle", "a_output_v5"),
            os.path.join(cwd, "kaggle", "a_output_v4"),
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


def collect_checkpoint_roots(work_root, env=None, kaggle_input=None):
    """Roots searched for auto-resume. S7 never scans leftover checkpoints_sota."""
    env = os.environ if env is None else env
    kaggle_input = KAGGLE_INPUT if kaggle_input is None else kaggle_input
    roots = []
    profile = continue_checkpoint_profile(env)
    if profile:
        explicit = (env.get("CPT_OUTPUT_DIR") or "").strip()
        local = explicit or os.path.join(work_root, "checkpoints_" + profile)
        if os.path.isdir(local):
            roots.append(local)
        return roots
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
    for root in collect_checkpoint_roots(work_root, env=env, kaggle_input=kaggle_input):
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


def parse_composite_seed_bests(env=None, default=None):
    """Parse COMPOSITE_SEED_BESTS JSON into eval_*_loss -> float. Empty/invalid → default."""
    env = os.environ if env is None else env
    raw = (env.get("COMPOSITE_SEED_BESTS") or "").strip()
    if not raw:
        return dict(default or {})
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return dict(default or {})
    if not isinstance(data, dict):
        return dict(default or {})
    out = {}
    for key, value in data.items():
        if value is None:
            continue
        try:
            out[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return out if out else dict(default or {})


def resolve_composite_early_stop_metrics(env=None, default=None):
    """Parse COMPOSITE_EARLY_STOP_METRICS CSV. Empty/invalid → default list."""
    env = os.environ if env is None else env
    raw = (env.get("COMPOSITE_EARLY_STOP_METRICS") or "").strip()
    if not raw:
        return list(default or [])
    keys = [part.strip() for part in raw.split(",") if part.strip()]
    return keys if keys else list(default or [])


def resolve_continue_training_config(env=None, packed_epoch_steps=None):
    """Overrides for CPT_RUN_MODE=continue. Empty dict when not in continue mode.

    CPT_CONTINUE_PROFILE=s7 selects Phase A knobs (lower LR, checkpoints_s7, seeded
    4-metric composite). CPT_CONTINUE_PROFILE=s8 is the rewarm profile (higher LR,
    empty composite seeds, optimizer checkpoints). Unset profile keeps S6 continue
    defaults (4e-6, 0.4 epoch floor).
    """
    env = os.environ if env is None else env
    if resolve_run_mode(env) != "continue":
        return {}

    profile = resolve_continue_profile(env)
    packed = int(packed_epoch_steps or 0)
    buckets_raw = (env.get("EVAL_BUCKETS_DURING_TRAIN") or "").strip()
    if buckets_raw:
        buckets = [part.strip() for part in buckets_raw.split(",") if part.strip()]
    else:
        buckets = ["spurgeon", "puritan", "confession"]

    if profile == "s8":
        continue_max = _env_int(env, "CONTINUE_MAX_STEPS", S8_DEFAULT_CONTINUE_MAX_STEPS)
        max_steps_env = (env.get("MAX_STEPS") or "").strip()
        if max_steps_env:
            continue_max = int(max_steps_env)
        explicit_min = (env.get("EARLY_STOP_MIN_STEPS") or "").strip()
        if explicit_min:
            min_steps = int(explicit_min)
        else:
            min_steps = max(1, math.ceil(0.5 * int(continue_max)))
        work_root = resolve_work_root(env)
        layout = layout_paths(work_root, env=env)
        lr_scheduler_type = (env.get("LR_SCHEDULER") or "cosine_with_min_lr").strip() or "cosine_with_min_lr"
        if lr_scheduler_type == "constant":
            sched_kwargs = None
        else:
            sched_kwargs = {"min_lr_rate": 0.1}
        if not buckets_raw:
            buckets = list(S7_DEFAULT_EVAL_BUCKETS)
        return {
            "run_mode": "continue",
            "continue_profile": "s8",
            "learning_rate": _env_float(env, "LEARNING_RATE", S8_DEFAULT_LEARNING_RATE),
            "embedding_learning_rate": _env_float(
                env, "EMBEDDING_LEARNING_RATE", S8_DEFAULT_EMBEDDING_LEARNING_RATE
            ),
            "warmup_ratio": _env_float(env, "WARMUP_RATIO", S8_DEFAULT_WARMUP_RATIO),
            "eval_docs_per_bucket": _env_int(env, "EVAL_DOCS_PER_BUCKET", 16),
            "eval_buckets_during_train": buckets,
            "eval_steps": _env_int(env, "EVAL_STEPS", 50),
            "save_steps": _env_int(env, "SAVE_STEPS", 50),
            "lr_scheduler_type": lr_scheduler_type,
            "lr_scheduler_kwargs": sched_kwargs,
            "abort_spurgeon_step": _env_int(env, "ABORT_SPURGEON_STEP", 0),
            "abort_spurgeon_delta": _env_float(env, "ABORT_SPURGEON_DELTA", 0.0),
            "s5_spurgeon_guardrail": _env_float(
                env, "S5_SPURGEON_GUARDRAIL", S7_DEFAULT_S5_SPURGEON_GUARDRAIL
            ),
            "general_warn_delta": _env_float(
                env, "GENERAL_WARN_DELTA", S7_DEFAULT_GENERAL_WARN_DELTA
            ),
            "early_stop_min_steps": min_steps,
            "early_stop_epsilon": _env_float(env, "EARLY_STOP_EPSILON", 0.003),
            "early_stop_patience": _env_int(env, "EARLY_STOPPING_PATIENCE", 4),
            "composite_early_stop_metrics": resolve_composite_early_stop_metrics(
                env,
                [
                    "eval_spurgeon_loss",
                    "eval_puritan_loss",
                    "eval_confession_loss",
                ],
            ),
            "use_composite_early_stop": True,
            "metric_for_best": (env.get("METRIC_FOR_BEST") or "eval_puritan_loss").strip()
            or "eval_puritan_loss",
            "continue_max_steps": continue_max,
            "output_dir": layout["output_dir"],
            # Empty: the first in-train eval seeds bests. Do not copy S6 constants.
            "composite_seed_bests": parse_composite_seed_bests(env, default={}),
            "s5_best_adapter_dir": os.path.join(work_root, "theology_cpt_lora_s5best"),
            "save_only_model": False,
        }

    if profile == "s7":
        min_steps = S7_DEFAULT_EARLY_STOP_MIN_STEPS
        explicit_min = (env.get("EARLY_STOP_MIN_STEPS") or "").strip()
        if explicit_min:
            min_steps = int(explicit_min)
        continue_max = _env_int(env, "CONTINUE_MAX_STEPS", S7_DEFAULT_CONTINUE_MAX_STEPS)
        # MAX_STEPS env also wins when set (pod overrides).
        max_steps_env = (env.get("MAX_STEPS") or "").strip()
        if max_steps_env:
            continue_max = int(max_steps_env)
        work_root = resolve_work_root(env)
        layout = layout_paths(work_root, env=env)
        # Default S7 buckets include general + new_authors (monitor-only); composite stays gate-only.
        if not buckets_raw:
            buckets = list(S7_DEFAULT_EVAL_BUCKETS)
        return {
            "run_mode": "continue",
            "continue_profile": "s7",
            "learning_rate": _env_float(env, "LEARNING_RATE", 2e-6),
            "embedding_learning_rate": _env_float(env, "EMBEDDING_LEARNING_RATE", 8e-7),
            "warmup_ratio": _env_float(env, "WARMUP_RATIO", 0.04),
            "eval_docs_per_bucket": _env_int(env, "EVAL_DOCS_PER_BUCKET", 16),
            "eval_buckets_during_train": buckets,
            "eval_steps": _env_int(env, "EVAL_STEPS", 50),
            "save_steps": _env_int(env, "SAVE_STEPS", 50),
            "lr_scheduler_type": (env.get("LR_SCHEDULER") or "cosine_with_min_lr").strip()
            or "cosine_with_min_lr",
            "lr_scheduler_kwargs": {"min_lr_rate": 0.1},
            "abort_spurgeon_step": _env_int(env, "ABORT_SPURGEON_STEP", 0),
            "abort_spurgeon_delta": _env_float(
                env, "ABORT_SPURGEON_DELTA", S7_DEFAULT_ABORT_SPURGEON_DELTA
            ),
            "s5_spurgeon_guardrail": _env_float(
                env, "S5_SPURGEON_GUARDRAIL", S7_DEFAULT_S5_SPURGEON_GUARDRAIL
            ),
            "general_warn_delta": _env_float(
                env, "GENERAL_WARN_DELTA", S7_DEFAULT_GENERAL_WARN_DELTA
            ),
            "early_stop_min_steps": min_steps,
            "early_stop_epsilon": _env_float(env, "EARLY_STOP_EPSILON", 0.003),
            "early_stop_patience": _env_int(env, "EARLY_STOPPING_PATIENCE", 4),
            "composite_early_stop_metrics": resolve_composite_early_stop_metrics(
                env,
                [
                    "eval_spurgeon_loss",
                    "eval_puritan_loss",
                    "eval_confession_loss",
                ],
            ),
            "use_composite_early_stop": True,
            # Hard gate is Puritan; load_best picks best Puritan eval (Spurgeon abort/guardrail remain).
            "metric_for_best": (env.get("METRIC_FOR_BEST") or "eval_puritan_loss").strip()
            or "eval_puritan_loss",
            "continue_max_steps": continue_max,
            "output_dir": layout["output_dir"],
            "composite_seed_bests": parse_composite_seed_bests(
                env, default=S7_DEFAULT_COMPOSITE_SEED_BESTS
            ),
            "s5_best_adapter_dir": os.path.join(work_root, "theology_cpt_lora_s5best"),
        }

    min_steps = 0
    if packed > 0:
        min_steps = max(1, math.ceil(0.4 * packed))
    explicit_min = (env.get("EARLY_STOP_MIN_STEPS") or "").strip()
    if explicit_min:
        min_steps = int(explicit_min)

    return {
        "run_mode": "continue",
        "continue_profile": "",
        "learning_rate": _env_float(env, "LEARNING_RATE", 4e-6),
        "embedding_learning_rate": _env_float(env, "EMBEDDING_LEARNING_RATE", 1.5e-6),
        "warmup_ratio": _env_float(env, "WARMUP_RATIO", 0.01),
        "eval_docs_per_bucket": _env_int(env, "EVAL_DOCS_PER_BUCKET", 16),
        "eval_buckets_during_train": buckets,
        "abort_spurgeon_step": _env_int(env, "ABORT_SPURGEON_STEP", 0),
        "early_stop_min_steps": min_steps,
        "early_stop_epsilon": _env_float(env, "EARLY_STOP_EPSILON", 0.005),
        "early_stop_patience": _env_int(env, "EARLY_STOPPING_PATIENCE", 2),
        "composite_early_stop_metrics": resolve_composite_early_stop_metrics(
            env, ["eval_spurgeon_loss", "eval_mix_loss"]
        ),
        "use_composite_early_stop": True,
        "continue_max_steps": None,
        "output_dir": None,
        "composite_seed_bests": parse_composite_seed_bests(env, default={}),
    }


def metric_improved(current, best, epsilon):
    """True when lower loss improved vs best by more than epsilon."""
    return float(current) < float(best) - float(epsilon)


def merge_eval_event_for_step(cache, step, metrics, metric_keys):
    """Merge one Hugging Face per-dataset eval event into a per-step cache.

    HF calls ``on_evaluate`` once per eval dataset, so mix and Spurgeon
    metrics arrive as separate dicts at the same ``global_step``. Score a
    cycle only when every ``metric_keys`` value is present for that exact
    step, then drop the step so it is not scored twice.

    Returns ``(new_cache, merged_or_none)``. ``merged`` is set only when the
    cycle is complete.
    """
    new_cache = dict(cache or {})
    keys = list(metric_keys or [])
    if not keys:
        return new_cache, None
    try:
        step_key = int(step)
    except (TypeError, ValueError):
        return new_cache, None
    bucket = dict(new_cache.get(step_key) or {})
    incoming = metrics or {}
    for key in keys:
        if key in incoming and incoming[key] is not None:
            bucket[key] = incoming[key]
    new_cache[step_key] = bucket
    if all(key in bucket and bucket[key] is not None for key in keys):
        merged = new_cache.pop(step_key)
        return new_cache, merged
    return new_cache, None


def update_composite_flat_state(bests, flat_streak, metrics, metric_keys, epsilon):
    """Update running bests / flat streak after one complete eval cycle dict.

    Returns ``(new_bests, new_streak, any_improved)``. Missing metric keys do not
    count as flat (``any_improved=True`` so streak resets). Callers that receive
    split HF events must merge via ``merge_eval_event_for_step`` first.
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


def s5_loss_from_metrics(metrics):
    """Mean of eval_puritan_loss + eval_confession_loss, or None if either missing."""
    if not metrics:
        return None
    try:
        puritan = metrics.get("eval_puritan_loss")
        confession = metrics.get("eval_confession_loss")
        if puritan is None or confession is None:
            return None
        return (float(puritan) + float(confession)) / 2.0
    except (TypeError, ValueError):
        return None


def s5_best_should_save(s5_loss, best_s5, spurgeon_loss, seed_spurgeon, guardrail=0.01):
    """True when s5 improves and spurgeon stays within seed + guardrail."""
    if s5_loss is None or spurgeon_loss is None or seed_spurgeon is None:
        return False
    try:
        s5 = float(s5_loss)
        spurgeon = float(spurgeon_loss)
        seed = float(seed_spurgeon)
        limit = seed + float(guardrail)
    except (TypeError, ValueError):
        return False
    if spurgeon > limit:
        return False
    if best_s5 is None:
        return True
    return s5 < float(best_s5)


def seed_regression_streak(current_spurgeon, seed_spurgeon, delta, prior_streak=0):
    """Consecutive cycles where spurgeon >= seed + delta. Resets to 0 when recovered."""
    if current_spurgeon is None or seed_spurgeon is None:
        return int(prior_streak or 0)
    try:
        if float(current_spurgeon) >= float(seed_spurgeon) + float(delta):
            return int(prior_streak or 0) + 1
    except (TypeError, ValueError):
        return int(prior_streak or 0)
    return 0


def seed_regression_should_abort(streak, required=2):
    """Halt after ``required`` consecutive seed-regression cycles."""
    return int(streak) >= int(required)


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


def resolve_eval_base_model(env=None):
    """Isolation-C base is the stock flagship. CPT_BASE_MODEL is the train base only."""
    env = os.environ if env is None else env
    explicit = (env.get("CPT_EVAL_BASE_MODEL") or "").strip()
    if explicit:
        return explicit
    return FLAGSHIP_BASE_MODEL


def apply_env_model_overrides(values, env=None):
    """Copy of model/rank/alpha with CPT_BASE_MODEL, LORA_RANK, LORA_ALPHA applied."""
    env = os.environ if env is None else env
    out = dict(values or {})
    base = (env.get("CPT_BASE_MODEL") or "").strip()
    if base:
        out["model_name"] = base
    rank = (env.get("LORA_RANK") or "").strip()
    if rank:
        out["lora_rank"] = int(rank)
    alpha = (env.get("LORA_ALPHA") or "").strip()
    if alpha:
        out["lora_alpha"] = int(alpha)
    return out


def _env_flag(env, key):
    raw = (env.get(key) or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return None


def resolve_fresh_training_env(env=None):
    """Env overrides for CPT_RUN_MODE=fresh. Missing keys stay at the cell defaults."""
    env = os.environ if env is None else env
    out = {}
    for key, caster in (
        ("LEARNING_RATE", float),
        ("EMBEDDING_LEARNING_RATE", float),
        ("WARMUP_RATIO", float),
        ("MAX_STEPS", int),
        ("ABORT_SPURGEON_STEP", int),
        ("EARLY_STOP_MIN_STEPS", int),
        ("EARLY_STOPPING_PATIENCE", int),
        ("EVAL_STEPS", int),
        ("SAVE_STEPS", int),
        ("EVAL_DOCS_PER_BUCKET", int),
    ):
        raw = (env.get(key) or "").strip()
        if raw:
            out[key.lower()] = caster(raw)
    buckets_raw = (env.get("EVAL_BUCKETS_DURING_TRAIN") or "").strip()
    if buckets_raw:
        out["eval_buckets_during_train"] = [
            part.strip() for part in buckets_raw.split(",") if part.strip()
        ]
    sched = (env.get("LR_SCHEDULER") or "").strip()
    if sched:
        out["lr_scheduler_type"] = sched
        if sched == "cosine_with_min_lr":
            out["lr_scheduler_kwargs"] = {"min_lr_rate": 0.1}
    metric = (env.get("METRIC_FOR_BEST") or "").strip()
    if metric:
        out["metric_for_best"] = metric
    composite = _env_flag(env, "USE_COMPOSITE_EARLY_STOP")
    if composite is not None:
        out["use_composite_early_stop"] = composite
        if composite:
            out["composite_early_stop_metrics"] = resolve_composite_early_stop_metrics(
                env,
                [
                    "eval_spurgeon_loss",
                    "eval_puritan_loss",
                    "eval_confession_loss",
                ],
            )
    return out


def aggregate_token_losses(doc_rows):
    """Token-weighted mean loss. Rows need index, tokens, loss. Drops tokens < 2."""
    total_loss = 0.0
    total_tokens = 0
    kept = []
    for row in doc_rows or []:
        try:
            tokens = int(row.get("tokens") or 0)
        except (TypeError, ValueError):
            continue
        if tokens < 2 or row.get("loss") is None:
            continue
        loss = float(row["loss"])
        total_loss += loss * tokens
        total_tokens += tokens
        kept.append(
            {
                "index": int(row.get("index", len(kept))),
                "tokens": tokens,
                "loss": loss,
            }
        )
    if total_tokens == 0:
        return {"tokens": 0, "loss": None, "ppl": None, "docs": 0, "per_doc": kept}
    avg = total_loss / float(total_tokens)
    return {
        "tokens": total_tokens,
        "loss": avg,
        "ppl": math.exp(avg),
        "docs": len(kept),
        "per_doc": kept,
    }


def exclude_doc_indices(bucket):
    """Diagnostic exclusions. Empty for buckets that are not on the noisy list."""
    raw = CLEAN_HOLDOUT_EXCLUDE.get(bucket) or ()
    return set(int(i) for i in raw)


def clean_subset_rows(bucket, doc_rows):
    skip = exclude_doc_indices(bucket)
    return [row for row in (doc_rows or []) if int(row.get("index", -1)) not in skip]


def _percentile(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = float(q) * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_vals[lo])
    weight = pos - lo
    return float(sorted_vals[lo]) * (1.0 - weight) + float(sorted_vals[hi]) * weight


def _rows_by_index(doc_rows):
    out = {}
    for row in doc_rows or []:
        if row.get("loss") is None:
            continue
        try:
            tokens = int(row.get("tokens") or 0)
            index = int(row.get("index"))
        except (TypeError, ValueError):
            continue
        if tokens < 2:
            continue
        out[index] = {"index": index, "tokens": tokens, "loss": float(row["loss"])}
    return out


def _weighted_loss(rows_by, indices):
    total_loss = 0.0
    total_tokens = 0.0
    for index in indices:
        row = rows_by[index]
        tokens = float(row["tokens"])
        total_loss += float(row["loss"]) * tokens
        total_tokens += tokens
    if total_tokens <= 0:
        return None
    return total_loss / total_tokens


def bootstrap_ppl_delta_ci(adapter_rows, base_rows, n_resamples=1000, seed=42, alpha=0.05):
    """95% CI on PPL percent change, resampling paired documents with replacement."""
    by_adapter = _rows_by_index(adapter_rows)
    by_base = _rows_by_index(base_rows)
    common = sorted(set(by_adapter) & set(by_base))
    empty = {
        "n": len(common),
        "delta_loss": None,
        "delta_pct": None,
        "ci_low": None,
        "ci_high": None,
        "n_resamples": 0,
    }
    if len(common) < 2:
        return empty
    point_adapter = _weighted_loss(by_adapter, common)
    point_base = _weighted_loss(by_base, common)
    if point_adapter is None or point_base is None:
        return empty
    base_ppl = math.exp(point_base)
    adapter_ppl = math.exp(point_adapter)
    rng = random.Random(int(seed))
    samples = []
    n = len(common)
    draws = int(n_resamples)
    for _ in range(draws):
        picked = [common[rng.randrange(n)] for _ in range(n)]
        a_loss = _weighted_loss(by_adapter, picked)
        b_loss = _weighted_loss(by_base, picked)
        if a_loss is None or b_loss is None:
            continue
        b_ppl = math.exp(b_loss)
        if b_ppl == 0:
            continue
        samples.append(100.0 * (math.exp(a_loss) - b_ppl) / b_ppl)
    samples.sort()
    return {
        "n": n,
        "delta_loss": point_adapter - point_base,
        "delta_pct": 100.0 * (adapter_ppl - base_ppl) / base_ppl,
        "ci_low": _percentile(samples, alpha / 2.0),
        "ci_high": _percentile(samples, 1.0 - alpha / 2.0),
        "n_resamples": len(samples),
    }


def attach_holdout_diagnostics(metrics, buckets, n_resamples=1000, seed=42):
    """Add clean sub-score and bootstrap CI. Does not change pinned holdout bytes."""
    metrics["clean"] = {}
    metrics["delta_clean_vs_base_pct"] = {}
    metrics["delta_ci95"] = {}
    v2 = metrics.get("v2") or {}
    base = metrics.get("base") or {}
    for name in buckets or []:
        v_rows = list((v2.get(name) or {}).get("per_doc") or [])
        b_rows = list((base.get(name) or {}).get("per_doc") or [])
        if v_rows and b_rows:
            metrics["delta_ci95"][name] = bootstrap_ppl_delta_ci(
                v_rows, b_rows, n_resamples=n_resamples, seed=seed
            )
        excluded = sorted(exclude_doc_indices(name))
        v_clean = aggregate_token_losses(clean_subset_rows(name, v_rows))
        b_clean = aggregate_token_losses(clean_subset_rows(name, b_rows))
        v_clean.pop("per_doc", None)
        b_clean.pop("per_doc", None)
        metrics["clean"][name] = {
            "v2": v_clean,
            "base": b_clean,
            "excluded_doc_indices": excluded,
        }
        b_ppl = b_clean.get("ppl")
        v_ppl = v_clean.get("ppl")
        if b_ppl and v_ppl:
            metrics["delta_clean_vs_base_pct"][name] = round(
                100.0 * (v_ppl - b_ppl) / b_ppl, 2
            )
    return metrics

# skipped notebook Unsloth install cell (use --install)

import torch
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

import os
import json
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Stock flagship. CPT_BASE_MODEL is the train base (merged weights) and is not the C reference.
MODEL_NAME = resolve_eval_base_model()
_train_base = (os.environ.get("CPT_BASE_MODEL") or "").strip()
if _train_base and _train_base != MODEL_NAME:
    print("CPT_BASE_MODEL", _train_base, "is the train base; eval base stays", MODEL_NAME)
print("eval base model", MODEL_NAME)
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
if ADAPTER_OVERRIDE and "checkpoint-25" in str(ADAPTER_OVERRIDE).replace("\\", "/"):
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

print("Config OK")

from unsloth import FastLanguageModel
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


def maybe_sync_tied_lm_head(model, modules_to_save=None, label="adapter"):
    """Diagnose + optionally copy embed_tokens → lm_head after embed-FT LoRA load.

    Qwen3.5 has tie_word_embeddings=True. Unsloth/PEFT with modules_to_save=['embed_tokens']
    and ensure_weight_tying=false can leave lm_head untied/stale at inference, inflating PPL.
    Env CPT_EVAL_SYNC_TIED_HEAD: default ON when embed_tokens is in modules_to_save;
    set 0/false/off to disable.
    """
    mts = list(modules_to_save or [])
    env = (os.environ.get("CPT_EVAL_SYNC_TIED_HEAD") or "").strip().lower()
    if env in ("0", "false", "no", "off"):
        want = False
    elif env in ("1", "true", "yes", "on"):
        want = True
    else:
        want = "embed_tokens" in mts

    emb = model.get_input_embeddings() if hasattr(model, "get_input_embeddings") else None
    head = model.get_output_embeddings() if hasattr(model, "get_output_embeddings") else None
    cfg = getattr(model, "config", None)
    tie = getattr(cfg, "tie_word_embeddings", None) if cfg is not None else None
    same = None
    max_delta = None
    if (
        emb is not None
        and head is not None
        and hasattr(emb, "weight")
        and hasattr(head, "weight")
        and emb.weight is not None
        and head.weight is not None
    ):
        same = int(emb.weight.data_ptr() == head.weight.data_ptr())
        if not same and tuple(emb.weight.shape) == tuple(head.weight.shape):
            max_delta = float(
                (emb.weight.detach().float() - head.weight.detach().float()).abs().max().item()
            )
    print(
        f"tie_diag label={label} tie_word_embeddings={tie} same_storage={same} "
        f"max_abs_delta={max_delta} modules_to_save={mts} sync_wanted={want}"
    )
    synced = 0
    if (
        want
        and same == 0
        and emb is not None
        and head is not None
        and hasattr(emb, "weight")
        and hasattr(head, "weight")
        and tuple(emb.weight.shape) == tuple(head.weight.shape)
    ):
        with torch.no_grad():
            head.weight.copy_(emb.weight)
        synced = 1
        max_after = float(
            (emb.weight.detach().float() - head.weight.detach().float()).abs().max().item()
        )
        same_after = int(emb.weight.data_ptr() == head.weight.data_ptr())
        print(
            f"embed_to_lm_head_synced={synced} same_storage_after={same_after} "
            f"max_abs_delta_after={max_after}"
        )
    else:
        print(f"embed_to_lm_head_synced={synced}")
    return synced


maybe_sync_tied_lm_head(model, modules_to_save=_mts, label="v2")


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
    raise RuntimeError("text tokenize smoke failed")

def eval_ppl(model, tokenizer, dataset, max_docs=None, max_seq=MAX_SEQ_LENGTH):
    n = len(dataset) if max_docs is None else min(len(dataset), max_docs)
    rows = []
    for i in range(n):
        text = dataset[i]["text"]
        inputs = tokenize_text(tokenizer, text, max_seq=max_seq, add_special_tokens=False)
        num_tokens = inputs["input_ids"].size(1)
        if num_tokens < 2:
            rows.append({"index": i, "tokens": int(num_tokens), "loss": None})
            continue
        with torch.no_grad():
            out = model(**inputs, labels=inputs["input_ids"])
            loss = out.loss.item()
        rows.append({"index": i, "tokens": int(num_tokens), "loss": float(loss)})
    return aggregate_token_losses(rows)

# §5 / Hub gate: spurgeon + puritan + confession (pinned v3). general + new_authors = monitor-only.
_gate_buckets = ["spurgeon", "puritan", "confession", "general"]
_monitor_buckets = ["new_authors"]
buckets = list(_gate_buckets)
for _mb in _monitor_buckets:
    _mp = os.path.join(HOLDOUT_ROOT, _mb)
    if os.path.isfile(os.path.join(_mp, "dataset_info.json")) or os.path.isfile(
        os.path.join(_mp, "state.json")
    ):
        buckets.append(_mb)
    else:
        print("Isolation C: skip missing monitor holdout", _mb)
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

# Optional: score first N Spurgeon holdout docs (train-eval protocol). Env CPT_EVAL_TRAIN_PROBE_DOCS.
_train_probe_n = 0
try:
    _train_probe_n = int((os.environ.get("CPT_EVAL_TRAIN_PROBE_DOCS") or "0").strip() or "0")
except ValueError:
    _train_probe_n = 0
if _train_probe_n > 0:
    _sp = load_holdout("spurgeon")
    if _sp is not None:
        print(f"Evaluating train-probe Spurgeon PPL (first {_train_probe_n} docs)...")
        metrics["train_probe_spurgeon"] = eval_ppl(
            model, tokenizer, _sp, max_docs=_train_probe_n
        )
        _tp = metrics["train_probe_spurgeon"]
        if _tp.get("ppl") is not None:
            print(
                f"  train_probe spurgeon@{_train_probe_n}: "
                f"ppl={_tp['ppl']:.2f} loss={_tp['loss']:.4f} tokens={_tp['tokens']:,} docs={_tp['docs']}"
            )
    else:
        print("train_probe skip: spurgeon holdout missing")

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
        scores = [option_logprob(model, tok, f"Q. {it['q']}\nA.", o) for o in opts]
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
    _score_mts = []
    _score_cfg = os.path.join(str(model_name_or_path), "adapter_config.json")
    if os.path.isfile(_score_cfg):
        try:
            _score_mts = json.load(open(_score_cfg, encoding="utf-8")).get("modules_to_save") or []
        except Exception:
            _score_mts = []
    maybe_sync_tied_lm_head(m, modules_to_save=_score_mts, label=label)
    out = {}
    for name in buckets:
        ds = load_holdout(name)
        if ds is None:
            continue
        out[name] = eval_ppl(m, t, ds, max_docs=MAX_DOCS_PER_BUCKET)
        if out[name]["ppl"] is not None:
            print(f"  {label} {name}: ppl={out[name]['ppl']:.2f}")
    if _train_probe_n > 0:
        _sp = load_holdout("spurgeon")
        if _sp is not None:
            _tp = eval_ppl(m, t, _sp, max_docs=_train_probe_n)
            out["_train_probe_spurgeon"] = _tp
            if _tp.get("ppl") is not None:
                print(
                    f"  {label} train_probe spurgeon@{_train_probe_n}: "
                    f"ppl={_tp['ppl']:.2f} loss={_tp['loss']:.4f} docs={_tp['docs']}"
                )
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
    _tpb = (metrics["base"] or {}).pop("_train_probe_spurgeon", None)
    if _tpb is not None:
        metrics["train_probe_spurgeon_base"] = _tpb
if EVAL_PHASE1 and PHASE1_ADAPTER_PATH:
    metrics["phase1"], _ = score_model("phase1", PHASE1_ADAPTER_PATH, also_mcq=False)

_tpa = (metrics.get("train_probe_spurgeon") or {}).get("ppl")
_tpb_ppl = (metrics.get("train_probe_spurgeon_base") or {}).get("ppl")
if _tpa and _tpb_ppl:
    _tp_pct = 100.0 * (_tpa - _tpb_ppl) / _tpb_ppl
    metrics["train_probe_spurgeon_delta_pct"] = round(_tp_pct, 2)
    print(f"train_probe spurgeon Δ% vs base@{_train_probe_n}: {_tp_pct:+.1f}%")

# Δ table vs base
print("\n=== Δ PPL vs base (% lower is better absorption for domain buckets) ===")
print(f"{'bucket':12s}  {'base':>8s}  {'v2':>8s}  {'%Δ':>8s}")
for name in buckets:
    b = (metrics["base"].get(name) or {}).get("ppl")
    v = (metrics["v2"].get(name) or {}).get("ppl")
    if b and v:
        pct = 100.0 * (v - b) / b
        metrics["delta_vs_base_pct"][name] = round(pct, 2)
        print(f"{name:12s}  {b:8.2f}  {v:8.2f}  {pct:7.1f}%")

attach_holdout_diagnostics(metrics, buckets)
print("\n=== clean sub-score + bootstrap 95% CI on %Δ (gate bytes unchanged) ===")
for name in buckets:
    pct = (metrics.get("delta_clean_vs_base_pct") or {}).get(name)
    ci = (metrics.get("delta_ci95") or {}).get(name) or {}
    excl = ((metrics.get("clean") or {}).get(name) or {}).get("excluded_doc_indices")
    lo = ci.get("ci_low")
    hi = ci.get("ci_high")
    if pct is None and lo is None:
        continue
    lo_s = f"{lo:.2f}" if isinstance(lo, float) else str(lo)
    hi_s = f"{hi:.2f}" if isinstance(hi, float) else str(hi)
    pct_s = f"{pct:.2f}" if isinstance(pct, float) else str(pct)
    print(f"{name:12s}  clean %Δ={pct_s}  ci95=[{lo_s}, {hi_s}]  excluded={excl}")

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
        m = re.match(r"checkpoint-(\d+)$", name)
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
        print("\n=== last ckpt Δ PPL vs base ===")
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
print("Wrote", OUT_METRICS)

style_prompts = [
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
    print(f"\n=== {label.upper()} (greedy, seed={PROBE_SEED}) ===")
    for p in prompts:
        text = generate(p, greedy=True, max_new_tokens=120 if label != "forgetting" else 40)
        print("\n---\n", text[:800])
        entry = {"prompt": p, "completion": text}
        ratio = _trigram_repeat_ratio(text)
        if ratio >= 0.25:
            msg = f"PROBE WARNING: repetition loop ({label}, trigram_repeat={ratio:.2f})"
            print(msg)
            entry["repetition_ratio"] = round(ratio, 3)
            probe_log["repetition_warnings"].append({"label": label, "ratio": round(ratio, 3), "prompt": p[:80]})
        probe_log["greedy"][label].append(entry)

# Optional flavor (non-comparable)
print("\n=== Style (sampled, flavor only) ===")
probe_log["sampled"]["style"] = []
for p in style_prompts[:1]:
    text = generate(p, greedy=False)
    print(text[:500])
    probe_log["sampled"]["style"].append({"prompt": p, "completion": text})

if probe_log["repetition_warnings"]:
    print(f"\nRC6: {len(probe_log['repetition_warnings'])} greedy probe(s) showed repetition loops (informational).")

metrics["probes"] = probe_log
with open(OUT_METRICS, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

mcq_metrics = dict(metrics.get("mcq") or {})
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
print("Updated", OUT_METRICS)

if RUN_MERGE:
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

print("Done. Metrics at", OUT_METRICS)

