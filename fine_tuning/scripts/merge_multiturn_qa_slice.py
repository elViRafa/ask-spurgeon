#!/usr/bin/env python3
"""Append qa_multiturn_slice.jsonl onto qa_mix_train (overlay-safe).

Does not touch val/frozen test or rewrite existing single-turn rows.
Updates qa_mix_manifest.json.

Usage (repo root):
  python fine_tuning/scripts/merge_multiturn_qa_slice.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl, repo_root  # noqa: E402


def row_key(row: dict) -> str:
    if row.get("id"):
        return str(row["id"])
    msgs = row.get("messages") or []
    raw = json.dumps(msgs, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def is_multiturn(row: dict) -> bool:
    msgs = row.get("messages") or []
    return len(msgs) > 3


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Merge multi-turn slice into qa_mix_train")
    p.add_argument(
        "--slice",
        default="fine_tuning/data/qa_multiturn_slice.jsonl",
        help="Side JSONL to append",
    )
    args = p.parse_args(argv)

    root = repo_root()
    data = root / "fine_tuning" / "data"
    slice_path = Path(args.slice)
    if not slice_path.is_absolute():
        slice_path = root / slice_path
    train_path = data / "qa_mix_train.jsonl"
    manifest_path = data / "qa_mix_manifest.json"
    slice_manifest_path = data / "qa_multiturn_slice_manifest.json"

    if not slice_path.exists():
        print(f"ERROR: missing {slice_path}", file=sys.stderr)
        return 2
    rows = read_jsonl(slice_path)
    if not rows:
        print("ERROR: empty multi-turn slice", file=sys.stderr)
        return 2

    train = read_jsonl(train_path)
    existing = {row_key(r) for r in train if is_multiturn(r)}
    # Also avoid duplicate message fingerprints.
    existing_fp = {
        hashlib.sha256(json.dumps(r.get("messages") or [], ensure_ascii=False).encode()).hexdigest()
        for r in train
        if is_multiturn(r)
    }

    added = 0
    for row in rows:
        if not is_multiturn(row):
            continue
        key = row_key(row)
        fp = hashlib.sha256(json.dumps(row.get("messages") or [], ensure_ascii=False).encode()).hexdigest()
        if key in existing or fp in existing_fp:
            continue
        train.append({"id": row.get("id"), "slice": "multiturn", "messages": row["messages"]})
        existing.add(key)
        existing_fp.add(fp)
        added += 1

    tmp = train_path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in train:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(train_path)

    multiturn_n = sum(1 for r in train if is_multiturn(r))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts = dict(manifest.get("counts") or {})
    counts["train"] = len(train)
    manifest["counts"] = counts
    slices = dict(manifest.get("slices_train") or {})
    slices["multiturn"] = multiturn_n
    manifest["slices_train"] = slices
    train_n = len(train)
    refusal_n = int(slices.get("refusal") or 0)
    if refusal_n:
        manifest["train_refusal_pct"] = round(100.0 * refusal_n / train_n, 2)
    entry = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "rows_added": added,
        "multiturn_total": multiturn_n,
        "source": str(slice_path.relative_to(root)).replace("\\", "/"),
    }
    prev = list(manifest.get("multiturn_overlays") or [])
    prev.append(entry)
    manifest["multiturn_overlays"] = prev
    manifest["multiturn_overlay"] = entry
    gaps = list(manifest.get("gaps") or [])
    gaps = [g for g in gaps if "multi-turn" not in g.lower() and "multiturn" not in g.lower()]
    gaps.append(
        f"Multi-turn slice merged ({multiturn_n} train rows, ~{100.0 * multiturn_n / train_n:.1f}%); "
        "shape mirrors build_chat_messages."
    )
    manifest["gaps"] = gaps
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if slice_manifest_path.exists():
        sm = json.loads(slice_manifest_path.read_text(encoding="utf-8"))
        sm["merge_into_train"] = True
        sm["merged_at"] = datetime.now(timezone.utc).isoformat()
        sm["rows_added"] = added
        slice_manifest_path.write_text(json.dumps(sm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Appended {added} multi-turn rows; train now {len(train)} (multiturn={multiturn_n})")
    print("Re-run 12_package_kaggle_qa_mix.py and 13_sft_local_readiness.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
