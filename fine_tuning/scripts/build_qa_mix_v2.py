#!/usr/bin/env python3
"""
Build Spurgeon Q&A mix v2 — serve-shaped contexts (Fable 5 F3/F5).

Transforms existing `spurgeon_qa_train_final.jsonl` without paid teacher APIs:
  (a) wrap each example in multi-chunk headed CONTEXT matching `utils.prompts.format_context`
      and the fine-tuned serve contract (k≈4, CHUNK_SIZE=768 / overlap=128)
  (b) synthesize insufficient-context refusals by pairing questions with unrelated chunks
  (c) write qa_mix_train/val + frozen test + manifest (then run 12_package_kaggle_qa_mix.py)

Usage (repo root):
  python fine_tuning/scripts/build_qa_mix_v2.py
  python fine_tuning/scripts/12_package_kaggle_qa_mix.py
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Reuse v1 helpers (system prompt, refusal detect, jsonl IO, split utilities).
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import (  # noqa: E402
    REFUSAL_PATTERNS,
    dedupe_key,
    is_refusal,
    load_system_prompt,
    read_jsonl,
    repo_root,
    sha256_file,
)

HEADER_RE = re.compile(
    r"^#\s*Sermon\s+(\d+)(?:\s*[&\-–—]\s*\d+)?\s*\|\s*(.+?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
SCRIPTURE_RE = re.compile(
    r"(Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|"
    r"1 Samuel|2 Samuel|1 Kings|2 Kings|1 Chronicles|2 Chronicles|Ezra|Nehemiah|"
    r"Esther|Job|Psalm|Psalms|Proverbs|Ecclesiastes|Song of Solomon|Isaiah|"
    r"Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|"
    r"Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|"
    r"Acts|Romans|1 Corinthians|2 Corinthians|Galatians|Ephesians|Philippians|"
    r"Colossians|1 Thessalonians|2 Thessalonians|1 Timothy|2 Timothy|Titus|"
    r"Philemon|Hebrews|James|1 Peter|2 Peter|1 John|2 John|3 John|Jude|"
    r"Revelation)\s+\d+(?::\d+(?:\s*[-–]\s*\d+)?)?",
    re.I,
)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“‘'])")
USER_SPLIT = re.compile(
    r"CONTEXT:\s*\n(?P<ctx>.*?)\n\s*QUESTION:\s*\n(?P<q>.*)\s*$",
    re.S | re.I,
)

# ~768 tokens / ~128 overlap in English theological prose (no GPU tokenizer).
TARGET_CHUNK_CHARS = 2800
OVERLAP_CHARS = 450
MIN_CHUNK_CHARS = 400
DEFAULT_K = 4

REFUSAL_ANSWERS = (
    "These excerpts do not treat of this matter, and I will not invent "
    "an answer where the text is silent. The context is insufficient.",
    "I do not find in these excerpts any instruction upon that question; therefore "
    "I must say the provided sermons do not address it, and I will not speculate.",
    "These passages do not contain enough to answer faithfully. Where the Word "
    "as preached here is silent, so must the answer be.",
    "I would rather confess the lack than go beyond what is written. The "
    "context before us does not contain enough information to answer this question.",
    "I cannot answer from these excerpts: they do not speak to the question, and "
    "I will not guess beyond the sermons provided.",
)

ANACHRONISM_QUESTIONS = (
    "What did Spurgeon think about Charles Darwin's theory of evolution?",
    "What is Spurgeon's view on modern Christian rock music?",
    "How does Spurgeon explain building the Metropolitan Tabernacle with steel frames?",
    "What does Spurgeon say about the sovereignty of God in electronic media?",
    "How did Spurgeon describe a trip to the United States in 1885?",
    "What did Spurgeon teach about Sunday School classrooms in the 21st century?",
    "What warning does Spurgeon give regarding telephone lines in the church?",
    "How should a church live-stream the Lord's Supper according to these sermons?",
)


def clean_for_search(text: str) -> str:
    """Match generate_qa_pairs.clean_sermon_text plus case-folding."""
    text = html.unescape(text)
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = re.sub(r"#+\s+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def normalize_ws(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\u2014", "-").replace("\u2013", "-").replace("&mdash;", "-")
    text = re.sub(r"#+\s+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_user(content: str) -> tuple[str, str] | None:
    m = USER_SPLIT.search(content.strip())
    if m:
        return m.group("ctx").strip(), m.group("q").strip()
    # Serve-shaped already
    m2 = re.search(
        r"QUESTION:\s*(.+)$",
        content,
        re.S | re.I,
    )
    if m2 and "CONTEXT" in content.upper():
        q = m2.group(1).strip()
        ctx = re.split(r"\n\s*---\s*\n|\n\s*QUESTION:", content, maxsplit=1)[0]
        ctx = re.sub(r"^CONTEXT[^\n]*\n+", "", ctx, flags=re.I).strip()
        return ctx, q
    return None


def format_header(sermon_num, title: str, volume, scripture: str) -> str:
    header = f'[Sermon {sermon_num if sermon_num is not None else "?"} — "{title}"'
    if volume:
        header += f", Volume {volume}"
    if scripture:
        header += f" | Text: {scripture}"
    header += "]"
    return header


def format_user(question: str, blocks: list[str]) -> str:
    context = "\n\n".join(blocks)
    return (
        "CONTEXT (excerpts from Charles Haddon Spurgeon's sermons):\n\n"
        f"{context}\n\n"
        "---\n\n"
        f"QUESTION: {question}\n\n"
        "Answer based ONLY on the context above."
    )


def chunk_text(text: str, target: int = TARGET_CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    body = normalize_ws(text)
    if len(body) < MIN_CHUNK_CHARS:
        return [body] if body else []
    sentences = SENT_SPLIT.split(body) or [body]
    chunks: list[str] = []
    buf = ""
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if buf and len(buf) + 1 + len(sent) > target:
            chunks.append(buf.strip())
            if overlap > 0 and len(buf) > overlap:
                buf = buf[-overlap:].lstrip() + " " + sent
            else:
                buf = sent
        else:
            buf = (buf + " " + sent).strip() if buf else sent
    if buf.strip() and (not chunks or buf.strip() != chunks[-1]):
        if len(buf.strip()) >= MIN_CHUNK_CHARS or not chunks:
            chunks.append(buf.strip())
    return chunks


def parse_sermon_file(path: Path) -> dict | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    title_m = HEADER_RE.search(raw)
    sermon_number = int(title_m.group(1)) if title_m else None
    title = title_m.group(2).strip() if title_m else path.stem.replace("-", " ").replace("_", " ")
    vol = None
    vol_m = re.search(r"volume-(\d+)", str(path), re.I)
    if vol_m:
        vol = int(vol_m.group(1))
    head = raw[:2500]
    sm = SCRIPTURE_RE.search(head)
    scripture = sm.group(0).strip() if sm else ""
    body = HEADER_RE.sub("", raw, count=1)
    chunks = chunk_text(body)
    if not chunks:
        return None
    return {
        "path": path,
        "sermon_number": sermon_number,
        "title": title,
        "volume": vol,
        "scripture": scripture,
        "norm": clean_for_search(body),
        "chunks": chunks,
    }


def load_sermons(sermons_dir: Path) -> list[dict]:
    files = sorted(
        p
        for p in sermons_dir.rglob("*.md")
        if p.name.lower().startswith("sermon") and p.name.lower() != "readme.md"
    )
    sermons: list[dict] = []
    for p in files:
        rec = parse_sermon_file(p)
        if rec:
            sermons.append(rec)
    return sermons


def build_haystack(sermons: list[dict]) -> tuple[str, list[tuple[int, int, int]]]:
    sep = "\n\n@@@\n\n"
    parts: list[str] = []
    spans: list[tuple[int, int, int]] = []
    pos = 0
    for i, s in enumerate(sermons):
        t = s["norm"]
        parts.append(t)
        spans.append((pos, pos + len(t), i))
        pos += len(t) + len(sep)
    return sep.join(parts), spans


def span_index(pos: int, spans: list[tuple[int, int, int]]) -> int | None:
    lo, hi = 0, len(spans) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        start, end, idx = spans[mid]
        if pos < start:
            hi = mid - 1
        elif pos >= end:
            lo = mid + 1
        else:
            return idx
    return None


def match_sermon(ctx: str, haystack: str, spans: list[tuple[int, int, int]]) -> int | None:
    needle_src = clean_for_search(ctx)
    if len(needle_src) < 48:
        return None
    for start, nlen in ((48, 72), (80, 64), (120, 56), (8, 48)):
        if start + nlen > len(needle_src):
            continue
        needle = needle_src[start : start + nlen]
        pos = haystack.find(needle)
        if pos >= 0:
            return span_index(pos, spans)
    return None


def headed_block(sermon: dict, chunk: str) -> str:
    return (
        f"{format_header(sermon['sermon_number'], sermon['title'], sermon['volume'], sermon['scripture'])}\n"
        f"{chunk}"
    )


def pick_neighbors(sermon: dict, primary_idx: int, need: int, rng: random.Random) -> list[str]:
    chunks = sermon["chunks"]
    order: list[int] = []
    for delta in (1, -1, 2, -2, 3, -3):
        j = primary_idx + delta
        if 0 <= j < len(chunks):
            order.append(j)
    leftover = [i for i in range(len(chunks)) if i != primary_idx and i not in order]
    rng.shuffle(leftover)
    chosen: list[str] = []
    for j in order + leftover:
        if len(chosen) >= need:
            break
        chosen.append(headed_block(sermon, chunks[j]))
    return chosen


def other_sermon_blocks(
    sermons: list[dict],
    exclude_idx: int | None,
    n: int,
    rng: random.Random,
) -> list[str]:
    if n <= 0 or not sermons:
        return []
    out: list[str] = []
    tries = 0
    while len(out) < n and tries < n * 20:
        tries += 1
        i = rng.randrange(len(sermons))
        if i == exclude_idx:
            continue
        s = sermons[i]
        chunk = rng.choice(s["chunks"])
        out.append(headed_block(s, chunk))
    return out


def sample_k(rng: random.Random) -> int:
    # Weighted toward serve-time k=4 (FINE_TUNED_SIMILARITY_TOP_K).
    return rng.choices([1, 3, 4, 5], weights=[5, 15, 70, 10], k=1)[0]


def primary_chunk_for(sermon: dict, original_ctx: str) -> tuple[str, int]:
    """Prefer the ingest-sized chunk that contains the original evidence."""
    needle = clean_for_search(original_ctx)
    probe = needle[40:100] if len(needle) > 100 else needle[: min(60, len(needle))]
    for i, ch in enumerate(sermon["chunks"]):
        ch_l = ch.lower()
        if probe and probe in ch_l:
            return ch, i
        if needle[:80] and needle[:80] in ch_l:
            return ch, i
    return normalize_ws(original_ctx), 0


def maybe_cite(answer: str, sermon_num) -> str:
    if sermon_num is None or re.search(r"\[Sermon\s+\d+", answer):
        return answer
    text = answer.rstrip()
    if text and text[-1] not in ".!?":
        text += "."
    return f"{text} [Sermon {sermon_num}]"


def wrap_answerable(
    ctx: str,
    question: str,
    answer: str,
    sermons: list[dict],
    haystack: str,
    spans: list[tuple[int, int, int]],
    rng: random.Random,
) -> tuple[str, str, dict]:
    match_i = match_sermon(ctx, haystack, spans)
    k = sample_k(rng)
    if match_i is None:
        dummy = {
            "sermon_number": None,
            "title": "Untitled Sermon",
            "volume": None,
            "scripture": "",
            "chunks": [normalize_ws(ctx)],
        }
        blocks = [headed_block(dummy, dummy["chunks"][0])]
        extras = other_sermon_blocks(sermons, None, max(0, k - 1), rng)
        blocks.extend(extras)
        meta = {"matched": False, "k": len(blocks), "sermon_number": None}
        return format_user(question, blocks), answer, meta

    sermon = sermons[match_i]
    primary, pidx = primary_chunk_for(sermon, ctx)
    blocks = [headed_block(sermon, primary)]
    need = max(0, k - 1)
    neighbors = pick_neighbors(sermon, pidx, need, rng)
    blocks.extend(neighbors)
    if len(blocks) < k:
        blocks.extend(other_sermon_blocks(sermons, match_i, k - len(blocks), rng))
    blocks = blocks[:k]
    cited = maybe_cite(answer, sermon["sermon_number"])
    meta = {
        "matched": True,
        "k": len(blocks),
        "sermon_number": sermon["sermon_number"],
    }
    return format_user(question, blocks), cited, meta


def make_refusal_user(question: str, sermons: list[dict], exclude_idx: int | None, k: int, rng: random.Random) -> str:
    blocks = other_sermon_blocks(sermons, exclude_idx, k, rng)
    return format_user(question, blocks)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    root = repo_root()
    p = argparse.ArgumentParser(description="Build SFT qa_mix v2 (serve-shaped, local, no GPU)")
    p.add_argument(
        "--input",
        default=str(root / "fine_tuning" / "data" / "spurgeon_qa_train_final.jsonl"),
    )
    p.add_argument("--output-dir", default=str(root / "fine_tuning" / "data"))
    p.add_argument(
        "--sermons-dir",
        default=str(root / "data" / "chspurgeon-sermons"),
    )
    p.add_argument("--seed", type=int, default=3407)
    p.add_argument("--val-frac", type=float, default=0.05)
    p.add_argument("--test-size", type=int, default=100)
    p.add_argument("--train-refusal-frac", type=float, default=0.12)
    p.add_argument("--k", type=int, default=DEFAULT_K)
    args = p.parse_args(argv)

    inp = Path(args.input).resolve()
    out_dir = Path(args.output_dir).resolve()
    sermons_dir = Path(args.sermons_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not inp.exists():
        print(f"ERROR: missing input {inp}", file=sys.stderr)
        return 2
    if not sermons_dir.exists():
        print(f"ERROR: missing sermons dir {sermons_dir}", file=sys.stderr)
        return 2

    print(f"Loading sermons from {sermons_dir} ...")
    sermons = load_sermons(sermons_dir)
    if len(sermons) < 50:
        print(f"ERROR: only {len(sermons)} sermons parsed", file=sys.stderr)
        return 2
    print(f"Parsed {len(sermons)} sermons")
    haystack, spans = build_haystack(sermons)
    print(f"Haystack chars: {len(haystack):,}")

    system_prompt = load_system_prompt()
    raw_rows = read_jsonl(inp)
    rng = random.Random(args.seed)

    answerable: list[dict] = []
    original_refusals: list[dict] = []
    skipped = 0
    match_hits = 0
    k_hist: Counter[int] = Counter()

    for raw in raw_rows:
        msgs = raw.get("messages") or []
        by_role = {m.get("role"): m.get("content", "") for m in msgs if isinstance(m, dict)}
        user, assistant = by_role.get("user", ""), by_role.get("assistant", "")
        parsed = parse_user(user)
        if not parsed or not assistant:
            skipped += 1
            continue
        ctx, question = parsed
        orig_refusal = any(p.search(assistant) for p in REFUSAL_PATTERNS)

        if orig_refusal:
            match_i = match_sermon(ctx, haystack, spans)
            user_fmt = make_refusal_user(question, sermons, match_i, args.k, rng)
            ex = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_fmt},
                    {"role": "assistant", "content": assistant},
                ]
            }
            original_refusals.append(ex)
            k_hist[args.k] += 1
            continue

        user_fmt, new_answer, meta = wrap_answerable(
            ctx, question, assistant, sermons, haystack, spans, rng
        )
        if meta["matched"]:
            match_hits += 1
        k_hist[meta["k"]] += 1
        answerable.append(
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_fmt},
                    {"role": "assistant", "content": new_answer},
                ],
                "_match_i": meta.get("sermon_number"),
                "_question": question,
            }
        )

    # Dedupe by user+assistant after wrap.
    def strip_tmp(ex: dict) -> dict:
        return {"messages": ex["messages"]}

    def unique(rows: list[dict]) -> list[dict]:
        seen: set[str] = set()
        out: list[dict] = []
        for ex in rows:
            clean = strip_tmp(ex)
            key = dedupe_key(clean)
            if key in seen:
                continue
            seen.add(key)
            out.append(ex)
        return out

    answerable = unique(answerable)
    original_refusals = unique(original_refusals)

    n_answerable_test = args.test_size // 2
    n_refusal_test = args.test_size - n_answerable_test
    # Train refusal target after pulling test rows:
    # (R - n_refusal_test) / ((A - n_a_test) + (R - n_refusal_test)) ≈ train_refusal_frac
    a_pool = max(0, len(answerable) - n_answerable_test)
    frac = args.train_refusal_frac
    # R_pool / (a_pool + R_pool) = frac  =>  R_pool = frac/(1-frac) * a_pool
    r_pool_needed = int(round((frac / (1.0 - frac)) * a_pool))
    r_total_needed = r_pool_needed + n_refusal_test
    n_synth = max(0, r_total_needed - len(original_refusals))

    print(f"Synthesizing {n_synth} refusal examples (target train refusal {frac:.0%}) ...")
    synth_refusals: list[dict] = []
    # Mix: 70% real questions + mismatched chunks; 30% anachronism questions.
    for i in range(n_synth):
        k = args.k
        if i % 10 < 3:
            q = ANACHRONISM_QUESTIONS[i % len(ANACHRONISM_QUESTIONS)]
            exclude = None
        else:
            src = answerable[i % len(answerable)]
            q = src["_question"]
            exclude = None
        user_fmt = make_refusal_user(q, sermons, exclude, k, rng)
        ans = REFUSAL_ANSWERS[i % len(REFUSAL_ANSWERS)]
        synth_refusals.append(
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_fmt},
                    {"role": "assistant", "content": ans},
                ]
            }
        )

    refusals = unique(original_refusals + synth_refusals)
    rng.shuffle(answerable)
    rng.shuffle(refusals)

    n_a_test = min(n_answerable_test, len(answerable))
    n_r_test = min(n_refusal_test, len(refusals))
    test_set = [strip_tmp(x) for x in (refusals[:n_r_test] + answerable[:n_a_test])]
    rng.shuffle(test_set)
    test_keys = {dedupe_key(e) for e in test_set}

    pool = [strip_tmp(x) for x in (answerable[n_a_test:] + refusals[n_r_test:]) if dedupe_key(strip_tmp(x)) not in test_keys]
    rng.shuffle(pool)
    n_val = max(1, int(len(pool) * args.val_frac))
    val_set = pool[:n_val]
    train_set = pool[n_val:]

    slices = Counter()
    for e in train_set:
        slices["refusal" if is_refusal(e) else "answerable"] += 1
    train_refusal_pct = 100.0 * slices["refusal"] / max(1, len(train_set))

    train_keys = {dedupe_key(x) for x in train_set}
    guard = 0
    while train_refusal_pct < 10.0 and guard < 200:
        guard += 1
        q = ANACHRONISM_QUESTIONS[guard % len(ANACHRONISM_QUESTIONS)]
        extra = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": make_refusal_user(q, sermons, None, args.k, rng)},
                {"role": "assistant", "content": REFUSAL_ANSWERS[guard % len(REFUSAL_ANSWERS)]},
            ]
        }
        key = dedupe_key(extra)
        if key in train_keys:
            continue
        train_set.append(extra)
        train_keys.add(key)
        slices["refusal"] += 1
        train_refusal_pct = 100.0 * slices["refusal"] / len(train_set)
    rng.shuffle(train_set)

    if not (10.0 <= train_refusal_pct <= 15.5):
        print(
            f"WARNING: train refusal {train_refusal_pct:.1f}% outside 10–15% target",
            file=sys.stderr,
        )

    source_rel = str(inp.relative_to(root)) if inp.is_relative_to(root) else str(inp)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "qa_mix_v2",
        "source": source_rel,
        "source_sha256": sha256_file(inp),
        "system_prompt": "config.SPURGEON_SFT_SYSTEM_PROMPT",
        "serve_contract": {
            "FINE_TUNED_SIMILARITY_TOP_K": args.k,
            "CHUNK_SIZE": 768,
            "CHUNK_OVERLAP": 128,
            "header": '[Sermon N — "Title", Volume V | Text: ref]',
            "user_wrapper": "CONTEXT (excerpts...) + format_context blocks + QUESTION",
            "chunk_chars_approx": TARGET_CHUNK_CHARS,
            "overlap_chars_approx": OVERLAP_CHARS,
        },
        "counts": {
            "raw": len(raw_rows),
            "skipped": skipped,
            "answerable_wrapped": len(answerable),
            "original_refusals": len(original_refusals),
            "synth_refusals": n_synth,
            "sermons_indexed": len(sermons),
            "match_hits": match_hits,
            "match_rate": round(match_hits / max(1, len(answerable)), 4),
            "train": len(train_set),
            "val": len(val_set),
            "test_frozen": len(test_set),
        },
        "slices_train": dict(slices),
        "train_refusal_pct": round(train_refusal_pct, 2),
        "test_composition": {
            "answerable": sum(1 for e in test_set if not is_refusal(e)),
            "refusal": sum(1 for e in test_set if is_refusal(e)),
        },
        "k_histogram": {str(k): int(v) for k, v in sorted(k_hist.items())},
        "gaps": [
            "No new teacher-generated 5–6k set (existing QA rewrapped).",
            "No catechism/confession slice (~8% in F5 target).",
            "No multi-turn examples.",
            "Chunking is char-approx of 768 tokens (not LlamaIndex SentenceSplitter).",
            "Citation injection is a trailing [Sermon N], not teacher-written inline quotes.",
        ],
        "seed": args.seed,
    }

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
    print("Train slices:", dict(slices), f"refusal={train_refusal_pct:.1f}%")
    print("Test:", manifest["test_composition"])
    print(f"Match rate: {manifest['counts']['match_rate']:.1%} ({match_hits}/{len(answerable)})")
    print("k histogram:", dict(k_hist))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
