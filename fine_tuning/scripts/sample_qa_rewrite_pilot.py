#!/usr/bin/env python3
"""Sample 20 qa_mix_v2 train rows for a gold assistant-rewrite pilot.

Does not touch qa_mix_train/val/test or the Kaggle zip.

Usage (repo root):
  python fine_tuning/scripts/sample_qa_rewrite_pilot.py
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import is_refusal, read_jsonl, repo_root  # noqa: E402
from build_qa_mix_v2 import parse_user  # noqa: E402

SERMON_HEADER_RE = re.compile(r"\[Sermon\s+(\d+)", re.I)
SEED = 3407
N_ANSWERABLE = 16
N_REFUSAL = 4


def sermon_ids(user: str) -> list[int]:
    seen: list[int] = []
    for n in SERMON_HEADER_RE.findall(user):
        v = int(n)
        if v not in seen:
            seen.append(v)
    return seen


def assistant_text(row: dict) -> str:
    msgs = row.get("messages") or []
    return next((m["content"] for m in msgs if m.get("role") == "assistant"), "")


def user_text(row: dict) -> str:
    msgs = row.get("messages") or []
    return next((m["content"] for m in msgs if m.get("role") == "user"), "")


def system_text(row: dict) -> str:
    msgs = row.get("messages") or []
    return next((m["content"] for m in msgs if m.get("role") == "system"), "")


def question_of(user: str) -> str:
    parsed = parse_user(user)
    if parsed:
        return parsed[1]
    return ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sample 20 v2 rows for gold rewrite")
    p.add_argument(
        "--input",
        default=str(repo_root() / "fine_tuning" / "data" / "qa_mix_train.jsonl"),
    )
    p.add_argument(
        "--output-dir",
        default=str(repo_root() / "fine_tuning" / "data" / "qa_rewrite_pilot"),
    )
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--n-answerable", type=int, default=N_ANSWERABLE)
    p.add_argument("--n-refusal", type=int, default=N_REFUSAL)
    args = p.parse_args(argv)

    inp = Path(args.input).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(inp)
    answerable: list[tuple[int, dict]] = []
    refusals: list[tuple[int, dict]] = []
    for i, row in enumerate(rows, start=1):
        item = (i, row)
        if is_refusal(row):
            refusals.append(item)
        else:
            answerable.append(item)

    if len(answerable) < args.n_answerable or len(refusals) < args.n_refusal:
        print(
            f"ERROR: not enough rows (answerable={len(answerable)}, refusal={len(refusals)})",
            file=sys.stderr,
        )
        return 2

    rng = random.Random(args.seed)
    # Prefer short original answers among answerable (those benefit most from rewrite).
    answerable.sort(key=lambda t: len(assistant_text(t[1])))
    short_pool = answerable[: max(args.n_answerable * 8, 80)]
    rng.shuffle(short_pool)
    picked_ans = short_pool[: args.n_answerable]

    rng.shuffle(refusals)
    picked_ref = refusals[: args.n_refusal]

    picked = picked_ans + picked_ref
    # Stable order: answerable first (by source_line), then refusals.
    picked.sort(key=lambda t: (is_refusal(t[1]), t[0]))

    payloads = []
    for seq, (source_line, row) in enumerate(picked, start=1):
        user = user_text(row)
        assistant = assistant_text(row)
        payloads.append(
            {
                "id": f"pilot-{seq:02d}",
                "source_line": source_line,
                "slice": "refusal" if is_refusal(row) else "answerable",
                "question": question_of(user),
                "sermon_ids": sermon_ids(user),
                "original_answer": assistant,
                "system": system_text(row),
                "user": user,
            }
        )

    out_path = out_dir / "sample.json"
    out_path.write_text(json.dumps(payloads, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(payloads)} rows)")
    print(
        "slices:",
        sum(1 for x in payloads if x["slice"] == "answerable"),
        "answerable /",
        sum(1 for x in payloads if x["slice"] == "refusal"),
        "refusal",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
