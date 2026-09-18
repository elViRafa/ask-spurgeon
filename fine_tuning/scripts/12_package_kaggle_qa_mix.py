#!/usr/bin/env python3
"""
Package qa_mix JSONL files for Kaggle dataset upload (SFT v2).

Usage:
  python fine_tuning/scripts/build_qa_mix.py          # v1 (legacy single-chunk)
  python fine_tuning/scripts/build_qa_mix_v2.py       # v2 serve-shaped (preferred)
  python fine_tuning/scripts/12_package_kaggle_qa_mix.py
"""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    repo = Path(__file__).resolve().parent.parent.parent
    data = repo / "fine_tuning" / "data"
    out_dir = data / "kaggle_upload"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [
        "qa_mix_train.jsonl",
        "qa_mix_val.jsonl",
        "qa_test_frozen.jsonl",
        "qa_mix_manifest.json",
    ]
    for name in files:
        if not (data / name).exists():
            raise SystemExit(f"Missing {data / name} — run build_qa_mix.py first")

    zip_path = out_dir / "spurgeon-qa-mix-v1.zip"
    tmp_path = out_dir / "spurgeon-qa-mix-v1.zip.tmp"
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in files:
            zf.write(data / name, arcname=name)
    tmp_path.replace(zip_path)

    manifest = json.loads((data / "qa_mix_manifest.json").read_text(encoding="utf-8"))
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": "spurgeon-qa-mix-v1",
        "mix_version": manifest.get("version", "unknown"),
        "files": files,
        "zip_bytes": zip_path.stat().st_size,
        "counts": manifest.get("counts", {}),
        "train_refusal_pct": manifest.get("train_refusal_pct"),
    }
    (out_dir / "qa_mix_package_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {zip_path} ({zip_path.stat().st_size / 1e6:.2f} MB)")
    print("Upload to Kaggle as dataset: spurgeon-qa-mix-v1")


if __name__ == "__main__":
    main()
