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


def test_teacher_prompt_quote_format_rule():
    # train-puritan-057/049 (single quotes), -145 (OCR corrected), spurgeon-042 (title quoted),
    # puritan-031 (\\' in JSON), puritan-110 (backslash-escaped quote inside quote).
    rule = next(l for l in OPEN_THEOLOGY_TEACHER_SYSTEM.splitlines() if l.startswith("4a."))
    assert "ASCII double quotes only, never single quotes" in rule
    assert "Never correct spelling, archaic forms, or OCR errors inside the quote" in rule
    assert "Never use the sermon or work title as the quotation" in rule
    assert "write apostrophes as a plain '" in rule and "(never \\')" in rule


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


# --- Teacher 429 / quota is not a quality reject (2026-10-09 15:30 BRT halt) ---
import generate_open_theology_qa as _gen  # noqa: E402
from generate_open_theology_qa import is_rate_limit_error  # noqa: E402
from requeue_open_theology_teacher_errors import maintain  # noqa: E402

_GOOD_PASSAGE = "Christ is the Beloved of the Father. What a remarkable instance of love."
_GOOD_HEADING = '[Sermon 1 \u2014 "The Immutability of God"]'
_GOOD_RAW = json.dumps({
    "question": "What does Spurgeon teach about Christ?",
    "answer": f'Spurgeon teaches that Christ is "the Beloved of the Father." {_GOOD_HEADING}',
})
_429 = ('teacher failed after 4 tries: 429: {"error":{"message":"Rate limit reached for model '
        '`openai/gpt-oss-120b` ... tokens per day (TPD): Limit 200000, Used 199111')


def _gen_dir(tmp_path: Path, n: int) -> Path:
    out = tmp_path / "qa"
    out.mkdir()
    jobs = [{"job_id": f"train-spurgeon-{i:03d}", "role": "train", "work_id": f"w{i}",
             "bucket": "spurgeon", "heading": _GOOD_HEADING, "source_path": f"s{i}.md",
             "passage": _GOOD_PASSAGE, "title": "t"} for i in range(n)]
    (out / "jobs.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs), encoding="utf-8")
    (out / "status.json").write_text(json.dumps({"halted": False, "counts": {}}), encoding="utf-8")
    return out


def _fake_teacher(script):
    it = iter(script)

    def fake(*a, **k):
        x = next(it)
        if isinstance(x, Exception):
            raise x
        return x
    return fake


def test_is_rate_limit_error():
    assert is_rate_limit_error("teacher error: " + _429)
    assert not is_rate_limit_error("teacher error: bad response shape: KeyError('choices')")


def test_429_halts_without_writing_reject(tmp_path: Path, monkeypatch):
    out = _gen_dir(tmp_path, 4)
    monkeypatch.setattr(_gen, "call_teacher", _fake_teacher([_GOOD_RAW, RuntimeError(_429)]))
    rep = run_batch(out_dir=out, limit=4, apply=True, provider="groq", model="m", sleep_s=0)
    assert rep["halted"] and "rate limit" in rep["halt_reason"]
    assert rep["rejected_new"] == 0 and rep["accepted_new"] == 1
    assert not (out / "rejected.jsonl").exists() or (out / "rejected.jsonl").read_text(encoding="utf-8") == ""
    st = json.loads((out / "status.json").read_text(encoding="utf-8"))
    assert st["halted"] and "429" in st["last_error"]
    done = done_job_ids(_gen.read_jsonl(out / "accepted.jsonl"), _gen.read_jsonl(out / "rejected.jsonl"))
    assert "train-spurgeon-001" not in done  # 429 job still pending


def test_transport_errors_do_not_trip_reject_rate(tmp_path: Path, monkeypatch):
    # 2 non-429 transport errors among 6 jobs: no rejects written, no reject-rate halt.
    out = _gen_dir(tmp_path, 6)
    err = RuntimeError("bad response shape")
    monkeypatch.setattr(_gen, "call_teacher", _fake_teacher(
        [_GOOD_RAW, err, _GOOD_RAW, _GOOD_RAW, err, _GOOD_RAW]))
    rep = run_batch(out_dir=out, limit=6, apply=True, provider="groq", model="m", sleep_s=0)
    assert not rep["halted"]
    assert rep["accepted_new"] == 4 and rep["rejected_new"] == 0 and rep["teacher_errors"] == 2


def test_three_consecutive_transport_errors_still_halt(tmp_path: Path, monkeypatch):
    out = _gen_dir(tmp_path, 5)
    err = RuntimeError("connection reset")
    monkeypatch.setattr(_gen, "call_teacher", _fake_teacher([err, err, err, _GOOD_RAW, _GOOD_RAW]))
    rep = run_batch(out_dir=out, limit=5, apply=True, provider="groq", model="m", sleep_s=0)
    assert rep["halted"] and "consecutive" in rep["halt_reason"]
    assert rep["rejected_new"] == 0


def _maint_dir(tmp_path: Path) -> Path:
    d = tmp_path / "m"
    d.mkdir()
    jobs = [{"job_id": i, "bucket": "confession", "work_id": i, "source_path": "x", "heading": "[H]"}
            for i in ("j-429", "j-quote", "j-bad", "j-acc")]
    (d / "jobs.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs), encoding="utf-8")
    (d / "accepted.jsonl").write_text(json.dumps({"job_id": "j-acc"}) + "\n", encoding="utf-8")
    rej = [{"job_id": "j-429", "errors": ["teacher error: " + _429]},
           {"job_id": "j-quote", "errors": ["answerable row has no quote found in source passage"]}]
    (d / "rejected.jsonl").write_text("".join(json.dumps(r) + "\r\n" for r in rej), encoding="utf-8",
                                      newline="")
    return d


def test_maintain_dry_run_writes_nothing(tmp_path: Path):
    d = _maint_dir(tmp_path)
    before = {p.name: p.read_bytes() for p in d.iterdir()}
    res = maintain(d, skip=["j-bad", "j-acc"], apply=False)
    assert res == {"requeue": ["j-429"], "skip": ["j-bad"], "ignored": ["j-acc"], "ids_missing": []}
    assert {p.name: p.read_bytes() for p in d.iterdir()} == before


def test_maintain_apply_requeues_429_and_skips(tmp_path: Path):
    d = _maint_dir(tmp_path)
    acc_before = (d / "accepted.jsonl").read_bytes()
    maintain(d, skip=["j-bad"], apply=True)
    raw = (d / "rejected.jsonl").read_bytes()
    assert b"\r\n" in raw  # line endings kept
    ids = [json.loads(l)["job_id"] for l in raw.decode().splitlines() if l.strip()]
    assert ids == ["j-quote", "j-bad"]
    rq = [json.loads(l)["job_id"] for l in (d / "requeued_from_rejected.jsonl").read_text().splitlines()]
    assert rq == ["j-429"]
    assert len(list(d.glob("rejected.jsonl.bak-*"))) == 1
    assert (d / "accepted.jsonl").read_bytes() == acc_before
    assert maintain(d, apply=False)["requeue"] == []


def test_maintain_ids_requeues_quality_reject(tmp_path: Path):
    d = _maint_dir(tmp_path)
    before = (d / "rejected.jsonl").read_bytes()
    res = maintain(d, ids=["j-quote", "nope"], apply=False)
    assert res["requeue"] == ["j-429", "j-quote"] and res["ids_missing"] == ["nope"]
    assert (d / "rejected.jsonl").read_bytes() == before
    maintain(d, ids=["j-quote"], apply=True)
    assert (d / "rejected.jsonl").read_text(encoding="utf-8").strip() == ""
    rq = [json.loads(l)["job_id"] for l in (d / "requeued_from_rejected.jsonl").read_text().splitlines()]
    assert rq == ["j-429", "j-quote"]


# --- plan --append N (grow the train queue) ---
from plan_open_theology_jobs import append_jobs, append_split  # noqa: E402


def test_append_split_scales_150_100_50():
    assert append_split(300) == {"puritan": 150, "spurgeon": 100, "confession": 50}
    assert append_split(30) == {"puritan": 15, "spurgeon": 10, "confession": 5}
    assert sum(append_split(7).values()) == 7


def _cand(bucket: str, i: int, path_i: int | None = None) -> dict:
    pi = i if path_i is None else path_i
    return {"work_id": f"{bucket}-w{i}", "bucket": bucket, "heading": f"[A \u2014 W{pi}]",
            "source_path": f"data/{bucket}/f{pi}.txt", "passage": f"{bucket} passage {i} " * 30,
            "title": f"W{pi}"}


def _append_dir(tmp_path: Path) -> tuple[Path, dict]:
    d = tmp_path / "q"
    d.mkdir()
    pools = {b: [_cand(b, i) for i in range(40)] for b in ("puritan", "spurgeon", "confession")}
    used = [pools["puritan"][0], pools["spurgeon"][0], pools["confession"][0]]
    jobs = [dict(build_job_like(c, f"train-{c['bucket']}-{k:03d}")) for k, c in
            zip((149, 99, 49), used)]
    ev = dict(build_job_like(pools["puritan"][1], "eval-puritan-000"), role="eval")
    (d / "jobs.jsonl").write_bytes("".join(json.dumps(j) + "\r\n" for j in jobs).encode())
    (d / "eval_jobs.jsonl").write_text(json.dumps(ev) + "\n", encoding="utf-8")
    cat = {"created_at": "x", "entries": [{"work_id": j["work_id"], "source_path": j["source_path"],
                                           "job_id": j["job_id"]} for j in jobs + [ev]]}
    (d / "catalog.json").write_text(json.dumps(cat, indent=2), encoding="utf-8")
    return d, pools


def build_job_like(c: dict, job_id: str) -> dict:
    return {"job_id": job_id, "role": "train", **{k: c[k] for k in
            ("work_id", "bucket", "heading", "source_path", "passage", "title")}}


def test_append_dry_writes_nothing_and_is_deterministic(tmp_path: Path):
    d, pools = _append_dir(tmp_path)
    before = {p.name: p.read_bytes() for p in d.iterdir()}
    a = append_jobs(out_dir=d, holdout_dir=d, n=12, pools=pools)
    b = append_jobs(out_dir=d, holdout_dir=d, n=12, pools=pools)
    assert a == b and a["apply"] is False and a["batch"] == 1
    assert a["by_bucket"] == {"puritan": 6, "spurgeon": 4, "confession": 2}
    assert a["id_ranges"]["puritan"] == ["train-puritan-150", "train-puritan-155"]
    assert {p.name: p.read_bytes() for p in d.iterdir()} == before


def test_append_apply_appends_excludes_used_and_backs_up(tmp_path: Path):
    d, pools = _append_dir(tmp_path)
    old = (d / "jobs.jsonl").read_bytes()
    res = append_jobs(out_dir=d, holdout_dir=d, n=12, pools=pools, apply=True)
    raw = (d / "jobs.jsonl").read_bytes()
    assert raw.startswith(old)  # existing rows untouched
    assert raw.count(b"\r\n") == 15  # CRLF kept, 3 old + 12 new
    rows = [json.loads(l) for l in raw.decode().splitlines()]
    new = rows[3:]
    assert len(new) == 12 and len({r["job_id"] for r in rows}) == 15
    used = {"puritan-w0", "spurgeon-w0", "confession-w0", "puritan-w1"}  # train + eval
    assert not ({r["work_id"] for r in new} & used)
    assert len(list(d.glob("jobs.jsonl.bak-*"))) == 1 and len(list(d.glob("catalog.json.bak-*"))) == 1
    cat = json.loads((d / "catalog.json").read_text(encoding="utf-8"))
    assert len(cat["entries"]) == 16 and cat["appends"][0]["batch"] == 1
    assert res["new_source_files"] == 12
    # Second append: new batch/seed, continues ids, no reuse of batch-1 passages.
    res2 = append_jobs(out_dir=d, holdout_dir=d, n=6, pools=pools, apply=True)
    assert res2["batch"] == 2 and res2["id_ranges"]["puritan"] == ["train-puritan-156", "train-puritan-158"]
    rows2 = [json.loads(l) for l in (d / "jobs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len({r["work_id"] for r in rows2}) == len(rows2) == 21


def test_append_raises_when_pool_exhausted(tmp_path: Path):
    d, pools = _append_dir(tmp_path)
    with pytest.raises(RuntimeError):
        append_jobs(out_dir=d, holdout_dir=d, n=300, pools=pools)


# --- Rule 6a: no "the passage" wording (warning only) ---
from open_theology_qa_checks import meta_wording_warnings  # noqa: E402


def test_teacher_prompt_forbids_passage_wording():
    rule = next(l for l in OPEN_THEOLOGY_TEACHER_SYSTEM.splitlines() if l.startswith("6a."))
    for w in ('"the passage"', '"the text"', '"the excerpt"', '"this quote"'):
        assert w in rule
    assert "Attribute to the author or work" in rule and "Boston teaches" in rule


@pytest.mark.parametrize(
    "user, assistant, n",
    [
        ("According to the passage, what is grace?", "The passage states that grace is free.", 2),
        ("What does Boston teach about grace?", 'Boston teaches that "grace is free." [Boston \u2014 Fourfold State]', 0),
        ("Why?", "As this quote shows, it is free.", 1),
        ("Why?", "In the Text he cites, it is free.", 1),
        ("What is the context of Romans 8?", "Paul's textual argument and contextual point.", 0),
    ],
)
def test_meta_wording_warnings(user, assistant, n):
    assert len(meta_wording_warnings(user, assistant)) == n


def test_meta_wording_is_warning_not_reject(tmp_path: Path, monkeypatch):
    out = _gen_dir(tmp_path, 1)
    raw = json.dumps({
        "question": "What does the passage say about Christ?",
        "answer": f'Spurgeon teaches that Christ is "the Beloved of the Father." {_GOOD_HEADING}',
    })
    monkeypatch.setattr(_gen, "call_teacher", _fake_teacher([raw]))
    rep = run_batch(out_dir=out, limit=1, apply=True, provider="groq", model="m", sleep_s=0)
    assert rep["accepted_new"] == 1 and rep["rejected_new"] == 0 and rep["meta_wording_warnings"] == 1
    row = json.loads((out / "accepted.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["meta"]["warnings"] == ["meta wording in question: 'the passage'"]
    st = json.loads((out / "status.json").read_text(encoding="utf-8"))
    assert st["counts"]["meta_wording_warnings"] == 1
