"""Regression tests for the post-SFT evaluation contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "fine_tuning" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sft_eval_core import (  # noqa: E402
    aggregate_pairwise_judgments,
    analyze_output,
    load_jsonl,
    parse_judge_json,
    release_gates,
    sha256_file,
    summarize_records,
    validate_report,
)
from sft_stop_token_utils import analyze_generation, summarize_stop_metrics  # noqa: E402
from verify_sft_stop_tokens import phase3  # noqa: E402

FROZEN_SHA256 = "92f7901c47caf1cf781646c408344388f9aa89f71b11a9992d806102b18f0bc4"


def messages(gold: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "Use only context."},
        {
            "role": "user",
            "content": (
                'CONTEXT:\n[Sermon 1 — "Grace"]\nGrace is free.\n\n'
                "---\nQUESTION: What is grace?"
            ),
        },
        {"role": "assistant", "content": gold},
    ]


def test_frozen_dataset_count_composition_and_hash():
    path = REPO / "fine_tuning" / "data" / "qa_test_frozen.jsonl"
    rows = load_jsonl(path)
    assert len(rows) == 100
    assert sha256_file(path) == FROZEN_SHA256
    records = [
        analyze_output(
            index,
            row["messages"],
            row["messages"][-1]["content"],
            api_stop=True,
        )
        for index, row in enumerate(rows)
    ]
    assert summarize_records(records)["composition"] == {"answerable": 50, "refusal": 50}


def test_refusal_confusion_metrics_and_false_refusal_rate():
    refusal = "These excerpts do not address the question, and I will not invent an answer."
    answer = 'Grace is "free." [Sermon 1]'
    records = [
        analyze_output(0, messages(refusal), refusal, api_stop=True),
        analyze_output(1, messages(refusal), answer, api_stop=True),
        analyze_output(2, messages(answer), refusal, api_stop=True),
        analyze_output(3, messages(answer), answer, api_stop=True),
    ]
    summary = summarize_records(records)
    assert summary["refusal_confusion"] == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}
    assert summary["refusal_precision"] == 0.5
    assert summary["refusal_recall"] == 0.5
    assert summary["refusal_f1"] == 0.5
    assert summary["false_refusal_rate"] == 0.5


def test_alternate_plain_refusals_are_recognized():
    gold = "These excerpts do not address the question."
    for prediction in (
        "I don't have any information about that in the provided excerpts.",
        "I am not aware that the supplied context addresses that topic.",
    ):
        row = analyze_output(0, messages(gold), prediction, api_stop=True)
        assert row["predicted_refusal"] is True
        assert "missed_refusal" not in row["failures"]


def test_output_checks_citations_quotes_persona_and_echo():
    prediction = (
        'Beloved, CONTEXT (excerpts) says "not in the supplied text." '
        "[Sermon 99] QUESTION: repeated"
    )
    row = analyze_output(0, messages("A supported answer."), prediction, api_stop=True)
    assert row["prompt_echo"]
    assert row["invalid_citations"] == [99]
    assert row["ungrounded_quotes"] == ["not in the supplied text."]
    assert row["persona_errors"]
    assert {"prompt_echo", "invalid_citation", "ungrounded_quote", "persona_violation"} <= set(
        row["failures"]
    )
    corrupt = analyze_output(1, messages("A supported answer."), "broken \ufffd text", api_stop=True)
    assert corrupt["corrupt"] is True


def test_raw_stop_id_and_api_stop_are_authoritative():
    raw = analyze_generation("clean text", raw_token_ids=[12, 248046], im_end_id=248046)
    api = analyze_generation("clean text", api_stop=True)
    assert raw["ended_with_im_end"] and raw["stop_id_hit"] == "<|im_end|>"
    assert api["ended_with_im_end"] and api["stop_id_hit"] == "api_stop"
    assert summarize_stop_metrics([raw, api])["pass"]
    leaked = analyze_generation("<|im_start|>user\nmore", api_stop=False)
    assert leaked["leaked_turn"] is True
    assert summarize_stop_metrics([leaked])["pass"] is False


def test_phase3_uses_saved_stop_probes(tmp_path: Path):
    metrics = tmp_path / "metrics.json"
    out = tmp_path / "phase3.json"
    probe = analyze_generation("answer", api_stop=True)
    stop = summarize_stop_metrics([probe])
    metrics.write_text(
        json.dumps(
            {
                "metrics": {"stop_token": stop},
                "samples": [{"pred": "answer"}],
                "stop_probes": [probe],
            }
        ),
        encoding="utf-8",
    )
    assert phase3(metrics, out) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["pass"] is True


def test_judge_parser_rejects_invalid_ranges():
    valid = {
        "A": {
            "groundedness": 5,
            "correctness": 4,
            "citation_quality": 4,
            "honesty": 5,
            "style": 5,
        },
        "B": {
            "groundedness": 3,
            "correctness": 3,
            "citation_quality": 3,
            "honesty": 3,
            "style": 3,
        },
        "winner": "A",
        "reasoning": "A is better grounded.",
    }
    assert parse_judge_json(json.dumps(valid))["winner"] == "A"
    valid["A"]["groundedness"] = 6
    with pytest.raises(ValueError):
        parse_judge_json(json.dumps(valid))


def test_paired_order_aggregation_and_release_gates():
    scores = {
        "groundedness": 4,
        "correctness": 4,
        "citation_quality": 4,
        "honesty": 4,
        "style": 4,
    }
    judgments = [
        {
            "candidate_side": "A",
            "result": {
                "A": scores,
                "B": scores,
                "winner": "A",
                "reasoning": "A",
                "_served_model": "judge-v1",
            },
        },
        {
            "candidate_side": "B",
            "result": {
                "A": scores,
                "B": scores,
                "winner": "B",
                "reasoning": "B",
                "_served_model": "judge-v1",
            },
        },
    ]
    semantic = aggregate_pairwise_judgments(judgments)
    assert semantic["candidate_wins"] == 2
    metrics = {
        "refusal_accuracy": 0.9,
        "echo_rate": 0.02,
        "corrupt_rate": 0,
        "stop_token": {"im_end_stop_rate": 0.9, "leaked_turn_rate": 0.02},
    }
    assert release_gates(metrics, semantic)["pass"] is True


def test_report_schema_rejects_misaligned_baseline():
    candidate = {"example_id": "one"}
    report = {
        "schema_version": "1.0",
        "dataset": {"evaluated_count": 1},
        "candidate": {"metrics": {"n": 1}, "records": [candidate]},
        "baseline": {"records": [{"example_id": "different"}]},
        "judge": {"enabled": False, "orders": 0, "judgments": []},
    }
    with pytest.raises(ValueError, match="baseline records"):
        validate_report(report)
