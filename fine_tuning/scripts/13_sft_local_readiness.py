#!/usr/bin/env python3
"""Verify SFT v2 local assets before Kaggle upload or RunPod GATE-0."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="SFT v2 local readiness")
    parser.add_argument(
        "--gate0",
        action="store_true",
        help="Also verify RunPod GATE-0 orchestration scripts exist",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent.parent
    ft = repo / "fine_tuning"
    data = ft / "data"
    errors: list[str] = []

    required = [
        data / "qa_mix_train.jsonl",
        data / "qa_mix_val.jsonl",
        data / "qa_test_frozen.jsonl",
        data / "qa_mix_manifest.json",
        data / "kaggle_upload" / "spurgeon-qa-mix-v1.zip",
        ft / "notebooks" / "D_qa_data_prep_sota.ipynb",
        ft / "notebooks" / "E_qa_training_sota.ipynb",
        ft / "notebooks" / "F_qa_eval_sota.ipynb",
        ft / "KAGGLE_RUNBOOK_SFT_V2.md",
        ft / "models" / "Modelfile.qwen35-spurgeon-qa-v2",
        ft / "scripts" / "smoke_test_ollama.py",
        ft / "scripts" / "verify_sft_stop_tokens.py",
        ft / "scripts" / "sft_stop_token_utils.py",
        ft / "STOP_TOKEN_PHASES.md",
        repo / "config.py",
    ]
    if args.gate0:
        required.extend(
            [
                ft / "RUNPOD_RUNBOOK_SFT.md",
                ft / "VULTR_RUNBOOK_SFT.md",
                ft / "scripts" / "vultr_orchestrate.ps1",
                ft / "scripts" / "merge_cpt_lora.py",
                ft / "scripts" / "train_sft_sota.py",
                ft / "scripts" / "eval_sft_sota.py",
                ft / "scripts" / "sft_runpod_common.ps1",
                ft / "scripts" / "sft_orchestrate.ps1",
                ft / "scripts" / "sft_remote_train.sh",
                ft / "scripts" / "sft_remote_merge.sh",
            ]
        )

    for p in required:
        if not p.exists():
            errors.append(f"missing {p.relative_to(repo)}")

    cfg = (repo / "config.py").read_text(encoding="utf-8")
    if "SPURGEON_SFT_SYSTEM_PROMPT" not in cfg:
        errors.append("config.py missing SPURGEON_SFT_SYSTEM_PROMPT")
    if "FINE_TUNED_SIMILARITY_TOP_K" not in cfg:
        errors.append("config.py missing FINE_TUNED_SIMILARITY_TOP_K")

    manifest = json.loads((data / "qa_mix_manifest.json").read_text(encoding="utf-8"))
    counts = manifest.get("counts", {})
    if counts.get("train", 0) < 500:
        errors.append(f"train set too small: {counts.get('train')}")

    version = manifest.get("version", "")
    slices = manifest.get("slices_train") or {}
    refusal_n = int(slices.get("refusal") or 0)
    train_n = int(counts.get("train") or 0)
    refusal_pct = 100.0 * refusal_n / train_n if train_n else 0.0
    if version == "qa_mix_v2" and not (10.0 <= refusal_pct <= 15.5):
        errors.append(f"v2 train refusal {refusal_pct:.1f}% outside 10–15% target")

    zip_path = data / "kaggle_upload" / "spurgeon-qa-mix-v1.zip"
    train_path = data / "qa_mix_train.jsonl"
    if zip_path.exists() and train_path.exists() and train_path.stat().st_mtime > zip_path.stat().st_mtime + 1:
        errors.append(
            "spurgeon-qa-mix-v1.zip is older than qa_mix_train.jsonl — "
            "re-run 12_package_kaggle_qa_mix.py"
        )

    sample_line = (data / "qa_mix_train.jsonl").read_text(encoding="utf-8").splitlines()[0]
    sample = json.loads(sample_line)
    user = sample["messages"][1]["content"]
    if version == "qa_mix_v2" and "[Sermon " not in user:
        errors.append("v2 train example missing [Sermon …] header")

    sys.path.insert(0, str(repo))
    from config import SPURGEON_SFT_SYSTEM_PROMPT

    train_system = sample["messages"][0]["content"]
    if train_system != SPURGEON_SFT_SYSTEM_PROMPT:
        errors.append("train jsonl system prompt does not match config.SPURGEON_SFT_SYSTEM_PROMPT")

    verify = ft / "scripts" / "verify_sft_stop_tokens.py"
    for phase in (0, 1):
        proc = subprocess.run(
            [sys.executable, str(verify), "--phase", str(phase)],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            msg = detail[-1] if detail else f"exit {proc.returncode}"
            errors.append(f"stop-token phase {phase} failed: {msg}")

    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 2

    label = "SFT GATE-0 RunPod readiness" if args.gate0 else "SFT Kaggle readiness"
    print(f"{label}: PASS")
    print(f"  version={version or 'unknown'}")
    print(f"  train={counts.get('train')} val={counts.get('val')} test={counts.get('test_frozen')}")
    print(f"  train_refusal={refusal_n} ({refusal_pct:.1f}%)")
    print("  stop-token phases 0-1: PASS")
    overlay = manifest.get("gold_overlay") or {}
    if overlay.get("rows"):
        print(f"  gold_overlay={overlay.get('rows')} teacher={overlay.get('teacher')}")
    if args.gate0:
        print("Next: .\\fine_tuning\\scripts\\vultr_orchestrate.ps1  (or sft_orchestrate.ps1 on RunPod)")
    else:
        print("Next: upload spurgeon-qa-mix-v1.zip -> follow KAGGLE_RUNBOOK_SFT_V2.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
