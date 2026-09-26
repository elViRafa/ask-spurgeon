#!/usr/bin/env python3
"""Unit tests for Phase B continue-reweight (no GPU, no mix rebuild)."""
from __future__ import annotations

import random
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import audit_cpt_mix_sources as audit  # noqa: E402
import importlib

mix07 = importlib.import_module("07_build_theology_mix")


def test_author_lists_match() -> None:
    assert mix07.NEW_AUTHOR_FILES == audit.NEW_AUTHOR_FILES
    assert len(mix07.NEW_AUTHOR_FILES) == 11


def test_is_new_author_source() -> None:
    assert mix07.is_new_author_source(
        "C:/repo/data/puritans/downame/guide_to_godliness.txt#3"
    )
    assert mix07.is_new_author_source(
        "data/puritans/ambrose/looking_unto_jesus.txt"
    )
    assert not mix07.is_new_author_source(
        "data/puritans/owen/death_of_death.txt#1"
    )
    assert not mix07.is_new_author_source("continued_pretrain/data/spurgeon_train.txt")


def test_reweight_one_pass_no_copies() -> None:
    rng = random.Random(0)
    new_docs = [
        mix07.Doc(
            text="n" * 100,
            bucket="puritan",
            source=f"data/puritans/downame/guide_to_godliness.txt#{i}",
            author="downame",
        )
        for i in range(5)
    ]
    old_docs = [
        mix07.Doc(
            text="o" * 100,
            bucket="spurgeon",
            source=f"data/spurgeon_train.txt#{i}",
            author="spurgeon",
        )
        for i in range(40)
    ]
    out, report = mix07.apply_continue_reweight(new_docs + old_docs, 0.15, rng)
    new_out = [d for d in out if mix07.is_new_author_source(d.source)]
    assert len(new_out) == 5
    assert report["new_author_docs"] == 5
    assert report["new_author_chars"] == 500
    assert 0.13 <= report["new_author_char_share"] <= 0.18
    assert report["old_docs_out"] < report["old_docs_in"]
    assert len(out) == report["new_author_docs"] + report["old_docs_out"]


def test_holdout_sibling_replay() -> None:
    rng = random.Random(0)
    hold = mix07.Doc(
        text="HOLD" + ("h" * 200),
        bucket="puritan",
        source="data/puritans/owen/death_of_death.txt#0",
        author="owen",
    )
    sibs = [
        mix07.Doc(
            text=f"SIB{i}" + ("s" * 100),
            bucket="puritan",
            source=f"data/puritans/owen/death_of_death.txt#{i + 1}",
            author="owen",
        )
        for i in range(4)
    ]
    spurgeon = [
        mix07.Doc(
            text="SP" + ("g" * 100),
            bucket="spurgeon",
            source=f"data/spurgeon_train.txt#{i}",
            author="spurgeon",
        )
        for i in range(30)
    ]
    new_auth = [
        mix07.Doc(
            text="NW" + ("n" * 100),
            bucket="puritan",
            source=f"data/puritans/downame/guide_to_godliness.txt#{i}",
            author="downame",
        )
        for i in range(8)
    ]
    other = [
        mix07.Doc(
            text="OT" + ("o" * 100),
            bucket="confession",
            source=f"data/confessions/wcf.txt#{i}",
            author="wcf",
        )
        for i in range(10)
    ]
    catalog = [hold] + sibs
    train = sibs + spurgeon + new_auth + other
    out, report = mix07.apply_holdout_sibling_replay(
        train, [hold], catalog, 0.25, rng, spurgeon_floor=0.35, new_author_cap=0.05
    )
    assert report["sibling_docs"] == 4
    assert 0.20 <= report["sibling_char_share"] <= 0.40
    assert report["spurgeon_char_share"] >= 0.30
    assert report["new_author_char_share"] <= 0.10
    assert all(mix07.source_stem(d.source).endswith("death_of_death.txt") for d in sibs)
    assert hold not in out


def test_reweight_refuses_empty_new() -> None:
    rng = random.Random(0)
    docs = [
        mix07.Doc(text="o" * 50, bucket="spurgeon", source="spurgeon_train.txt", author="s")
    ]
    try:
        mix07.apply_continue_reweight(docs, 0.15, rng)
    except ValueError as exc:
        assert "no new-author" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def main() -> None:
    test_author_lists_match()
    test_is_new_author_source()
    test_reweight_one_pass_no_copies()
    test_holdout_sibling_replay()
    test_reweight_refuses_empty_new()
    print("PASS: author lists match")
    print("PASS: new-author source match")
    print("PASS: one-pass reweight no copies")
    print("PASS: holdout-sibling replay")
    print("PASS: empty new authors rejected")


if __name__ == "__main__":
    main()
