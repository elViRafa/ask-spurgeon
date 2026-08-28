#!/usr/bin/env python3
"""
Verify local CPT v2 assets are ready for Kaggle upload (no GPU).

Checks corpus zip, notebooks, preflight report, and M1 docs.

Usage:
  python continued_pretrain/scripts/14_kaggle_cpt_readiness.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    repo = root.parent
    data = root / "data"
    errors: list[str] = []
    warnings: list[str] = []

    required = [
        data / "theology_mix_train.txt",
        data / "theology_mix_manifest.json",
        data / "holdouts" / "spurgeon_holdout.txt",
        data / "catechism_mcq.json",
        root / "notebooks" / "A_data_prep_sota.ipynb",
        root / "notebooks" / "B_training_sota.ipynb",
        root / "notebooks" / "C_eval_sota.ipynb",
        root / "KAGGLE_RUNBOOK_V2.md",
        data / "M1_BASE_MODEL_GATE.md",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"missing {p.relative_to(repo)}")

    zip_path = data / "kaggle_upload" / "theology-cpt-corpus.zip"
    if not zip_path.exists():
        warnings.append(f"zip not built — run scripts/12_package_kaggle_corpus.py")
    else:
        print(f"OK zip: {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")

    preflight = data / "preflight_report.json"
    if preflight.exists():
        rep = json.loads(preflight.read_text(encoding="utf-8"))
        if rep.get("overall") not in ("PASS", "PASS_WITH_WARNINGS"):
            errors.append(f"preflight not PASS: {preflight} ({rep.get('overall')})")
        else:
            print("OK preflight PASS")
    else:
        warnings.append("run scripts/13_local_preflight.py")

    gen = root / "scripts" / "_gen_sota_notebooks.py"
    if gen.exists():
        text = gen.read_text(encoding="utf-8")
        if "Mistral-7B-v0.3" not in text:
            errors.append("CPT generator fallback should be Mistral-7B-v0.3")
        else:
            print("OK CPT fallback = Mistral-7B-v0.3")

    if warnings:
        for w in warnings:
            print("WARN:", w)
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 2

    print("\nCPT Kaggle readiness: PASS")
    print("Next: upload theology-cpt-corpus.zip -> follow KAGGLE_RUNBOOK_V2.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
