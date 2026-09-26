#!/usr/bin/env python3
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
    """``s7`` when CPT_CONTINUE_PROFILE=s7; otherwise empty (S6 continue defaults)."""
    env = os.environ if env is None else env
    profile = (env.get("CPT_CONTINUE_PROFILE") or "").strip().lower()
    return "s7" if profile == "s7" else ""


def layout_paths(work_root, env=None):
    """Resolve work-root layout. S7 continue writes to checkpoints_s7, not sota."""
    env = os.environ if env is None else env
    explicit = (env.get("CPT_OUTPUT_DIR") or "").strip()
    if explicit:
        output_dir = explicit
    elif resolve_run_mode(env) == "continue" and resolve_continue_profile(env) == "s7":
        output_dir = os.path.join(work_root, "checkpoints_s7")
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
            os.path.join(work_root, "a_output_v6"),
            os.path.join(work_root, "a_output_v5"),
            os.path.join(work_root, "a_output_v4"),
            os.path.join(work_root, "a_output_v3"),
            os.path.join(work_root, "kaggle", "a_output"),
            os.path.join(work_root, "kaggle", "a_output_v6"),
            os.path.join(work_root, "kaggle", "a_output_v5"),
            os.path.join(work_root, "kaggle", "a_output_v4"),
            os.path.join(work_root, "kaggle", "a_output_v3"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v6"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v5"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v4"),
            os.path.join(cwd, "continued_pretrain", "kaggle", "a_output_v3"),
            os.path.join(cwd, "kaggle", "a_output"),
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
    if resolve_run_mode(env) == "continue" and resolve_continue_profile(env) == "s7":
        explicit = (env.get("CPT_OUTPUT_DIR") or "").strip()
        local = explicit or os.path.join(work_root, "checkpoints_s7")
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
    4-metric composite). Unset profile keeps S6 continue defaults (4e-6, 0.4 epoch floor).
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
