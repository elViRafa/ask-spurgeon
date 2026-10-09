#!/usr/bin/env python3
"""Rewrite doubled-quote Spurgeon headings in an existing open-theology queue.

`[Sermon 2806 — ""Jesus Our Lord""]` -> `[Sermon 2806 — "Jesus Our Lord"]` (see
plan_open_theology_jobs.clean_sermon_title). Touches catalog.json and the PENDING rows of
jobs.jsonl only (job_ids not yet in accepted.jsonl / rejected.jsonl). Never touches
accepted.jsonl, rejected.jsonl, status.json, qa_mix_train.jsonl or qa_test_frozen.jsonl.

Dry by default: prints what would change. With --apply, writes a timestamped .bak copy of
each changed file first, then rewrites it.

Usage (repo root):
  python fine_tuning/scripts/fix_open_theology_catalog_headings.py
  python fine_tuning/scripts/fix_open_theology_catalog_headings.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from plan_open_theology_jobs import OUT_DIR, clean_sermon_title, sermon_heading  # noqa: E402

SERMON_HEADING_RE = re.compile(r'^\[Sermon (\S+) — "(.*)"\]$', re.S)


def fixed_heading(heading: str) -> str:
    """Return the canonical heading; unchanged for non-sermon or already-clean headings."""
    m = SERMON_HEADING_RE.match(heading or "")
    if not m:
        return heading
    return sermon_heading(m.group(1), m.group(2))


def _job_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(json.loads(line).get("job_id", ""))
    return ids


def _newline(path: Path) -> str:
    """Keep the file's existing line endings (pc1 files are CRLF)."""
    return "\r\n" if b"\r\n" in path.read_bytes()[:65536] else "\n"


def migrate(data_dir: Path, *, apply: bool = False) -> dict:
    catalog_p = data_dir / "catalog.json"
    jobs_p = data_dir / "jobs.jsonl"
    done = _job_ids(data_dir / "accepted.jsonl") | _job_ids(data_dir / "rejected.jsonl")

    catalog = json.loads(catalog_p.read_text(encoding="utf-8"))
    cat_changes: list[tuple[str, str, str]] = []
    for e in catalog.get("entries", []):
        new = fixed_heading(e.get("heading", ""))
        if new != e.get("heading"):
            cat_changes.append((e.get("job_id", e.get("work_id", "?")), e["heading"], new))
            e["heading"] = new

    jobs = [json.loads(l) for l in jobs_p.read_text(encoding="utf-8").splitlines() if l.strip()]
    job_changes: list[tuple[str, str, str]] = []
    skipped_done: list[str] = []
    for j in jobs:
        new = fixed_heading(j.get("heading", ""))
        if new == j.get("heading"):
            continue
        if j.get("job_id") in done:
            skipped_done.append(j["job_id"])
            continue
        job_changes.append((j["job_id"], j["heading"], new))
        j["heading"] = new
        if j.get("title"):
            j["title"] = clean_sermon_title(j["title"])

    mode = "APPLY" if apply else "DRY RUN"
    print(f"[{mode}] {data_dir}")
    print(f"catalog.json: {len(cat_changes)} heading(s) to fix")
    for jid, old, new in cat_changes:
        print(f"  {jid}: {old}  ->  {new}")
    print(f"jobs.jsonl: {len(job_changes)} pending heading(s) to fix; "
          f"{len(skipped_done)} already done left as-is {sorted(skipped_done)}")
    for jid, old, new in job_changes:
        print(f"  {jid}: {old}  ->  {new}")

    if apply:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if cat_changes:
            shutil.copy2(catalog_p, catalog_p.with_name(f"catalog.json.bak-{stamp}"))
            nl = _newline(catalog_p)
            with catalog_p.open("w", encoding="utf-8", newline="") as f:
                f.write(json.dumps(catalog, indent=2).replace("\n", nl))
        if job_changes:
            shutil.copy2(jobs_p, jobs_p.with_name(f"jobs.jsonl.bak-{stamp}"))
            nl = _newline(jobs_p)
            with jobs_p.open("w", encoding="utf-8", newline="") as f:
                for j in jobs:
                    f.write(json.dumps(j, ensure_ascii=False) + nl)
        print(f"written; backups suffixed .bak-{stamp}" if (cat_changes or job_changes) else "nothing to write")
    else:
        print("dry run: nothing written (pass --apply to rewrite with backups)")
    return {"catalog": len(cat_changes), "jobs": len(job_changes), "skipped_done": skipped_done}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--apply", action="store_true", help="rewrite files (backs up originals)")
    args = ap.parse_args()
    migrate(args.data_dir, apply=args.apply)


if __name__ == "__main__":
    main()
