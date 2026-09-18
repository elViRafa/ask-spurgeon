#!/usr/bin/env python3
"""Merge passing bulk_pending.jsonl assistants into qa_mix_train.jsonl.

Only rows with ok=true and a clean mechanical re-check are applied.
Does not touch val or frozen test.

Usage (after teacher --apply and review PASS):
  python fine_tuning/scripts/merge_qa_bulk_rewrite.py
  python fine_tuning/scripts/12_package_kaggle_qa_mix.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl, repo_root  # noqa: E402
from qa_rewrite_checks import check_assistant, role  # noqa: E402


def main() -> int:
    repo = repo_root()
    data = repo / "fine_tuning" / "data"
    pending_path = data / "qa_rewrite_pilot" / "bulk_pending.jsonl"
    train_path = data / "qa_mix_train.jsonl"
    manifest_path = data / "qa_mix_manifest.json"

    if not pending_path.exists():
        print(f"ERROR: missing {pending_path}", file=sys.stderr)
        return 2

    pending = read_jsonl(pending_path)
    train = read_jsonl(train_path)
    applied = 0
    skipped = 0
    newly_applied: list[int] = []
    for rec in pending:
        if rec.get("ok") is not True:
            skipped += 1
            continue
        line_no = int(rec["source_line"])
        idx = line_no - 1
        current = train[idx]
        user = role(current["messages"], "user")
        gold_user = role(rec["messages"], "user")
        if user != gold_user:
            print(f"ERROR: user mismatch at line {line_no}", file=sys.stderr)
            return 2
        ans = role(rec["messages"], "assistant")
        slice_name = rec.get("slice") or "answerable"
        errs = check_assistant(user, ans, slice_name)
        if errs:
            print(f"ERROR: line {line_no} failed re-check: {errs[0]}", file=sys.stderr)
            return 2
        prev_ans = role(current["messages"], "assistant")
        train[idx] = {
            "messages": [
                {"role": "system", "content": role(current["messages"], "system")},
                {"role": "user", "content": user},
                {"role": "assistant", "content": ans},
            ]
        }
        applied += 1
        if prev_ans != ans:
            newly_applied.append(line_no)

    if applied == 0:
        print("Nothing to merge (no ok=true rows).")
        return 0

    tmp = train_path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in train:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    last_err: Exception | None = None
    for attempt in range(1, 6):
        try:
            tmp.replace(train_path)
            last_err = None
            break
        except PermissionError as e:
            last_err = e
            time.sleep(min(2 * attempt, 8))
    if last_err is not None:
        print(f"ERROR: could not replace {train_path}: {last_err}", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    overlay = dict(manifest.get("gold_overlay") or {})
    bulk = list(overlay.get("bulk_merges") or [])
    # Unique source lines ever successfully merged (dedupe across re-runs).
    bulk_lines = {int(n) for n in (overlay.get("bulk_source_lines") or [])}
    bulk_lines.update(int(rec["source_line"]) for rec in pending if rec.get("ok") is True)
    if newly_applied or not bulk:
        bulk.append(
            {
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "rows": len(newly_applied),
                "rows_touched": applied,
                "skipped_not_ok": skipped,
                "new_source_lines": newly_applied,
                "source": "fine_tuning/data/qa_rewrite_pilot/bulk_pending.jsonl",
            }
        )
    overlay["bulk_merges"] = bulk
    overlay["bulk_source_lines"] = sorted(bulk_lines)
    overlay["bulk_rows_total"] = len(bulk_lines)
    manifest["gold_overlay"] = overlay
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Patched {applied} bulk assistants in {train_path} "
        f"(new_answers={len(newly_applied)} unique_bulk={len(bulk_lines)} skipped_not_ok={skipped})"
    )
    print("Re-run 12_package_kaggle_qa_mix.py before Kaggle upload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
