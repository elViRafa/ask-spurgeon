#!/usr/bin/env python3
"""Normalize EEBO-TCP long-s and light editorial glyphs, or audit mix sources.

Uses the same map as 10_fetch_puritans.normalize_early_modern_orthography.
Default apply walk: data/puritans, data/confessions, data/hymns, data/bible,
Spurgeon concat, and general replay. Holdout concats are never rewritten
unless --include-holdouts (that would change pinned C probes).
"""

from __future__ import annotations

import argparse
from pathlib import Path

LONG_S = ("\u017f", "\u017F")
MAPPED_GLYPHS = (
    "\u017f",
    "\u017F",
    "\u01b2",
    "\u028b",
    "\u25ca",
    "\u25aa",
    "\u25a0",
    "\u3008",
    "\u3009",
    "\ufffd",
)
HOLDOUT_DIR_NAMES = frozenset(
    {"holdouts", "holdouts_pinned_v3", "holdouts_manual"}
)


def normalize(text: str) -> str:
    if not text:
        return text
    text = text.replace("\u017f", "s").replace("\u017F", "s")
    text = text.replace("\u01b2", "V").replace("\u028b", "v")
    for ch in ("\u25ca", "\u25aa", "\u25a0", "\u3008", "\u3009", "\ufffd"):
        text = text.replace(ch, "")
    return text


def has_mapped_glyph(text: str) -> bool:
    return any(ch in text for ch in MAPPED_GLYPHS)


def is_holdout_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & HOLDOUT_DIR_NAMES:
        return True
    return "holdout" in path.name.lower()


def mix_source_roots(repo: Path) -> list[Path]:
    return [
        repo / "data" / "puritans",
        repo / "data" / "confessions",
        repo / "data" / "hymns",
        repo / "data" / "bible",
        repo / "continued_pretrain" / "data" / "replay" / "general_replay.txt",
        repo / "continued_pretrain" / "data" / "spurgeon_train.txt",
        repo / "continued_pretrain" / "data" / "spurgeon_holdout.txt",
    ]


def iter_text_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in {".txt", ".md"})


def collect_mix_source_paths(repo: Path, *, include_holdouts: bool = False) -> list[Path]:
    paths: list[Path] = []
    for root in mix_source_roots(repo):
        paths.extend(iter_text_files(root))
    if include_holdouts:
        for extra in (
            repo / "continued_pretrain" / "data" / "holdouts",
            repo / "continued_pretrain" / "data" / "holdouts_pinned_v3",
        ):
            paths.extend(iter_text_files(extra))
    return paths


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--only-downame",
        action="store_true",
        help="Only rewrite data/puritans/downame/*.txt",
    )
    p.add_argument(
        "--audit",
        action="store_true",
        help="Report mapped glyphs; do not rewrite",
    )
    p.add_argument(
        "--include-holdouts",
        action="store_true",
        help="Also walk pinned/live holdouts (do not use before a C-comparable continue)",
    )
    args = p.parse_args()
    repo = Path(__file__).resolve().parent.parent.parent
    if args.only_downame:
        paths = sorted((repo / "data" / "puritans" / "downame").glob("*.txt"))
    else:
        paths = collect_mix_source_paths(repo, include_holdouts=args.include_holdouts)

    changed = 0
    skipped = 0
    holdout_skipped = 0
    dirty = 0
    for path in paths:
        if is_holdout_path(path) and not args.include_holdouts and not args.audit:
            holdout_skipped += 1
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        if not has_mapped_glyph(raw):
            skipped += 1
            continue
        before_s = sum(raw.count(ch) for ch in LONG_S)
        if args.audit:
            rel = path.relative_to(repo)
            print(f"DIRTY {rel}  long_s={before_s:,}  chars={len(raw):,}")
            dirty += 1
            continue
        out = normalize(raw)
        path.write_text(out, encoding="utf-8", newline="\n")
        after_s = sum(out.count(ch) for ch in LONG_S)
        rel = path.relative_to(repo)
        print(f"OK  {rel}  long_s {before_s:,} -> {after_s:,}  chars {len(raw):,} -> {len(out):,}")
        changed += 1
    if args.audit:
        print(
            f"Done. dirty={dirty} clean={skipped} holdout_skipped={holdout_skipped}"
        )
        return
    print(
        f"Done. rewritten={changed} untouched={skipped} holdout_skipped={holdout_skipped}"
    )


if __name__ == "__main__":
    main()
