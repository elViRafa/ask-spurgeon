#!/usr/bin/env python3
"""Merge gold-pilot assistant rewrites into qa_mix_train.jsonl.

Replaces assistant text at gold source_line indices after verifying the user
message still matches. Does not touch val or frozen test.

Usage (repo root):
  python fine_tuning/scripts/merge_qa_gold_rewrite.py
  python fine_tuning/scripts/12_package_kaggle_qa_mix.py
  python fine_tuning/scripts/13_sft_local_readiness.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl, repo_root  # noqa: E402
from qa_rewrite_checks import role  # noqa: E402


def main() -> int:
    repo = repo_root()
    data = repo / "fine_tuning" / "data"
    gold_path = data / "qa_rewrite_pilot" / "qa_gold_rewrite_pilot.jsonl"
    train_path = data / "qa_mix_train.jsonl"
    manifest_path = data / "qa_mix_manifest.json"
    pilot_manifest_path = data / "qa_rewrite_pilot" / "pilot_manifest.json"

    gold_rows = read_jsonl(gold_path)
    train = read_jsonl(train_path)
    if not gold_rows:
        print("ERROR: empty gold jsonl", file=sys.stderr)
        return 2

    patched: list[dict] = []
    for g in gold_rows:
        line_no = int(g["source_line"])
        if line_no < 1 or line_no > len(train):
            print(f"ERROR: source_line {line_no} out of range", file=sys.stderr)
            return 2
        idx = line_no - 1
        current = train[idx]
        gold_user = role(g["messages"], "user")
        train_user = role(current["messages"], "user")
        if gold_user != train_user:
            print(f"ERROR: user mismatch at train line {line_no}", file=sys.stderr)
            return 2
        gold_sys = role(g["messages"], "system")
        train_sys = role(current["messages"], "system")
        if gold_sys != train_sys:
            print(f"ERROR: system mismatch at train line {line_no}", file=sys.stderr)
            return 2
        new_msgs = [
            {"role": "system", "content": train_sys},
            {"role": "user", "content": train_user},
            {"role": "assistant", "content": role(g["messages"], "assistant")},
        ]
        train[idx] = {"messages": new_msgs}
        patched.append({"id": g.get("id"), "source_line": line_no, "slice": g.get("slice")})

    tmp = train_path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in train:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(train_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["gold_overlay"] = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "teacher": "cursor-session",
        "rows": len(patched),
        "source": "fine_tuning/data/qa_rewrite_pilot/qa_gold_rewrite_pilot.jsonl",
        "source_lines": [p["source_line"] for p in patched],
        "ids": [p["id"] for p in patched],
    }
    gaps = list(manifest.get("gaps") or [])
    note = (
        "20 train rows have inline-quote gold answers (qa_gold_rewrite_pilot); "
        "the rest still use original short answers / trailing citations."
    )
    if note not in gaps:
        gaps.append(note)
    manifest["gaps"] = gaps
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if pilot_manifest_path.exists():
        pm = json.loads(pilot_manifest_path.read_text(encoding="utf-8"))
        pm["merged_into_train"] = True
        pm["merged_at"] = datetime.now(timezone.utc).isoformat()
        pm["notes"] = [
            "Assistant-only rewrite; system and user copied byte-identical from sample.json.",
            "Merged into qa_mix_train.jsonl via merge_qa_gold_rewrite.py.",
            "Frozen test and val were not sampled or patched.",
        ]
        pilot_manifest_path.write_text(
            json.dumps(pm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    print(f"Patched {len(patched)} assistants in {train_path}")
    for p in patched:
        print(f"  {p['id']} line {p['source_line']} ({p['slice']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
