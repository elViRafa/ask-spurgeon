#!/usr/bin/env python3
"""
Package theology CPT corpus for Kaggle dataset upload.

Creates a zip under continued_pretrain/data/kaggle_upload/theology-cpt-corpus.zip with:
  - theology_mix_train.txt
  - theology_mix_manifest.json
  - holdouts/*.txt
  - catechism_mcq.json
  - M1_BASE_MODEL_GATE.md (if present)

Usage:
  python continued_pretrain/scripts/12_package_kaggle_corpus.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    args = p.parse_args(argv)
    repo = Path(args.repo_root).resolve()
    data = repo / "continued_pretrain" / "data"
    out_dir = data / "kaggle_upload"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "theology-cpt-corpus.zip"

    files = [
        data / "theology_mix_train.txt",
        data / "theology_mix_manifest.json",
        data / "catechism_mcq.json",
        data / "M1_BASE_MODEL_GATE.md",
    ]
    holdouts = list((data / "holdouts").glob("*_holdout.txt"))
    files.extend(holdouts)

    missing = [f for f in files if not f.exists()]
    if missing:
        print("ERROR missing required files:")
        for m in missing:
            print(" ", m)
        raise SystemExit(1)

    # Empty holdouts warning
    for h in holdouts:
        if h.stat().st_size == 0:
            print(f"WARNING empty holdout: {h.name}")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.name.endswith("_holdout.txt"):
                arc = f"holdouts/{f.name}"
            else:
                arc = f.name
            zf.write(f, arcname=arc)
            print(f"  + {arc} ({f.stat().st_size:,} bytes)")

    # Sidecar metadata for the operator
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "zip": str(zip_path),
        "zip_sha256": sha256(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "files": {
            str(f.relative_to(data)): {"bytes": f.stat().st_size, "sha256": sha256(f)}
            for f in files
            if f.exists()
        },
    }
    # Pull mix shares
    manifest = json.loads((data / "theology_mix_manifest.json").read_text(encoding="utf-8"))
    meta["mix_buckets"] = {
        k: v.get("char_share") for k, v in (manifest.get("buckets") or {}).items()
    }
    meta["train_docs"] = manifest.get("train_docs")
    meta["train_chars"] = manifest.get("train_chars")
    meta_path = out_dir / "package_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("=" * 60)
    print(f"Wrote {zip_path}")
    print(f"  size={zip_path.stat().st_size / 1e6:.1f} MB")
    print(f"  sha256={meta['zip_sha256']}")
    print(f"  meta={meta_path}")
    print("Upload this zip as Kaggle dataset: theology-cpt-corpus")
    print("Then run A_data_prep_sota.ipynb with that dataset mounted.")


if __name__ == "__main__":
    main()
