#!/usr/bin/env python3
"""Audit qa_mix_train against the knowledge-not-persona rewrite contract.

Prints quote coverage, caricature counts, and teacher-overlay size.

Usage (repo root):
  python fine_tuning/scripts/audit_qa_mix_quality.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import is_refusal, read_jsonl, repo_root  # noqa: E402
from qa_rewrite_checks import caricature_errors, check_assistant, role  # noqa: E402


def last_role(msgs: list, name: str) -> str:
    for m in reversed(msgs or []):
        if m.get("role") == name:
            return m.get("content") or ""
    return ""


def main() -> int:
    data = repo_root() / "fine_tuning" / "data"
    train = read_jsonl(data / "qa_mix_train.jsonl")
    manifest = json.loads((data / "qa_mix_manifest.json").read_text(encoding="utf-8"))
    overlay = manifest.get("gold_overlay") or {}
    gold_n = int(overlay.get("rows") or 0)
    bulk_n = int(overlay.get("bulk_rows_total") or 0)

    answerable = 0
    with_quote = 0
    caric = 0
    refusal = 0
    multiturn = 0
    for row in train:
        msgs = row["messages"]
        if len(msgs) > 3:
            multiturn += 1
            user = last_role(msgs, "user")
            ans = last_role(msgs, "assistant")
        else:
            user = role(msgs, "user")
            ans = role(msgs, "assistant")
        if caricature_errors(ans):
            caric += 1
        if len(msgs) <= 3 and is_refusal(row):
            refusal += 1
            continue
        answerable += 1
        errs = check_assistant(user, ans, "answerable")
        if not any("quote" in e for e in errs):
            with_quote += 1

    n = len(train)
    quote_pct = 100.0 * with_quote / answerable if answerable else 0.0
    teacherish = gold_n + bulk_n
    catechism_n = sum(
        1
        for row in train
        for m in row.get("messages") or []
        if m.get("role") == "user" and "Puritan Catechism Q." in (m.get("content") or "")
    )
    knowledge_voice = teacherish + catechism_n
    print(f"train={n}")
    print(f"refusal={refusal} ({100.0 * refusal / n:.1f}%)")
    print(f"answerable={answerable}")
    print(f"answerable_with_CONTEXT_quote={with_quote} ({quote_pct:.1f}%)")
    print(f"caricature_rows={caric}")
    print(f"multiturn={multiturn} ({100.0 * multiturn / n:.1f}%)")
    print(f"gold_overlay={gold_n} bulk_merged={bulk_n} teacherish={teacherish}")
    print(
        f"catechism_rows={catechism_n} ({100.0 * catechism_n / n:.1f}%) "
        f"knowledge_voice~={knowledge_voice}"
    )
    print(f"remaining_originalish~={n - knowledge_voice - multiturn}")
    if quote_pct < 10.0:
        print("GATE: quote coverage <10% - keep rewriting before GPU")
        return 0
    if quote_pct < 15.0:
        print("GATE: quote coverage 10-15% - continue batches; GPU still discouraged")
        return 0
    print("GATE: quote coverage >=15% - Phase-1 lift visible; GPU still needs operator go")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
