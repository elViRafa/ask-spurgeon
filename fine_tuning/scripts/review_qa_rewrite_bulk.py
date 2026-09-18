#!/usr/bin/env python3
"""Review bulk_pending.jsonl against the gold rewrite contract.

Only rows with ok=true (or --all) are scored. Does not patch train.

Usage:
  python fine_tuning/scripts/review_qa_rewrite_bulk.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl  # noqa: E402
from qa_rewrite_checks import check_assistant, quote_cite_counts, role  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Review bulk teacher rewrite JSONL")
    p.add_argument(
        "--pending",
        default=str(_SCRIPTS.parent / "data" / "qa_rewrite_pilot" / "bulk_pending.jsonl"),
    )
    p.add_argument("--all", action="store_true", help="Include rows already marked ok=false")
    args = p.parse_args(argv)

    path = Path(args.pending)
    if not path.exists():
        print(f"No bulk file yet at {path} — next session: rewrite_qa_answers_teacher.py --apply")
        return 0

    rows = read_jsonl(path)
    errors: list[str] = []
    n = 0
    print(f"{'line':8} {'slice':12} quotes cites")
    for rec in rows:
        if not args.all and rec.get("ok") is False:
            continue
        n += 1
        line = rec.get("source_line", "?")
        msgs = rec.get("messages") or []
        user = role(msgs, "user")
        ans = role(msgs, "assistant")
        slice_name = rec.get("slice") or "answerable"
        errs = check_assistant(user, ans, slice_name)
        ok_q, cites = quote_cite_counts(user, ans)
        print(f"{str(line):8} {slice_name:12} {ok_q:6} {cites}")
        for e in errs:
            errors.append(f"line {line}: {e}")

    if n == 0:
        print("No bulk rows to review yet (run --apply next session).")
        return 0
    if errors:
        print("FAIL")
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 2
    print(f"PASS ({n} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
