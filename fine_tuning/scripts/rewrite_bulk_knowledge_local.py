#!/usr/bin/env python3
"""Local knowledge-voice pass over ok=true bulk_pending rows (no API).

Strips leading vocatives and replaces a few roleplay phrases, then re-runs
qa_rewrite_checks. Use when --rerun-ok teacher is unavailable.

Usage (repo root):
  python fine_tuning/scripts/rewrite_bulk_knowledge_local.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl, repo_root  # noqa: E402
from qa_rewrite_checks import check_assistant, role, strip_leading_vocative  # noqa: E402

_REPLACEMENTS = (
    (re.compile(r"\bwhen I preached\b", re.I), "when Spurgeon preached"),
    (re.compile(r"\bin my pulpit\b", re.I), "in the pulpit"),
    (re.compile(r"\bthese lips must\b", re.I), "the preacher must"),
    (re.compile(r"\bas Spurgeon I\b", re.I), "as the sermons teach, one"),
    (re.compile(r"^I send you to\b", re.I), "Spurgeon sends the hearer to"),
    (re.compile(r"^I would not send\b", re.I), "Spurgeon would not send"),
    (re.compile(r"^I would say,\b", re.I), "He would say,"),
)


def knowledge_voice(text: str) -> str:
    out = strip_leading_vocative(text)
    for pat, repl in _REPLACEMENTS:
        out = pat.sub(repl, out)
    return out


def main() -> int:
    path = repo_root() / "fine_tuning" / "data" / "qa_rewrite_pilot" / "bulk_pending.jsonl"
    rows = read_jsonl(path)
    n_ok = 0
    n_fail = 0
    for rec in rows:
        if rec.get("ok") is not True:
            continue
        user = role(rec["messages"], "user")
        ans = role(rec["messages"], "assistant")
        slice_name = rec.get("slice") or "answerable"
        new = knowledge_voice(ans)
        errs = check_assistant(user, new, slice_name)
        rec["messages"] = [
            {"role": "system", "content": role(rec["messages"], "system")},
            {"role": "user", "content": user},
            {"role": "assistant", "content": new},
        ]
        rec["ok"] = not errs
        rec["errors"] = errs
        rec["teacher"] = "local-knowledge-voice"
        rec["created_at"] = datetime.now(timezone.utc).isoformat()
        if errs:
            n_fail += 1
            print(f"FAIL line {rec.get('source_line')}: {errs[0]}")
        else:
            n_ok += 1
    tmp = path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for rec in rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"Local knowledge pass: still_ok={n_ok} now_fail={n_fail}")
    return 0 if n_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
