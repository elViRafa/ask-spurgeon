#!/usr/bin/env python3
"""Append qa_catechism_slice.jsonl onto qa_mix_train after RAG ingest.

Does not touch val/frozen test. Updates qa_mix_manifest.json.

Usage (repo root, after ingest_catechism.py succeeds):
  python fine_tuning/scripts/merge_catechism_qa_slice.py
  python fine_tuning/scripts/merge_catechism_qa_slice.py --slice fine_tuning/data/qa_catechism_variants.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl, repo_root  # noqa: E402

_Q_RE = re.compile(r"\[Puritan Catechism Q\.(\d+)")


def catechism_key(user: str) -> str:
    """Stable id: Q.N + QUESTION line (CONTEXT prefix is identical across rows)."""
    m = _Q_RE.search(user)
    qn = m.group(1) if m else "x"
    qline = ""
    for line in user.splitlines():
        if line.startswith("QUESTION:"):
            qline = line.strip()
            break
    return f"Q.{qn}|{qline}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Merge catechism CONTEXT slice into qa_mix_train")
    p.add_argument(
        "--slice",
        default="fine_tuning/data/qa_catechism_slice.jsonl",
        help="Side JSONL to append (overlay-safe).",
    )
    args = p.parse_args(argv)

    data = repo_root() / "fine_tuning" / "data"
    slice_path = Path(args.slice)
    if not slice_path.is_absolute():
        slice_path = repo_root() / slice_path
    train_path = data / "qa_mix_train.jsonl"
    manifest_path = data / "qa_mix_manifest.json"
    slice_manifest_path = slice_path.with_name(slice_path.stem + "_manifest.json")
    if not slice_manifest_path.exists():
        alt = data / "qa_catechism_slice_manifest.json"
        slice_manifest_path = alt if alt.exists() else slice_manifest_path

    if not slice_path.exists():
        print(f"ERROR: missing {slice_path}", file=sys.stderr)
        return 2
    rows = read_jsonl(slice_path)
    if not rows:
        print("ERROR: empty catechism slice", file=sys.stderr)
        return 2

    train = read_jsonl(train_path)
    existing_ids = {
        catechism_key(m.get("content") or "")
        for row in train
        for m in row.get("messages") or []
        if m.get("role") == "user" and "Puritan Catechism Q." in (m.get("content") or "")
    }
    added = 0
    answerable_add = 0
    refusal_add = 0
    for row in rows:
        user = next((m["content"] for m in row["messages"] if m["role"] == "user"), "")
        key = catechism_key(user)
        if key in existing_ids:
            continue
        train.append({"messages": row["messages"]})
        existing_ids.add(key)
        added += 1
        if row.get("slice") == "refusal":
            refusal_add += 1
        else:
            answerable_add += 1

    tmp = train_path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in train:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(train_path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    counts = dict(manifest.get("counts") or {})
    counts["train"] = len(train)
    manifest["counts"] = counts
    slices = dict(manifest.get("slices_train") or {})
    slices["answerable"] = int(slices.get("answerable") or 0) + answerable_add
    slices["refusal"] = int(slices.get("refusal") or 0) + refusal_add
    manifest["slices_train"] = slices
    train_n = len(train)
    refusal_n = int(slices.get("refusal") or 0)
    manifest["train_refusal_pct"] = round(100.0 * refusal_n / train_n, 2) if train_n else 0.0
    overlay_key = "catechism_overlay"
    prev = list(manifest.get("catechism_overlays") or [])
    if manifest.get(overlay_key) and manifest[overlay_key] not in prev:
        prev.append(manifest[overlay_key])
    entry = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "rows_added": added,
        "source": str(slice_path.relative_to(repo_root())).replace("\\", "/"),
        "rag": "fine_tuning/scripts/ingest_catechism.py",
    }
    prev.append(entry)
    manifest["catechism_overlays"] = prev
    manifest[overlay_key] = entry
    catechism_n = sum(
        1
        for row in train
        for m in row.get("messages") or []
        if m.get("role") == "user" and "Puritan Catechism Q." in (m.get("content") or "")
    )
    gaps = list(manifest.get("gaps") or [])
    gaps = [
        g
        for g in gaps
        if "Catechism CONTEXT slice" not in g and "catechism/confession" not in g.lower()
    ]
    gaps.append(
        f"Catechism CONTEXT slice merged ({catechism_n} train rows, "
        f"~{100.0 * catechism_n / train_n:.1f}%); RAG via ingest_catechism.py (Chroma)."
    )
    manifest["gaps"] = gaps
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if slice_manifest_path.exists():
        sm = json.loads(slice_manifest_path.read_text(encoding="utf-8"))
        sm["merge_into_train"] = True
        sm["merged_at"] = datetime.now(timezone.utc).isoformat()
        sm["rows_added"] = added
        slice_manifest_path.write_text(json.dumps(sm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Appended {added} catechism rows; train now {len(train)} (catechism~={catechism_n})")
    print("Re-run 12_package_kaggle_qa_mix.py and 13_sft_local_readiness.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
