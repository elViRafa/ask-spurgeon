#!/usr/bin/env python3
"""Tests for open-theology QA planner, checker, and dry generator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from config import SPURGEON_SFT_SYSTEM_PROMPT, THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from generate_open_theology_qa import (  # noqa: E402
    build_accepted_row,
    done_job_ids,
    parse_qa,
    run_batch,
)
from open_theology_qa_checks import (  # noqa: E402
    check_open_theology_record,
    check_open_theology_row,
    quote_in_passage,
)
from plan_open_theology_jobs import (  # noqa: E402
    load_spurgeon_holdout_numbers,
    plan,
    sample_bucket,
)


def test_theology_prompt_distinct_from_rag():
    assert "CONTEXT" not in THEOLOGY_CHAT_SYSTEM_PROMPT
    assert "CONTEXT" in SPURGEON_SFT_SYSTEM_PROMPT
    assert THEOLOGY_CHAT_SYSTEM_PROMPT != SPURGEON_SFT_SYSTEM_PROMPT


def test_check_accepts_good_row():
    passage = (
        'Christ is the Beloved of the Father. What a remarkable instance you have '
        "of immutable love in the covenant of grace."
    )
    heading = '[Sermon 1 — "The Immutability of God"]'
    errs = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach about Christ as the Beloved?",
        assistant=(
            f'Spurgeon teaches that Christ is "the Beloved of the Father." {heading} '
            "The sermon argues from the text."
        ),
        passage=passage,
        heading=heading,
    )
    assert errs == []


def test_check_rejects_context_leak():
    passage = 'Christ is the Beloved of the Father. Extra words for length here.'
    heading = '[Sermon 1 — "The Immutability of God"]'
    errs = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="CONTEXT:\nfoo\n\nQUESTION: Why?",
        assistant=f'Spurgeon teaches that Christ is "the Beloved of the Father." {heading}',
        passage=passage,
        heading=heading,
    )
    assert any("CONTEXT" in e for e in errs)


def test_check_rejects_vocative():
    passage = 'Christ is the Beloved of the Father. Extra words for length here.'
    heading = '[Sermon 1 — "The Immutability of God"]'
    errs = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant=f'Beloved, hear this: "the Beloved of the Father." {heading}',
        passage=passage,
        heading=heading,
    )
    assert any("vocative" in e for e in errs)


def test_check_rejects_bad_quote():
    passage = 'Christ is the Beloved of the Father. Extra words for length here.'
    heading = '[Sermon 1 — "The Immutability of God"]'
    errs = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant=f'Spurgeon says "totally invented phrase here." {heading}',
        passage=passage,
        heading=heading,
    )
    assert any("quote" in e for e in errs)


# Synthetic strings modeled on the 2026-10-09 halt rejects.
_PUNCT_PASSAGE = (
    "10. Now because this way of entring into covenant is not between those that are "
    "equall, but between Lord and servant. Therefore it portaineth to God. Even "
    "Omnipotence cannot make a part to contain the whole. Divine works are as..."
)


@pytest.mark.parametrize(
    "assistant",
    [
        # train-puritan-121: passage "...servant." quoted as "...servant,"
        'As the passage states, "Now because this way of entring into covenant is not '
        'between those that are equall, but between Lord and servant," it follows.',
        # train-confession-019: curly quotes, passage "...whole." quoted as "...whole,"
        "He writes that \u201cEven Omnipotence cannot make a part to contain the whole,\u201d indicating.",
        # trailing "!" / ";" and a line break inside the passage span
        'He says "Omnipotence cannot make a\npart to contain the whole;" here.',
    ],
)
def test_quote_match_ignores_edge_punctuation(assistant):
    assert quote_in_passage(assistant, _PUNCT_PASSAGE) == 1


def test_quote_match_still_rejects_altered_words():
    # train-puritan-044: teacher "corrected" Sibbes -> Sibbs; must stay a reject.
    passage = "we find ' Thomas Sibbes was bmied January ye 18th 1690,' and Elizabeth"
    assistant = 'The register says: "Thomas Sibbs was bmied January ye 18th 1690."'
    assert quote_in_passage(assistant, passage) == 0


def test_quote_match_rejects_punctuation_only_core():
    # Stripping edges must not let a tiny core slip through.
    passage = "a b c d e f g h ... , , , ."
    assert quote_in_passage('x "  ...,,,.  ." y', passage) == 0
    assert quote_in_passage('x "a b c,,,,,," y', passage) == 0


def test_check_rejects_bad_citation():
    passage = 'Christ is the Beloved of the Father. Extra words for length here.'
    heading = '[Sermon 1 — "The Immutability of God"]'
    errs = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant='Spurgeon teaches that Christ is "the Beloved of the Father." [Sermon 999]',
        passage=passage,
        heading=heading,
    )
    assert any("heading" in e for e in errs)


def test_check_rejects_wrong_system_prompt():
    passage = 'Christ is the Beloved of the Father. Extra words for length here.'
    heading = '[Sermon 1 — "The Immutability of God"]'
    errs = check_open_theology_row(
        system=SPURGEON_SFT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant=f'Spurgeon teaches that Christ is "the Beloved of the Father." {heading}',
        passage=passage,
        heading=heading,
    )
    assert any("system prompt" in e for e in errs)


def test_check_rejects_refusal():
    passage = 'Christ is the Beloved of the Father. Extra words for length here.'
    heading = '[Sermon 1 — "The Immutability of God"]'
    errs = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What about quantum physics?",
        assistant=(
            'These excerpts do not address that question, and I will not invent an answer. '
            f'I do find "the Beloved of the Father." {heading}'
        ),
        passage=passage,
        heading=heading,
    )
    assert any("refusal" in e for e in errs)


def test_parse_qa_json():
    q, a = parse_qa('{"question": "Why faith?", "answer": "Because grace."}')
    assert q == "Why faith?"
    assert a == "Because grace."


def test_build_accepted_row_shape():
    job = {
        "job_id": "train-spurgeon-000",
        "bucket": "spurgeon",
        "work_id": "spurgeon-1",
        "source_path": "data/chspurgeon-sermons/volume-1/sermon-1.md",
        "heading": '[Sermon 1 — "The Immutability of God"]',
        "passage": 'Christ is the Beloved of the Father. Extra words for length here.',
    }
    row = build_accepted_row(
        job,
        "What does Spurgeon teach?",
        f'Spurgeon teaches that Christ is "the Beloved of the Father." {job["heading"]}',
        "groq",
        "test-model",
    )
    assert row["messages"][0]["content"] == THEOLOGY_CHAT_SYSTEM_PROMPT
    assert "CONTEXT" not in row["messages"][1]["content"]
    assert row["meta"]["passage"]
    assert check_open_theology_record(row) == []


def test_done_job_ids():
    ids = done_job_ids(
        [{"job_id": "a"}],
        [{"meta": {"job_id": "b"}}],
    )
    assert ids == {"a", "b"}


def test_sample_bucket_reserves_eval():
    import random

    cands = [
        {
            "work_id": f"w-{i}",
            "bucket": "spurgeon",
            "heading": f"[Sermon {i}]",
            "source_path": f"data/sermon-{i}.md",
            "passage": "x" * 500,
        }
        for i in range(30)
    ]
    tr, ev = sample_bucket(cands, 10, 5, random.Random(0))
    assert len(tr) == 10
    assert len(ev) == 5
    train_paths = {r["source_path"] for r in tr}
    eval_paths = {r["source_path"] for r in ev}
    assert train_paths.isdisjoint(eval_paths)


def test_plan_dry_run_no_files(tmp_path: Path):
    out = tmp_path / "qa_open_theology"
    summary = plan(
        out_dir=out,
        holdout_dir=_REPO / "continued_pretrain" / "data" / "mix_v7" / "holdouts",
        seed=3407,
        dry_run=True,
    )
    assert summary["train_jobs"] == 300
    assert summary["eval_jobs"] == 40
    assert summary["by_bucket_train"]["puritan"] == 150
    assert summary["by_bucket_train"]["spurgeon"] == 100
    assert summary["by_bucket_train"]["confession"] == 50
    assert not out.exists()


def test_plan_writes_and_skips_holdout_sermons(tmp_path: Path):
    out = tmp_path / "qa_open_theology"
    holdout_dir = _REPO / "continued_pretrain" / "data" / "mix_v7" / "holdouts"
    holdout_nums = load_spurgeon_holdout_numbers(holdout_dir)
    assert holdout_nums  # fixture present in repo

    summary = plan(out_dir=out, holdout_dir=holdout_dir, seed=3407, dry_run=False)
    assert summary["train_jobs"] == 300
    jobs = [
        json.loads(line)
        for line in (out / "jobs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    eval_jobs = [
        json.loads(line)
        for line in (out / "eval_jobs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(jobs) == 300
    assert len(eval_jobs) == 40
    train_ids = {j["job_id"] for j in jobs}
    eval_ids = {j["job_id"] for j in eval_jobs}
    assert train_ids.isdisjoint(eval_ids)

    for j in jobs + eval_jobs:
        if j["bucket"] != "spurgeon":
            continue
        # work_id like spurgeon-32
        num = int(j["work_id"].split("-")[1])
        assert num not in holdout_nums

    status = json.loads((out / "status.json").read_text(encoding="utf-8"))
    assert status["counts"]["remaining"] == 300
    assert status["halted"] is False


def test_dry_generator_writes_zero(tmp_path: Path):
    out = tmp_path / "qa_open_theology"
    plan(
        out_dir=out,
        holdout_dir=_REPO / "continued_pretrain" / "data" / "mix_v7" / "holdouts",
        seed=3407,
        dry_run=False,
    )
    report = run_batch(
        out_dir=out,
        limit=5,
        apply=False,
        provider="groq",
        model="",
        sleep_s=0,
    )
    assert report["apply"] is False
    assert report["batch"] == 5
    assert (out / "accepted.jsonl").read_text(encoding="utf-8") == ""
    assert (out / "rejected.jsonl").read_text(encoding="utf-8") == ""
    status = json.loads((out / "status.json").read_text(encoding="utf-8"))
    assert status["counts"]["accepted"] == 0
