#!/usr/bin/env python3
"""Weighted SFT on S8 merged CPT: RAG mix + open-theology slice. Does not rent."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DECISION = "sft_weighted"
RESUME_LORA_SHA = "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207"
HUB_LORA_SHA_PREFIX = "06354dfc"
HUB_LORA_REPO = "rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2"
S8_MERGED_REPO = "rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit"
S8_MERGED_REMOTE = "/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
GATE0_MERGED_REMOTE = "/workspace/theology_cpt_v2_merged_hf"
GATE0_OUTPUT = "spurgeon_qa_lora_v2"
WEIGHTED_OUTPUT = "/workspace/sft_s8_weighted/adapter"

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
    "SFT_OPEN_THEOLOGY": "1",
    "SFT_OPEN_THEOLOGY_REPEAT": "1",
    "SFT_OUTPUT_DIR": WEIGHTED_OUTPUT,
    "CUDA_VISIBLE_DEVICES": "0",
    "UNSLOTH_COMPILE_DISABLE": "1",
    "UNSLOTH_DISABLE_FAST_GENERATION": "1",
    "TORCHDYNAMO_DISABLE": "1",
    "TORCH_COMPILE_DISABLE": "1",
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
}


def next_stage() -> str:
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
    sft = ft / "data" / "qa_open_theology" / "sft"
    return {
        "merged_config": merged / "config.json",
        "merged_tokenizer": merged / "tokenizer_config.json",
        "train_jsonl": ft / "data" / "qa_mix_train.jsonl",
        "val_jsonl": ft / "data" / "qa_mix_val.jsonl",
        "open_theology_train": sft / "open_theology_train.jsonl",
        "open_theology_eval": sft / "open_theology_eval.jsonl",
        "open_theology_manifest": sft / "manifest.json",
        "train_py": ft / "scripts" / "train_sft_sota.py",
        "remote": ft / "scripts" / "sft_remote_train_s8_weighted.sh",
        "runbook": ft / "NEXT_SFT_S8_WEIGHTED.md",
        "orchestrator": ft / "scripts" / "vast_sft_s8_weighted_orchestrate.ps1",
    }


def contract_errors() -> list[str]:
    errors: list[str] = []
    if next_stage() != "sft_weighted":
        errors.append("next stage must be sft_weighted")
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
    if ENV["SFT_OPEN_THEOLOGY"] != "1":
        errors.append("SFT_OPEN_THEOLOGY must be 1")
    if ENV["SFT_OPEN_THEOLOGY_REPEAT"] != "1":
        errors.append("SFT_OPEN_THEOLOGY_REPEAT must be 1 (no upsample)")
    if ENV["SFT_OUTPUT_DIR"] != WEIGHTED_OUTPUT:
        errors.append("output dir must be sft_s8_weighted/adapter")
    if GATE0_OUTPUT in ENV["SFT_OUTPUT_DIR"]:
        errors.append("must not write into spurgeon_qa_lora_v2")
    return errors


def evaluate(paths: dict[str, Path]) -> list[str]:
    errors = contract_errors()
    labels = {
        "train_jsonl": "qa_mix_train.jsonl",
        "val_jsonl": "qa_mix_val.jsonl",
        "open_theology_train": "open_theology_train.jsonl",
        "open_theology_eval": "open_theology_eval.jsonl",
        "open_theology_manifest": "open_theology manifest.json",
        "train_py": "train_sft_sota.py",
        "remote": "sft_remote_train_s8_weighted.sh",
        "runbook": "NEXT_SFT_S8_WEIGHTED.md",
        "orchestrator": "vast_sft_s8_weighted_orchestrate.ps1",
    }
    for key, label in labels.items():
        path = paths[key]
        if not path.is_file():
            errors.append(f"missing {label}: {path}")

    # Local merge is optional for dry readiness (pod downloads from Hub).
    # Still report when absent so the operator knows fetch is remote-only.
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
    return errors


def emit() -> str:
    lines = [f"export {key}={value}" for key, value in ENV.items()]
    return "\n".join(lines) + "\n"


def readiness() -> list[str]:
    return evaluate(local_paths())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weighted SFT-on-S8 plan. Dry only.")
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
    print("base", S8_MERGED_REMOTE)
    print("hub_repo", S8_MERGED_REPO)
    print("hub_lora_v2", HUB_LORA_SHA_PREFIX, "unchanged")
    print("rag_train_rows", rag_n)
    print("open_theology_train_rows", train_n)
    print("mix_rows", rag_n + train_n)
    print("SFT_OPEN_THEOLOGY_REPEAT", ENV["SFT_OPEN_THEOLOGY_REPEAT"])
    print("SFT_OUTPUT_DIR", WEIGHTED_OUTPUT)
    print("SFT_EXPORT", ENV["SFT_EXPORT"])
    print("DRY — no rent, no train")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
