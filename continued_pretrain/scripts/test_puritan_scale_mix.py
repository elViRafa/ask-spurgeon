#!/usr/bin/env python3
"""Unit tests for the S9 puritan-scale mix (no GPU, no mix rebuild)."""
from __future__ import annotations

import importlib
import random
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

mix07 = importlib.import_module("07_build_theology_mix")
Doc = mix07.Doc

LONG_S_HOLDOUT = (
    "teacheth vs to denie vngodlines and worldly lu\u017fts: and to liue holily, "
    "righteou\u017fly, and \u017foberly in this pre\u017fent world, looking for that ble\u017f\u017fed hope "
) * 6


def _words(seed: int, n: int = 120) -> str:
    rng = random.Random(seed)
    vocab = ["grace", "faith", "covenant", "mercy", "sin", "soul", "christ", "law", "glory", "word"]
    return " ".join(rng.choice(vocab) + str(rng.randrange(1000)) for _ in range(n))


def test_fingerprint_ignores_long_s_and_spacing() -> None:
    a = "And  therefore  were  \u017fuch  external  rites"
    b = "And therefore were such external rites"
    assert mix07.holdout_fingerprint(a) == mix07.holdout_fingerprint(b)


def test_sibling_stems_match_long_s_holdout() -> None:
    hold = Doc(text=LONG_S_HOLDOUT, bucket="puritan", source="holdout#0")
    normalized_chunk = mix07.normalize_early_modern_orthography(LONG_S_HOLDOUT)
    catalog = [
        Doc(text=normalized_chunk, bucket="puritan", source="data/puritans/rogers/seven.txt#61"),
        Doc(text=_words(1), bucket="puritan", source="data/puritans/owen/vol1.txt#0"),
    ]
    stems = mix07.holdout_source_stems([hold], catalog)
    assert stems == {"data/puritans/rogers/seven.txt"}


def test_sibling_stems_probe_fallback_when_boundary_moved() -> None:
    body = _words(7, 400)
    hold = Doc(text=body, bucket="puritan", source="holdout#0")
    shifted = Doc(
        text="PREFACE " + _words(8, 30) + " " + body,
        bucket="puritan",
        source="data/puritans/burgess/refining.txt#552",
    )
    stems = mix07.holdout_source_stems([hold], [shifted])
    assert stems == {"data/puritans/burgess/refining.txt"}


def test_overlap_gate_drops_normalized_copy() -> None:
    hold = Doc(text=LONG_S_HOLDOUT, bucket="puritan", source="holdout#0")
    leaked = Doc(
        text=mix07.normalize_early_modern_orthography(LONG_S_HOLDOUT),
        bucket="puritan",
        source="data/puritans/rogers/seven.txt#61",
    )
    clean = Doc(text=_words(3, 300), bucket="puritan", source="data/puritans/rogers/seven.txt#62")
    out, report = mix07.drop_holdout_overlaps([leaked, clean], [hold])
    assert out == [clean]
    assert report["dropped_docs"] == 1


def test_overlap_gate_keeps_single_shared_quote() -> None:
    hold = Doc(text=_words(11, 400), bucket="puritan", source="holdout#0")
    probe = mix07.holdout_probes(hold.text)[3]
    doc = Doc(text=_words(12, 200) + " " + probe + " " + _words(13, 200), bucket="puritan", source="x#1")
    out, report = mix07.drop_holdout_overlaps([doc], [hold])
    assert out == [doc]
    assert report["dropped_docs"] == 0


def _scale_fixture():
    hold = Doc(text=_words(100, 300), bucket="puritan", source="holdout#0")
    sibs = [
        Doc(text=_words(200 + i, 300), bucket="puritan", source=f"data/puritans/owen/vol5.txt#{i}")
        for i in range(6)
    ]
    catalog_hold = Doc(text=hold.text, bucket="puritan", source="data/puritans/owen/vol5.txt#99")
    confession = [
        Doc(text=_words(300 + i, 200), bucket="confession", source=f"data/confessions/wcf.txt#{i}")
        for i in range(4)
    ]
    spurgeon = [
        Doc(text=_words(400 + i, 300), bucket="spurgeon", source=f"spurgeon_train.txt#{i}")
        for i in range(30)
    ]
    puritan = [
        Doc(text=_words(500 + i, 300), bucket="puritan", source=f"data/puritans/manton/vol{i}.txt#0")
        for i in range(60)
    ]
    general = [Doc(text=_words(600, 300), bucket="general", source="general#0")]
    train = sibs + confession + spurgeon + puritan + general
    catalog = sibs + [catalog_hold] + puritan
    return hold, sibs, confession, spurgeon, puritan, train, catalog


def test_puritan_scale_keeps_all_siblings_and_confession() -> None:
    hold, sibs, confession, _sp, _pur, train, catalog = _scale_fixture()
    total = sum(d.n_chars for d in train) // 2
    out, report = mix07.apply_puritan_scale(
        train, [hold], catalog, total, random.Random(0), spurgeon_share=0.30
    )
    for d in sibs + confession:
        assert d in out
    assert report["sibling_docs"] == len(sibs)
    assert report["sibling_stems"] == ["data/puritans/owen/vol5.txt"]
    assert report["confession_nonsibling_docs"] == len(confession)
    out_chars = sum(d.n_chars for d in out)
    conf_chars = sum(d.n_chars for d in out if d.bucket == "confession")
    assert report["confession_char_share"] == round(conf_chars / out_chars, 4)
    assert 0.25 <= report["spurgeon_char_share"] <= 0.36
    assert report["dropped_buckets"] == ["general"]
    assert not any(d.bucket == "general" for d in out)
    assert len(out) == len({id(d) for d in out})


def test_puritan_scale_prefers_unseen() -> None:
    hold, _sibs, _conf, spurgeon, puritan, train, catalog = _scale_fixture()
    seen = {mix07.holdout_fingerprint(d.text, 160) for d in puritan[:40] + spurgeon[:20]}
    fill = sum(d.n_chars for d in puritan[40:]) // 2
    sp = sum(d.n_chars for d in spurgeon[20:]) // 2
    fixed = sum(d.n_chars for d in train if d.bucket == "confession") + sum(
        d.n_chars for d in train if mix07.source_stem(d.source) == "data/puritans/owen/vol5.txt"
    )
    total = fixed + fill + sp
    out, report = mix07.apply_puritan_scale(
        train, [hold], catalog, total, random.Random(0),
        spurgeon_share=sp / total, seen_fps=seen,
    )
    kept_fill = [d for d in out if d in puritan]
    assert kept_fill
    assert all(d in puritan[40:] for d in kept_fill)
    assert report["puritan_fill_unseen_chars"] == report["puritan_fill_chars"]
    assert report["prefer_unseen"] is True


def test_puritan_scale_rejects_bad_share() -> None:
    hold, *_rest, train, catalog = _scale_fixture()
    try:
        mix07.apply_puritan_scale(train, [hold], catalog, 1000, random.Random(0), spurgeon_share=1.2)
    except ValueError as exc:
        assert "spurgeon_share" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_scale_args_are_exclusive() -> None:
    args = mix07.parse_args(
        ["--puritan-scale-total-chars", "1000", "--holdout-sibling-share", "0.25", "--out-dir", "x"]
    )
    try:
        mix07.build_mix(args)
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected SystemExit(2)")
