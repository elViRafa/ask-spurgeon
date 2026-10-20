#!/usr/bin/env python3
"""Plan a bounded honesty / anti-invent open-theology teacher batch (no API).

Samples ~60 passages from existing accepted.jsonl meta (same works already in
the slice), writes honesty_jobs.jsonl with job_ids honesty-{bucket}-{nnn}.
Teacher apply is a separate go via generate_open_theology_qa.py --honesty.

Usage (repo root):
  python fine_tuning/scripts/plan_open_theology_honesty_jobs.py
  python fine_tuning/scripts/plan_open_theology_honesty_jobs.py --apply --n 60
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
for p in (_REPO, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from plan_open_theology_jobs import OUT_DIR, SEED  # noqa: E402

DEFAULT_N = 60
TARGET_BUCKETS = {"puritan": 30, "spurgeon": 20, "confession": 10}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def is_junk_passage(passage: str) -> bool:
    p = passage or ""
    if p.count("file:///") >= 2 or p.count("scrBook=") >= 3:
        return True
    letters = sum(c.isalpha() for c in p)
    return letters < 200


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args(argv)

    accepted = read_jsonl(OUT_DIR / "accepted.jsonl")
    pools: dict[str, list[dict]] = {"puritan": [], "spurgeon": [], "confession": []}
    seen_works: set[str] = set()
    for rec in accepted:
        meta = rec.get("meta") or {}
        bucket = str(meta.get("bucket") or "")
        if bucket not in pools:
            continue
        passage = str(meta.get("passage") or "")
        if is_junk_passage(passage):
            continue
        work_id = str(meta.get("work_id") or "")
        # Prefer diverse works.
        key = work_id or str(meta.get("source_path") or "")
        if key in seen_works and len(pools[bucket]) > TARGET_BUCKETS.get(bucket, 10):
            continue
        seen_works.add(key)
        pools[bucket].append(meta)

    rng = random.Random(args.seed)
    for b in pools:
        rng.shuffle(pools[b])

    # Scale targets to --n while keeping ratio.
    total_t = sum(TARGET_BUCKETS.values())
    targets = {
        b: max(1, round(args.n * TARGET_BUCKETS[b] / total_t)) for b in TARGET_BUCKETS
    }
    # Fix rounding to exact n.
    while sum(targets.values()) > args.n:
        b = max(targets, key=targets.get)
        targets[b] -= 1
    while sum(targets.values()) < args.n:
        b = min(targets, key=targets.get)
        targets[b] += 1

    jobs: list[dict] = []
    counters = {b: 0 for b in TARGET_BUCKETS}
    for bucket, need in targets.items():
        for meta in pools[bucket][:need]:
            counters[bucket] += 1
            n = counters[bucket]
            jobs.append(
                {
                    "job_id": f"honesty-{bucket}-{n:03d}",
                    "role": "train",
                    "bucket": bucket,
                    "work_id": meta.get("work_id"),
                    "source_path": meta.get("source_path"),
                    "heading": meta.get("heading"),
                    "passage": meta.get("passage"),
                    "honesty": True,
                    "note": (
                        "Ask a question that tempts inventing a sermon number, fake "
                        "title, or verbatim quote; gold must refuse to invent and still "
                        "teach the doctrine from the passage."
                    ),
                }
            )

    out_jobs = OUT_DIR / "honesty_jobs.jsonl"
    out_status = OUT_DIR / "honesty_status.json"
    print(
        f"honesty_jobs planned n={len(jobs)} "
        f"by_bucket={ {b: counters[b] for b in counters} } "
        f"pools={[ (b, len(pools[b])) for b in pools ]}"
    )
    if not args.apply:
        print("DRY — pass --apply to write honesty_jobs.jsonl + honesty_status.json")
        print("After operator go:")
        print(
            "  python fine_tuning/scripts/generate_open_theology_qa.py "
            "--honesty --apply --limit 60"
        )
        return 0

    if out_jobs.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        shutil.copy2(out_jobs, out_jobs.with_suffix(f".jsonl.bak-{stamp}"))
    write_jsonl(out_jobs, jobs)
    status = {
        "halted": False,
        "halt_reason": "",
        "counts": {
            "accepted": 0,
            "rejected": 0,
            "remaining": len(jobs),
            "honesty_jobs": len(jobs),
        },
        "next_job_id": jobs[0]["job_id"] if jobs else "",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "honesty_anti_invent_v1",
    }
    out_status.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    # Ensure empty accepted/rejected exist for the honesty split.
    for name in ("honesty_accepted.jsonl", "honesty_rejected.jsonl"):
        p = OUT_DIR / name
        if not p.exists():
            p.write_text("", encoding="utf-8")
    print(f"wrote {out_jobs} and {out_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
