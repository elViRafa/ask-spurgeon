#!/usr/bin/env python3
"""RunPod Unsloth weighted SFT on S8 merged CPT. Dry only — does not rent."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import sft_s8_weighted_plan as base

DECISION = "sft_weighted_runpod_unsloth"
HOST = "runpod"
BACKEND = "unsloth"

# Same contract as Vast PEFT weighted, except backend + host paths.
ENV = dict(base.ENV)
ENV["SFT_BACKEND"] = BACKEND

S8_MERGED_REPO = base.S8_MERGED_REPO
S8_MERGED_REMOTE = base.S8_MERGED_REMOTE
WEIGHTED_OUTPUT = base.WEIGHTED_OUTPUT
HUB_LORA_SHA_PREFIX = base.HUB_LORA_SHA_PREFIX
GATE0_MERGED_REMOTE = base.GATE0_MERGED_REMOTE
GATE0_OUTPUT = base.GATE0_OUTPUT
HUB_LORA_REPO = base.HUB_LORA_REPO


def next_stage() -> str:
    return DECISION


def repo_root_from_script(script: Path) -> Path | None:
    return base.repo_root_from_script(script)


def local_paths(script: Path | None = None) -> dict[str, Path]:
    root = repo_root_from_script(script or Path(__file__))
    if root is None:
        raise SystemExit("repo root not found; --emit does not need local paths")
    ft = root / "fine_tuning"
    paths = base.local_paths(script or Path(__file__))
    paths["orchestrator"] = ft / "scripts" / "runpod_sft_s8_weighted_orchestrate.ps1"
    paths["runbook"] = ft / "NEXT_SFT_S8_WEIGHTED_RUNPOD_UNSLOTH.md"
    paths["vast_orchestrator"] = ft / "scripts" / "vast_sft_s8_weighted_orchestrate.ps1"
    paths["vast_runbook"] = ft / "NEXT_SFT_S8_WEIGHTED.md"
    return paths


def contract_errors() -> list[str]:
    errors: list[str] = []
    if next_stage() != "sft_weighted_runpod_unsloth":
        errors.append("next stage must be sft_weighted_runpod_unsloth")
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
    if ENV["SFT_BACKEND"] != "unsloth":
        errors.append("RunPod path backend is unsloth")
    if ENV["USE_CPT_MERGE"] != "1":
        errors.append("train on the merged S8 weights")
    if ENV["SFT_OPEN_THEOLOGY"] != "1":
        errors.append("SFT_OPEN_THEOLOGY must be 1")
    if ENV["SFT_OPEN_THEOLOGY_REPEAT"] != "1":
        errors.append("SFT_OPEN_THEOLOGY_REPEAT must be 1 (no upsample)")
    if ENV["SFT_OUTPUT_DIR"] != WEIGHTED_OUTPUT:
        errors.append("output dir must be sft_s8_weighted/adapter")
    if GATE0_OUTPUT in ENV["SFT_OUTPUT_DIR"]:
        errors.append("must not write into spurgeon_qa_lora_v2")
    if ENV["SFT_MAX_SEQ_LENGTH"] != "4608":
        errors.append("seq must stay 4608 unless operator accepts tradeoff")
    return errors


def evaluate(paths: dict[str, Path]) -> list[str]:
    errors = contract_errors()
    labels = {
        "train_jsonl": "qa_mix_train.jsonl",
        "val_jsonl": "qa_mix_val.jsonl",
        "open_theology_train": "open_theology_train.jsonl",
        "open_theology_eval": "open_theology_eval.jsonl",
        "open_theology_manifest": "open-theology manifest.json",
        "train_py": "train_sft_sota.py",
        "remote": "sft_remote_train_s8_weighted.sh",
        "runbook": "NEXT_SFT_S8_WEIGHTED_RUNPOD_UNSLOTH.md",
        "orchestrator": "runpod_sft_s8_weighted_orchestrate.ps1",
        "vast_orchestrator": "vast_sft_s8_weighted_orchestrate.ps1",
        "vast_runbook": "NEXT_SFT_S8_WEIGHTED.md",
    }
    for key, label in labels.items():
        path = paths[key]
        if not path.is_file():
            errors.append(f"missing {label}: {path}")

    if not paths["merged_config"].is_file():
        print("NOTE local S8 merged config absent; pod will snapshot_download")

    manifest_path = paths.get("open_theology_manifest")
    if manifest_path and manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"manifest.json invalid JSON: {exc}")
        else:
            if manifest.get("eval_partial") is not False:
                errors.append("open-theology manifest eval_partial must be false")
            train_rows = (manifest.get("files") or {}).get("train", {}).get("rows")
            eval_rows = (manifest.get("files") or {}).get("eval", {}).get("rows")
            if not isinstance(train_rows, int) or train_rows < 1:
                errors.append("manifest train rows missing")
            if not isinstance(eval_rows, int) or eval_rows < 1:
                errors.append("manifest eval rows missing")

    remote = paths["remote"]
    if remote.is_file():
        text = remote.read_text(encoding="utf-8")
        if "SFT_BACKEND:-peft" not in text and '_backend_in="${SFT_BACKEND:-peft}"' not in text:
            errors.append("remote launcher must allow SFT_BACKEND override (default peft)")
        if "SMOKE_ONLY_DONE" not in text:
            errors.append("remote launcher must support SFT_SMOKE_ONLY / SMOKE_ONLY_DONE")
    return errors


def emit() -> str:
    lines = [f"export {key}={value}" for key, value in ENV.items()]
    return "\n".join(lines) + "\n"


def readiness() -> list[str]:
    return evaluate(local_paths())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RunPod Unsloth weighted SFT plan. Dry only.")
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
    paths = local_paths()
    train_n = sum(1 for line in paths["open_theology_train"].open(encoding="utf-8") if line.strip())
    rag_n = sum(1 for line in paths["train_jsonl"].open(encoding="utf-8") if line.strip())
    print("READY")
    print("decision", next_stage())
    print("host", HOST)
    print("backend", BACKEND)
    print("base", S8_MERGED_REMOTE)
    print("hub_repo", S8_MERGED_REPO)
    print("hub_lora_v2", HUB_LORA_SHA_PREFIX, "unchanged")
    print("rag_train_rows", rag_n)
    print("open_theology_train_rows", train_n)
    print("mix_rows", rag_n + train_n)
    print("SFT_OPEN_THEOLOGY_REPEAT", ENV["SFT_OPEN_THEOLOGY_REPEAT"])
    print("SFT_OUTPUT_DIR", WEIGHTED_OUTPUT)
    print("SFT_EXPORT", ENV["SFT_EXPORT"])
    print("SFT_BACKEND", ENV["SFT_BACKEND"])
    print("DRY — no rent, no train")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
