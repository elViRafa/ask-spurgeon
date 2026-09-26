#!/usr/bin/env python3
"""Unit tests for new-authors diagnostic holdout builder (no GPU, no corpus required)."""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

mix07 = importlib.import_module("07_build_theology_mix")
na = importlib.import_module("19_build_new_authors_holdout")
import cpt_runtime as cr  # noqa: E402


def _fake_docs(n_files: int = 4, chunks_each: int = 6) -> list:
    docs = []
    for i in range(n_files):
        author = f"author{i}"
        name = f"work{i}.txt"
        for j in range(chunks_each):
            text = f"CHUNK-{author}-{j}-" + ("x" * 600)
            docs.append(
                mix07.Doc(
                    text=text,
                    bucket="puritan",
                    source=f"/data/puritans/{author}/{name}#{j}",
                    author=author,
                    work=f"work{i}",
                )
            )
    return docs


def test_stratified_take_holdout_covers_sources() -> None:
    import random

    docs = _fake_docs()
    rng = random.Random(42)
    train, hold = na.stratified_take_holdout(docs, 8, rng)
    assert len(hold) == 8
    assert len(train) == len(docs) - 8
    stems = {mix07.source_stem(d.source) for d in hold}
    assert len(stems) >= 4  # one per file at minimum


def test_forbidden_out_blocks_live_and_frozen() -> None:
    repo = Path("/tmp/ask-spurgeon-fake")
    # Use real-ish relative layout under a temp root via Path construction
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "continued_pretrain" / "data" / "holdouts").mkdir(parents=True)
        (root / "continued_pretrain" / "data" / "holdouts_pinned_v3").mkdir(parents=True)
        (root / "continued_pretrain" / "kaggle" / "a_output_v3").mkdir(parents=True)
        assert na.forbidden_out(root / "continued_pretrain" / "data" / "holdouts", root)
        assert na.forbidden_out(
            root / "continued_pretrain" / "data" / "holdouts_pinned_v3" / "x.txt", root
        )
        assert na.forbidden_out(
            root / "continued_pretrain" / "kaggle" / "a_output_v3" / "theology_holdouts", root
        )
        ok = root / "continued_pretrain" / "data" / "holdouts_new_authors"
        assert na.forbidden_out(ok, root) is None


def test_s7_composite_excludes_new_authors_monitor() -> None:
    cfg = cr.resolve_continue_training_config(
        env={"CPT_RUN_MODE": "continue", "CPT_CONTINUE_PROFILE": "s7"},
        packed_epoch_steps=100,
    )
    assert "new_authors" in cfg["eval_buckets_during_train"]
    assert "general" in cfg["eval_buckets_during_train"]
    assert "eval_new_authors_loss" not in cfg["composite_early_stop_metrics"]
    assert "eval_general_loss" not in cfg["composite_early_stop_metrics"]
    assert cfg["composite_early_stop_metrics"] == [
        "eval_spurgeon_loss",
        "eval_puritan_loss",
        "eval_confession_loss",
    ]


def test_remote_s7_composite_env_untouched() -> None:
    sh = (SCRIPTS / "vast_cpt_s7_remote_continue_b.sh").read_text(encoding="utf-8")
    assert (
        "COMPOSITE_EARLY_STOP_METRICS='eval_spurgeon_loss,eval_puritan_loss,eval_confession_loss'"
        in sh
    )
    assert "eval_new_authors_loss" not in sh
    assert "a_output_v6" in (SCRIPTS / "vast_cpt_s7_common.ps1").read_text(encoding="utf-8")


def test_builder_writes_manifest_with_synthetic_corpus() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pur = root / "continued_pretrain" / "data" / "puritans"
        # Enough chars per file for multiple 7k chunks so holdout_n=11 leaves train mass.
        body = ("Paragraph of practical divinity.\n\n" * 200) + ("word " * 8000)
        for author, name in mix07.NEW_AUTHOR_FILES:
            d = pur / author
            d.mkdir(parents=True, exist_ok=True)
            (d / name).write_text(body, encoding="utf-8")
        out = root / "continued_pretrain" / "data" / "holdouts_new_authors"
        na.main(
            [
                "--repo-root",
                str(root),
                "--puritans-dir",
                str(pur),
                "--out-dir",
                str(out),
                "--holdout-n",
                "11",
                "--seed",
                "42",
            ]
        )
        concat = out / "new_authors_holdout.txt"
        man = out / "MANIFEST.json"
        assert concat.is_file()
        assert man.is_file()
        data = json.loads(man.read_text(encoding="utf-8"))
        assert data["bucket"] == "new_authors"
        assert data["holdout_docs"] == 11
        assert data["concat_sha256"]
        assert "monitor-only" in data["role"]


if __name__ == "__main__":
    test_stratified_take_holdout_covers_sources()
    print("PASS: stratified holdout")
    test_forbidden_out_blocks_live_and_frozen()
    print("PASS: forbidden paths")
    test_s7_composite_excludes_new_authors_monitor()
    print("PASS: composite excludes new_authors")
    test_remote_s7_composite_env_untouched()
    print("PASS: remote S7 composite untouched / still v6")
    test_builder_writes_manifest_with_synthetic_corpus()
    print("PASS: builder synthetic corpus")
    print("ALL PASS")
