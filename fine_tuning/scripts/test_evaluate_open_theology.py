#!/usr/bin/env python3
"""Unit tests for open-theology chat eval (mechanical + join; no GPU/judge)."""

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

from config import THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from evaluate_open_theology import (  # noqa: E402
    OT_CONTRACT,
    OT_REPORT_SCHEMA,
    absolute_ot_judge_prompt,
    build_records,
    informational_verdict,
    load_accepted_by_id,
    load_eval_set,
    match_predictions,
    merge_inline_ooc_meta,
    ot_predicted_refusal,
    parse_absolute_ot_judge,
    row_id,
    score_mechanical,
    summarize_mechanical,
)


PASSAGE = (
    "Christ is the Beloved of the Father. What a remarkable instance you have "
    "of immutable love in the covenant of grace."
)
HEADING = '[Sermon 1 — "The Immutability of God"]'


def _good_pred() -> str:
    return (
        f'Spurgeon teaches that Christ is "the Beloved of the Father." {HEADING} '
        "The sermon argues from the text, not from costume."
    )


def test_score_mechanical_good():
    m = score_mechanical(prediction=_good_pred(), passage=PASSAGE, heading=HEADING)
    assert m["quote_in_passage"] is True
    assert m["heading_cited"] is True
    assert m["persona_errors"] == []
    assert m["predicted_refusal"] is False
    assert m["failures"] == []
    assert m["diagnostics"] == []


def test_score_mechanical_cite_miss_is_diagnostic_not_failure():
    pred = (
        "Spurgeon teaches that Christ is the Beloved of the Father, "
        "an instance of immutable love in the covenant of grace."
    )
    m = score_mechanical(prediction=pred, passage=PASSAGE, heading=HEADING)
    assert m["quote_in_passage"] is False
    assert m["heading_cited"] is False
    assert "quote_not_in_passage" in m["diagnostics"]
    assert "missing_or_wrong_heading" in m["diagnostics"]
    assert m["failures"] == []


def test_score_mechanical_persona_still_fails():
    pred = f'Beloved, hear this: "totally invented phrase here." [Sermon 999]'
    m = score_mechanical(prediction=pred, passage=PASSAGE, heading=HEADING)
    assert m["persona_errors"]
    assert m["quote_in_passage"] is False
    assert m["heading_cited"] is False
    assert "persona_violation" in m["failures"]
    assert "quote_not_in_passage" in m["diagnostics"]
    assert "missing_or_wrong_heading" in m["diagnostics"]


def test_ot_refusal_predicate_skips_doctrinal_insufficient():
    # Dabney-style FP under the old RAG patterns.
    doctrinal = (
        "Dabney rejects utility as the sole basis of moral obligation because it "
        "fails to account for the intrinsic nature of moral duties."
    )
    assert ot_predicted_refusal(doctrinal) is False
    assert ot_predicted_refusal(
        "I cannot answer this question from the corpus of Spurgeon and the Puritans."
    )
    assert ot_predicted_refusal(
        "The writings do not contain any reference to Greenham."
    )


def test_join_accepted_by_job_id(tmp_path: Path):
    accepted = tmp_path / "accepted.jsonl"
    accepted.write_text(
        json.dumps(
            {
                "job_id": "eval-puritan-000",
                "messages": [],
                "meta": {"passage": PASSAGE, "heading": HEADING, "bucket": "puritan"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    by_id = load_accepted_by_id(accepted)
    assert "eval-puritan-000" in by_id
    assert by_id["eval-puritan-000"]["meta"]["heading"] == HEADING


def test_match_predictions_from_report_by_index():
    eval_rows = [
        {
            "id": "eval-a",
            "messages": [
                {"role": "system", "content": THEOLOGY_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": "What does Spurgeon teach?"},
                {"role": "assistant", "content": "gold"},
            ],
        }
    ]
    report = {
        "candidate": {
            "records": [
                {
                    "index": 0,
                    "question": "What does Spurgeon teach?",
                    "prediction": _good_pred(),
                }
            ]
        }
    }
    preds = match_predictions(eval_rows, from_report=report)
    assert preds == [_good_pred()]


def test_build_records_and_summarize():
    eval_rows = [
        {
            "id": "eval-a",
            "messages": [
                {"role": "system", "content": THEOLOGY_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": "Q?"},
                {"role": "assistant", "content": "gold"},
            ],
        }
    ]
    accepted = {
        "eval-a": {
            "job_id": "eval-a",
            "meta": {"passage": PASSAGE, "heading": HEADING, "bucket": "spurgeon"},
        }
    }
    records = build_records(eval_rows, accepted, [_good_pred()])
    assert records[0]["id"] == "eval-a"
    assert records[0]["mechanical"]["failures"] == []
    summary = summarize_mechanical(records)
    assert summary["n"] == 1
    assert summary["quote_in_passage_rate"] == 1.0
    assert summary["heading_cited_rate"] == 1.0
    assert summary["persona_violation_rate"] == 0.0


def test_parse_absolute_ot_judge():
    payload = parse_absolute_ot_judge(
        json.dumps(
            {
                "correctness": 4,
                "citation_fidelity": 5,
                "persona_leakage": 5,
                "honesty": 4,
                "reasoning": "Faithful cite and quote.",
            }
        )
    )
    assert payload["correctness"] == 4
    with pytest.raises(ValueError):
        parse_absolute_ot_judge(
            '{"correctness": 9, "citation_fidelity": 1, '
            '"persona_leakage": 1, "honesty": 1, "reasoning": "x"}'
        )


def test_absolute_prompt_optional_cite_contract():
    prompt = absolute_ot_judge_prompt(
        question="Q",
        gold="G",
        prediction="P",
        heading=HEADING,
        passage_excerpt=PASSAGE[:40],
    )
    assert "NO retrieval CONTEXT" in prompt
    assert "OPTIONAL" in prompt
    assert "do not require a cite" in prompt.lower() or "Do not penalize" in prompt
    assert "persona_leakage" in prompt
    assert "citation_fidelity" in prompt


def test_informational_verdict_useful_without_cite_gates():
    mech = {
        "persona_violation_rate": 0.0,
        "quote_in_passage_rate": 0.1,
        "heading_cited_rate": 0.0,
        "false_refusal_rate": 0.0,
    }
    judge = {
        "means": {
            "correctness": 4.0,
            "honesty": 4.2,
            "persona_leakage": 4.8,
            "citation_fidelity": 2.0,
        }
    }
    v = informational_verdict(mech, judge)
    assert v["release_gate"] is False
    assert v["next_ft_knob"] == "rag_refusal_slice"
    assert v["useful_theology_chat"] is True
    assert v["label"] == "useful_theology_chat"
    assert "quote_ok" not in v["checks"]
    assert "heading_ok" not in v["checks"]
    assert v["contract"] == OT_CONTRACT


def test_informational_verdict_weak():
    mech = {
        "persona_violation_rate": 0.3,
        "quote_in_passage_rate": 0.2,
        "heading_cited_rate": 0.2,
        "false_refusal_rate": 0.2,
    }
    judge = {
        "means": {
            "correctness": 2.5,
            "honesty": 2.0,
            "persona_leakage": 2.0,
            "citation_fidelity": 2.0,
        }
    }
    v = informational_verdict(mech, judge)
    assert v["useful_theology_chat"] is False
    assert v["label"] == "weak_not_useful_yet"
    assert v["release_gate"] is False


def test_real_eval_set_joins_accepted():
    eval_path = _REPO / "fine_tuning" / "data" / "qa_open_theology" / "sft" / "open_theology_eval.jsonl"
    accepted_path = _REPO / "fine_tuning" / "data" / "qa_open_theology" / "eval_accepted.jsonl"
    if not eval_path.is_file() or not accepted_path.is_file():
        pytest.skip("OT eval fixtures missing")
    rows = load_eval_set(eval_path)
    accepted = load_accepted_by_id(accepted_path)
    assert len(rows) == 40
    for row in rows:
        rid = row_id(row)
        assert rid in accepted
        meta = accepted[rid]["meta"]
        assert meta.get("passage")
        assert meta.get("heading")
        assert row["messages"][0]["content"] == THEOLOGY_CHAT_SYSTEM_PROMPT


def test_schema_constant():
    assert OT_REPORT_SCHEMA == "open_theology_eval_1.1"
    assert OT_CONTRACT == "open_theology_chat_corpus_v1"


def test_ooc_eval_set_inline_meta():
    ooc_path = (
        _REPO / "fine_tuning" / "data" / "qa_open_theology" / "sft" / "open_theology_eval_ooc.jsonl"
    )
    if not ooc_path.is_file():
        pytest.skip("OOC eval fixture missing")
    rows = load_eval_set(ooc_path)
    assert len(rows) == 8
    accepted = merge_inline_ooc_meta(rows, {})
    assert set(accepted) == {row_id(r) for r in rows}
    preds = ["I cannot answer; that question is outside the Spurgeon/Puritan corpus."] * len(rows)
    records = build_records(rows, accepted, preds)
    assert all(r["mechanical"]["expect_refusal"] for r in records)
    assert all(r["mechanical"]["predicted_refusal"] for r in records)
    assert all(r["mechanical"]["failures"] == [] for r in records)
    bad = build_records(rows[:1], accepted, ["Barth taught the analogia entis as follows…"])
    assert "missed_ooc_refusal" in bad[0]["mechanical"]["failures"]
