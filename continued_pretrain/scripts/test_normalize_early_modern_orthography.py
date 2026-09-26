#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import normalize_early_modern_orthography as ortho  # noqa: E402


def test_normalize_long_s_and_squares() -> None:
    raw = "confe\u017fsion \u25a0 page"
    assert ortho.has_mapped_glyph(raw)
    assert ortho.normalize(raw) == "confession  page"


def test_holdout_paths_are_skipped() -> None:
    repo = Path("continued_pretrain")
    assert ortho.is_holdout_path(repo / "data" / "holdouts" / "puritan_holdout.txt")
    assert ortho.is_holdout_path(repo / "data" / "holdouts_pinned_v3" / "confession_holdout.txt")
    assert ortho.is_holdout_path(Path("puritan_holdout.txt"))
    assert not ortho.is_holdout_path(Path("data") / "puritans" / "downame" / "guide_to_godliness.txt")


def test_mix_roots_cover_every_bucket() -> None:
    repo = Path("/repo")
    roots = {p.as_posix() for p in ortho.mix_source_roots(repo)}
    assert any(r.endswith("data/puritans") for r in roots)
    assert any(r.endswith("data/confessions") for r in roots)
    assert any(r.endswith("data/hymns") for r in roots)
    assert any(r.endswith("data/bible") for r in roots)
    assert any(r.endswith("general_replay.txt") for r in roots)
    assert any(r.endswith("spurgeon_train.txt") for r in roots)


def main() -> None:
    test_normalize_long_s_and_squares()
    test_holdout_paths_are_skipped()
    test_mix_roots_cover_every_bucket()
    print("PASS: normalize long-s")
    print("PASS: holdout skip")
    print("PASS: mix roots")


if __name__ == "__main__":
    main()
