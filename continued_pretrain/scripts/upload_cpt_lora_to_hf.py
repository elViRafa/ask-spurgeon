#!/usr/bin/env python3
"""Upload the keepable CPT v2 LoRA folder to Hugging Face (private by default).

Does not merge, quantize, or publish GGUF. Weights stay LoRA-only.

Usage (from repo root, after `hf auth login` or HF_TOKEN in .env):

  python continued_pretrain/scripts/upload_cpt_lora_to_hf.py
  python continued_pretrain/scripts/upload_cpt_lora_to_hf.py --public
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

EXPECTED_SHA256 = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"
DEFAULT_REPO = "rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_token() -> str | None:
    env_file = repo_root() / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("HF_TOKEN=") or s.startswith("HUGGING_FACE_HUB_TOKEN="):
                token = s.split("=", 1)[1].strip().strip("'\"")
                if token and not token.startswith("your_"):
                    return token
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument(
        "--adapter-dir",
        default=str(
            repo_root() / "continued_pretrain/kaggle/runpod_cpt_v2/theology_cpt_lora"
        ),
    )
    p.add_argument(
        "--public",
        action="store_true",
        help="Create/update a public repo (default is private)",
    )
    args = p.parse_args(argv)

    adapter = Path(args.adapter_dir)
    weights = adapter / "adapter_model.safetensors"
    if not weights.is_file():
        print(f"ERROR: missing {weights}", file=sys.stderr)
        return 2

    digest = sha256_file(weights)
    if digest != EXPECTED_SHA256:
        print(
            f"ERROR: SHA256 mismatch\n  got  {digest}\n  want {EXPECTED_SHA256}",
            file=sys.stderr,
        )
        return 2

    token = load_token()
    if not token:
        print(
            "ERROR: not logged in. Run `hf auth login` or set HF_TOKEN in .env",
            file=sys.stderr,
        )
        return 2

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(
        repo_id=args.repo,
        repo_type="model",
        private=not args.public,
        exist_ok=True,
    )
    print(f"Uploading {adapter} ({weights.stat().st_size / 1e9:.2f} GB weights) -> {args.repo}")
    api.upload_folder(
        folder_path=str(adapter),
        repo_id=args.repo,
        repo_type="model",
        commit_message="CPT v2 Runpod LoRA best-400 (embed FT, Ampere bf16)",
    )
    extra = repo_root() / "continued_pretrain/kaggle/runpod_cpt_v2"
    for name in ("SNAPSHOT.json", "SHA256SUMS", "theology_cpt_eval_metrics.json"):
        path = extra / name
        if path.is_file():
            api.upload_file(
                path_or_fileobj=str(path),
                path_in_repo=name,
                repo_id=args.repo,
                repo_type="model",
                commit_message=f"Add {name}",
            )
    vis = "public" if args.public else "private"
    print(f"SUCCESS ({vis}): https://huggingface.co/{args.repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
