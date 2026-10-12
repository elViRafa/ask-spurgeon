#!/usr/bin/env python3
"""Queue maintenance for the open-theology QA slice (dry by default).

1. Requeue: move rejected.jsonl rows whose ONLY errors are teacher transport errors
   ("teacher error: ..." e.g. groq 429 TPD quota) out of rejected.jsonl and append them to
   requeued_from_rejected.jsonl, so those jobs are pending again. Quality rejects stay.
   With --ids JOB_ID ..., also requeue those specific rejected rows (any error type),
   e.g. teacher-format quote rejects worth retrying after a prompt change.
2. Skip (optional, --skip JOB_ID ...): append a rejected row for pending jobs whose
   passage is unusable (link lists, index pages), so the teacher is never called for them.

Never touches accepted.jsonl, jobs.jsonl, catalog.json, qa_mix_train.jsonl or
qa_test_frozen.jsonl. With --apply, rejected.jsonl is backed up (.bak-<ts>) first.
status.json counts are refreshed by the next generator run.

Usage (repo root):
  python fine_tuning/scripts/requeue_open_theology_teacher_errors.py
  python fine_tuning/scripts/requeue_open_theology_teacher_errors.py --ids train-puritan-057 train-puritan-049
  python fine_tuning/scripts/requeue_open_theology_teacher_errors.py \
      --skip train-confession-030 train-confession-032 --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from plan_open_theology_jobs import OUT_DIR  # noqa: E402


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _newline(path: Path) -> str:
    return "\r\n" if path.exists() and b"\r\n" in path.read_bytes()[:65536] else "\n"


def is_teacher_error_only(row: dict) -> bool:
    errs = row.get("errors") or []
    return bool(errs) and all(str(e).startswith("teacher error:") for e in errs)


def maintain(
    data_dir: Path,
    *,
    skip: list[str] | None = None,
    ids: list[str] | None = None,
    apply: bool = False,
) -> dict:
    rejected_p = data_dir / "rejected.jsonl"
    requeued_p = data_dir / "requeued_from_rejected.jsonl"
    rejected = _read(rejected_p)
    accepted_ids = {r.get("job_id") for r in _read(data_dir / "accepted.jsonl")}
    jobs = {j["job_id"]: j for j in _read(data_dir / "jobs.jsonl")}

    want = set(ids or [])
    rejected_ids = {r.get("job_id") for r in rejected}
    ids_missing = sorted(want - rejected_ids)

    def _move(r: dict) -> bool:
        return is_teacher_error_only(r) or r.get("job_id") in want

    move = [r for r in rejected if _move(r)]
    keep = [r for r in rejected if not _move(r)]
    kept_ids = {r.get("job_id") for r in keep}

    skip_rows, skip_bad = [], []
    for jid in skip or []:
        if jid not in jobs or jid in accepted_ids or jid in kept_ids:
            skip_bad.append(jid)
            continue
        j = jobs[jid]
        skip_rows.append({
            "job_id": jid,
            "ok": False,
            "errors": ["skipped: unusable source passage (operator skip)"],
            "meta": {k: j.get(k) for k in ("bucket", "work_id", "source_path", "heading")},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    print(f"[{'APPLY' if apply else 'DRY RUN'}] {data_dir}")
    print(f"rejected.jsonl: {len(rejected)} rows; {len(move)} -> requeue "
          f"(teacher-error-only or --ids), {len(keep)} kept")
    if ids_missing:
        print(f"  --ids not in rejected.jsonl (ignored): {ids_missing}")
    for r in move:
        print(f"  requeue {r.get('job_id')}: {str(r['errors'][0])[:90]}")
    print(f"skip: {len(skip_rows)} job(s) {[r['job_id'] for r in skip_rows]}"
          + (f"; ignored (unknown/already done) {skip_bad}" if skip_bad else ""))

    if apply and (move or skip_rows):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        nl = _newline(rejected_p)
        if rejected_p.exists():
            shutil.copy2(rejected_p, rejected_p.with_name(f"rejected.jsonl.bak-{stamp}"))
        with rejected_p.open("w", encoding="utf-8", newline="") as f:
            for r in keep + skip_rows:
                f.write(json.dumps(r, ensure_ascii=False) + nl)
        if move:
            rq_nl = _newline(requeued_p) if requeued_p.exists() else nl
            with requeued_p.open("a", encoding="utf-8", newline="") as f:
                for r in move:
                    f.write(json.dumps(r, ensure_ascii=False) + rq_nl)
        print(f"written; backup rejected.jsonl.bak-{stamp}")
    elif not apply:
        print("dry run: nothing written (pass --apply)")
    return {"requeue": [r.get("job_id") for r in move], "skip": [r["job_id"] for r in skip_rows],
            "ignored": skip_bad, "ids_missing": ids_missing}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--skip", nargs="*", default=[], help="pending job_ids to mark skipped")
    ap.add_argument("--ids", nargs="*", default=[], help="rejected job_ids to requeue (any error)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    maintain(args.data_dir, skip=args.skip, ids=args.ids, apply=args.apply)


if __name__ == "__main__":
    main()
