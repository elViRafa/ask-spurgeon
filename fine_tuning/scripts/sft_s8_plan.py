#!/usr/bin/env python3
"""Next job after S8 Isolation C: SFT on the merged S8 weights. Does not rent.

Isolation C on adapter 22698039 missed section 5 (puritan loss 1.6605 vs
1.6349) and the last resume was already flat (in-train puritan 1.708 to 1.701
from step 800 to 2250). The shipped GATE-0 SFT (spurgeon-qa-v2) already
cleared groundedness and failed only refusal recall (0.54 vs 0.85). The next
GPU hour is a new SFT on the S8 merged 16-bit base, same QA mix, same PEFT
4090 recipe. Hub LoRA v2 stays Phase A 06354dfc.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DECISION = "sft"
RESUME_LORA_SHA = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"
HUB_LORA_SHA_PREFIX = "06354dfc"
HUB_LORA_REPO = "rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2"
S8_MERGED_REPO = "rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit"
S8_MERGED_REMOTE = "/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
GATE0_MERGED_REMOTE = "/workspace/theology_cpt_v2_merged_hf"
PURITAN_LOSS = 1.6605
PURITAN_GATE = 1.6349
PRIOR_SFT_REFUSAL = 0.54
REFUSAL_GATE = 0.85
PRIOR_SFT_GROUNDEDNESS = 4.51
GROUNDEDNESS_GATE = 4.0

ENV = {
    "USE_CPT_MERGE": "1",
    "SFT_GATE0_MERGED": S8_MERGED_REMOTE,
    "SFT_BASE_REPO": S8_MERGED_REPO,
    "SFT_WORK_ROOT": "/workspace",
    "HF_HOME": "/workspace/hf_home",
    "PYTHONUNBUFFERED": "1",
    "SFT_EXPORT": "0",
    "SFT_GPU_PROFILE": "4090",
    "SFT_BACKEND": "peft",
    "SFT_MAX_SEQ_LENGTH": "2048",
    "SFT_PER_DEVICE_BATCH": "1",
    "SFT_GRAD_ACCUM": "16",
    "SFT_EVAL_STRATEGY": "no",
    "SFT_SAVE_STEPS": "40",
    "CUDA_VISIBLE_DEVICES": "0",
    "UNSLOTH_COMPILE_DISABLE": "1",
    "UNSLOTH_DISABLE_FAST_GENERATION": "1",
    "TORCHDYNAMO_DISABLE": "1",
    "TORCH_COMPILE_DISABLE": "1",
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
}


def next_stage() -> str:
    """SFT. Another CPT resume at this slope does not close the 0.0256 nat gap."""
    return DECISION


def repo_root_from_script(script: Path) -> Path | None:
    for parent in script.resolve().parents:
        if (parent / "continued_pretrain").is_dir() and (parent / "fine_tuning").is_dir():
            return parent
    return None


def local_paths(script: Path | None = None) -> dict[str, Path]:
    root = repo_root_from_script(script or Path(__file__))
    if root is None:
        raise SystemExit("repo root not found; --emit does not need local paths")
    ft = root / "fine_tuning"
    merged = ft / "models" / "qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    return {
        "merged_config": merged / "config.json",
        "merged_tokenizer": merged / "tokenizer_config.json",
        "train_jsonl": ft / "data" / "qa_mix_train.jsonl",
        "val_jsonl": ft / "data" / "qa_mix_val.jsonl",
        "train_py": ft / "scripts" / "train_sft_sota.py",
        "remote": ft / "scripts" / "sft_remote_train_s8.sh",
        "runbook": ft / "NEXT_SFT_S8.md",
    }


def contract_errors() -> list[str]:
    errors: list[str] = []
    if next_stage() != "sft":
        errors.append("next stage must be sft")
    if ENV["SFT_GATE0_MERGED"] != S8_MERGED_REMOTE:
        errors.append("SFT base must be the S8 merged directory")
    if ENV["SFT_BASE_REPO"] != S8_MERGED_REPO:
        errors.append("SFT base repo must be the private S8 merge")
    if GATE0_MERGED_REMOTE in ENV.values():
        errors.append("GATE-0 v2 merge must not be this job's base")
    if HUB_LORA_REPO in ENV.values():
        errors.append("do not train SFT by remapping Hub LoRA v2")
    if ENV["SFT_EXPORT"] != "0":
        errors.append("SFT_EXPORT stays 0 until F gates")
    if ENV["SFT_BACKEND"] != "peft":
        errors.append("Vast SFT backend is peft")
    if ENV["USE_CPT_MERGE"] != "1":
        errors.append("train on the merged S8 weights")
    return errors


def evaluate(paths: dict[str, Path]) -> list[str]:
    errors = contract_errors()
    labels = {
        "merged_config": "S8 merged config.json",
        "merged_tokenizer": "S8 merged tokenizer_config.json",
        "train_jsonl": "qa_mix_train.jsonl",
        "val_jsonl": "qa_mix_val.jsonl",
        "train_py": "train_sft_sota.py",
        "remote": "sft_remote_train_s8.sh",
        "runbook": "NEXT_SFT_S8.md",
    }
    for key, label in labels.items():
        path = paths[key]
        if not path.is_file():
            errors.append(f"missing {label}: {path}")
    return errors


def emit() -> str:
    lines = [f"export {key}={value}" for key, value in ENV.items()]
    return "\n".join(lines) + "\n"


def readiness() -> list[str]:
    return evaluate(local_paths())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SFT-on-S8 plan. Dry only.")
    parser.add_argument("--emit", action="store_true", help="print pod exports")
    args = parser.parse_args(argv)
    if args.emit:
        sys.stdout.write(emit())
        return 0
    errors = readiness()
    if errors:
        for item in errors:
            print("FAIL", item)
        return 1
    print("READY")
    print("decision", next_stage())
    print("base", S8_MERGED_REMOTE)
    print("hub_repo", S8_MERGED_REPO)
    print("hub_lora_v2", HUB_LORA_SHA_PREFIX, "unchanged")
    print("puritan_loss", PURITAN_LOSS, "gate", PURITAN_GATE)
    print("prior_sft_refusal", PRIOR_SFT_REFUSAL, "gate", REFUSAL_GATE)
    print("DRY — no rent, no train")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
