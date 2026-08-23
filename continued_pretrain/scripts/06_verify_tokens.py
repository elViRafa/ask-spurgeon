#!/usr/bin/env python3
"""
Token verification for Spurgeon corpus and theology mix (D3).

Modes:
  python continued_pretrain/scripts/06_verify_tokens.py
      → estimate tokens on spurgeon_train.txt (legacy)

  python continued_pretrain/scripts/06_verify_tokens.py --mix
      → estimate tokens on theology_mix_train.txt, per-bucket from
        theology_mix_manifest.json, and write verified_tokens into the manifest.

  python continued_pretrain/scripts/06_verify_tokens.py --mix --tokenizer Qwen/Qwen3.5-4B-Base
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DOC_SEP = "<|endoftext|>"
DEFAULT_TOKENIZER = "Qwen/Qwen2.5-3B"
FLAGSHIP_TOKENIZER = "Qwen/Qwen3.5-4B-Base"


def load_tokenizer(name: str):
    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("Error: transformers is not installed. pip install transformers huggingface_hub")
        sys.exit(1)

    print(f"Loading tokenizer: {name} ...")
    try:
        return AutoTokenizer.from_pretrained(name, trust_remote_code=True)
    except Exception as e:
        print(f"Error loading {name}: {e}")
        print("Falling back to gpt2 for estimation...")
        try:
            return AutoTokenizer.from_pretrained("gpt2")
        except Exception as fallback_err:
            print(f"Fallback tokenizer failed: {fallback_err}")
            sys.exit(1)


def estimate_tokens(text: str, tokenizer, sample_chars: int = 500_000) -> dict:
    n_chars = len(text)
    if n_chars == 0:
        return {
            "chars": 0,
            "sample_chars": 0,
            "sample_tokens": 0,
            "token_char_ratio": 0.0,
            "estimated_tokens": 0,
        }
    sample_size = min(sample_chars, n_chars)
    # Prefer mid-file sample when large (avoids header bias)
    if n_chars > sample_size * 2:
        start = (n_chars - sample_size) // 2
        sample_text = text[start : start + sample_size]
    else:
        sample_text = text[:sample_size]

    tokens = tokenizer(sample_text, add_special_tokens=False)["input_ids"]
    sample_token_count = len(tokens)
    ratio = sample_token_count / sample_size
    return {
        "chars": n_chars,
        "sample_chars": sample_size,
        "sample_tokens": sample_token_count,
        "token_char_ratio": round(ratio, 6),
        "estimated_tokens": int(n_chars * ratio),
    }


def verify_spurgeon(base_dir: Path, tokenizer, sample_chars: int) -> None:
    train_file = base_dir / "continued_pretrain" / "data" / "spurgeon_train.txt"
    holdout_file = base_dir / "continued_pretrain" / "data" / "spurgeon_holdout.txt"

    if not train_file.exists():
        print(f"Error: {train_file} does not exist. Run 05_build_corpus.py first.")
        sys.exit(1)

    train_text = train_file.read_text(encoding="utf-8")
    est = estimate_tokens(train_text, tokenizer, sample_chars)
    holdout_text = holdout_file.read_text(encoding="utf-8") if holdout_file.exists() else ""
    hold_est = estimate_tokens(holdout_text, tokenizer, sample_chars) if holdout_text else None

    print("=" * 60)
    print("Spurgeon train verification")
    print("-" * 60)
    print(f"Train file size:      {est['chars'] / 1024 / 1024:.2f} MB ({est['chars']:,} chars)")
    print(f"Sample token count:   {est['sample_tokens']:,}")
    print(f"Token/Char ratio:     {est['token_char_ratio']:.4f}")
    print(f"Est. Train tokens:    {est['estimated_tokens']:,}")
    if hold_est:
        print(f"Est. Holdout tokens:  {hold_est['estimated_tokens']:,}")
    print("=" * 60)
    delim_count = train_text.count(DOC_SEP)
    print(f"Found {delim_count} occurrences of {DOC_SEP} in train file.")


def verify_mix(base_dir: Path, tokenizer, tokenizer_name: str, sample_chars: int, update_manifest: bool) -> None:
    data_dir = base_dir / "continued_pretrain" / "data"
    train_file = data_dir / "theology_mix_train.txt"
    manifest_path = data_dir / "theology_mix_manifest.json"

    if not train_file.exists():
        print(f"Error: {train_file} missing. Run 07_build_theology_mix.py first.")
        sys.exit(1)

    train_text = train_file.read_text(encoding="utf-8")
    est = estimate_tokens(train_text, tokenizer, sample_chars)
    delim_count = train_text.count(DOC_SEP)

    # Max doc size check
    docs = [d.strip() for d in train_text.split(DOC_SEP) if d.strip()]
    max_doc = max((len(d) for d in docs), default=0)
    over_8k = sum(1 for d in docs if len(d) > 8000)

    bucket_verified: dict[str, dict] = {}
    manifest: dict = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        buckets = manifest.get("buckets") or {}
        # Approximate per-bucket tokens via share * total ratio
        ratio = est["token_char_ratio"]
        for name, info in buckets.items():
            chars = int(info.get("chars") or 0)
            bucket_verified[name] = {
                "chars": chars,
                "estimated_tokens": int(chars * ratio),
                "char_share": info.get("char_share"),
                "docs": info.get("docs"),
            }

    print("=" * 60)
    print("Theology mix verification (D3)")
    print("-" * 60)
    print(f"Tokenizer:            {tokenizer_name}")
    print(f"Train file size:      {est['chars'] / 1024 / 1024:.2f} MB ({est['chars']:,} chars)")
    print(f"Docs (sep count):     {len(docs)}  ({delim_count} separators)")
    print(f"Max doc chars:        {max_doc:,}")
    print(f"Docs > 8k chars:      {over_8k}")
    print(f"Token/Char ratio:     {est['token_char_ratio']:.4f}")
    print(f"Est. total tokens:    {est['estimated_tokens']:,}")
    if bucket_verified:
        print("Per-bucket (from manifest chars × ratio):")
        for name, info in sorted(bucket_verified.items()):
            share = info.get("char_share")
            share_s = f"{share:.1%}" if isinstance(share, float) else "?"
            print(
                f"  {name:12s}  share={share_s}  docs={info.get('docs')}  "
                f"~tok={info['estimated_tokens']:,}"
            )
    print("=" * 60)

    if update_manifest and manifest_path.exists():
        manifest["verified_tokens"] = {
            "tokenizer": tokenizer_name,
            "method": "sample_ratio",
            "sample_chars": est["sample_chars"],
            "token_char_ratio": est["token_char_ratio"],
            "train_estimated_tokens": est["estimated_tokens"],
            "train_chars": est["chars"],
            "max_doc_chars": max_doc,
            "docs_over_8k_chars": over_8k,
            "n_docs": len(docs),
            "buckets": bucket_verified,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Updated verified_tokens in {manifest_path}")
    elif update_manifest:
        print(f"NOTE: no manifest at {manifest_path}; skipped write.")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Verify token counts for CPT corpora")
    p.add_argument(
        "--mix",
        action="store_true",
        help="Verify theology_mix_train.txt + update manifest verified_tokens",
    )
    p.add_argument(
        "--tokenizer",
        default=None,
        help=f"HF tokenizer id (default: {DEFAULT_TOKENIZER}; with --mix prefer flagship)",
    )
    p.add_argument("--sample-chars", type=int, default=500_000)
    p.add_argument(
        "--no-update-manifest",
        action="store_true",
        help="With --mix, do not write verified_tokens into the manifest",
    )
    p.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent.parent.parent),
    )
    args = p.parse_args(argv)

    base_dir = Path(args.repo_root).resolve()
    tok_name = args.tokenizer or (FLAGSHIP_TOKENIZER if args.mix else DEFAULT_TOKENIZER)
    # Prefer local/offline-friendly default if flagship fails — load_tokenizer handles fallback
    tokenizer = load_tokenizer(tok_name)

    if args.mix:
        verify_mix(
            base_dir,
            tokenizer,
            tok_name,
            args.sample_chars,
            update_manifest=not args.no_update_manifest,
        )
    else:
        verify_spurgeon(base_dir, tokenizer, args.sample_chars)


if __name__ == "__main__":
    main()
