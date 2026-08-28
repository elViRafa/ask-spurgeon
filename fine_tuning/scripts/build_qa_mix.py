#!/usr/bin/env python3
"""
Build Spurgeon Q&A mix for SFT v2 (Fable 5 FN plan).

v1: reformats legacy spurgeon_qa_train_final.jsonl with canonical system prompt,
95/5 train/val split, frozen 100-question test set (50 answerable / 50 insufficient).

Outputs under fine_tuning/data/:
  - qa_mix_train.jsonl
  - qa_mix_val.jsonl
  - qa_test_frozen.jsonl
  - qa_mix_manifest.json

Usage (repo root):
  python fine_tuning/scripts/build_qa_mix.py
  python fine_tuning/scripts/build_qa_mix.py --input fine_tuning/data/spurgeon_qa_train_final.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REFUSAL_PATTERNS = (
    re.compile(r"does not contain", re.I),
    re.compile(r"could not find", re.I),
    re.compile(r"not contain enough", re.I),
    re.compile(r"cannot answer", re.I),
    re.compile(r"no relevant", re.I),
    re.compile(r"insufficient", re.I),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_system_prompt() -> str:
    try:
        sys.path.insert(0, str(repo_root()))
        from config import SPURGEON_SFT_SYSTEM_PROMPT

        return SPURGEON_SFT_SYSTEM_PROMPT
    except Exception:
        return (
            "You are Charles Haddon Spurgeon (1834–1892). Answer using only the "
            "information in the provided CONTEXT from your sermons."
        )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{i} invalid JSON: {e}") from e
    return rows


def is_refusal(example: dict) -> bool:
    msgs = example.get("messages") or []
    assistant = next((m["content"] for m in msgs if m.get("role") == "assistant"), "")
    return any(p.search(assistant) for p in REFUSAL_PATTERNS)


def normalize_example(raw: dict, system_prompt: str) -> dict | None:
    msgs = raw.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 3:
        return None
    by_role = {m.get("role"): m.get("content", "") for m in msgs if isinstance(m, dict)}
    if "user" not in by_role or "assistant" not in by_role:
        return None
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": by_role["user"]},
            {"role": "assistant", "content": by_role["assistant"]},
        ]
    }


def dedupe_key(example: dict) -> str:
    user = example["messages"][1]["content"]
    assistant = example["messages"][2]["content"]
    return hashlib.sha256((user + "\n---\n" + assistant).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build SFT qa_mix v1 from legacy JSONL")
    p.add_argument(
        "--input",
        default=str(repo_root() / "fine_tuning" / "data" / "spurgeon_qa_train_final.jsonl"),
    )
    p.add_argument("--output-dir", default=str(repo_root() / "fine_tuning" / "data"))
    p.add_argument("--seed", type=int, default=3407)
    p.add_argument("--val-frac", type=float, default=0.05)
    p.add_argument("--test-size", type=int, default=100)
    p.add_argument("--test-refusal-frac", type=float, default=0.5)
    args = p.parse_args(argv)

    inp = Path(args.input).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not inp.exists():
        print(f"ERROR: missing input {inp}", file=sys.stderr)
        return 2

    system_prompt = load_system_prompt()
    raw_rows = read_jsonl(inp)
    normalized: list[dict] = []
    seen: set[str] = set()
    dupes = 0
    skipped = 0

    for raw in raw_rows:
        ex = normalize_example(raw, system_prompt)
        if ex is None:
            skipped += 1
            continue
        key = dedupe_key(ex)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        normalized.append(ex)

    if len(normalized) < 200:
        print(f"ERROR: only {len(normalized)} examples after normalize/dedup", file=sys.stderr)
        return 2

    rng = random.Random(args.seed)
    rng.shuffle(normalized)

    refusals = [e for e in normalized if is_refusal(e)]
    answerable = [e for e in normalized if not is_refusal(e)]

    test_n = min(args.test_size, len(normalized))
    # Keep roughly half of scarce refusal rows for train/val (legacy set has ~1% refusals)
    n_refusal_test = min(
        len(refusals),
        max(1, int(round(test_n * args.test_refusal_frac))),
        max(1, len(refusals) // 2) if len(refusals) > 2 else len(refusals),
    )
    n_answerable_test = min(len(answerable), test_n - n_refusal_test)

    test_refusal = rng.sample(refusals, n_refusal_test) if n_refusal_test else []
    test_answerable = rng.sample(answerable, n_answerable_test) if n_answerable_test else []
    test_set = test_refusal + test_answerable
    test_keys = {dedupe_key(e) for e in test_set}

    pool = [e for e in normalized if dedupe_key(e) not in test_keys]
    rng.shuffle(pool)
    n_val = max(1, int(len(pool) * args.val_frac))
    val_set = pool[:n_val]
    train_set = pool[n_val:]

    slices = Counter()
    for e in train_set:
        slices["answerable" if not is_refusal(e) else "refusal"] += 1

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "qa_mix_v1",
        "source": str(inp.relative_to(repo_root())) if inp.is_relative_to(repo_root()) else str(inp),
        "source_sha256": sha256_file(inp),
        "system_prompt": "config.SPURGEON_SFT_SYSTEM_PROMPT",
        "counts": {
            "raw": len(raw_rows),
            "normalized": len(normalized),
            "deduped_dropped": dupes,
            "skipped": skipped,
            "train": len(train_set),
            "val": len(val_set),
            "test_frozen": len(test_set),
        },
        "slices_train": dict(slices),
        "test_composition": {
            "answerable": sum(1 for e in test_set if not is_refusal(e)),
            "refusal": sum(1 for e in test_set if is_refusal(e)),
        },
        "seed": args.seed,
    }

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    train_path = out_dir / "qa_mix_train.jsonl"
    val_path = out_dir / "qa_mix_val.jsonl"
    test_path = out_dir / "qa_test_frozen.jsonl"
    manifest_path = out_dir / "qa_mix_manifest.json"

    write_jsonl(train_path, train_set)
    write_jsonl(val_path, val_set)
    write_jsonl(test_path, test_set)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {train_path} ({len(train_set)} rows)")
    print(f"Wrote {val_path} ({len(val_set)} rows)")
    print(f"Wrote {test_path} ({len(test_set)} rows)")
    print(f"Wrote {manifest_path}")
    print("Train slices:", dict(slices))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
