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

EXPECTED_SHA256_V2 = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"
EXPECTED_SHA256_S6 = "6aab91940ce3e854f72a5308ae41e8ce1ae4c457752ff76390581f09ba436f0c"
EXPECTED_SHA256_S7 = "06354dfc5a720143617ee2ffeef38faa48200811bed89e71561ff357ed547432"
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
        "--expected-sha256",
        default=EXPECTED_SHA256_S7,
        help=(
            f"Adapter weights digest (S7 s5best default; S6={EXPECTED_SHA256_S6}; "
            f"v2={EXPECTED_SHA256_V2})"
        ),
    )
    p.add_argument(
        "--commit-message",
        default="CPT S7 s5best step-1200 isolation-C (embed FT, Ampere bf16)",
    )
    p.add_argument(
        "--metrics-dir",
        default="",
        help="Optional folder with SHA256SUMS / theology_cpt_eval_metrics.json to upload",
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

    want = (args.expected_sha256 or "").strip().lower()
    digest = sha256_file(weights)
    if want and digest != want:
        print(
            f"ERROR: SHA256 mismatch\n  got  {digest}\n  want {want}",
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
    print(f"SHA256 {digest}")
    api.upload_folder(
        folder_path=str(adapter),
        repo_id=args.repo,
        repo_type="model",
        commit_message=args.commit_message,
    )
    metrics_dir = Path(args.metrics_dir) if args.metrics_dir else (
        repo_root() / "continued_pretrain/kaggle/runpod_cpt_v2"
    )
    for name in ("SNAPSHOT.json", "SHA256SUMS", "theology_cpt_eval_metrics.json", "STACK_PIN.txt"):
        path = metrics_dir / name
        if path.is_file():
            api.upload_file(
                path_or_fileobj=str(path),
                path_in_repo=name,
                repo_id=args.repo,
                repo_type="model",
                commit_message=f"Add {name}",
            )
    # Always write a small identity file for the uploaded digest.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        ident = Path(tmp) / "ADAPTER_SHA256.txt"
        ident.write_text(digest + "\n", encoding="utf-8")
        api.upload_file(
            path_or_fileobj=str(ident),
            path_in_repo="ADAPTER_SHA256.txt",
            repo_id=args.repo,
            repo_type="model",
            commit_message=f"Record adapter SHA256 {digest[:12]}…",
        )
    vis = "public" if args.public else "private"
    print(f"SUCCESS ({vis}): https://huggingface.co/{args.repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
