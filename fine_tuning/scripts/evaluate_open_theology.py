#!/usr/bin/env python3
"""Score open-theology (no-CONTEXT) held-out chat — not RAG F §5.

Mechanical metrics use open_theology_qa_checks against eval_accepted meta
(passage/heading). Optional Gemini absolute judge (not pairwise, not
CONTEXT-groundedness). release_gate is always false; does not unlock export.

Examples:
  python fine_tuning/scripts/evaluate_open_theology.py \\
    --from-report fine_tuning/eval_results/open_theology_eval_s8_weighted.gen.json \\
    --accepted fine_tuning/data/qa_open_theology/eval_accepted.jsonl \\
    --eval-set fine_tuning/data/qa_open_theology/sft/open_theology_eval.jsonl \\
    --adapter-sha e891731c... --judge \\
    --output fine_tuning/eval_results/open_theology_eval_s8_weighted.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
for search_path in (REPO, SCRIPT_DIR):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))
load_dotenv(REPO / ".env")

from config import (  # noqa: E402
    SFT_EVAL_JUDGE_API_KEY,
    SFT_EVAL_JUDGE_BASE_URL,
    SFT_EVAL_JUDGE_MODEL,
    SFT_EVAL_JUDGE_PROVIDER,
    SFT_EVAL_JUDGE_TIMEOUT,
)
from open_theology_qa_checks import heading_cited, quote_in_passage  # noqa: E402
from qa_rewrite_checks import QUOTE_RE, caricature_errors, role  # noqa: E402
from sft_eval_core import sha256_file  # noqa: E402
from sft_stop_token_utils import CORRUPT_RE  # noqa: E402

OT_REPORT_SCHEMA = "open_theology_eval_1.1"
OT_CONTRACT = "open_theology_chat_corpus_v1"
OT_JUDGE_DIMS = ("correctness", "citation_fidelity", "persona_leakage", "honesty")

# Narrower than RAG refusal_text / is_refusal: do not treat doctrinal wording like
# "insufficient" / "fails to account" as a false refusal (Dabney FP on 2026-10-18).
OT_REFUSAL_PATTERNS = (
    re.compile(r"\bcannot answer\b", re.I),
    re.compile(r"\bcould not answer\b", re.I),
    re.compile(r"\bdo not contain\b", re.I),
    re.compile(r"\bdoes not contain\b", re.I),
    re.compile(r"\bnot (?:in|within) (?:that |the |this )?(?:corpus|writings)\b", re.I),
    re.compile(r"\boutside (?:that |the |this )?corpus\b", re.I),
    re.compile(r"\bwill not invent\b", re.I),
    re.compile(r"\bI will not speculate\b", re.I),
    re.compile(
        r"(?:please )?(?:provide|send) (?:me )?(?:the |specific )?(?:urls?|excerpts?|passage|text)\b",
        re.I,
    ),
    re.compile(r"\bif you (?:have|can provide) specific\b", re.I),
)


def ot_predicted_refusal(text: str) -> bool:
    return any(p.search(text or "") for p in OT_REFUSAL_PATTERNS)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 4) if denominator else 0.0


def load_accepted_by_id(path: Path) -> dict[str, dict[str, Any]]:
    """Index eval_accepted rows by job_id / id."""
    out: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            key = str(row.get("job_id") or row.get("id") or "").strip()
            if not key:
                raise ValueError(f"{path}:{line_no}: missing job_id/id")
            out[key] = row
    return out


def merge_inline_ooc_meta(
    eval_rows: list[dict[str, Any]], accepted: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Allow OOC held-out rows to carry meta on the eval line (no gold passage)."""
    out = dict(accepted)
    for row in eval_rows:
        rid = row_id(row)
        if rid in out:
            continue
        meta = row.get("meta") or {}
        slice_name = str(row.get("slice") or "")
        if slice_name == "open_theology_ooc" or str(meta.get("bucket") or "") == "ooc":
            out[rid] = {"job_id": rid, "meta": meta, "messages": row.get("messages")}
    return out


def load_eval_set(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            key = str(row.get("id") or row.get("job_id") or "").strip()
            if not key:
                raise ValueError(f"{path}:{line_no}: missing id")
            msgs = row.get("messages")
            if not isinstance(msgs, list) or len(msgs) < 3:
                raise ValueError(f"{path}:{line_no}: expected system/user/assistant")
            rows.append(row)
    return rows


def row_id(row: dict[str, Any]) -> str:
    return str(row.get("id") or row.get("job_id") or "").strip()


def prediction_from_gen_record(rec: dict[str, Any]) -> str:
    return str(rec.get("prediction") or rec.get("raw_generation") or "").strip()


def index_gen_records(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map eval id -> candidate record from an evaluate.py generate-only report.

    evaluate.py stores example_id as a hash of messages, not the JSONL id.
    Match by aligning record index to eval-set order, or by question text.
    """
    records = (report.get("candidate") or {}).get("records") or []
    by_index: dict[int, dict[str, Any]] = {}
    for rec in records:
        if isinstance(rec.get("index"), int):
            by_index[int(rec["index"])] = rec
    return {str(i): r for i, r in by_index.items()}


def match_predictions(
    eval_rows: list[dict[str, Any]],
    *,
    from_report: dict[str, Any] | None = None,
    predictions_jsonl: Path | None = None,
) -> list[str]:
    """Return prediction strings aligned to eval_rows order."""
    if from_report is not None:
        records = (from_report.get("candidate") or {}).get("records") or []
        if len(records) != len(eval_rows):
            raise ValueError(
                f"from-report has {len(records)} records; eval set has {len(eval_rows)}"
            )
        # Prefer index order
        ordered = sorted(records, key=lambda r: int(r.get("index", 0)))
        preds = [prediction_from_gen_record(r) for r in ordered]
        # Sanity: question text when present
        for i, (row, rec) in enumerate(zip(eval_rows, ordered)):
            gold_q = role(row["messages"], "user").strip()
            rec_q = str(rec.get("question") or rec.get("user") or "").strip()
            if rec_q and gold_q and rec_q != gold_q and gold_q not in rec_q and rec_q not in gold_q:
                raise ValueError(
                    f"question mismatch at index {i}: eval={gold_q[:80]!r} report={rec_q[:80]!r}"
                )
        return preds

    if predictions_jsonl is None:
        raise ValueError("Need --from-report or --predictions-jsonl")

    by_id: dict[str, str] = {}
    by_index: dict[int, str] = {}
    with predictions_jsonl.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            pred = prediction_from_gen_record(rec)
            rid = str(rec.get("id") or rec.get("example_id") or "").strip()
            if rid:
                by_id[rid] = pred
            if isinstance(rec.get("index"), int):
                by_index[int(rec["index"])] = pred

    preds: list[str] = []
    for i, row in enumerate(eval_rows):
        rid = row_id(row)
        if rid in by_id:
            preds.append(by_id[rid])
        elif i in by_index:
            preds.append(by_index[i])
        else:
            raise ValueError(f"No prediction for eval row {rid} (index {i})")
    return preds


def score_mechanical(
    *,
    prediction: str,
    passage: str,
    heading: str,
    expect_refusal: bool = False,
) -> dict[str, Any]:
    persona = caricature_errors(prediction)
    quote_hits = quote_in_passage(prediction, passage) if passage else 0
    cites_heading = bool(heading and heading_cited(prediction, heading))
    predicted_refusal = ot_predicted_refusal(prediction)
    corrupt = bool(CORRUPT_RE.search(prediction))
    quotes = QUOTE_RE.findall(prediction)
    format_ok = len(prediction.strip()) > 20 and not corrupt

    # Quote / heading misses are diagnostics only under corpus-chat contract 1.1.
    diagnostics: list[str] = []
    if not expect_refusal:
        if quote_hits < 1:
            diagnostics.append("quote_not_in_passage")
        if not cites_heading:
            diagnostics.append("missing_or_wrong_heading")

    failures: list[str] = []
    if persona:
        failures.append("persona_violation")
    if expect_refusal:
        if not predicted_refusal:
            failures.append("missed_ooc_refusal")
    elif predicted_refusal:
        failures.append("false_refusal")
    if corrupt:
        failures.append("corrupt_output")
    if not format_ok:
        failures.append("format_fail")

    return {
        "persona_errors": persona,
        "quote_in_passage_hits": quote_hits,
        "quote_in_passage": quote_hits >= 1,
        "heading_cited": cites_heading,
        "predicted_refusal": predicted_refusal,
        "expect_refusal": expect_refusal,
        "corrupt": corrupt,
        "format_ok": format_ok,
        "quotes": quotes,
        "diagnostics": diagnostics,
        "failures": failures,
    }

def summarize_mechanical(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)
    return {
        "n": n,
        "persona_violation_rate": _safe_div(
            sum(bool(r["mechanical"]["persona_errors"]) for r in records), n
        ),
        "quote_in_passage_rate": _safe_div(
            sum(bool(r["mechanical"]["quote_in_passage"]) for r in records), n
        ),
        "heading_cited_rate": _safe_div(
            sum(bool(r["mechanical"]["heading_cited"]) for r in records), n
        ),
        "false_refusal_rate": _safe_div(
            sum("false_refusal" in r["mechanical"]["failures"] for r in records), n
        ),
        "missed_ooc_refusal_rate": _safe_div(
            sum("missed_ooc_refusal" in r["mechanical"]["failures"] for r in records), n
        ),
        "format_ok_rate": _safe_div(sum(bool(r["mechanical"]["format_ok"]) for r in records), n),
        "corrupt_rate": _safe_div(sum(bool(r["mechanical"]["corrupt"]) for r in records), n),
        "persona_violations": sum(bool(r["mechanical"]["persona_errors"]) for r in records),
        "quote_in_passage_hits": sum(bool(r["mechanical"]["quote_in_passage"]) for r in records),
        "heading_cited_hits": sum(bool(r["mechanical"]["heading_cited"]) for r in records),
        "false_refusals": sum("false_refusal" in r["mechanical"]["failures"] for r in records),
        "missed_ooc_refusals": sum(
            "missed_ooc_refusal" in r["mechanical"]["failures"] for r in records
        ),
    }


def absolute_ot_judge_prompt(
    *,
    question: str,
    gold: str,
    prediction: str,
    heading: str,
    passage_excerpt: str,
) -> str:
    return f"""You are an independent evaluator of open theological Q&A (Spurgeon / Puritan / confession corpus).

There is NO retrieval CONTEXT block. The assistant is a knowledge assistant about that corpus (never Spurgeon or a Puritan as a character). A catalog heading or verbatim quote is OPTIONAL. Do not penalize a correct doctrinal answer merely for missing a heading or quote. Score doctrine against GOLD intent, not verbatim match to GOLD.

Score the PREDICTION from 1 to 5 on:
- correctness: answers the QUESTION accurately relative to GOLD intent / doctrine (do not require verbatim match to GOLD; do not require a cite)
- citation_fidelity: diagnostic only — if the PREDICTION invents sermon numbers, works, authors, or fabricated quotes, score low; if it cites nothing, score 3 (neutral); if cites match HEADING / PASSAGE_EXCERPT when present, score high
- persona_leakage: 5 = clean knowledge assistant; 1 = preacher roleplay, vocatives (Beloved, Dear friends, etc.), or first-person Puritan costume
- honesty: does not invent corpus claims; refuses briefly only when the question is outside the corpus (false refusal on an in-corpus question scores poorly). Invented works or fake quotes also lower honesty.

Output only JSON:
{{
  "correctness": 1,
  "citation_fidelity": 1,
  "persona_leakage": 1,
  "honesty": 1,
  "reasoning": "brief evidence-based reason"
}}

QUESTION:
{question}

GOLD:
{gold}

HEADING:
{heading}

PASSAGE_EXCERPT:
{passage_excerpt}

PREDICTION:
{prediction}
"""


def parse_absolute_ot_judge(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = (
            stripped.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
    start, finish = stripped.find("{"), stripped.rfind("}")
    if start < 0 or finish < start:
        raise ValueError("judge response does not contain a JSON object")
    payload = json.loads(stripped[start : finish + 1])
    for dim in OT_JUDGE_DIMS:
        value = payload.get(dim)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 1 <= value <= 5:
            raise ValueError(f"{dim} must be numeric in [1, 5]")
    if not isinstance(payload.get("reasoning"), str) or not payload["reasoning"].strip():
        raise ValueError("judge reasoning must be a non-empty string")
    return payload


def summarize_judge(judgments: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(judgments)
    means: dict[str, float] = {}
    for dim in OT_JUDGE_DIMS:
        vals = [float(j["scores"][dim]) for j in judgments]
        means[dim] = round(sum(vals) / n, 4) if n else 0.0
    served = sorted({str(j.get("served_model") or "") for j in judgments if j.get("served_model")})
    return {
        "n_judgments": n,
        "means": means,
        "served_models": served,
        "judge_model_consistent": len(served) <= 1,
    }


def informational_verdict(mech: dict[str, Any], judge_summary: dict[str, Any] | None) -> dict[str, Any]:
    """Informational only — never a release gate.

    Corpus-chat contract 1.1: cite/quote rates are diagnostics, not pass/fail.
    """
    checks: dict[str, bool] = {
        "persona_ok": mech["persona_violation_rate"] <= 0.05,
        "false_refusal_ok": mech["false_refusal_rate"] <= 0.10,
    }
    means = (judge_summary or {}).get("means") or {}
    if means:
        checks["correctness_ok"] = float(means.get("correctness") or 0) >= 3.5
        checks["honesty_ok"] = float(means.get("honesty") or 0) >= 3.5
        checks["persona_judge_ok"] = float(means.get("persona_leakage") or 0) >= 4.0
    useful = all(checks.values()) if checks else False
    if useful:
        label = "useful_theology_chat"
    elif mech["persona_violation_rate"] > 0.15 or (
        means and float(means.get("correctness") or 0) <= 3.0
    ):
        label = "weak_not_useful_yet"
    else:
        label = "mixed_needs_review"
    return {
        "useful_theology_chat": useful,
        "label": label,
        "checks": checks,
        "diagnostics": {
            "quote_in_passage_rate": mech.get("quote_in_passage_rate"),
            "heading_cited_rate": mech.get("heading_cited_rate"),
            "citation_fidelity_mean": means.get("citation_fidelity"),
        },
        "contract": OT_CONTRACT,
        "next_ft_knob": "rag_refusal_slice",
        "release_gate": False,
        "note": (
            "OT score (corpus-chat contract) does not unlock Hub/Ollama export. "
            "RAG refusal remains the F §5 release gate."
        ),
    }

def write_human_summary(path: Path, report: dict[str, Any], sample: int = 8) -> None:
    mech = report["metrics"]["mechanical"]
    verdict = report["verdict"]
    lines = [
        "# Open-theology chat eval — human summary",
        "",
        f"- Created: `{report.get('created_at')}`",
        f"- Adapter SHA256: `{report.get('adapter_sha256')}`",
        f"- Eval set: `{report['dataset']['path']}` (n={mech['n']})",
        f"- Contract: `{report.get('contract') or verdict.get('contract') or OT_CONTRACT}` "
        f"(schema `{report.get('schema_version')}`)",
        f"- Release gate: **false** (informational only; does not unlock Hub/Ollama)",
        f"- Verdict label: **{verdict['label']}**",
        f"- Next FT knob: `{verdict['next_ft_knob']}`",
        "",
        "## Mechanical rates (gates)",
        "",
        f"- persona_violation_rate: {mech['persona_violation_rate']}",
        f"- false_refusal_rate: {mech['false_refusal_rate']}",
        f"- format_ok_rate: {mech['format_ok_rate']}",
        f"- corrupt_rate: {mech['corrupt_rate']}",
        "",
        "## Citation diagnostics (not pass/fail)",
        "",
        f"- quote_in_passage_rate: {mech['quote_in_passage_rate']}",
        f"- heading_cited_rate: {mech['heading_cited_rate']}",
        "",
    ]
    judge = report.get("judge") or {}
    if judge.get("enabled") and judge.get("summary"):
        means = judge["summary"].get("means") or {}
        lines += [
            "## Judge means (1–5)",
            "",
            f"- provider/model: `{judge.get('provider')}` / `{judge.get('model')}`",
            f"- correctness: {means.get('correctness')} (gate)",
            f"- honesty: {means.get('honesty')} (gate)",
            f"- persona_leakage: {means.get('persona_leakage')} (gate)",
            f"- citation_fidelity: {means.get('citation_fidelity')} (diagnostic)",
            "",
        ]
    lines += ["## Failure examples", ""]
    failures = [r for r in report["records"] if r["mechanical"]["failures"]]
    priority = ("persona_violation", "false_refusal", "corrupt_output", "format_fail")
    ranked = sorted(
        failures,
        key=lambda r: min(
            (priority.index(f) if f in priority else 99 for f in r["mechanical"]["failures"]),
            default=99,
        ),
    )
    for rec in ranked[:sample]:
        diag = rec["mechanical"].get("diagnostics") or []
        lines.append(
            f"### `{rec['id']}` failures={rec['mechanical']['failures']}"
            + (f" diagnostics={diag}" if diag else "")
        )
        lines.append("")
        lines.append(f"- Q: {rec['question'][:200]}")
        lines.append(f"- Heading: {rec.get('heading')}")
        pred = rec["prediction"]
        lines.append(f"- Prediction: {pred[:500]}{'…' if len(pred) > 500 else ''}")
        if rec.get("judge"):
            lines.append(f"- Judge: {rec['judge'].get('scores')} — {rec['judge'].get('reasoning', '')[:200]}")
        lines.append("")
    if not failures:
        lines.append("_No mechanical failures (persona / false refusal / format)._")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_records(
    eval_rows: list[dict[str, Any]],
    accepted: dict[str, dict[str, Any]],
    predictions: list[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for i, (row, pred) in enumerate(zip(eval_rows, predictions)):
        rid = row_id(row)
        acc = accepted.get(rid)
        if acc is None:
            raise ValueError(f"No accepted meta for id={rid}")
        meta = acc.get("meta") or {}
        passage = str(meta.get("passage") or "")
        heading = str(meta.get("heading") or "")
        bucket = str(meta.get("bucket") or "")
        expect_refusal = bucket == "ooc" or str(row.get("slice") or "") == "open_theology_ooc"
        msgs = row["messages"]
        mech = score_mechanical(
            prediction=pred,
            passage=passage,
            heading=heading,
            expect_refusal=expect_refusal,
        )
        records.append(
            {
                "index": i,
                "id": rid,
                "bucket": bucket,
                "heading": heading,
                "question": role(msgs, "user"),
                "gold": role(msgs, "assistant"),
                "prediction": pred,
                "mechanical": mech,
                "judge": None,
            }
        )
    return records


def run_absolute_judge(
    records: list[dict[str, Any]],
    accepted: dict[str, dict[str, Any]],
    *,
    retries: int = 2,
    progress_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Lazy import JudgeClient from evaluate.py
    from evaluate import JudgeClient  # noqa: WPS433

    client = JudgeClient(
        model=SFT_EVAL_JUDGE_MODEL,
        base_url=SFT_EVAL_JUDGE_BASE_URL,
        api_key=SFT_EVAL_JUDGE_API_KEY,
        timeout=SFT_EVAL_JUDGE_TIMEOUT,
        retries=retries,
    )
    judgments: list[dict[str, Any]] = []
    for rec in records:
        acc = accepted[rec["id"]]
        meta = acc.get("meta") or {}
        passage = str(meta.get("passage") or "")
        excerpt = passage[:1200] + ("…" if len(passage) > 1200 else "")
        prompt = absolute_ot_judge_prompt(
            question=rec["question"],
            gold=rec["gold"],
            prediction=rec["prediction"],
            heading=rec["heading"],
            passage_excerpt=excerpt,
        )
        last_err: Exception | None = None
        parsed: dict[str, Any] | None = None
        served: str | None = None
        for attempt in range(retries + 1):
            try:
                text, served = client._chat(prompt)
                parsed = parse_absolute_ot_judge(text)
                break
            except Exception as exc:  # noqa: BLE001 — retry then raise
                last_err = exc
                if attempt < retries:
                    time.sleep(min(2**attempt, 5))
        if parsed is None:
            raise RuntimeError(f"OT judge failed for {rec['id']}: {last_err}")
        scores = {dim: parsed[dim] for dim in OT_JUDGE_DIMS}
        entry = {
            "id": rec["id"],
            "scores": scores,
            "reasoning": parsed["reasoning"],
            "served_model": served,
        }
        rec["judge"] = entry
        judgments.append(entry)
        if progress_path is not None:
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            with progress_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return judgments, summarize_judge(judgments)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Open-theology held-out chat eval (not F §5)")
    p.add_argument(
        "--eval-set",
        default=str(REPO / "fine_tuning" / "data" / "qa_open_theology" / "sft" / "open_theology_eval.jsonl"),
        help=(
            "Held-out JSONL. Answerable set: open_theology_eval.jsonl. "
            "OOC honesty slice (unscored until GPU go): open_theology_eval_ooc.jsonl"
        ),
    )
    p.add_argument(
        "--accepted",
        default=str(REPO / "fine_tuning" / "data" / "qa_open_theology" / "eval_accepted.jsonl"),
        help="eval_accepted.jsonl with passage/heading meta (optional for OOC inline-meta rows)",
    )
    p.add_argument("--from-report", default="", help="evaluate.py generate-only JSON report")
    p.add_argument("--predictions-jsonl", default="", help="Progress JSONL with prediction fields")
    p.add_argument(
        "--output",
        default=str(REPO / "fine_tuning" / "eval_results" / "open_theology_eval_s8_weighted.json"),
    )
    p.add_argument("--adapter-sha", default="", help="Expected LoRA SHA256 (recorded in report)")
    p.add_argument("--judge", action="store_true")
    p.add_argument("--judge-retries", type=int, default=2)
    p.add_argument("--review-sample", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    eval_path = Path(args.eval_set).resolve()
    accepted_path = Path(args.accepted).resolve()
    output = Path(args.output).resolve()

    eval_rows = load_eval_set(eval_path)
    if args.limit and args.limit > 0:
        eval_rows = eval_rows[: args.limit]
    accepted = merge_inline_ooc_meta(eval_rows, load_accepted_by_id(accepted_path))
    missing = [row_id(r) for r in eval_rows if row_id(r) not in accepted]
    if missing:
        raise ValueError(f"Missing accepted meta for: {missing[:5]}{'…' if len(missing) > 5 else ''}")

    from_report = None
    if args.from_report:
        from_report = json.loads(Path(args.from_report).read_text(encoding="utf-8"))
    preds_path = Path(args.predictions_jsonl).resolve() if args.predictions_jsonl else None
    predictions = match_predictions(
        eval_rows, from_report=from_report, predictions_jsonl=preds_path
    )

    records = build_records(eval_rows, accepted, predictions)
    mech = summarize_mechanical(records)

    judge_payload: dict[str, Any] = {
        "requested": bool(args.judge),
        "enabled": False,
        "status": "not_requested",
        "provider": None,
        "model": None,
        "summary": None,
        "judgments": [],
    }
    if args.judge:
        if SFT_EVAL_JUDGE_PROVIDER.lower() != "gemini":
            print(
                f"WARNING: SFT_EVAL_JUDGE_PROVIDER={SFT_EVAL_JUDGE_PROVIDER!r}; "
                "plan recommends gemini (Groq 403s).",
                file=sys.stderr,
            )
        progress = output.with_name(f"{output.stem}.judge.progress.jsonl")
        if progress.exists():
            progress.unlink()
        judgments, summary = run_absolute_judge(
            records, accepted, retries=args.judge_retries, progress_path=progress
        )
        judge_payload = {
            "requested": True,
            "enabled": True,
            "status": "complete",
            "provider": SFT_EVAL_JUDGE_PROVIDER,
            "model": SFT_EVAL_JUDGE_MODEL,
            "summary": summary,
            "judgments": judgments,
        }
        progress.unlink(missing_ok=True)

    verdict = informational_verdict(mech, judge_payload.get("summary"))
    report = {
        "schema_version": OT_REPORT_SCHEMA,
        "contract": OT_CONTRACT,
        "release_gate": False,
        "created_at": utc_now(),
        "adapter_sha256": (args.adapter_sha or "").lower() or None,
        "dataset": {
            "path": str(eval_path),
            "sha256": sha256_file(eval_path),
            "accepted_path": str(accepted_path),
            "accepted_sha256": sha256_file(accepted_path),
            "evaluated_count": len(records),
        },
        "source_generation": {
            "from_report": str(Path(args.from_report).resolve()) if args.from_report else None,
            "predictions_jsonl": str(preds_path) if preds_path else None,
        },
        "metrics": {"mechanical": mech},
        "judge": judge_payload,
        "verdict": verdict,
        "records": records,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path = output.with_name(f"{output.stem}_human_summary.md")
    write_human_summary(summary_path, report, sample=args.review_sample)

    print(
        json.dumps(
            {
                "mechanical": mech,
                "judge_means": (judge_payload.get("summary") or {}).get("means"),
                "verdict": verdict,
            },
            indent=2,
        )
    )
    print("Wrote", output)
    print("Wrote", summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
