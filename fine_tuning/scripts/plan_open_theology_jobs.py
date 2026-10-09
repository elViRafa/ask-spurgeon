#!/usr/bin/env python3
"""Plan the open-theology QA job queue (no network).

Builds fine_tuning/data/qa_open_theology/{catalog.json,jobs.jsonl,eval_jobs.jsonl,status.json}.
Does not call a teacher API. Does not touch qa_mix_train.jsonl.

Usage (repo root):
  python fine_tuning/scripts/plan_open_theology_jobs.py
  python fine_tuning/scripts/plan_open_theology_jobs.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

DOC_SEP = "<|endoftext|>"
SEED = 3407
PASSAGE_CHARS = 1600
MIN_PASSAGE = 400
TARGET_TRAIN = {"puritan": 150, "spurgeon": 100, "confession": 50}
TARGET_EVAL = {"puritan": 20, "spurgeon": 12, "confession": 8}
OUT_DIR = _REPO / "fine_tuning" / "data" / "qa_open_theology"
HOLDOUT_DIR = _REPO / "continued_pretrain" / "data" / "mix_v7" / "holdouts"

SERMON_TITLE_RE = re.compile(
    r"^#?\s*Sermon\s+(\d+)\s*\|\s*(.+?)\s*$",
    re.I | re.M,
)
SKIP_NAME_RE = re.compile(r"^(README|PROVENANCE|\.gitkeep)", re.I)


def repo_root() -> Path:
    return _REPO


def _clean_ws(text: str) -> str:
    text = re.sub(r"&mdash;", "—", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fingerprint(text: str, n: int = 200) -> str:
    return re.sub(r"\s+", " ", text).strip()[:n]


def load_holdout_fingerprints(holdout_dir: Path) -> dict[str, set[str]]:
    """Return per-bucket fingerprints (first 200 chars of each DOC_SEP part)."""
    out: dict[str, set[str]] = {
        "spurgeon": set(),
        "puritan": set(),
        "confession": set(),
        "general": set(),
    }
    if not holdout_dir.is_dir():
        return out
    for bucket in out:
        path = holdout_dir / f"{bucket}_holdout.txt"
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        for part in raw.split(DOC_SEP):
            fp = _fingerprint(part)
            if len(fp) >= 40:
                out[bucket].add(fp)
    return out


def load_spurgeon_holdout_numbers(holdout_dir: Path) -> set[int]:
    path = holdout_dir / "spurgeon_holdout.txt"
    nums: set[int] = set()
    if not path.exists():
        return nums
    raw = path.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"(?im)^Sermon\s+(\d+)\s*\|", raw):
        nums.add(int(m.group(1)))
    return nums


def chunk_text(text: str, size: int = PASSAGE_CHARS, min_len: int = MIN_PASSAGE) -> list[str]:
    text = _clean_ws(text)
    if len(text) < min_len:
        return []
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            # Prefer a sentence boundary near the cut.
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind(".\n"), window.rfind("? "))
            if cut >= min_len // 2:
                end = start + cut + 1
        piece = text[start:end].strip()
        if len(piece) >= min_len:
            chunks.append(piece)
        if end >= len(text):
            break
        start = end
    return chunks


def _title_case_work(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").strip().title()


_QUOTE_CHARS = "\"\u201c\u201d"


def clean_sermon_title(raw: str) -> str:
    """Canonical sermon title for catalog headings.

    Some sermon .md headers quote the title themselves (`# Sermon 2806 | "Jesus Our Lord"`,
    a scripture-phrase title). The heading template adds its own quotes, which produced
    `[Sermon 2806 — ""Jesus Our Lord""]`. Collapse doubled quotes and strip ONE wrapping
    pair when nothing else is quoted inside, so the heading is `[Sermon 2806 — "Jesus Our Lord"]`.
    Inner quotes (`How "The Unspeakable" is Spoken of`) are kept.
    """
    title = (raw or "").strip().strip("#").strip()
    while '""' in title:
        title = title.replace('""', '"')
    if len(title) >= 2 and title[0] in _QUOTE_CHARS and title[-1] in _QUOTE_CHARS:
        inner = title[1:-1].strip()
        if inner and not any(ch in inner for ch in _QUOTE_CHARS):
            title = inner
    return title


def sermon_heading(num: int | str, title: str) -> str:
    return f'[Sermon {num} — "{clean_sermon_title(title)}"]'


def scan_spurgeon(
    sermons_dir: Path,
    holdout_nums: set[int],
    holdout_fps: set[str],
) -> list[dict]:
    rows: list[dict] = []
    if not sermons_dir.is_dir():
        return rows
    for path in sorted(sermons_dir.rglob("*.md")):
        if SKIP_NAME_RE.match(path.name):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        m = SERMON_TITLE_RE.search(raw)
        if not m:
            continue
        num = int(m.group(1))
        title = clean_sermon_title(m.group(2))
        if num in holdout_nums:
            continue
        body = SERMON_TITLE_RE.sub("", raw, count=1)
        body = re.sub(r"^>\s*.+$", "", body, flags=re.M)  # drop blockquote scripture
        chunks = chunk_text(body)
        if not chunks:
            continue
        # Mid-sermon passage tends to carry doctrine; avoid pure openings when possible.
        passage = chunks[min(1, len(chunks) - 1)]
        if _fingerprint(passage) in holdout_fps:
            continue
        heading = sermon_heading(num, title)
        rel = path.relative_to(_REPO).as_posix()
        rows.append(
            {
                "work_id": f"spurgeon-{num}",
                "bucket": "spurgeon",
                "heading": heading,
                "source_path": rel,
                "passage": passage,
                "title": title,
            }
        )
    return rows


def scan_tree(
    root: Path,
    bucket: str,
    holdout_fps: set[str],
) -> list[dict]:
    rows: list[dict] = []
    if not root.is_dir():
        return rows
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        if SKIP_NAME_RE.match(path.name):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        cleaned = _clean_ws(raw)
        if _fingerprint(cleaned) in holdout_fps:
            continue
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            rel_parts = (path.name,)
        author = rel_parts[0] if len(rel_parts) > 1 else bucket
        work = path.stem
        author_label = _title_case_work(str(author))
        work_label = _title_case_work(work)
        heading = f"[{author_label} — {work_label}]"
        rel = path.relative_to(_REPO).as_posix()
        for i, passage in enumerate(chunk_text(cleaned)):
            if _fingerprint(passage) in holdout_fps:
                continue
            rows.append(
                {
                    "work_id": f"{bucket}-{path.stem}-{i}",
                    "bucket": bucket,
                    "heading": heading,
                    "source_path": rel,
                    "passage": passage,
                    "title": work_label,
                    "author": author_label,
                    "chunk_index": i,
                }
            )
    return rows


def scan_catechism(src: Path) -> list[dict]:
    rows: list[dict] = []
    if not src.exists():
        return rows
    raw = json.loads(src.read_text(encoding="utf-8"))
    for item in raw.get("Data") or []:
        n = int(item["Number"])
        q = str(item["Question"]).strip()
        a = str(item.get("AnswerWithProofs") or item["Answer"]).strip()
        heading = f'[Puritan Catechism Q.{n} — "Puritan Catechism"]'
        passage = f"Q. {q}\nA. {a}"
        if len(passage) < MIN_PASSAGE // 2:
            continue
        rows.append(
            {
                "work_id": f"catechism-{n:02d}",
                "bucket": "confession",  # counted with confession/catechism share
                "heading": heading,
                "source_path": src.relative_to(_REPO).as_posix(),
                "passage": passage,
                "title": f"Puritan Catechism Q.{n}",
            }
        )
    return rows


def _dedupe_by_work(candidates: list[dict], rng: random.Random) -> list[dict]:
    """Prefer one passage per source file / sermon, then shuffle."""
    by_key: dict[str, list[dict]] = {}
    for c in candidates:
        key = c["source_path"]
        by_key.setdefault(key, []).append(c)
    picked: list[dict] = []
    for paths in by_key.values():
        picked.append(rng.choice(paths))
    rng.shuffle(picked)
    return picked


def sample_bucket(
    candidates: list[dict],
    n_train: int,
    n_eval: int,
    rng: random.Random,
) -> tuple[list[dict], list[dict]]:
    pool = _dedupe_by_work(candidates, rng)
    need = n_train + n_eval
    if len(pool) < need:
        # Allow extra chunks from the same file when the shelf is thin.
        extras = [c for c in candidates if c not in pool]
        rng.shuffle(extras)
        for c in extras:
            if len(pool) >= need:
                break
            pool.append(c)
    if len(pool) < need:
        raise RuntimeError(
            f"bucket {candidates[0]['bucket'] if candidates else '?'} "
            f"has only {len(pool)} passages; need {need}"
        )
    train = pool[:n_train]
    eval_rows = pool[n_train : n_train + n_eval]
    return train, eval_rows


def build_job(rec: dict, job_id: str, role: str) -> dict:
    return {
        "job_id": job_id,
        "role": role,  # train | eval
        "work_id": rec["work_id"],
        "bucket": rec["bucket"],
        "heading": rec["heading"],
        "source_path": rec["source_path"],
        "passage": rec["passage"],
        "title": rec.get("title") or "",
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def plan(
    *,
    out_dir: Path,
    holdout_dir: Path,
    seed: int = SEED,
    dry_run: bool = False,
) -> dict:
    rng = random.Random(seed)
    holdout_fps = load_holdout_fingerprints(holdout_dir)
    holdout_nums = load_spurgeon_holdout_numbers(holdout_dir)

    spurgeon = scan_spurgeon(
        _REPO / "data" / "chspurgeon-sermons",
        holdout_nums,
        holdout_fps["spurgeon"],
    )
    puritan = scan_tree(
        _REPO / "data" / "puritans",
        "puritan",
        holdout_fps["puritan"],
    )
    confession = scan_tree(
        _REPO / "data" / "confessions",
        "confession",
        holdout_fps["confession"],
    )
    catechism = scan_catechism(_REPO / "data" / "catechism" / "puritan_catechism.json")
    confession_pool = confession + catechism

    train_jobs: list[dict] = []
    eval_jobs: list[dict] = []
    catalog: list[dict] = []

    for bucket, cands, n_tr, n_ev in (
        ("puritan", puritan, TARGET_TRAIN["puritan"], TARGET_EVAL["puritan"]),
        ("spurgeon", spurgeon, TARGET_TRAIN["spurgeon"], TARGET_EVAL["spurgeon"]),
        ("confession", confession_pool, TARGET_TRAIN["confession"], TARGET_EVAL["confession"]),
    ):
        tr, ev = sample_bucket(cands, n_tr, n_ev, rng)
        for i, rec in enumerate(tr):
            job = build_job(rec, f"train-{bucket}-{i:03d}", "train")
            train_jobs.append(job)
            catalog.append(
                {
                    "work_id": rec["work_id"],
                    "bucket": rec["bucket"],
                    "heading": rec["heading"],
                    "source_path": rec["source_path"],
                    "role": "train",
                    "job_id": job["job_id"],
                }
            )
        for i, rec in enumerate(ev):
            job = build_job(rec, f"eval-{bucket}-{i:03d}", "eval")
            eval_jobs.append(job)
            catalog.append(
                {
                    "work_id": rec["work_id"],
                    "bucket": rec["bucket"],
                    "heading": rec["heading"],
                    "source_path": rec["source_path"],
                    "role": "eval",
                    "job_id": job["job_id"],
                }
            )

    rng.shuffle(train_jobs)
    status = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "version": "qa_open_theology_v1",
        "targets": {"train": TARGET_TRAIN, "eval": TARGET_EVAL},
        "counts": {
            "train_jobs": len(train_jobs),
            "eval_jobs": len(eval_jobs),
            "catalog": len(catalog),
            "accepted": 0,
            "rejected": 0,
            "remaining": len(train_jobs),
        },
        "halted": False,
        "halt_reason": "",
        "last_error": "",
        "next_job_id": train_jobs[0]["job_id"] if train_jobs else "",
        "holdout_dir": holdout_dir.relative_to(_REPO).as_posix(),
        "spurgeon_holdout_sermons_skipped": len(holdout_nums),
        "candidate_pool": {
            "spurgeon": len(spurgeon),
            "puritan": len(puritan),
            "confession_files": len(confession),
            "catechism": len(catechism),
        },
    }

    summary = {
        "train_jobs": len(train_jobs),
        "eval_jobs": len(eval_jobs),
        "by_bucket_train": {
            b: sum(1 for j in train_jobs if j["bucket"] == b)
            for b in ("puritan", "spurgeon", "confession")
        },
        "out_dir": str(out_dir),
        "dry_run": dry_run,
    }

    if dry_run:
        return summary

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "catalog.json").write_text(
        json.dumps({"created_at": status["created_at"], "entries": catalog}, indent=2),
        encoding="utf-8",
    )
    write_jsonl(out_dir / "jobs.jsonl", train_jobs)
    write_jsonl(out_dir / "eval_jobs.jsonl", eval_jobs)
    (out_dir / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    # Empty campaign logs so Clerk can read them immediately.
    for name in ("accepted.jsonl", "rejected.jsonl"):
        path = out_dir / name
        if not path.exists():
            path.write_text("", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Plan open-theology QA jobs (no API)")
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--holdout-dir", default=str(HOLDOUT_DIR))
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and print counts; write nothing",
    )
    args = p.parse_args(argv)
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = _REPO / out_dir
    holdout_dir = Path(args.holdout_dir)
    if not holdout_dir.is_absolute():
        holdout_dir = _REPO / holdout_dir

    try:
        summary = plan(
            out_dir=out_dir,
            holdout_dir=holdout_dir,
            seed=args.seed,
            dry_run=args.dry_run,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2))
    if args.dry_run:
        print("DRY COMPLETE (no files written)")
    else:
        print(f"READY wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
