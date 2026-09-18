"""Reusable deterministic and semantic helpers for post-SFT evaluation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from build_qa_mix import REFUSAL_PATTERNS
from qa_rewrite_checks import (
    HEADER_RE,
    QUOTE_RE,
    SERMON_CITE_RE,
    caricature_errors,
    context_of,
    norm_ws,
)
from sft_stop_token_utils import CORRUPT_RE, analyze_generation, summarize_stop_metrics

REPORT_SCHEMA_VERSION = "1.0"
QUESTION_RE = re.compile(r"(?:^|\n)(?:---\s*\n)?QUESTION:\s*(.*)", re.I | re.S)
PREDICTED_REFUSAL_PATTERNS = REFUSAL_PATTERNS + (
    re.compile(r"does not mention", re.I),
    re.compile(r"do not mention", re.I),
    re.compile(r"(?:context|excerpts?) (?:does|do) not (?:provide|include|say)", re.I),
    re.compile(r"no (?:specific|relevant|such) (?:information|answer|reference|detail)", re.I),
    re.compile(r"not (?:stated|provided|addressed) in (?:the|these) (?:context|excerpts?)", re.I),
    re.compile(r"(?:do not|don't) have any information", re.I),
    re.compile(r"(?:I am|I'm) not aware (?:that|of)", re.I),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            messages = row.get("messages")
            if not isinstance(messages, list) or len(messages) < 3:
                raise ValueError(f"{path}:{line_no}: expected system, user, and assistant messages")
            rows.append(row)
    return rows


def refusal_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in PREDICTED_REFUSAL_PATTERNS)


def question_of(user: str) -> str:
    match = QUESTION_RE.search(user)
    if not match:
        return user.strip()
    question = match.group(1).strip()
    return re.split(r"\n\s*Answer based ONLY on", question, maxsplit=1, flags=re.I)[0].strip()


def example_id(messages: list[dict[str, str]]) -> str:
    canonical = json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 4) if denominator else 0.0


def analyze_output(
    index: int,
    messages: list[dict[str, str]],
    prediction: str,
    *,
    raw_text: str | None = None,
    raw_token_ids: list[int] | None = None,
    im_end_id: int | None = None,
    eot_id: int | None = None,
    api_stop: bool = False,
    latency_seconds: float | None = None,
    backend_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one complete, auditable deterministic evaluation record."""
    user = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
    gold = next((m.get("content", "") for m in messages if m.get("role") == "assistant"), "")
    gold_refusal = refusal_text(gold)
    predicted_refusal = refusal_text(prediction)

    headers = {int(n) for n in HEADER_RE.findall(user)}
    citations = [int(n) for n in SERMON_CITE_RE.findall(prediction)]
    invalid_citations = [number for number in citations if number not in headers]
    normalized_context = norm_ws(context_of(user))
    quotes = QUOTE_RE.findall(prediction)
    grounded_quotes = [quote for quote in quotes if norm_ws(quote) in normalized_context]
    ungrounded_quotes = [quote for quote in quotes if norm_ws(quote) not in normalized_context]
    persona_errors = caricature_errors(prediction)
    prompt_echo = (
        prediction.count("CONTEXT:") > 1
        or "CONTEXT (excerpts" in prediction
        or ("QUESTION:" in prediction and "CONTEXT" in prediction)
    )
    corrupt = bool(CORRUPT_RE.search(prediction))
    stop = analyze_generation(
        raw_text if raw_text is not None else prediction,
        raw_token_ids=raw_token_ids,
        im_end_id=im_end_id,
        eot_id=eot_id,
        api_stop=api_stop,
    )
    format_ok = len(prediction.strip()) > 20 and not corrupt and not stop["leaked_turn"]

    failures: list[str] = []
    if corrupt:
        failures.append("corrupt_output")
    if stop["leaked_turn"]:
        failures.append("leaked_turn")
    if prompt_echo:
        failures.append("prompt_echo")
    if invalid_citations:
        failures.append("invalid_citation")
    if ungrounded_quotes:
        failures.append("ungrounded_quote")
    if persona_errors:
        failures.append("persona_violation")
    if gold_refusal and not predicted_refusal:
        failures.append("missed_refusal")
    if not gold_refusal and predicted_refusal:
        failures.append("false_refusal")

    return {
        "index": index,
        "example_id": example_id(messages),
        "slice": "refusal" if gold_refusal else "answerable",
        "question": question_of(user),
        "user": user,
        "gold": gold,
        "prediction": prediction,
        "raw_generation": raw_text if raw_text is not None else prediction,
        "gold_refusal": gold_refusal,
        "predicted_refusal": predicted_refusal,
        "format_ok": format_ok,
        "prompt_echo": prompt_echo,
        "corrupt": corrupt,
        "citations": citations,
        "invalid_citations": invalid_citations,
        "quotes": quotes,
        "grounded_quotes": grounded_quotes,
        "ungrounded_quotes": ungrounded_quotes,
        "persona_errors": persona_errors,
        "stop": stop,
        "latency_seconds": latency_seconds,
        "backend_metadata": backend_metadata or {},
        "failures": failures,
    }


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    refusal_total = sum(bool(row["gold_refusal"]) for row in records)
    answerable_total = n - refusal_total
    tp = sum(bool(row["gold_refusal"] and row["predicted_refusal"]) for row in records)
    fn = sum(bool(row["gold_refusal"] and not row["predicted_refusal"]) for row in records)
    fp = sum(bool(not row["gold_refusal"] and row["predicted_refusal"]) for row in records)
    tn = sum(bool(not row["gold_refusal"] and not row["predicted_refusal"]) for row in records)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0
    latencies = [
        float(row["latency_seconds"])
        for row in records
        if row.get("latency_seconds") is not None
    ]
    stop_metrics = summarize_stop_metrics([row["stop"] for row in records])
    citation_rows = [row for row in records if row["citations"]]
    quote_rows = [row for row in records if row["quotes"]]

    return {
        "n": n,
        "evaluated_count": n,
        "composition": {"answerable": answerable_total, "refusal": refusal_total},
        "format_ok": sum(bool(row["format_ok"]) for row in records),
        "format_ok_rate": _safe_div(sum(bool(row["format_ok"]) for row in records), n),
        "echo": sum(bool(row["prompt_echo"]) for row in records),
        "echo_rate": _safe_div(sum(bool(row["prompt_echo"]) for row in records), n),
        "corrupt": sum(bool(row["corrupt"]) for row in records),
        "corrupt_rate": _safe_div(sum(bool(row["corrupt"]) for row in records), n),
        "persona_violations": sum(bool(row["persona_errors"]) for row in records),
        "persona_violation_rate": _safe_div(sum(bool(row["persona_errors"]) for row in records), n),
        "invalid_citation_rows": sum(bool(row["invalid_citations"]) for row in records),
        "citation_validity_rate": _safe_div(
            sum(not row["invalid_citations"] for row in citation_rows), len(citation_rows)
        ),
        "ungrounded_quote_rows": sum(bool(row["ungrounded_quotes"]) for row in records),
        "quote_grounding_rate": _safe_div(
            sum(not row["ungrounded_quotes"] for row in quote_rows), len(quote_rows)
        ),
        "refusal_confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "refusal_hits": tp,
        "refusal_total": refusal_total,
        "refusal_accuracy": recall,
        "refusal_precision": precision,
        "refusal_recall": recall,
        "refusal_f1": f1,
        "false_refusal_rate": _safe_div(fp, answerable_total),
        "latency_seconds": {
            "count": len(latencies),
            "mean": round(sum(latencies) / len(latencies), 4) if latencies else None,
            "max": round(max(latencies), 4) if latencies else None,
        },
        "stop_token": stop_metrics,
    }


def parse_judge_json(text: str) -> dict[str, Any]:
    """Parse and strictly validate a paired-judge response."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.I)
    start, finish = stripped.find("{"), stripped.rfind("}")
    if start < 0 or finish < start:
        raise ValueError("judge response does not contain a JSON object")
    payload = json.loads(stripped[start : finish + 1])
    winner = payload.get("winner")
    if isinstance(winner, str):
        normalized_winner = winner.strip().lower()
        winner = {"a": "A", "b": "B", "tie": "tie"}.get(normalized_winner, winner)
        payload["winner"] = winner
    if winner not in {"A", "B", "tie"}:
        raise ValueError("judge winner must be A, B, or tie")
    dimensions = ("groundedness", "correctness", "citation_quality", "honesty", "style")
    for side in ("A", "B"):
        scores = payload.get(side)
        if not isinstance(scores, dict):
            raise ValueError(f"judge response missing {side} scores")
        for dimension in dimensions:
            value = scores.get(dimension)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 1 <= value <= 5:
                raise ValueError(f"{side}.{dimension} must be numeric in [1, 5]")
    if not isinstance(payload.get("reasoning"), str) or not payload["reasoning"].strip():
        raise ValueError("judge reasoning must be a non-empty string")
    return payload


def pairwise_judge_prompt(
    *,
    question: str,
    context: str,
    answer_a: str,
    answer_b: str,
) -> str:
    return f"""You are an independent evaluator of grounded theological question answering.

Score Answer A and Answer B from 1 to 5 on:
- groundedness: every claim follows from CONTEXT
- correctness: directly and completely answers the QUESTION
- citation_quality: citations are present when useful and name only headings in CONTEXT
- honesty: refuses when CONTEXT is insufficient and does not falsely refuse when it is sufficient
- style: clear knowledge-assistant prose, no preacher roleplay or reader vocatives

Choose winner A, B, or tie. Ignore answer order and verbosity. A polished unsupported claim must score poorly.
Output only JSON:
{{
  "A": {{"groundedness": 1, "correctness": 1, "citation_quality": 1, "honesty": 1, "style": 1}},
  "B": {{"groundedness": 1, "correctness": 1, "citation_quality": 1, "honesty": 1, "style": 1}},
  "winner": "A",
  "reasoning": "brief evidence-based reason"
}}

QUESTION:
{question}

CONTEXT:
{context}

ANSWER A:
{answer_a}

ANSWER B:
{answer_b}
"""


def aggregate_pairwise_judgments(judgments: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize A/B order and aggregate candidate/baseline judge outcomes."""
    dimensions = ("groundedness", "correctness", "citation_quality", "honesty", "style")
    wins = losses = ties = 0
    served_models: set[str] = set()
    candidate_scores = {dimension: [] for dimension in dimensions}
    baseline_scores = {dimension: [] for dimension in dimensions}
    for judgment in judgments:
        served_model = judgment["result"].get("_served_model")
        if served_model:
            served_models.add(str(served_model))
        candidate_side = judgment["candidate_side"]
        baseline_side = "B" if candidate_side == "A" else "A"
        winner = judgment["result"]["winner"]
        if winner == "tie":
            ties += 1
        elif winner == candidate_side:
            wins += 1
        else:
            losses += 1
        for dimension in dimensions:
            candidate_scores[dimension].append(float(judgment["result"][candidate_side][dimension]))
            baseline_scores[dimension].append(float(judgment["result"][baseline_side][dimension]))
    n = len(judgments)
    return {
        "n_judgments": n,
        "candidate": {
            dimension: round(sum(values) / len(values), 4) if values else None
            for dimension, values in candidate_scores.items()
        },
        "baseline": {
            dimension: round(sum(values) / len(values), 4) if values else None
            for dimension, values in baseline_scores.items()
        },
        "candidate_wins": wins,
        "baseline_wins": losses,
        "ties": ties,
        "candidate_win_rate": _safe_div(wins, n),
        "served_models": sorted(served_models),
        "judge_model_consistent": len(served_models) == 1,
    }


def release_gates(
    metrics: dict[str, Any],
    semantic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    groundedness = (semantic or {}).get("candidate", {}).get("groundedness")
    checks = {
        "refusal_accuracy_gte_0_85": metrics.get("refusal_accuracy", 0) >= 0.85,
        "echo_rate_lte_0_02": metrics.get("echo_rate", 1) <= 0.02,
        "corrupt_rate_eq_0": metrics.get("corrupt_rate", 1) == 0,
        "im_end_stop_rate_gte_0_85": metrics.get("stop_token", {}).get(
            "im_end_stop_rate", 0
        )
        >= 0.85,
        "leaked_turn_rate_lte_0_02": metrics.get("stop_token", {}).get(
            "leaked_turn_rate", 1
        )
        <= 0.02,
        "groundedness_gte_4": groundedness is not None and groundedness >= 4.0,
        "judge_model_consistent": bool(
            semantic and semantic.get("judge_model_consistent")
        ),
    }
    return {"checks": checks, "pass": all(checks.values())}


def validate_report(report: dict[str, Any]) -> None:
    """Fail closed when a persisted report is internally inconsistent."""
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ValueError("unsupported or missing report schema_version")
    dataset = report.get("dataset") or {}
    candidate = report.get("candidate") or {}
    records = candidate.get("records") or []
    evaluated = dataset.get("evaluated_count")
    if evaluated != len(records) or (candidate.get("metrics") or {}).get("n") != len(records):
        raise ValueError("candidate evaluated counts do not match records")
    ids = [record.get("example_id") for record in records]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("candidate example IDs must be present and unique")
    baseline = report.get("baseline")
    if baseline:
        baseline_records = baseline.get("records") or []
        if [record.get("example_id") for record in baseline_records] != ids:
            raise ValueError("baseline records must align with candidate example IDs")
    judge = report.get("judge") or {}
    if judge.get("enabled"):
        expected = len(records) * int(judge.get("orders") or 0)
        if len(judge.get("judgments") or []) != expected:
            raise ValueError("judge count does not match records x orders")


def refresh_report_metrics(report: dict[str, Any]) -> dict[str, Any]:
    """Recompute deterministic checks from persisted full generations."""
    for section_name in ("candidate", "baseline"):
        section = report.get(section_name)
        if not section:
            continue
        refreshed = []
        for old in section.get("records") or []:
            messages = [
                {"role": "system", "content": ""},
                {"role": "user", "content": old["user"]},
                {"role": "assistant", "content": old["gold"]},
            ]
            stop = old.get("stop") or {}
            row = analyze_output(
                old["index"],
                messages,
                old["prediction"],
                raw_text=old.get("raw_generation"),
                api_stop=bool(stop.get("api_stop")),
                latency_seconds=old.get("latency_seconds"),
                backend_metadata=old.get("backend_metadata"),
            )
            row["example_id"] = old["example_id"]
            refreshed.append(row)
        section["records"] = refreshed
        section["metrics"] = summarize_records(refreshed)
    semantic = ((report.get("judge") or {}).get("summary"))
    report["gates"] = release_gates(report["candidate"]["metrics"], semantic)
    validate_report(report)
    return report
