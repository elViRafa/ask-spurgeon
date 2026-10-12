#!/usr/bin/env python3
"""S8 CPT sweep plan and local readiness. Does not rent a GPU or start training.

Arms (one pack, new LoRA each):
  m_lo  merged a70fded8 + r=128, body LR 2e-5
  m_hi  merged a70fded8 + r=128, body LR 5e-5
  f_hi  stock Qwen3.5-4B-Base + r=128, body LR 5e-5

Plateau is broken when an arm's best in-train puritan loss is at least
0.015 nats under the plateau reference, with Spurgeon and general still in band.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

INIT_SHA = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
MIX_SHA = "ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962"
STOCK_BASE = "unsloth/Qwen3.5-4B-Base"
MERGED_DIR = "/workspace/theology_cpt_merged_a70"
STACK_PIN = "Unsloth 2026.8.22 + torch 2.8"
# Replay checkpoint-600 in-train puritan CE. P0 did not move this band.
PURITAN_REF_LOSS = 1.7354
PURITAN_BREAK_DELTA = 0.015
SPURGEON_CEILING = 2.490  # plateau band 2.480 + 0.01
OOM_RANK = "64"
OOM_ALPHA = "45"

SHARED = {
    "CPT_RUN_MODE": "fresh",
    "CPT_DATA_ROOT": "/workspace",
    "CPT_HOLDOUT_PATH": "/workspace/theology_holdouts",
    "HF_HOME": "/workspace/hf_home",
    "GPU_PROFILE": "ampere",
    "PREV_RUN_CHECKPOINT": "",
    "LORA_RANK": "128",
    "LORA_ALPHA": "64",
    "MAX_STEPS": "400",
    "WARMUP_RATIO": "0.05",
    "ABORT_SPURGEON_STEP": "0",
    "EARLY_STOP_MIN_STEPS": "400",
    "LR_SCHEDULER": "cosine_with_min_lr",
    "METRIC_FOR_BEST": "eval_puritan_loss",
    "EVAL_DOCS_PER_BUCKET": "16",
    "EVAL_STEPS": "50",
    "SAVE_STEPS": "50",
    "EVAL_BUCKETS_DURING_TRAIN": "spurgeon,puritan,confession,general",
    "USE_COMPOSITE_EARLY_STOP": "1",
    "COMPOSITE_EARLY_STOP_METRICS": "eval_spurgeon_loss,eval_puritan_loss,eval_confession_loss",
    "EARLY_STOPPING_PATIENCE": "4",
    "PYTHONUNBUFFERED": "1",
    "UNSLOTH_PIP_SPEC": "unsloth[colab-new]==2026.8.22",
    "UNSLOTH_SKIP_TORCHVISION_CHECK": "1",
}

ARMS = (
    {
        "id": "m_lo",
        "learning_rate": "2e-5",
        "embedding_learning_rate": "2e-6",
        "base_model": MERGED_DIR,
        "needs_merge": True,
    },
    {
        "id": "m_hi",
        "learning_rate": "5e-5",
        "embedding_learning_rate": "5e-6",
        "base_model": MERGED_DIR,
        "needs_merge": True,
    },
    {
        "id": "f_hi",
        "learning_rate": "5e-5",
        "embedding_learning_rate": "5e-6",
        "base_model": STOCK_BASE,
        "needs_merge": False,
    },
)


def repo_root() -> Path:
    """Directory that contains continued_pretrain and fine_tuning.

    Called only from readiness(). --emit-arm must not touch this: on the pod
    the script is /workspace/vast_cpt_s8_sweep_plan.py and has no parents[2].
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "continued_pretrain").is_dir() and (parent / "fine_tuning").is_dir():
            return parent
    raise SystemExit(f"repo root not found from {here}")


def local_paths() -> dict[str, Path]:
    repo = repo_root()
    cpt = repo / "continued_pretrain"
    return {
        "adapter": (
            cpt
            / "kaggle"
            / "runpod_cpt_v3"
            / "vast_cpt_s7_p0"
            / "fetch"
            / "theology_cpt_lora_s5best"
            / "adapter_model.safetensors"
        ),
        "meta": cpt / "kaggle" / "a_output_v6_p0" / "DATASET_META.json",
        "dataset": cpt / "kaggle" / "a_output_v6_p0" / "theology_dataset" / "dataset_dict.json",
        "holdout": cpt / "kaggle" / "a_output_v6_p0" / "theology_holdouts" / "spurgeon" / "dataset_info.json",
        "train": cpt / "scripts" / "train_cpt_sota.py",
        "eval": cpt / "scripts" / "eval_cpt_sota.py",
        "runtime": cpt / "scripts" / "cpt_runtime.py",
        "merge": repo / "fine_tuning" / "scripts" / "merge_cpt_lora.py",
        "remote": cpt / "scripts" / "vast_cpt_s8_sweep_remote.sh",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def arm_by_id(arm_id: str) -> dict:
    for arm in ARMS:
        if arm["id"] == arm_id:
            return arm
    raise SystemExit(f"unknown arm {arm_id}")


def arm_env(arm: dict, *, oom_fallback: bool = False) -> dict:
    env = dict(SHARED)
    env["CPT_WORK_ROOT"] = f"/workspace/sweep/{arm['id']}"
    env["CPT_OUTPUT_DIR"] = f"/workspace/sweep/{arm['id']}/checkpoints"
    env["CPT_BASE_MODEL"] = arm["base_model"]
    env["LEARNING_RATE"] = arm["learning_rate"]
    env["EMBEDDING_LEARNING_RATE"] = arm["embedding_learning_rate"]
    if oom_fallback:
        env["LORA_RANK"] = OOM_RANK
        env["LORA_ALPHA"] = OOM_ALPHA
    return env


def emit_arm(arm_id: str, *, oom_fallback: bool = False) -> str:
    env = arm_env(arm_by_id(arm_id), oom_fallback=oom_fallback)
    lines = [f"export {key}={value}" if value else f"export {key}=" for key, value in env.items()]
    return "\n".join(lines) + "\n"


def readiness() -> list[str]:
    paths = local_paths()
    errors: list[str] = []
    required = (
        (paths["adapter"], "P0 adapter a70fded8"),
        (paths["meta"], "a_output_v6_p0 DATASET_META"),
        (paths["dataset"], "a_output_v6_p0 dataset"),
        (paths["holdout"], "a_output_v6_p0 spurgeon holdout"),
        (paths["train"], "train_cpt_sota.py"),
        (paths["eval"], "eval_cpt_sota.py"),
        (paths["runtime"], "cpt_runtime.py"),
        (paths["merge"], "merge_cpt_lora.py"),
        (paths["remote"], "vast_cpt_s8_sweep_remote.sh"),
    )
    for path, label in required:
        if not path.is_file():
            errors.append(f"missing {label}: {path}")
    if paths["adapter"].is_file():
        got = sha256_file(paths["adapter"])
        if got.lower() != INIT_SHA.lower():
            errors.append(f"adapter SHA {got} != {INIT_SHA}")
    if paths["meta"].is_file():
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        mix = (meta.get("mix_sha256") or "").lower()
        if mix != MIX_SHA.lower():
            errors.append(f"mix SHA {mix} != {MIX_SHA}")
    if paths["train"].is_file():
        train = paths["train"].read_text(encoding="utf-8")
        for needle in ("apply_env_model_overrides", "resolve_fresh_training_env", "MAX_STEPS pinned"):
            if needle not in train:
                errors.append(f"train_cpt_sota.py missing {needle}")
    if paths["eval"].is_file():
        text = paths["eval"].read_text(encoding="utf-8")
        for needle in ("resolve_eval_base_model", "attach_holdout_diagnostics", "per_doc"):
            if needle not in text:
                errors.append(f"eval_cpt_sota.py missing {needle}")
    if paths["runtime"].is_file() and 'profile == "s8"' not in paths["runtime"].read_text(encoding="utf-8"):
        errors.append("cpt_runtime.py missing s8 profile")
    if paths["remote"].is_file():
        remote = paths["remote"].read_text(encoding="utf-8")
        for needle in (
            "merge_cpt_lora.py",
            "--emit-arm",
            "2026.8.22",
            "torch==2.8.0",
            INIT_SHA,
            'test -s "$emit_file"',
        ):
            if needle not in remote:
                errors.append(f"remote launcher missing {needle}")
    return errors


def print_ready() -> None:
    print("=== Vast CPT S8 sweep readiness (no rent) ===")
    print(f"pack=a_output_v6_p0 mix_sha256={MIX_SHA}")
    print(f"init_adapter={INIT_SHA}")
    print(f"stack={STACK_PIN}")
    print(f"merged_base={MERGED_DIR}")
    print(
        f"decision: puritan in-train loss <= {PURITAN_REF_LOSS - PURITAN_BREAK_DELTA:.4f} "
        f"(ref {PURITAN_REF_LOSS} - {PURITAN_BREAK_DELTA}); "
        f"spurgeon <= {SPURGEON_CEILING}; general within base +2%"
    )
    print("oom_fallback: LORA_RANK=64 LORA_ALPHA=45 (rsLoRA scale stays ~5.66)")
    for arm in ARMS:
        env = arm_env(arm)
        print(
            f"arm {arm['id']}: base={env['CPT_BASE_MODEL']} "
            f"lr={env['LEARNING_RATE']} emb_lr={env['EMBEDDING_LEARNING_RATE']} "
            f"r={env['LORA_RANK']} alpha={env['LORA_ALPHA']} steps={env['MAX_STEPS']}"
        )
    print("READY")


def _best_puritan(log_history) -> float | None:
    best = None
    for entry in log_history or []:
        if not isinstance(entry, dict):
            continue
        value = entry.get("eval_puritan_loss")
        if value is None:
            continue
        loss = float(value)
        best = loss if best is None else min(best, loss)
    return best


def summarize(sweep_root: Path) -> int:
    threshold = PURITAN_REF_LOSS - PURITAN_BREAK_DELTA
    print(f"puritan break threshold {threshold:.4f} (ref {PURITAN_REF_LOSS})")
    any_broke = False
    for arm in ARMS:
        state = sweep_root / arm["id"] / "checkpoints" / "trainer_state.json"
        matches = list((sweep_root / arm["id"]).rglob("trainer_state.json"))
        path = state if state.is_file() else (matches[-1] if matches else None)
        if path is None or not Path(path).is_file():
            print(f"{arm['id']}: no trainer_state")
            continue
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        best = _best_puritan(data.get("log_history"))
        if best is None:
            print(f"{arm['id']}: no eval_puritan_loss in {path}")
            continue
        broke = best <= threshold
        any_broke = any_broke or broke
        print(f"{arm['id']}: best eval_puritan_loss={best:.4f} broke={broke} state={path}")
    print("SWEEP_BROKE_PLATEAU" if any_broke else "SWEEP_STILL_FLAT")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S8 sweep plan (no GPU)")
    parser.add_argument("--emit-arm", default="", help="Print bash exports for one arm")
    parser.add_argument("--oom-fallback", action="store_true", help="Emit r=64 alpha=45")
    parser.add_argument("--summarize", default="", help="Read sweep dir trainer states")
    args = parser.parse_args(argv)
    if args.emit_arm:
        sys.stdout.write(emit_arm(args.emit_arm, oom_fallback=args.oom_fallback))
        return 0
    if args.summarize:
        return summarize(Path(args.summarize))
    errors = readiness()
    if errors:
        print("=== Vast CPT S8 sweep readiness FAIL ===")
        for err in errors:
            print("ERROR", err)
        return 1
    print_ready()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
