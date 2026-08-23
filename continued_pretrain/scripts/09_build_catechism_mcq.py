#!/usr/bin/env python3
"""
Build catechism MCQ items for C_eval_sota doctrine metric (Phase 3).

Parses Q/A style catechism text and emits JSON:
  [{"q": "...", "a": "...", "distractors": ["...", "...", "..."]}, ...]

Distractors = answers from other questions of the same set (seeded).

Usage:
  python continued_pretrain/scripts/09_build_catechism_mcq.py \\
    --wsc path/to/wsc.txt \\
    --heidelberg continued_pretrain/data/holdouts_manual/heidelberg_catechism.txt \\
    --out continued_pretrain/data/catechism_mcq.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path


# Common catechism patterns:
#   Q. 1. What is ...?
#   A. ...
#   Question 1: ...
#   Answer: ...
QA_PATTERNS = [
    re.compile(
        r"(?:^|\n)\s*(?:Q\.?|Question)\s*(?P<num>\d+)[.:)\s]+(?P<q>.+?)\n\s*"
        r"(?:A\.?|Answer)[.:)\s]+(?P<a>.+?)(?=\n\s*(?:Q\.?|Question)\s*\d+|\Z)",
        re.I | re.S,
    ),
]


def parse_catechism(text: str) -> list[dict]:
    items: list[dict] = []
    for pat in QA_PATTERNS:
        for m in pat.finditer(text):
            q = re.sub(r"\s+", " ", m.group("q")).strip()
            a = re.sub(r"\s+", " ", m.group("a")).strip()
            # Trim trailing junk
            a = re.split(r"\s{2,}Scripture|\nProof", a, maxsplit=1)[0].strip()
            if len(q) < 8 or len(a) < 8:
                continue
            if len(a) > 600:
                a = a[:600].rsplit(" ", 1)[0] + "…"
            items.append({"q": q, "a": a, "num": int(m.group("num"))})
    # Dedupe by num keeping first
    by_num: dict[int, dict] = {}
    for it in items:
        by_num.setdefault(it["num"], it)
    return [{"q": v["q"], "a": v["a"]} for _, v in sorted(by_num.items())]


def add_distractors(items: list[dict], n_distractors: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    out = []
    answers = [it["a"] for it in items]
    for i, it in enumerate(items):
        pool = [a for j, a in enumerate(answers) if j != i and a != it["a"]]
        if len(pool) < n_distractors:
            # allow fewer distractors
            distractors = pool
        else:
            distractors = rng.sample(pool, n_distractors)
        out.append({"q": it["q"], "a": it["a"], "distractors": distractors})
    return out


def load_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Build catechism MCQ JSON for CPT eval")
    p.add_argument("--wsc", default=None, help="Westminster Shorter Catechism text path")
    p.add_argument("--heidelberg", default=None, help="Heidelberg Catechism text path")
    p.add_argument(
        "--out",
        default=None,
        help="Output JSON path (default: continued_pretrain/data/catechism_mcq.json)",
    )
    p.add_argument("--cap", type=int, default=50, help="Max items per catechism")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    args = p.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    out = Path(args.out) if args.out else repo / "continued_pretrain" / "data" / "catechism_mcq.json"

    wsc_path = Path(args.wsc) if args.wsc else None
    # Default search
    if wsc_path is None:
        candidates = list((repo / "data" / "confessions").rglob("*shorter*")) + list(
            (repo / "data" / "confessions").rglob("*wsc*")
        )
        wsc_path = candidates[0] if candidates else None

    heid_path = Path(args.heidelberg) if args.heidelberg else (
        repo / "continued_pretrain" / "data" / "holdouts_manual" / "heidelberg_catechism.txt"
    )

    payload: dict = {"seed": args.seed, "sets": {}}

    for name, path in [("wsc", wsc_path), ("heidelberg", heid_path)]:
        if path is None or not Path(path).exists():
            print(f"NOTE: missing {name} at {path}")
            payload["sets"][name] = []
            continue
        raw = load_text(Path(path))
        items = parse_catechism(raw)
        items = items[: args.cap]
        items = add_distractors(items, 3, args.seed + hash(name) % 1000)
        payload["sets"][name] = items
        print(f"{name}: {len(items)} MCQ items from {path}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
