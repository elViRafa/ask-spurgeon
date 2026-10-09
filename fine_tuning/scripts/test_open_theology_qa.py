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
    OPEN_THEOLOGY_TEACHER_SYSTEM,
    build_accepted_row,
    done_job_ids,
    parse_qa,
    run_batch,
)
from open_theology_qa_checks import (  # noqa: E402
    check_open_theology_record,
    check_open_theology_row,
    heading_cited,
    ot_normalize,
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


def test_quote_match_ignores_case():
    # train-confession-046: passage "The human foetus, \nfor example", quote starts lowercase.
    passage = (
        "He lays great stress also on the foetal \ndevelopment of the higher orders of animals. "
        "The human foetus, \nfor example, assuming in succession the peculiarities of structure of \n"
        "the reptile, of the fish, of the bird, and of man. This is supposed"
    )
    assistant = (
        'He writes that "the human foetus, for example, assuming in succession the '
        'peculiarities of structure of the reptile, of the fish, of the bird, and of man."'
    )
    assert quote_in_passage(assistant, passage) == 1


def test_quote_match_joins_ocr_linebreak_hyphen():
    # train-puritan-002: passage "be- \nfore", quote "before".
    passage = (
        "not considering that their most secret \nthoughts and actions will, at that day, "
        "be discovered, be- \nfore the great congregation ! How eagerly"
    )
    assistant = (
        '"their most secret thoughts and actions will, at that day, be discovered, '
        'before the great congregation."'
    )
    assert quote_in_passage(assistant, passage) == 1


def test_quote_match_keeps_real_hyphen_at_linebreak():
    passage = "The Lord is our Law-\ngiver, the Lord is our King; he will save us."
    assert quote_in_passage('"the Lord is our Law-giver, the Lord is our King"', passage) == 1
    assert quote_in_passage('"the Lord is our Lawgiver, the Lord is our King"', passage) == 1


@pytest.mark.parametrize(
    "text",
    ["the\u00a0Lord\u2009is  our\nKing", "THE LORD IS OUR KING", "the Lord is our King"],
)
def test_ot_normalize_whitespace_and_case(text):
    assert ot_normalize(text) == "the lord is our king"


def test_quote_match_still_rejects_paraphrase_after_normalization():
    passage = "The human foetus, \nfor example, assuming in succession the peculiarities"
    assert quote_in_passage('"the human fetus, for example, assuming in succession"', passage) == 0


@pytest.mark.parametrize(
    "cite",
    [
        "[Cotton \u2014 Keys Of The Kingdom]",
        "[Cotton \u2013 Keys Of The Kingdom]",
        "[Cotton - Keys of the Kingdom]",
        "[Cotton\u00a0\u2014 Keys  Of The Kingdom]",
    ],
)
def test_heading_cite_normalizes_dash_space_case(cite):
    assert heading_cited(f'He says "x y z w v u t s". {cite}', "[Cotton \u2014 Keys Of The Kingdom]")


@pytest.mark.parametrize(
    "assistant",
    [
        # train-puritan-125: parentheses instead of the catalog brackets.
        'He says "x y z w v u t s" (Cotton \u2014 Keys Of The Kingdom).',
        # train-puritan-002: heading named inline in prose, no bracketed cite.
        'The Boston \u2014 Fourfold State teaches that "x y z w v u t s".',
        # wrong work
        'He says "x y z w v u t s". [Cotton \u2014 Way Of The Churches]',
    ],
)
def test_heading_cite_still_requires_brackets_and_right_work(assistant):
    heading = (
        "[Boston \u2014 Fourfold State]" if "Boston" in assistant else "[Cotton \u2014 Keys Of The Kingdom]"
    )
    assert not heading_cited(assistant, heading)


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


def test_teacher_prompt_requires_bracketed_heading_at_end():
    # train-puritan-002 (heading as prose) / train-puritan-125 (heading in parentheses).
    rule5 = next(l for l in OPEN_THEOLOGY_TEACHER_SYSTEM.splitlines() if l.startswith("5."))
    assert "End the answer with the HEADING string exactly as given" in rule5
    assert "including its square brackets" in rule5
    assert "[Boston \u2014 Fourfold State]" in rule5
    assert "Do not put it in parentheses" in rule5
    assert "do not turn it into a sentence" in rule5


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


# --- Doubled-quote Spurgeon headings (train-spurgeon-036 / train-spurgeon-031) ---
from fix_open_theology_catalog_headings import fixed_heading, migrate  # noqa: E402
from plan_open_theology_jobs import clean_sermon_title, sermon_heading  # noqa: E402


@pytest.mark.parametrize(
    "raw, want",
    [
        ('"Jesus Our Lord"', "Jesus Our Lord"),
        ('""The True Sayings of God""', "The True Sayings of God"),
        ("\u201cHiding in You!\u201d", "Hiding in You!"),
        ("The Silver Trumpet", "The Silver Trumpet"),
        ('How "The Unspeakable" is Spoken of', 'How "The Unspeakable" is Spoken of'),
        ('"Foo" and "Bar"', '"Foo" and "Bar"'),
        ("Christ's Yoke and Burden", "Christ's Yoke and Burden"),
        ("# Three Arrows--or Six? #", "Three Arrows--or Six?"),
    ],
)
def test_clean_sermon_title(raw, want):
    assert clean_sermon_title(raw) == want


def test_sermon_heading_matches_teacher_cite():
    # What the teacher actually wrote in train-spurgeon-036.
    assert sermon_heading(2806, '"Jesus Our Lord"') == '[Sermon 2806 \u2014 "Jesus Our Lord"]'
    assert fixed_heading('[Sermon 2806 \u2014 ""Jesus Our Lord""]') == '[Sermon 2806 \u2014 "Jesus Our Lord"]'
    assert fixed_heading("[Boston \u2014 Fourfold State]") == "[Boston \u2014 Fourfold State]"


def test_fixed_heading_lets_teacher_cite_pass():
    passage = "She calls Him Lord in every part of His work and suffering, and she believes."
    stored = '[Sermon 2806 \u2014 ""Jesus Our Lord""]'
    answer = 'Spurgeon says "calls Him Lord in every part of His work". [Sermon 2806 \u2014 "Jesus Our Lord"]'
    kw = dict(system=THEOLOGY_CHAT_SYSTEM_PROMPT, user="Why Lord?", assistant=answer, passage=passage)
    assert any("heading" in e for e in check_open_theology_row(heading=stored, **kw))
    assert check_open_theology_row(heading=fixed_heading(stored), **kw) == []


def _write_queue(d: Path) -> None:
    bad = lambda n, t: f'[Sermon {n} \u2014 ""{t}""]'  # noqa: E731
    entries = [
        {"job_id": "train-spurgeon-001", "heading": bad(1, "A B")},
        {"job_id": "train-spurgeon-002", "heading": bad(2, "C D")},
        {"job_id": "train-puritan-003", "heading": "[Owen \u2014 Mortification]"},
    ]
    (d / "catalog.json").write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    jobs = [dict(e, title=e["heading"].split("\u2014 ")[1][:-1]) for e in entries]
    (d / "jobs.jsonl").write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs), encoding="utf-8")
    (d / "rejected.jsonl").write_text(json.dumps({"job_id": "train-spurgeon-001"}) + "\n", encoding="utf-8")
    (d / "accepted.jsonl").write_text("", encoding="utf-8")


def test_migration_dry_run_writes_nothing(tmp_path: Path):
    _write_queue(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    res = migrate(tmp_path, apply=False)
    assert res["catalog"] == 2 and res["jobs"] == 1 and res["skipped_done"] == ["train-spurgeon-001"]
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_migration_apply_pending_only_with_backup(tmp_path: Path):
    _write_queue(tmp_path)
    rejected_before = (tmp_path / "rejected.jsonl").read_bytes()
    migrate(tmp_path, apply=True)
    assert len(list(tmp_path.glob("catalog.json.bak-*"))) == 1
    assert len(list(tmp_path.glob("jobs.jsonl.bak-*"))) == 1
    cat = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))["entries"]
    assert [e["heading"] for e in cat] == [
        '[Sermon 1 \u2014 "A B"]', '[Sermon 2 \u2014 "C D"]', "[Owen \u2014 Mortification]",
    ]
    jobs = {j["job_id"]: j for j in map(json.loads, (tmp_path / "jobs.jsonl").read_text(encoding="utf-8").splitlines())}
    assert jobs["train-spurgeon-001"]["heading"] == '[Sermon 1 \u2014 ""A B""]'  # done: untouched
    assert jobs["train-spurgeon-002"]["heading"] == '[Sermon 2 \u2014 "C D"]'
    assert jobs["train-spurgeon-002"]["title"] == "C D"
    assert (tmp_path / "rejected.jsonl").read_bytes() == rejected_before
    assert migrate(tmp_path, apply=False)["jobs"] == 0  # idempotent
