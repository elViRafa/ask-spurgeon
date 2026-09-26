#!/usr/bin/env python3
"""
Build a **diagnostic** new-authors holdout (Downame + wave 5).

Separates train-excluded probe docs from the Phase B upweighted shelf into
``continued_pretrain/data/holdouts_new_authors/`` — **not** live ``holdouts/``,
**not** ``holdouts_pinned_v3/``, and **not** frozen a_output_v3/v4/v5.

Monitor-only for v6 S7 replay (like ``general``): report in train eval / Isolation C;
do **not** add to COMPOSITE_EARLY_STOP_METRICS or §5 / Hub promote.

Usage (from repo root, corpus must exist on the operator machine):

  python continued_pretrain/scripts/19_build_new_authors_holdout.py

  # Also pack HF bucket into an existing a_output_v6 (does not rewrite theology_dataset):
  python continued_pretrain/scripts/19_build_new_authors_holdout.py \\
    --hf-out-dir continued_pretrain/kaggle/a_output_v6/theology_holdouts

Then rebuild mix_v6 with --new-authors-holdout so fingerprints stay out of train,
and/or pass --extra-holdout-dir to 18_prep_hf_dataset.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import importlib

mix07 = importlib.import_module("07_build_theology_mix")

DOC_SEP = mix07.DOC_SEP
NEW_AUTHOR_FILES = mix07.NEW_AUTHOR_FILES
DEFAULT_MAX_CHUNK_CHARS = mix07.DEFAULT_MAX_CHUNK_CHARS
DEFAULT_SEED = 42
DEFAULT_HOLDOUT_N = 20
BUCKET_NAME = "new_authors"


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def forbidden_out(path: Path, repo: Path) -> str | None:
    """Refuse writes into live/pinned/frozen holdout packs."""
    resolved = path.resolve()
    data = (repo / "continued_pretrain" / "data").resolve()
    kaggle = (repo / "continued_pretrain" / "kaggle").resolve()
    forbidden = [
        (data / "holdouts", "live holdouts/"),
        (data / "holdouts_pinned_v3", "holdouts_pinned_v3/"),
        (kaggle / "a_output_v3", "frozen a_output_v3"),
        (kaggle / "a_output_v4", "frozen a_output_v4"),
        (kaggle / "a_output_v5", "frozen a_output_v5"),
    ]
    for root, label in forbidden:
        try:
            resolved.relative_to(root)
            return label
        except ValueError:
            if resolved == root:
                return label
    return None


def load_new_author_docs(
    puritans_dir: Path,
    max_chunk_chars: int,
    files: tuple[tuple[str, str], ...] = NEW_AUTHOR_FILES,
) -> list:
    """Load + chunk only Downame / wave-5 shelf files (same cleaner as 07)."""
    docs = []
    missing = []
    for author, name in files:
        path = puritans_dir / author / name
        if not path.is_file():
            missing.append(f"{author}/{name}")
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        cleaned = mix07.clean_generic_text(raw)
        if not cleaned:
            continue
        for j, chunk in enumerate(mix07.split_long_text(cleaned, max_chars=max_chunk_chars)):
            docs.append(
                mix07.Doc(
                    text=chunk,
                    bucket="puritan",
                    source=f"{path.as_posix()}#{j}" if j else path.as_posix(),
                    author=author,
                    work=Path(name).stem,
                )
            )
    if missing:
        print("MISSING new-author files (need corpus on operator machine):")
        for m in missing:
            print(f"  - data/puritans/{m}")
    return docs


def stratified_take_holdout(
    docs: list,
    n: int,
    rng: random.Random,
) -> tuple[list, list]:
    """Prefer ≥1 doc per source file when possible, then fill to n."""
    if n <= 0 or not docs:
        return list(docs), []
    by_stem: dict[str, list] = defaultdict(list)
    for d in docs:
        by_stem[mix07.source_stem(d.source)].append(d)

    holdout: list = []
    # One random chunk per file first (stable across authors).
    stems = sorted(by_stem.keys())
    rng.shuffle(stems)
    for stem in stems:
        if len(holdout) >= n:
            break
        pick = rng.choice(by_stem[stem])
        holdout.append(pick)

    hold_ids = {id(d) for d in holdout}
    if len(holdout) < n:
        rest = [d for d in docs if id(d) not in hold_ids]
        need = min(n - len(holdout), len(rest))
        if need > 0 and len(rest) >= need * 2:
            extra = rng.sample(rest, need)
            holdout.extend(extra)
            hold_ids = {id(d) for d in holdout}
        elif need > 0 and len(docs) >= n * 2:
            # Fallback: classic take_holdout when stratified under-fills.
            train, classic = mix07.take_holdout(docs, n, rng)
            return train, classic

    train = [d for d in docs if id(d) not in hold_ids]
    # Guard: leave enough train mass (same spirit as take_holdout).
    if len(train) < max(1, len(holdout)):
        return list(docs), []
    return train, holdout


def write_hf_bucket(docs: list, dest: Path) -> None:
    try:
        from datasets import Dataset
    except ImportError as exc:
        raise SystemExit(
            "datasets is required for --hf-out-dir. Install: python -m pip install datasets"
        ) from exc
    if dest.exists():
        import shutil

        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    ds = Dataset.from_dict(
        {
            "text": [d.text for d in docs],
            "bucket": [BUCKET_NAME] * len(docs),
        }
    )
    ds.save_to_disk(str(dest))
    print("Saved HF holdout", dest, "docs", len(docs))


def main(argv: list[str] | None = None) -> None:
    here = Path(__file__).resolve()
    repo = here.parent.parent.parent
    data = repo / "continued_pretrain" / "data"
    default_out = data / "holdouts_new_authors"

    p = argparse.ArgumentParser(
        description="Build diagnostic new-authors holdout (Downame + wave 5; monitor-only)"
    )
    p.add_argument("--repo-root", default=str(repo))
    p.add_argument("--puritans-dir", default=None, help="Default: continued_pretrain/data/puritans")
    p.add_argument("--out-dir", default=str(default_out))
    p.add_argument("--holdout-n", type=int, default=DEFAULT_HOLDOUT_N)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--max-chunk-chars", type=int, default=DEFAULT_MAX_CHUNK_CHARS)
    p.add_argument(
        "--hf-out-dir",
        default=None,
        help=(
            "Optional theology_holdouts root (e.g. kaggle/a_output_v6/theology_holdouts). "
            "Writes only the new_authors/ HF bucket; refuses v3/v4/v5."
        ),
    )
    args = p.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    puritans_dir = (
        Path(args.puritans_dir)
        if args.puritans_dir
        else repo / "continued_pretrain" / "data" / "puritans"
    )
    out_dir = Path(args.out_dir)
    hit = forbidden_out(out_dir, repo)
    if hit:
        raise SystemExit(f"refusing to write into {hit}: {out_dir}")

    docs = load_new_author_docs(puritans_dir, max_chunk_chars=int(args.max_chunk_chars))
    if not docs:
        raise SystemExit(
            "No new-author docs loaded. Fetch Downame + wave 5 under data/puritans/ "
            "(see NEXT_CPT_S7.md shelf table), then re-run this script."
        )

    rng = random.Random(int(args.seed))
    _train, holdout = stratified_take_holdout(docs, int(args.holdout_n), rng)
    if not holdout:
        raise SystemExit(
            f"Could not carve holdout of {args.holdout_n} from {len(docs)} chunks "
            "(need roughly ≥2× docs)."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    concat_path = out_dir / f"{BUCKET_NAME}_holdout.txt"
    mix07.write_concat(concat_path, holdout)
    concat_sha = sha256_file(concat_path)

    per_author: dict[str, int] = defaultdict(int)
    per_source: dict[str, int] = defaultdict(int)
    fingerprints = []
    for d in holdout:
        per_author[d.author] += 1
        per_source[mix07.source_stem(d.source)] += 1
        fingerprints.append(
            {
                "author": d.author,
                "work": d.work,
                "source": d.source,
                "chars": d.n_chars,
                "text_sha256_first200": sha256_text(d.text[:200]),
            }
        )

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bucket": BUCKET_NAME,
        "role": "monitor-only diagnostic (not COMPOSITE / not §5 / not Hub promote)",
        "seed": int(args.seed),
        "holdout_n_target": int(args.holdout_n),
        "holdout_docs": len(holdout),
        "holdout_chars": sum(d.n_chars for d in holdout),
        "catalog_docs": len(docs),
        "catalog_chars": sum(d.n_chars for d in docs),
        "max_chunk_chars": int(args.max_chunk_chars),
        "files": [f"{a}/{n}" for a, n in NEW_AUTHOR_FILES],
        "per_author_docs": dict(sorted(per_author.items())),
        "per_source_docs": dict(sorted(per_source.items())),
        "concat_path": str(concat_path),
        "concat_sha256": concat_sha,
        "fingerprints": fingerprints,
        "notes": [
            "Keep out of live holdouts/ and holdouts_pinned_v3.",
            "Rebuild mix_v6 with 07 --new-authors-holdout pointing at this concat "
            "so these fingerprints stay train-excluded.",
            "Wire as EVAL bucket new_authors (monitor-only like general).",
        ],
    }
    man_path = out_dir / "MANIFEST.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    readme = out_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# New-authors diagnostic holdout (Downame + wave 5)",
                "",
                "Monitor-only probe for v6 holdout-sibling replay CPT.",
                "Not part of §5 gate, COMPOSITE_EARLY_STOP_METRICS, or Hub promote.",
                "Do not copy into `holdouts/` or `holdouts_pinned_v3/`.",
                "",
                f"- Concat: `{BUCKET_NAME}_holdout.txt`",
                f"- SHA256: `{concat_sha}`",
                f"- Docs: {len(holdout)}",
                "",
                "Rebuild with `19_build_new_authors_holdout.py` after corpus fetch.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("=" * 60)
    print("New-authors diagnostic holdout")
    print(f"  Out:      {out_dir}")
    print(f"  Docs:     {len(holdout)} / catalog {len(docs)}")
    print(f"  Chars:    {sum(d.n_chars for d in holdout):,}")
    print(f"  SHA256:   {concat_sha}")
    print(f"  Authors:  {dict(per_author)}")
    print(f"  Manifest: {man_path}")
    print("=" * 60)

    if args.hf_out_dir:
        hf_root = Path(args.hf_out_dir)
        hit = forbidden_out(hf_root / BUCKET_NAME, repo)
        if hit:
            raise SystemExit(f"refusing HF write into {hit}: {hf_root}")
        write_hf_bucket(holdout, hf_root / BUCKET_NAME)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    main()
