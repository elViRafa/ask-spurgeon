#!/usr/bin/env python3
"""Mechanical review of the 20-row gold assistant rewrite.

Checks (no teacher API):
  - system/user match sample.json exactly
  - gold contract via qa_rewrite_checks (citations, quotes, refusals)

Usage (repo root):
  python fine_tuning/scripts/review_qa_gold_rewrite.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from qa_rewrite_checks import check_assistant, quote_cite_counts, role  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Review gold rewrite pilot JSONL")
    p.add_argument(
        "--sample",
        default=str(_SCRIPTS.parent / "data" / "qa_rewrite_pilot" / "sample.json"),
    )
    p.add_argument(
        "--gold",
        default=str(_SCRIPTS.parent / "data" / "qa_rewrite_pilot" / "qa_gold_rewrite_pilot.jsonl"),
    )
    args = p.parse_args(argv)

    sample_path = Path(args.sample)
    gold_path = Path(args.gold)
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in sample}

    gold_rows: list[dict] = []
    with gold_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                gold_rows.append(json.loads(line))

    errors: list[str] = []
    print(f"{'id':10} {'slice':12} {'orig':>5} {'new':>5} quotes cites")
    for row in gold_rows:
        pid = row.get("id", "?")
        src = by_id.get(pid)
        if src is None:
            errors.append(f"{pid}: not in sample.json")
            continue
        msgs = row.get("messages") or []
        sys_c = role(msgs, "system")
        user = role(msgs, "user")
        ans = role(msgs, "assistant")
        if sys_c != src["system"]:
            errors.append(f"{pid}: system text differs from sample")
        if user != src["user"]:
            errors.append(f"{pid}: user text differs from sample")

        slice_name = row.get("slice") or src["slice"]
        for e in check_assistant(user, ans, slice_name):
            errors.append(f"{pid}: {e}")
        ok_quotes, cites = quote_cite_counts(user, ans)
        print(
            f"{pid:10} {slice_name:12} {len(src['original_answer']):5} {len(ans):5} "
            f"{ok_quotes:6} {cites}"
        )

    if len(gold_rows) != 20:
        errors.append(f"expected 20 gold rows, got {len(gold_rows)}")

    if errors:
        print("FAIL")
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 2
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
