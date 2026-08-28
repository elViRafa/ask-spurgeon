#!/usr/bin/env python3
"""Verify SFT v2 local assets before Kaggle upload."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
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
        repo / "config.py",
    ]
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

    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 2

    print("SFT Kaggle readiness: PASS")
    print(f"  train={counts.get('train')} val={counts.get('val')} test={counts.get('test_frozen')}")
    print("Next: upload spurgeon-qa-mix-v1.zip -> follow KAGGLE_RUNBOOK_SFT_V2.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
