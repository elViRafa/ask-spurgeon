#!/usr/bin/env python3
"""
Build a multi-source theology CPT mix for SOTA continued pretraining (v2 / Fable 5).

Combines:
  - Spurgeon sermons (share-targeted weight; chunked ≤ max_chunk_chars)
  - Puritan texts under data/puritans/
  - Confessions / systematic under data/confessions/
  - Scripture under data/bible/
  - Optional general English replay (local .txt or HF sample)

Outputs (under continued_pretrain/data/ by default):
  - theology_mix_train.txt          # packed docs separated by <|endoftext|>
  - theology_mix_manifest.json      # shares, provenance, dedup report, verified fields
  - holdouts/{spurgeon,puritan,confession,general}_holdout.txt

v2 changes (PLAN_FABLE5_TO_IMPROVE_CPT.md):
  - Default max_chunk_chars=7000 (F1 truncation fix); Spurgeon also chunked
  - Guard: refuse Spurgeon-only mixes unless --allow-spurgeon-only (G2)
  - Cross-mix exact paragraph dedup + top-20 frequent paragraphs in manifest
  - --target-spurgeon-share auto-computes spurgeon_weight from other buckets
  - --keep-all-spurgeon (default): never subsample Spurgeon when weight<1; oversample
    other domain buckets to hold the share target (cap --max-other-weight)
  - Optional --author-tags for E1 conditioning headers

Does not overwrite spurgeon_train.txt or B_training.ipynb artifacts.

Usage (from repo root):
  python continued_pretrain/scripts/07_build_theology_mix.py
  python continued_pretrain/scripts/07_build_theology_mix.py --target-spurgeon-share 0.45 --replay-frac 0.10
  python continued_pretrain/scripts/07_build_theology_mix.py --allow-spurgeon-only  # diagnostics only
"""

from __future__ import annotations

import argparse
import fnmatch
import html
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# Mix denylist (relative to a bucket root, or **/glob). Henry commentary stays on disk
# for RAG but must not enter theology_mix train. See corpus_v3_catalog.json.
DEFAULT_EXCLUDE_GLOBS = [
    "henry/exposition*",
    "**/henry/exposition*",
]


DOC_SEP = "<|endoftext|>"
MIN_DOC_CHARS = 500
DEFAULT_SPURGEON_WEIGHT = 1.0  # v2: share-targeted; 2.5 only if deliberately oversampling
DEFAULT_REPLAY_FRAC = 0.10
DEFAULT_HOLDOUT_PER_BUCKET = 20
DEFAULT_SEED = 42
DEFAULT_MAX_CHUNK_CHARS = 7_000
DEFAULT_TARGET_SPURGEON_SHARE = 0.45
MIN_PARA_DEDUP_CHARS = 200
MAX_DOC_CHARS_WARN = 8_000


# ---------------------------------------------------------------------------
# Cleaning (aligned with 05_build_corpus.py + generic PD book cleanup)
# ---------------------------------------------------------------------------

def clean_md_sermon(raw_text: str) -> str:
    """Clean Spurgeon-style markdown sermons (same rules as 05_build_corpus)."""
    text = raw_text.replace("\r\n", "\n")
    text = html.unescape(text)

    lines = text.splitlines()
    total_lines = len(lines)
    scan_start = max(0, total_lines - 25)
    truncate_idx = None

    footer_patterns = [
        re.compile(r"portion\s+of\s+scripture\s+read", re.I),
        re.compile(r"portions\s+of\s+scripture\s+read", re.I),
        re.compile(r"hymns\s+from", re.I),
        re.compile(r"pray\s+the\s+holy\s+spirit\s+will\s+use", re.I),
        re.compile(r"adapted\s+from\s+the\s+c\.\s*h\.\s*spurgeon\s+collection", re.I),
        re.compile(r"the\s+tongue\s+of\s+the\s+wicked\s+has\s+assailed", re.I),
        re.compile(r"passmore\s*&\s*alabaster", re.I),
        re.compile(r"published\s+by\s+passmore", re.I),
        re.compile(r"london:\s+passmore", re.I),
    ]

    for i in range(scan_start, total_lines):
        line = lines[i]
        if any(p.search(line) for p in footer_patterns):
            truncate_idx = i
            break

    if truncate_idx is not None:
        text = "\n".join(lines[:truncate_idx])

    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", text)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"\[\^[^\]]+\]", "", text)
    text = re.sub(r"^\[\^[^\]]+\]:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^(SERMON\s+)?NO\.\s*\d+\.?\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^Volume\s+[IVXLCDM\d]+\.?\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_generic_text(raw_text: str) -> str:
    """Light cleanup for .txt / .md books (Puritans, confessions, Bible, replay)."""
    text = raw_text.replace("\r\n", "\n")
    text = html.unescape(text)

    gutenberg_start = re.search(
        r"\*\*\*\s*START OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text,
        re.I | re.S,
    )
    if gutenberg_start:
        text = text[gutenberg_start.end() :]
    gutenberg_end = re.search(
        r"\*\*\*\s*END OF (THIS|THE) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        text,
        re.I | re.S,
    )
    if gutenberg_end:
        text = text[: gutenberg_end.start()]

    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)
    text = text.replace("\f", "\n\n")
    text = re.sub(r"^\s*page\s+\d+\s*$", "", text, flags=re.MULTILINE | re.I)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_long_text(text: str, max_chars: int = DEFAULT_MAX_CHUNK_CHARS, min_chars: int = MIN_DOC_CHARS) -> list[str]:
    """Split long docs into paragraph-bounded chunks (F1: default ≤7000 chars)."""
    if len(text) <= max_chars:
        return [text] if len(text) >= min_chars else []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    buf: list[str] = []
    buf_len = 0

    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        # Hard-split oversized single paragraphs
        if len(p) > max_chars:
            if buf:
                chunk = "\n\n".join(buf).strip()
                if len(chunk) >= min_chars:
                    chunks.append(chunk)
                buf, buf_len = [], 0
            for i in range(0, len(p), max_chars):
                piece = p[i : i + max_chars].strip()
                if len(piece) >= min_chars:
                    chunks.append(piece)
            continue
        if buf_len + len(p) + 2 > max_chars and buf:
            chunk = "\n\n".join(buf).strip()
            if len(chunk) >= min_chars:
                chunks.append(chunk)
            buf = [p]
            buf_len = len(p)
        else:
            buf.append(p)
            buf_len += len(p) + 2

    if buf:
        chunk = "\n\n".join(buf).strip()
        if len(chunk) >= min_chars:
            chunks.append(chunk)
    return chunks


def normalize_paragraph(p: str) -> str:
    return re.sub(r"\s+", " ", p.strip().lower())


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------

@dataclass
class Doc:
    text: str
    bucket: str  # spurgeon | puritan | confession | bible | general
    source: str
    author: str = "unknown"
    work: str = ""

    @property
    def n_chars(self) -> int:
        return len(self.text)


@dataclass
class MixStats:
    bucket_docs: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    bucket_chars: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    train_docs: int = 0
    train_chars: int = 0
    holdout_docs: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def iter_text_files(root: Path) -> Iterator[Path]:
    if not root.exists():
        return
    skip_names = {"readme.md", "license", "license.md", ".gitkeep", "provenance.md"}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.lower() in skip_names:
            continue
        if path.suffix.lower() in {".md", ".txt"}:
            yield path


def path_excluded(path: Path, root: Path, globs: list[str]) -> bool:
    """Match exclude globs against filename, path-relative-to-bucket, and posix path."""
    if not globs:
        return False
    rel = path.relative_to(root).as_posix() if root in path.parents or path.parent == root else path.name
    candidates = [path.name, rel, path.as_posix().replace("\\", "/")]
    for g in globs:
        pat = g.replace("\\", "/")
        for c in candidates:
            if fnmatch.fnmatch(c, pat):
                return True
            if pat.startswith("**/") and fnmatch.fnmatch(c, pat[3:]):
                return True
            if "/" in c and fnmatch.fnmatch(c.split("/", 1)[-1], pat):
                return True
    return False


def load_spurgeon_from_concat(
    train_txt: Path,
    bucket: str = "spurgeon",
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> list[Doc]:
    if not train_txt.exists():
        print(f"WARNING: Spurgeon train file missing: {train_txt}")
        return []
    raw = train_txt.read_text(encoding="utf-8", errors="replace")
    docs: list[Doc] = []
    for i, part in enumerate(raw.split(DOC_SEP)):
        text = part.strip()
        if len(text) < MIN_DOC_CHARS:
            continue
        for j, chunk in enumerate(split_long_text(text, max_chars=max_chunk_chars)):
            src = f"{train_txt.name}#{i}" if j == 0 else f"{train_txt.name}#{i}.{j}"
            docs.append(
                Doc(text=chunk, bucket=bucket, source=src, author="spurgeon", work="sermons")
            )
    return docs


def load_tree(
    root: Path,
    bucket: str,
    cleaner,
    default_author: str = "unknown",
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    exclude_globs: list[str] | None = None,
) -> list[Doc]:
    if not root.exists():
        print(f"NOTE: optional source dir missing (skipping): {root}")
        return []

    docs: list[Doc] = []
    seen: set[str] = set()
    skipped = 0
    for path in iter_text_files(root):
        if path_excluded(path, root, exclude_globs or []):
            skipped += 1
            print(f"  exclude from mix: {path}")
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        try:
            rel = path.relative_to(root)
            author = rel.parts[0] if len(rel.parts) > 1 else default_author
            work = path.stem if path.stem else path.name
            if len(rel.parts) > 1:
                work = rel.parts[-1]
                if work.endswith(path.suffix):
                    work = path.stem
        except ValueError:
            author = default_author
            work = path.stem

        cleaned = cleaner(raw)
        if not cleaned:
            continue
        fingerprint = cleaned[:300]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)

        for j, chunk in enumerate(split_long_text(cleaned, max_chars=max_chunk_chars)):
            docs.append(
                Doc(
                    text=chunk,
                    bucket=bucket,
                    source=f"{path.as_posix()}#{j}" if j else path.as_posix(),
                    author=str(author),
                    work=str(work),
                )
            )
    if skipped:
        print(f"  excluded {skipped} file(s) under {root} via denylist")
    return docs


def load_replay_hf(dataset_name: str, split: str, text_field: str, n_docs: int, seed: int) -> list[Doc]:
    try:
        from datasets import load_dataset
    except ImportError:
        print("WARNING: `datasets` not installed; cannot load HF replay. Install or use --replay-txt.")
        return []

    print(f"Loading HF replay sample: {dataset_name} ({n_docs} docs)...")
    try:
        ds = load_dataset(dataset_name, split=split, streaming=True)
        docs: list[Doc] = []
        rng = random.Random(seed)
        buffer: list[str] = []
        for i, row in enumerate(ds):
            text = row.get(text_field) or row.get("text") or ""
            text = clean_generic_text(str(text))
            if len(text) < MIN_DOC_CHARS:
                continue
            buffer.append(text)
            if len(buffer) >= n_docs * 5:
                break
            if i > n_docs * 50:
                break
        if not buffer:
            return []
        chosen = buffer if len(buffer) <= n_docs else rng.sample(buffer, n_docs)
        for i, t in enumerate(chosen):
            for j, chunk in enumerate(split_long_text(t, max_chars=DEFAULT_MAX_CHUNK_CHARS)):
                docs.append(
                    Doc(
                        text=chunk,
                        bucket="general",
                        source=f"{dataset_name}#{i}.{j}",
                        author="general",
                        work="replay",
                    )
                )
        return docs
    except Exception as exc:
        print(f"WARNING: HF replay load failed: {exc}")
        return []


def load_replay_txt(path: Path, max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS) -> list[Doc]:
    if not path.exists():
        print(f"WARNING: replay txt missing: {path}")
        return []
    raw = path.read_text(encoding="utf-8", errors="replace")
    docs: list[Doc] = []
    if DOC_SEP in raw:
        parts = raw.split(DOC_SEP)
    else:
        parts = split_long_text(clean_generic_text(raw), max_chars=max_chunk_chars)
        return [
            Doc(text=p, bucket="general", source=f"{path.name}#{i}", author="general", work="replay")
            for i, p in enumerate(parts)
        ]

    for i, part in enumerate(parts):
        text = clean_generic_text(part)
        if len(text) < MIN_DOC_CHARS:
            continue
        for j, chunk in enumerate(split_long_text(text, max_chars=max_chunk_chars)):
            docs.append(
                Doc(
                    text=chunk,
                    bucket="general",
                    source=f"{path.name}#{i}.{j}",
                    author="general",
                    work="replay",
                )
            )
    return docs


# ---------------------------------------------------------------------------
# Mix logic
# ---------------------------------------------------------------------------

def subsample_by_chars(docs: list[Doc], target_chars: int, rng: random.Random) -> list[Doc]:
    """Shuffle and take docs until cumulative chars ≈ target_chars."""
    if not docs or target_chars <= 0:
        return []
    order = list(docs)
    rng.shuffle(order)
    out: list[Doc] = []
    acc = 0
    for d in order:
        out.append(d)
        acc += d.n_chars
        if acc >= target_chars:
            break
    return out


def oversample(docs: list[Doc], weight: float, rng: random.Random) -> list[Doc]:
    """Repeat list floor(weight) times, then sample fractional remainder.

    ``weight<1`` subsamples by chars (drops most of the list). Prefer
    ``--keep-all-spurgeon`` for the Spurgeon bucket so sermons are not silently dropped.
    """
    if not docs:
        return []
    if weight <= 0:
        return []
    total_chars = sum(d.n_chars for d in docs)
    if weight < 1.0:
        target = max(MIN_DOC_CHARS, int(round(total_chars * weight)))
        return subsample_by_chars(docs, target, rng)
    if weight == 1.0:
        return list(docs)

    full = int(weight)
    frac = weight - full
    out: list[Doc] = []
    for _ in range(full):
        out.extend(docs)
    if frac > 0:
        target = max(MIN_DOC_CHARS, int(round(total_chars * frac)))
        out.extend(subsample_by_chars(docs, target, rng))
    return out


def compute_spurgeon_weight(
    spurgeon_chars: int,
    other_chars: int,
    target_share: float,
) -> float:
    """
    spurgeon_weight so that after weighting:
      (w * S) / (w * S + O) ≈ target_share
    => w = target_share * O / (S * (1 - target_share))
    """
    if spurgeon_chars <= 0 or other_chars <= 0:
        return 1.0
    if not (0.05 < target_share < 0.95):
        raise ValueError(f"target_spurgeon_share must be in (0.05, 0.95), got {target_share}")
    w = target_share * other_chars / (spurgeon_chars * (1.0 - target_share))
    # Allow deep undersampling when other buckets are still small (no artificial 0.05 floor
    # that would blow past the target share). Cap upside only.
    return max(0.01, min(w, 10.0))


def other_weight_for_keep_all_spurgeon(
    spurgeon_chars: int,
    other_chars: int,
    target_share: float,
    max_weight: float = 5.0,
) -> tuple[float, bool]:
    """Weight for non-Spurgeon domain buckets so S / (S + w*O) ≈ target_share.

    Used when we refuse to subsample Spurgeon (weight would have been < 1). Repeating
    others holds the share target instead of silently dropping ~84% of sermons.
    Returns (weight, capped). If others are too small, weight is capped and actual
    Spurgeon share will exceed ``target_share``.
    """
    if spurgeon_chars <= 0 or other_chars <= 0:
        return 1.0, False
    if not (0.05 < target_share < 0.95):
        raise ValueError(f"target_spurgeon_share must be in (0.05, 0.95), got {target_share}")
    needed_other = spurgeon_chars * (1.0 - target_share) / target_share
    w = needed_other / other_chars
    if w <= 1.0:
        return 1.0, False
    if w > max_weight:
        return float(max_weight), True
    return float(w), False


def take_holdout(docs: list[Doc], n: int, rng: random.Random) -> tuple[list[Doc], list[Doc]]:
    if n <= 0 or not docs:
        return list(docs), []
    if len(docs) < n * 2:
        return list(docs), []
    holdout = rng.sample(docs, min(n, max(1, len(docs) // 5)))
    hold_ids = {id(d) for d in holdout}
    train = [d for d in docs if id(d) not in hold_ids]
    return train, holdout


def dedup_paragraphs(docs: list[Doc]) -> tuple[list[Doc], dict]:
    """
    Exact-duplicate paragraph removal across the mix (normalized paras ≥ 200 chars).
    Keeps first occurrence; rebuilds each doc without dropped paras.
    """
    seen: set[str] = set()
    para_counter: Counter[str] = Counter()
    out: list[Doc] = []
    dropped_paras = 0
    dropped_docs = 0

    for d in docs:
        paras = [p.strip() for p in re.split(r"\n\s*\n", d.text) if p.strip()]
        kept: list[str] = []
        for p in paras:
            key = normalize_paragraph(p)
            if len(key) >= MIN_PARA_DEDUP_CHARS:
                para_counter[key] += 1
                if key in seen:
                    dropped_paras += 1
                    continue
                seen.add(key)
            kept.append(p)
        if not kept:
            dropped_docs += 1
            continue
        new_text = "\n\n".join(kept).strip()
        if len(new_text) < MIN_DOC_CHARS:
            dropped_docs += 1
            continue
        out.append(
            Doc(
                text=new_text,
                bucket=d.bucket,
                source=d.source,
                author=d.author,
                work=d.work,
            )
        )

    top20 = [
        {"preview": k[:160], "count": c, "chars": len(k)}
        for k, c in para_counter.most_common(20)
        if c > 1
    ]
    report = {
        "dropped_duplicate_paragraphs": dropped_paras,
        "dropped_docs_after_dedup": dropped_docs,
        "docs_in": len(docs),
        "docs_out": len(out),
        "unique_long_paragraphs": len(seen),
        "top_frequent_paragraphs": top20,
    }
    return out, report


def apply_author_tags(docs: list[Doc]) -> list[Doc]:
    tagged: list[Doc] = []
    for d in docs:
        author = d.author.replace("_", " ").title() if d.author else "Unknown"
        work = (d.work or d.source).replace("_", " ")
        header = f"[AUTHOR: {author}] [WORK: {work}]\n\n"
        tagged.append(
            Doc(
                text=header + d.text,
                bucket=d.bucket,
                source=d.source,
                author=d.author,
                work=d.work,
            )
        )
    return tagged


def write_concat(path: Path, docs: list[Doc]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(d.text.strip())
            f.write(f"\n{DOC_SEP}\n\n")


def approx_tokens(n_chars: int) -> int:
    return n_chars // 4


def non_empty_domain_buckets(spurgeon, puritan, confession, bible) -> list[str]:
    buckets = []
    if spurgeon:
        buckets.append("spurgeon")
    if puritan:
        buckets.append("puritan")
    if confession:
        buckets.append("confession")
    if bible:
        buckets.append("bible")
    return buckets


def build_mix(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    base = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else base / "continued_pretrain" / "data"
    holdout_dir = out_dir / "holdouts"
    holdout_dir.mkdir(parents=True, exist_ok=True)
    max_chunk = int(args.max_chunk_chars)

    spurgeon_train = Path(args.spurgeon_train) if args.spurgeon_train else (
        base / "continued_pretrain" / "data" / "spurgeon_train.txt"
    )
    spurgeon_holdout_src = Path(args.spurgeon_holdout) if args.spurgeon_holdout else (
        base / "continued_pretrain" / "data" / "spurgeon_holdout.txt"
    )

    puritan_root = Path(args.puritans_dir) if args.puritans_dir else base / "data" / "puritans"
    confession_root = Path(args.confessions_dir) if args.confessions_dir else base / "data" / "confessions"
    bible_root = Path(args.bible_dir) if args.bible_dir else base / "data" / "bible"
    hymns_root = Path(args.hymns_dir) if args.hymns_dir else base / "data" / "hymns"
    replay_txt = Path(args.replay_txt) if args.replay_txt else None
    exclude_globs = list(DEFAULT_EXCLUDE_GLOBS) + list(args.exclude_glob or [])

    # --- Load domain buckets (all chunked) ---
    spurgeon_docs = load_spurgeon_from_concat(spurgeon_train, max_chunk_chars=max_chunk)
    puritan_docs = load_tree(
        puritan_root,
        "puritan",
        clean_generic_text,
        default_author="puritan",
        max_chunk_chars=max_chunk,
        exclude_globs=exclude_globs,
    )
    hymn_docs = load_tree(
        hymns_root,
        "puritan",
        clean_generic_text,
        default_author="hymns",
        max_chunk_chars=max_chunk,
        exclude_globs=exclude_globs,
    )
    if hymn_docs:
        print(f"Folded {len(hymn_docs)} hymn docs into puritan bucket from {hymns_root}")
        puritan_docs.extend(hymn_docs)
    confession_docs = load_tree(
        confession_root,
        "confession",
        clean_generic_text,
        default_author="confession",
        max_chunk_chars=max_chunk,
        exclude_globs=exclude_globs,
    )
    bible_docs = load_tree(
        bible_root,
        "bible",
        clean_generic_text,
        default_author="scripture",
        max_chunk_chars=max_chunk,
        exclude_globs=exclude_globs,
    )

    print(
        f"Loaded raw docs — spurgeon={len(spurgeon_docs)}, puritan={len(puritan_docs)}, "
        f"confession={len(confession_docs)}, bible={len(bible_docs)} "
        f"(max_chunk_chars={max_chunk})"
    )

    domain_buckets = non_empty_domain_buckets(spurgeon_docs, puritan_docs, confession_docs, bible_docs)
    if len(domain_buckets) < 2 and not args.allow_spurgeon_only:
        print(
            "ERROR: multi-source SOTA mix requires ≥2 domain buckets "
            f"(found {domain_buckets or 'none'}). "
            "Add files under data/puritans, data/confessions, and/or data/bible, "
            "or pass --allow-spurgeon-only for diagnostics.\n"
            "See data/SOURCES_SOTA_CPT.md and scripts/08_fetch_pd_sources.py."
        )
        sys.exit(2)
    if len(domain_buckets) < 2 and args.allow_spurgeon_only:
        print("WARNING: --allow-spurgeon-only: building Spurgeon(+replay)-only mix (NOT for flagship v2).")

    # --- Holdouts (domain) ---
    if spurgeon_holdout_src.exists():
        spurgeon_holdout = load_spurgeon_from_concat(
            spurgeon_holdout_src, bucket="spurgeon", max_chunk_chars=max_chunk
        )
        hold_fps = {d.text[:200] for d in spurgeon_holdout}
        spurgeon_train_docs = [d for d in spurgeon_docs if d.text[:200] not in hold_fps]
    else:
        spurgeon_train_docs, spurgeon_holdout = take_holdout(
            spurgeon_docs, args.holdout_per_bucket, rng
        )

    puritan_train, puritan_holdout = take_holdout(puritan_docs, args.holdout_per_bucket, rng)
    confession_train, confession_holdout = take_holdout(
        confession_docs, max(5, args.holdout_per_bucket // 2), rng
    )

    # --- Cap secondary buckets (plan: bible 2–4%, confessions 3–6%), then size Spurgeon ---
    spurgeon_chars = sum(d.n_chars for d in spurgeon_train_docs)
    puritan_chars = sum(d.n_chars for d in puritan_train)

    def _cap_bucket_to_final_share(
        docs: list[Doc],
        max_share: float | None,
        fixed_other_chars: int,
        label: str,
    ) -> list[Doc]:
        """Cap docs so final share ≤ max_share given Spurgeon target S and fixed other chars."""
        if not docs or not max_share or max_share <= 0 or not args.target_spurgeon_share:
            return list(docs)
        S = float(args.target_spurgeon_share)
        m = float(max_share)
        other_share = max(1e-6, 1.0 - S)
        frac_of_other = min(0.95, m / other_share)
        if frac_of_other >= 1.0 or fixed_other_chars <= 0:
            return list(docs)
        max_chars = int((frac_of_other / max(1e-6, 1.0 - frac_of_other)) * fixed_other_chars)
        cur = sum(d.n_chars for d in docs)
        if cur > max_chars > 0:
            capped = subsample_by_chars(docs, max_chars, rng)
            print(
                f"Capped {label}: {cur:,} -> {sum(d.n_chars for d in capped):,} chars "
                f"(max_{label}_share={m})"
            )
            return capped
        return list(docs)

    # Prefer keeping short confessions fully; only subsample Institutes-heavy sets via char budget.
    capped_confession = _cap_bucket_to_final_share(
        confession_train,
        getattr(args, "max_confession_share", 0.06),
        puritan_chars,
        "confession",
    )
    confession_chars = sum(d.n_chars for d in capped_confession)
    non_bible_other_chars = puritan_chars + confession_chars

    capped_bible = list(bible_docs)
    if args.max_bible_share and bible_docs:
        capped_bible = _cap_bucket_to_final_share(
            bible_docs, args.max_bible_share, non_bible_other_chars, "bible"
        )
        if non_bible_other_chars == 0 and bible_docs:
            max_bible_chars = max(MIN_DOC_CHARS, int(0.1 * sum(d.n_chars for d in bible_docs)))
            capped_bible = subsample_by_chars(bible_docs, max_bible_chars, rng)

    other_chars = non_bible_other_chars + sum(d.n_chars for d in capped_bible)

    if args.spurgeon_weight is not None:
        spurgeon_weight = float(args.spurgeon_weight)
        weight_mode = "explicit"
    elif other_chars > 0 and args.target_spurgeon_share is not None:
        spurgeon_weight = compute_spurgeon_weight(
            spurgeon_chars, other_chars, float(args.target_spurgeon_share)
        )
        weight_mode = f"target_share={args.target_spurgeon_share}"
    else:
        spurgeon_weight = DEFAULT_SPURGEON_WEIGHT
        weight_mode = "default_no_other_buckets"

    print(
        f"Spurgeon weight={spurgeon_weight:.4f} ({weight_mode}); "
        f"spurgeon_chars={spurgeon_chars:,} other_domain_chars={other_chars:,}"
    )

    other_bucket_weight = 1.0
    other_weight_capped = False
    spurgeon_keep_all = False

    if args.spurgeon_weight is not None:
        spurgeon_weighted = oversample(spurgeon_train_docs, spurgeon_weight, rng)
    elif args.keep_all_spurgeon and spurgeon_weight < 1.0:
        spurgeon_keep_all = True
        spurgeon_weighted = list(spurgeon_train_docs)
        other_bucket_weight, other_weight_capped = other_weight_for_keep_all_spurgeon(
            spurgeon_chars,
            other_chars,
            float(args.target_spurgeon_share),
            max_weight=float(args.max_other_weight),
        )
        print(
            f"keep-all Spurgeon: keeping {len(spurgeon_weighted)} docs / {spurgeon_chars:,} chars; "
            f"other_bucket_weight={other_bucket_weight:.4f}"
            + (" (CAPPED — Spurgeon share will exceed target)" if other_weight_capped else "")
        )
        if other_bucket_weight > 1.0:
            puritan_train = oversample(puritan_train, other_bucket_weight, rng)
            capped_confession = oversample(capped_confession, other_bucket_weight, rng)
            capped_bible = oversample(capped_bible, other_bucket_weight, rng)
    else:
        if spurgeon_weight < 1.0:
            print(
                f"WARNING: Spurgeon weight={spurgeon_weight:.4f} < 1 subsamples by chars "
                "(~most sermons dropped). Pass --keep-all-spurgeon to keep every chunk "
                "and oversample others instead."
            )
        spurgeon_weighted = oversample(spurgeon_train_docs, spurgeon_weight, rng)
    domain_pool = spurgeon_weighted + puritan_train + capped_confession + capped_bible
    if not domain_pool:
        print("ERROR: no domain documents found. Build spurgeon_train.txt and/or add data under data/puritans etc.")
        sys.exit(1)

    domain_chars = sum(d.n_chars for d in domain_pool)

    # --- Replay ---
    general_docs: list[Doc] = []
    if replay_txt:
        general_docs = load_replay_txt(replay_txt, max_chunk_chars=max_chunk)
    elif args.replay_hf and args.replay_frac > 0:
        target_replay_chars = int((args.replay_frac / max(1e-6, 1.0 - args.replay_frac)) * domain_chars)
        n_docs = max(50, target_replay_chars // 4000)
        general_docs = load_replay_hf(
            dataset_name=args.replay_hf,
            split=args.replay_split,
            text_field=args.replay_text_field,
            n_docs=n_docs,
            seed=args.seed,
        )

    general_train, general_holdout = take_holdout(
        general_docs, min(20, max(5, args.holdout_per_bucket // 2)), rng
    )

    if args.replay_frac > 0 and general_train:
        g_chars = sum(d.n_chars for d in general_train)
        target = int((args.replay_frac / max(1e-6, 1.0 - args.replay_frac)) * domain_chars)
        if g_chars > target and g_chars > 0:
            rng.shuffle(general_train)
            acc = 0
            kept: list[Doc] = []
            for d in general_train:
                kept.append(d)
                acc += d.n_chars
                if acc >= target:
                    break
            general_train = kept
        elif g_chars < target and g_chars > 0:
            weight = target / g_chars
            general_train = oversample(general_train, min(weight, 5.0), rng)

    train_docs = domain_pool + general_train

    # --- Paragraph dedup (1d) ---
    train_docs, dedup_report = dedup_paragraphs(train_docs)
    print(
        f"Paragraph dedup: {dedup_report['docs_in']} -> {dedup_report['docs_out']} docs, "
        f"dropped_paras={dedup_report['dropped_duplicate_paragraphs']}"
    )

    if args.author_tags:
        train_docs = apply_author_tags(train_docs)
        print("Applied [AUTHOR]/ [WORK:] tags (E1).")

    rng.shuffle(train_docs)

    # Max-doc size check
    oversize = [d for d in train_docs if d.n_chars > MAX_DOC_CHARS_WARN]
    if oversize:
        print(
            f"WARNING: {len(oversize)} docs exceed {MAX_DOC_CHARS_WARN} chars "
            f"(max={max(d.n_chars for d in oversize)}); expected none after chunking."
        )

    # --- Write outputs ---
    train_path = out_dir / "theology_mix_train.txt"
    write_concat(train_path, train_docs)

    write_concat(holdout_dir / "spurgeon_holdout.txt", spurgeon_holdout)
    write_concat(holdout_dir / "puritan_holdout.txt", puritan_holdout)
    write_concat(holdout_dir / "confession_holdout.txt", confession_holdout)
    write_concat(holdout_dir / "general_holdout.txt", general_holdout)

    stats = MixStats()
    for d in train_docs:
        stats.bucket_docs[d.bucket] += 1
        stats.bucket_chars[d.bucket] += d.n_chars
    stats.train_docs = len(train_docs)
    stats.train_chars = sum(d.n_chars for d in train_docs)
    stats.holdout_docs = {
        "spurgeon": len(spurgeon_holdout),
        "puritan": len(puritan_holdout),
        "confession": len(confession_holdout),
        "general": len(general_holdout),
    }

    total_chars = max(1, stats.train_chars)
    bucket_share = {
        b: {
            "docs": stats.bucket_docs[b],
            "chars": stats.bucket_chars[b],
            "approx_tokens": approx_tokens(stats.bucket_chars[b]),
            "char_share": round(stats.bucket_chars[b] / total_chars, 4),
        }
        for b in sorted(stats.bucket_docs.keys())
    }

    max_doc_chars = max((d.n_chars for d in train_docs), default=0)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "plan": "PLAN_FABLE5_TO_IMPROVE_CPT v2",
        "max_chunk_chars": max_chunk,
        "spurgeon_weight": round(spurgeon_weight, 6),
        "spurgeon_weight_mode": weight_mode,
        "spurgeon_keep_all": spurgeon_keep_all,
        "other_bucket_weight": round(other_bucket_weight, 6),
        "other_weight_capped": other_weight_capped,
        "target_spurgeon_share": args.target_spurgeon_share,
        "replay_frac_target": args.replay_frac,
        "allow_spurgeon_only": bool(args.allow_spurgeon_only),
        "author_tags": bool(args.author_tags),
        "doc_separator": DOC_SEP,
        "train_path": str(train_path),
        "train_docs": stats.train_docs,
        "train_chars": stats.train_chars,
        "train_approx_tokens": approx_tokens(stats.train_chars),
        "max_doc_chars": max_doc_chars,
        "docs_over_8k_chars": len(oversize),
        "buckets": bucket_share,
        "domain_buckets_present": domain_buckets,
        "holdouts": stats.holdout_docs,
        "dedup": dedup_report,
        "sources": {
            "spurgeon_train": str(spurgeon_train),
            "puritans_dir": str(puritan_root),
            "confessions_dir": str(confession_root),
            "bible_dir": str(bible_root),
            "hymns_dir": str(hymns_root),
            "exclude_globs": exclude_globs,
            "replay_txt": str(replay_txt) if replay_txt else None,
            "replay_hf": args.replay_hf if not replay_txt else None,
        },
        "notes": [
            "approx_tokens uses chars/4; run 06_verify_tokens.py --mix to fill verified_tokens.",
            "Heidelberg Catechism + Belgic Confession belong in continued_pretrain/data/holdouts_manual/ (not training dirs).",
            "Flagship base: Qwen3.5-4B-Base (see plan §4.1). Baseline Spurgeon path remains B_training.ipynb.",
        ],
    }

    manifest_path = out_dir / "theology_mix_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("=" * 60)
    print("Theology mix built (v2)")
    print(f"  Train:    {train_path}")
    print(f"  Docs:     {stats.train_docs:,}")
    print(f"  Chars:    {stats.train_chars:,}")
    print(f"  ~Tokens:  {approx_tokens(stats.train_chars):,}")
    print(f"  Max doc:  {max_doc_chars:,} chars")
    print("  Bucket char shares:")
    for b, info in bucket_share.items():
        print(f"    {b:12s}  share={info['char_share']:.1%}  docs={info['docs']:,}  ~tok={info['approx_tokens']:,}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Holdouts: {holdout_dir}")
    if dedup_report.get("top_frequent_paragraphs"):
        print("  Top repeated paragraphs (review OCR/boilerplate):")
        for i, item in enumerate(dedup_report["top_frequent_paragraphs"][:5], 1):
            print(f"    {i}. count={item['count']}  {item['preview']!r}")
    print("=" * 60)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build multi-source theology CPT mix (v2)")
    p.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent.parent.parent),
        help="Repository root (default: auto)",
    )
    p.add_argument("--out-dir", default=None, help="Output directory (default: continued_pretrain/data)")
    p.add_argument("--spurgeon-train", default=None, help="Path to spurgeon_train.txt")
    p.add_argument("--spurgeon-holdout", default=None, help="Path to spurgeon_holdout.txt")
    p.add_argument("--puritans-dir", default=None, help="Root dir of Puritan texts")
    p.add_argument("--confessions-dir", default=None, help="Root dir of confessions/systematic")
    p.add_argument("--bible-dir", default=None, help="Root dir of Scripture text")
    p.add_argument(
        "--spurgeon-weight",
        type=float,
        default=None,
        help="Explicit Spurgeon oversample weight (overrides --target-spurgeon-share)",
    )
    p.add_argument(
        "--target-spurgeon-share",
        type=float,
        default=DEFAULT_TARGET_SPURGEON_SHARE,
        help="Target Spurgeon char share after weighting (default 0.45). Ignored if --spurgeon-weight set.",
    )
    p.add_argument(
        "--keep-all-spurgeon",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Keep every Spurgeon train chunk when computed weight<1; oversample other "
            "domain buckets to hold --target-spurgeon-share (default True). "
            "--no-keep-all-spurgeon restores the old subsample-by-chars path."
        ),
    )
    p.add_argument(
        "--max-other-weight",
        type=float,
        default=5.0,
        help=(
            "Cap on other-bucket oversample when --keep-all-spurgeon (default 5). "
            "If hit, Spurgeon share will exceed the target."
        ),
    )
    p.add_argument("--replay-frac", type=float, default=DEFAULT_REPLAY_FRAC, help="Target general-data fraction of final mix")
    p.add_argument("--replay-txt", default=None, help="Local general replay .txt (preferred offline)")
    p.add_argument(
        "--replay-hf",
        default=None,
        help="Optional HF dataset for replay (e.g. HuggingFaceFW/fineweb-edu). Needs network.",
    )
    p.add_argument("--replay-split", default="train")
    p.add_argument("--replay-text-field", default="text")
    p.add_argument("--holdout-per-bucket", type=int, default=DEFAULT_HOLDOUT_PER_BUCKET)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument(
        "--max-chunk-chars",
        type=int,
        default=DEFAULT_MAX_CHUNK_CHARS,
        help="Paragraph-bounded chunk size (default 7000; F1 fix)",
    )
    p.add_argument(
        "--allow-spurgeon-only",
        action="store_true",
        help="Permit Spurgeon(+replay)-only mix (diagnostics). Flagship v2 requires multi-bucket.",
    )
    p.add_argument(
        "--author-tags",
        action="store_true",
        help="Prepend [AUTHOR:] [WORK:] headers (stretch E1)",
    )
    p.add_argument(
        "--max-bible-share",
        type=float,
        default=0.04,
        help="Cap Bible char share of final domain mix (default 0.04). Set 0 to disable.",
    )
    p.add_argument(
        "--max-confession-share",
        type=float,
        default=0.06,
        help="Cap confession/systematic share (default 0.06; Institutes can dominate). Set 0 to disable.",
    )
    p.add_argument(
        "--hymns-dir",
        default=None,
        help="Optional hymns/psalter dir (folded into puritan bucket; default data/hymns)",
    )
    p.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help=(
            "Skip files matching this glob (repeatable). Matched against filename and "
            "path relative to the bucket root. Defaults already skip henry/exposition*."
        ),
    )
    return p.parse_args(argv)


if __name__ == "__main__":
    build_mix(parse_args())
