#!/usr/bin/env python3
"""S8 m_hi resume plan and local readiness. Does not rent a GPU or start training.

One arm: HF-resume the fetched continue checkpoint-800 (optimizer + rng) on a
fresh merge of a70fded8. 1600 new steps at the same 5e-6 constant floor.
Early-stop cannot fire before step 2400.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MERGE_SHA = "a70fded8aea1c9cb1a484e640e89137412519c28d95bdbfbf8d73ca2d2e42eac"
INIT_SHA = "8c1db3db74bcf03b876740a5cf8884899fb3efda4945a2ae74a02655a8359b84"
MIX_SHA = "ad817213af207428785c4cfac12ddc1bc390b3e59d6e97b43491fafdafe91962"
MERGED_DIR = "/workspace/theology_cpt_merged_a70"
INIT_DIR = "/workspace/mhi_lora"
CKPT_DIR = "/workspace/ckpt800"
WORK_ROOT = "/workspace/mhi_resume"
STACK_PIN = "Unsloth 2026.8.22 + torch 2.8"
PURITAN_C_PROXY = 1.670
PURITAN_C_TARGET = 1.6349
SPURGEON_CEILING = 2.490

ENV = {
    "CPT_RUN_MODE": "continue",
    "CPT_CONTINUE_PROFILE": "s8",
    "CPT_INIT_ADAPTER": INIT_DIR,
    "CPT_BASE_MODEL": MERGED_DIR,
    "CPT_WORK_ROOT": WORK_ROOT,
    "CPT_OUTPUT_DIR": f"{WORK_ROOT}/checkpoints",
    "CPT_DATA_ROOT": "/workspace",
    "CPT_HOLDOUT_PATH": "/workspace/theology_holdouts",
    "HF_HOME": "/workspace/hf_home",
    "GPU_PROFILE": "ampere",
    "PREV_RUN_CHECKPOINT": CKPT_DIR,
    "EXPECTED_ADAPTER_SHA256": INIT_SHA,
    "LORA_RANK": "128",
    "LORA_ALPHA": "64",
    "LEARNING_RATE": "5e-6",
    "EMBEDDING_LEARNING_RATE": "5e-7",
    "MAX_STEPS": "2400",
    "WARMUP_RATIO": "0",
    "LR_SCHEDULER": "constant",
    "ABORT_SPURGEON_STEP": "0",
    "EARLY_STOP_MIN_STEPS": "2400",
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


def repo_root() -> Path:
    """Directory that contains continued_pretrain and fine_tuning.

    Called only from readiness(). --emit must not touch this: on the pod the
    script is /workspace/vast_cpt_s8_mhi_resume_plan.py and has no parents[2].
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "continued_pretrain").is_dir() and (parent / "fine_tuning").is_dir():
            return parent
    raise SystemExit(f"repo root not found from {here}")


def local_paths() -> dict[str, Path]:
    repo = repo_root()
    cpt = repo / "continued_pretrain"
    ckpt = (
        cpt
        / "kaggle"
        / "runpod_cpt_v3"
        / "vast_cpt_s8_mhi_continue"
        / "fetch"
        / "mhi_continue"
        / "checkpoints"
        / "checkpoint-800"
    )
    return {
        "merge_adapter": (
            cpt
            / "kaggle"
            / "runpod_cpt_v3"
            / "vast_cpt_s7_p0"
            / "fetch"
            / "theology_cpt_lora_s5best"
            / "adapter_model.safetensors"
        ),
        "resume_adapter": ckpt / "adapter_model.safetensors",
        "resume_optimizer": ckpt / "optimizer.pt",
        "resume_rng": ckpt / "rng_state.pth",
        "resume_scheduler": ckpt / "scheduler.pt",
        "resume_state": ckpt / "trainer_state.json",
        "meta": cpt / "kaggle" / "a_output_v6_p0" / "DATASET_META.json",
        "dataset": cpt / "kaggle" / "a_output_v6_p0" / "theology_dataset" / "dataset_dict.json",
        "holdout": cpt / "kaggle" / "a_output_v6_p0" / "theology_holdouts" / "spurgeon" / "dataset_info.json",
        "train": cpt / "scripts" / "train_cpt_sota.py",
        "eval": cpt / "scripts" / "eval_cpt_sota.py",
        "runtime": cpt / "scripts" / "cpt_runtime.py",
        "merge": repo / "fine_tuning" / "scripts" / "merge_cpt_lora.py",
        "remote": cpt / "scripts" / "vast_cpt_s8_mhi_resume_remote.sh",
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


def emit() -> str:
    lines = [f"export {key}={value}" if value else f"export {key}=" for key, value in ENV.items()]
    return "\n".join(lines) + "\n"


def readiness() -> list[str]:
    paths = local_paths()
    errors: list[str] = []
    required = (
        (paths["merge_adapter"], "merge adapter a70fded8"),
        (paths["resume_adapter"], "checkpoint-800 adapter"),
        (paths["resume_optimizer"], "checkpoint-800 optimizer"),
        (paths["resume_rng"], "checkpoint-800 rng"),
        (paths["resume_scheduler"], "checkpoint-800 scheduler"),
        (paths["resume_state"], "checkpoint-800 trainer_state"),
        (paths["meta"], "a_output_v6_p0 DATASET_META"),
        (paths["dataset"], "a_output_v6_p0 dataset"),
        (paths["holdout"], "a_output_v6_p0 spurgeon holdout"),
        (paths["train"], "train_cpt_sota.py"),
        (paths["eval"], "eval_cpt_sota.py"),
        (paths["runtime"], "cpt_runtime.py"),
        (paths["merge"], "merge_cpt_lora.py"),
        (paths["remote"], "vast_cpt_s8_mhi_resume_remote.sh"),
    )
    for path, label in required:
        if not path.is_file():
            errors.append(f"missing {label}: {path}")
    if paths["merge_adapter"].is_file():
        got = sha256_file(paths["merge_adapter"])
        if got.lower() != MERGE_SHA.lower():
            errors.append(f"merge adapter SHA {got} != {MERGE_SHA}")
    if paths["resume_adapter"].is_file():
        got = sha256_file(paths["resume_adapter"])
        if got.lower() != INIT_SHA.lower():
            errors.append(f"resume adapter SHA {got} != {INIT_SHA}")
    if paths["resume_state"].is_file():
        state = json.loads(paths["resume_state"].read_text(encoding="utf-8"))
        step = int(state.get("global_step") or 0)
        if step != 800:
            errors.append(f"checkpoint-800 global_step {step} != 800")
    if paths["meta"].is_file():
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        mix = (meta.get("mix_sha256") or "").lower()
        if mix != MIX_SHA.lower():
            errors.append(f"mix SHA {mix} != {MIX_SHA}")
    if paths["train"].is_file():
        train = paths["train"].read_text(encoding="utf-8")
        for needle in ("CPT_INIT_ADAPTER", "LR_SCHEDULER", "sched_kwargs", "resume_from_checkpoint"):
            if needle not in train:
                errors.append(f"train_cpt_sota.py missing {needle}")
    if paths["runtime"].is_file() and 'profile == "s8"' not in paths["runtime"].read_text(encoding="utf-8"):
        errors.append("cpt_runtime.py missing s8 profile")
    if paths["remote"].is_file():
        remote = paths["remote"].read_text(encoding="utf-8")
        for needle in (
            "merge_cpt_lora.py",
            "--emit",
            "2026.8.22",
            "torch==2.8.0",
            MERGE_SHA,
            INIT_SHA,
            "mhi_lora",
            "ckpt800",
            "unset EXPECTED_ADAPTER_SHA256",
            "RECIPE_OK",
            'test "$LEARNING_RATE" = 5e-6',
            'test "$LR_SCHEDULER" = constant',
            'test "$PREV_RUN_CHECKPOINT" = /workspace/ckpt800',
            'test "$MAX_STEPS" = 2400',
            'test -s "$emit_file"',
        ):
            if needle not in remote:
                errors.append(f"remote launcher missing {needle}")
        if "export PREV_RUN_CHECKPOINT=\n" in remote or "vast_cpt_s8_mhi_continue_remote.sh" in remote:
            errors.append("remote launcher still points at the new-Adam continue")
        if "run_arm m_lo" in remote or "vast_cpt_s8_sweep_remote.sh" in remote:
            errors.append("remote launcher still points at the S8 sweep")
    return errors


def print_ready() -> None:
    print("=== Vast CPT S8 m_hi resume readiness (no rent) ===")
    print(f"pack=a_output_v6_p0 mix_sha256={MIX_SHA}")
    print(f"merge_adapter={MERGE_SHA}")
    print(f"resume_adapter={INIT_SHA}")
    print(f"stack={STACK_PIN}")
    print(f"merged_base={MERGED_DIR}")
    print(f"init_dir={INIT_DIR}")
    print(f"prev_checkpoint={CKPT_DIR}")
    print(
        f"lr={ENV['LEARNING_RATE']} emb_lr={ENV['EMBEDDING_LEARNING_RATE']} "
        f"warmup={ENV['WARMUP_RATIO']} scheduler={ENV['LR_SCHEDULER']} "
        f"steps={ENV['MAX_STEPS']} early_stop_min={ENV['EARLY_STOP_MIN_STEPS']}"
    )
    print(
        f"decision: in-train proxy <= {PURITAN_C_PROXY:.3f} then isolation C "
        f"(section-5 puritan <= {PURITAN_C_TARGET}); spurgeon <= {SPURGEON_CEILING}"
    )
    print("READY")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S8 m_hi resume plan (no GPU)")
    parser.add_argument("--emit", action="store_true", help="Print bash exports for the resume")
    args = parser.parse_args(argv)
    if args.emit:
        sys.stdout.write(emit())
        return 0
    errors = readiness()
    if errors:
        print("=== Vast CPT S8 m_hi resume readiness FAIL ===")
        for err in errors:
            print("ERROR", err)
        return 1
    print_ready()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
