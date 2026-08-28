#!/usr/bin/env python3
"""
Local A: mix txt + holdouts -> Hugging Face datasets (no GPU, no Kaggle push).

Mirrors continued_pretrain/notebooks/A_data_prep_sota.ipynb. Packing
(one_doc_padded) still happens on the GPU at B start.

Default output is kaggle/a_output_v3/. Refuses to overwrite v2 a_output or
runpod_cpt_v2.

Usage (Windows: PYTHONIOENCODING=utf-8):
  python continued_pretrain/scripts/18_prep_hf_dataset.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

DOC_SEP = "<|endoftext|>"
MIN_CHARS = 200
VAL_FRACTION = 0.01
SEED = 42
DOMAIN_BUCKETS = ("spurgeon", "puritan", "confession", "bible")
HOLDOUT_NAMES = ("spurgeon", "puritan", "confession", "general")
V2_TRAIN_DOCS = 8162


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_concat_txt(path: Path, min_chars: int = MIN_CHARS) -> tuple[list[str], int]:
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    docs = [d.strip() for d in text.split(DOC_SEP) if len(d.strip()) > min_chars]
    print(f"{path}: {len(text):,} chars -> {len(docs)} docs")
    max_doc = max((len(d) for d in docs), default=0)
    over = sum(1 for d in docs if len(d) > 8000)
    print(f"  max_doc_chars={max_doc}  docs>8k={over}")
    return docs, len(text)


def g2_guard(manifest: dict, allow_spurgeon_only: bool) -> list[str]:
    buckets = manifest.get("buckets") or {}
    domain = [b for b in DOMAIN_BUCKETS if b in buckets]
    non_empty = [b for b in domain if (buckets.get(b) or {}).get("chars", 0) > 0]
    print("Manifest domain buckets with chars:", non_empty)
    print("Bucket shares:", {b: buckets[b].get("char_share") for b in buckets})
    if len(non_empty) < 2 and not allow_spurgeon_only:
        raise SystemExit(
            "G2: theology mix has <2 domain buckets "
            f"{non_empty}. Add Puritans/confessions/Bible and rebuild with "
            "07_build_theology_mix.py (omit --allow-spurgeon-only). "
            "Set --allow-spurgeon-only only for diagnostics."
        )
    return non_empty


def _is_forbidden_out(path: Path, repo: Path) -> str | None:
    resolved = path.resolve()
    kaggle = (repo / "continued_pretrain" / "kaggle").resolve()
    v2_ds = kaggle / "a_output" / "theology_dataset"
    v2_ho = kaggle / "a_output" / "theology_holdouts"
    snap = kaggle / "runpod_cpt_v2"
    for forbidden, label in (
        (v2_ds, "v2 a_output theology_dataset"),
        (v2_ho, "v2 a_output theology_holdouts"),
        (snap, "runpod_cpt_v2 snapshot"),
    ):
        try:
            resolved.relative_to(forbidden)
            return label
        except ValueError:
            if resolved == forbidden:
                return label
    return None


def main(argv: list[str] | None = None) -> None:
    here = Path(__file__).resolve()
    repo = here.parent.parent.parent
    data = repo / "continued_pretrain" / "data"
    default_out = repo / "continued_pretrain" / "kaggle" / "a_output_v3"

    p = argparse.ArgumentParser(description="Local A: mix txt -> HF datasets (v3)")
    p.add_argument("--repo-root", default=str(repo))
    p.add_argument("--train-txt", default=str(data / "theology_mix_train.txt"))
    p.add_argument("--holdout-dir", default=str(data / "holdouts"))
    p.add_argument("--manifest", default=str(data / "theology_mix_manifest.json"))
    p.add_argument("--out-dir", default=str(default_out))
    p.add_argument("--min-chars", type=int, default=MIN_CHARS)
    p.add_argument("--val-fraction", type=float, default=VAL_FRACTION)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--allow-spurgeon-only", action="store_true")
    args = p.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    train_txt = Path(args.train_txt)
    holdout_dir = Path(args.holdout_dir)
    manifest_path = Path(args.manifest)
    out_dir = Path(args.out_dir)
    out_train = out_dir / "theology_dataset"
    out_holdouts = out_dir / "theology_holdouts"

    for target in (out_dir, out_train, out_holdouts):
        hit = _is_forbidden_out(target, repo)
        if hit:
            raise SystemExit(f"refusing to write into {hit}: {target}")

    if not train_txt.is_file():
        raise SystemExit(f"missing mix txt: {train_txt}")
    if not manifest_path.is_file():
        raise SystemExit(f"missing manifest: {manifest_path}")

    try:
        from datasets import Dataset
    except ImportError as exc:
        raise SystemExit(
            "datasets is required. Install in the project venv (Python 3.11-3.13):\n"
            "  python -m pip install datasets"
        ) from exc

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    g2_guard(manifest, args.allow_spurgeon_only)

    print(f"SHA256 {train_txt.name} ...")
    mix_sha = sha256_file(train_txt)
    train_docs, train_chars = parse_concat_txt(train_txt, min_chars=args.min_chars)
    if len(train_docs) <= V2_TRAIN_DOCS + 200:
        raise SystemExit(
            f"parsed {len(train_docs)} train docs; that looks like the v2 probe mix "
            f"(~{V2_TRAIN_DOCS}), not S4 (~51937). Aborting."
        )

    train_ds = Dataset.from_dict({"text": train_docs})
    split = train_ds.train_test_split(test_size=args.val_fraction, seed=args.seed)
    print(split)
    print(f"train={len(split['train'])} val={len(split['test'])}")

    holdouts: dict[str, object] = {}
    holdout_counts: dict[str, int] = {}
    for name in HOLDOUT_NAMES:
        path = holdout_dir / f"{name}_holdout.txt"
        if not path.is_file():
            print(f"NOTE: missing holdout (skip): {path}")
            continue
        docs, _chars = parse_concat_txt(path, min_chars=args.min_chars)
        if not docs:
            print(f"NOTE: empty holdout: {path}")
            continue
        holdouts[name] = Dataset.from_dict({"text": docs, "bucket": [name] * len(docs)})
        holdout_counts[name] = len(docs)
    print("Holdout buckets:", holdout_counts)
    if "puritan" not in holdouts and not args.allow_spurgeon_only:
        print("WARNING: puritan holdout empty — domain eval will be weak.")

    out_dir.mkdir(parents=True, exist_ok=True)
    if out_train.exists():
        shutil.rmtree(out_train)
    split.save_to_disk(str(out_train))
    print("Saved", out_train)

    if out_holdouts.exists():
        shutil.rmtree(out_holdouts)
    out_holdouts.mkdir(parents=True, exist_ok=True)
    for name, ds in holdouts.items():
        dest = out_holdouts / name
        ds.save_to_disk(str(dest))
        print("Saved", dest)

    storage_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "continued_pretrain/scripts/18_prep_hf_dataset.py",
        "packing_note": "text-only HF datasets; one_doc_padded packing happens on GPU at B",
        "mix_train_txt": str(train_txt),
        "mix_sha256": mix_sha,
        "mix_created_at": manifest.get("created_at"),
        "mix_train_docs_parsed": len(train_docs),
        "mix_train_chars": train_chars,
        "spurgeon_weight": manifest.get("spurgeon_weight"),
        "verified_tokens": (manifest.get("verified_tokens") or {}).get("train_estimated_tokens"),
        "hf_train_docs": len(split["train"]),
        "hf_val_docs": len(split["test"]),
        "val_fraction": args.val_fraction,
        "seed": args.seed,
        "holdout_docs": holdout_counts,
        "out_dir": str(out_dir),
        "storage_bytes": storage_bytes,
    }
    meta_path = out_dir / "DATASET_META.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print("Wrote", meta_path)
    print("Done. Do not copy kaggle/a_output (v2). Next session copies a_output_v3.")


if __name__ == "__main__":
    # Windows cp1252 can crash on mix prints; caller should also set PYTHONIOENCODING=utf-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    main()
