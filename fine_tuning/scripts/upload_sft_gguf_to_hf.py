#!/usr/bin/env python3
"""
Upload Spurgeon SFT v2 GGUF artifacts to Hugging Face.

Expects local files (after Kaggle export):
  fine_tuning/models/spurgeon-qa-v2.F16.gguf
  fine_tuning/models/spurgeon-qa-v2.Q4_K_M.gguf  (optional)

Usage:
  python fine_tuning/scripts/upload_sft_gguf_to_hf.py
  python fine_tuning/scripts/upload_sft_gguf_to_hf.py --repo rafaelvieirar1r/qwen3.5-4b-spurgeon-qa
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi


def load_token() -> str | None:
    for env_path in [Path(".env"), Path("fine_tuning/models/../../.env")]:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("HF_TOKEN=") or s.startswith("# HF_TOKEN="):
                token = s.split("=", 1)[1].strip("'\" ")
                if token:
                    return token
    return os.environ.get("HF_TOKEN")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default="rafaelvieirar1r/qwen3.5-4b-spurgeon-qa")
    p.add_argument("--models-dir", default="fine_tuning/models")
    args = p.parse_args(argv)

    models_dir = Path(args.models_dir)
    files = [
        models_dir / "spurgeon-qa-v2.F16.gguf",
        models_dir / "spurgeon-qa-v2.Q4_K_M.gguf",
    ]
    present = [f for f in files if f.exists()]
    if not present:
        print("ERROR: no GGUF files found. Expected at least:", files[0], file=sys.stderr)
        return 2

    token = load_token()
    if not token:
        print("ERROR: HF_TOKEN not found in .env or environment", file=sys.stderr)
        return 2

    api = HfApi(token=token)
    api.create_repo(repo_id=args.repo, repo_type="model", exist_ok=True)
    for path in present:
        print(f"Uploading {path.name} ({path.stat().st_size / 1e9:.2f} GB)...")
        api.upload_file(
            path_or_fileobj=str(path),
            path_in_repo=path.name,
            repo_id=args.repo,
            repo_type="model",
            commit_message=f"Upload {path.name} (Spurgeon QA v2)",
        )
    print(f"SUCCESS: https://huggingface.co/{args.repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
