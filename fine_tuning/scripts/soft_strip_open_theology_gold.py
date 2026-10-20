#!/usr/bin/env python3
"""Soft-strip cite theater from open-theology accepted gold (mechanical).

Aligns assistant gold with open_theology_chat_corpus_v1: drop bracketed catalog
heading cites and any quoted span that is not a contiguous substring of
meta.passage. Does not invent replacement prose or call a teacher.

Usage (repo root):
  python fine_tuning/scripts/soft_strip_open_theology_gold.py
  python fine_tuning/scripts/soft_strip_open_theology_gold.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
for p in (_REPO, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from open_theology_qa_checks import (  # noqa: E402
    HEADING_CITE_RE,
    check_open_theology_record,
    fabricated_quotes,
    quote_core,
    quote_in_passage,
)
from plan_open_theology_jobs import OUT_DIR  # noqa: E402
from qa_rewrite_checks import QUOTE_RE, role  # noqa: E402

_WS_RE = re.compile(r"[ \t]+")
_BLANK_RE = re.compile(r"\n{3,}")
_SPACE_BEFORE_PUNCT = re.compile(r" +([,.;:!?])")
_SPACE_AFTER_OPEN = re.compile(r"([(]) +")
_DANGLING_COMMA = re.compile(r",\s*,+")


def soft_strip_assistant(assistant: str, passage: str) -> tuple[str, dict]:
    """Return (stripped_assistant, stats).

    Stats keys: headings_removed, fabricated_quotes_removed, kept_quotes, changed.
    """
    stats = {
        "headings_removed": 0,
        "fabricated_quotes_removed": 0,
        "kept_quotes": 0,
        "changed": False,
    }
    text = assistant or ""
    cites = HEADING_CITE_RE.findall(text)
    if cites:
        stats["headings_removed"] = len(cites)
        text = HEADING_CITE_RE.sub(" ", text)

    # Drop fabricated quotes; re-scan because removing a span can expose others
    # (and heading cites can confuse the first QUOTE_RE pass on the raw string).
    for _ in range(8):
        bad = fabricated_quotes(text, passage)
        if not bad:
            break
        bad_cores = {quote_core(q) for q in bad}
        out_parts: list[str] = []
        last = 0
        removed_this_pass = 0
        for m in QUOTE_RE.finditer(text):
            out_parts.append(text[last : m.start()])
            quoted = m.group(1)
            full = m.group(0)
            core = quote_core(quoted)
            if len(core) >= 8 and core in bad_cores:
                stats["fabricated_quotes_removed"] += 1
                removed_this_pass += 1
            else:
                out_parts.append(full)
            last = m.end()
        out_parts.append(text[last:])
        text = "".join(out_parts)
        if removed_this_pass == 0:
            # Contained quote not matched by QUOTE_RE (should not happen); force-drop
            # by replacing exact fabricated substrings with spaces.
            for q in bad:
                needle = f'"{q}"'
                if needle in text:
                    text = text.replace(needle, " ")
                    stats["fabricated_quotes_removed"] += 1
                else:
                    curly = f"\u201c{q}\u201d"
                    if curly in text:
                        text = text.replace(curly, " ")
                        stats["fabricated_quotes_removed"] += 1
            break

    # Count remaining verified quotes for stats.
    stats["kept_quotes"] = quote_in_passage(text, passage)

    text = _cleanup_prose(text)
    original_clean = _cleanup_prose(assistant or "")
    stats["changed"] = text != original_clean
    return text, stats


def _cleanup_outside_quotes(text: str) -> str:
    """Whitespace/punct cleanup that must not rewrite characters inside quotes.

    Soft-strip previously collapsed ``Christ ;`` → ``Christ;`` inside a verbatim
    quote, which broke ``quote_in_passage`` on an otherwise good span.
    """
    parts: list[str] = []
    last = 0
    for m in QUOTE_RE.finditer(text):
        parts.append(_cleanup_chunk(text[last : m.start()]))
        parts.append(m.group(0))  # keep quoted span byte-identical
        last = m.end()
    parts.append(_cleanup_chunk(text[last:]))
    return "".join(parts).strip()


def _cleanup_chunk(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = _WS_RE.sub(" ", text)
    text = _BLANK_RE.sub("\n\n", text)
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    text = _SPACE_AFTER_OPEN.sub(r"\1", text)
    text = _DANGLING_COMMA.sub(",", text)
    text = re.sub(r" +\n", "\n", text)
    text = re.sub(r"\n +", "\n", text)
    text = re.sub(r" ,", ",", text)
    text = re.sub(r"\.\s*\.", ".", text)
    return text


def _cleanup_prose(text: str) -> str:
    return _cleanup_outside_quotes(text)


def soft_strip_record(rec: dict) -> tuple[dict, dict]:
    """Return (new_record, stats). Messages system/user unchanged."""
    msgs = list(rec.get("messages") or [])
    meta = rec.get("meta") or {}
    passage = str(meta.get("passage") or "")
    assistant = role(msgs, "assistant")
    new_asst, stats = soft_strip_assistant(assistant, passage)
    new_msgs = []
    for m in msgs:
        if m.get("role") == "assistant":
            new_msgs.append({**m, "content": new_asst})
        else:
            new_msgs.append(dict(m))
    out = dict(rec)
    out["messages"] = new_msgs
    return out, stats


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def process_file(path: Path, *, apply: bool) -> dict:
    rows = read_jsonl(path)
    out_rows: list[dict] = []
    summary = {
        "path": str(path),
        "n": len(rows),
        "changed": 0,
        "headings_removed": 0,
        "fabricated_quotes_removed": 0,
        "kept_quotes": 0,
        "check_fail_after": 0,
        "empty_assistant_after": 0,
        "fail_ids": [],
    }
    for rec in rows:
        new_rec, stats = soft_strip_record(rec)
        if stats["changed"]:
            summary["changed"] += 1
        summary["headings_removed"] += stats["headings_removed"]
        summary["fabricated_quotes_removed"] += stats["fabricated_quotes_removed"]
        summary["kept_quotes"] += stats["kept_quotes"]
        asst = role(new_rec.get("messages") or [], "assistant")
        if not asst.strip():
            summary["empty_assistant_after"] += 1
            summary["fail_ids"].append(rec.get("job_id") or rec.get("id") or "?")
            out_rows.append(rec)  # keep original rather than empty
            continue
        errs = check_open_theology_record(new_rec)
        if errs:
            summary["check_fail_after"] += 1
            summary["fail_ids"].append(
                f"{rec.get('job_id') or rec.get('id') or '?'}: {errs}"
            )
            # Still write stripped form if it only fails on legacy issues we cannot
            # fix mechanically; prefer stripped when check passes OR only meta warnings.
            # Hard errors: keep stripped anyway if assistant non-empty — operator reviews fail_ids.
        out_rows.append(new_rec)

    print(
        f"{path.name}: n={summary['n']} changed={summary['changed']} "
        f"headings_rm={summary['headings_removed']} "
        f"fab_quotes_rm={summary['fabricated_quotes_removed']} "
        f"kept_quotes={summary['kept_quotes']} "
        f"check_fail={summary['check_fail_after']} "
        f"empty={summary['empty_assistant_after']}"
    )
    if summary["fail_ids"][:5]:
        for fid in summary["fail_ids"][:8]:
            print(f"  fail: {fid}")

    if apply:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak-soft-strip-{stamp}")
        shutil.copy2(path, bak)
        write_jsonl(path, out_rows)
        print(f"  wrote {path} (backup {bak.name})")
    else:
        print(f"  DRY — no write for {path.name}")
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Soft-strip OT gold cite theater")
    p.add_argument("--apply", action="store_true", help="Write accepted files (with .bak)")
    p.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Override paths (default: accepted.jsonl + eval_accepted.jsonl)",
    )
    args = p.parse_args(argv)

    defaults = [OUT_DIR / "accepted.jsonl", OUT_DIR / "eval_accepted.jsonl"]
    paths = [Path(x) for x in args.files] if args.files else defaults
    totals = {"changed": 0, "n": 0}
    for path in paths:
        if not path.exists():
            print(f"MISSING {path}", file=sys.stderr)
            return 1
        s = process_file(path, apply=args.apply)
        totals["changed"] += s["changed"]
        totals["n"] += s["n"]

    mode = "APPLY" if args.apply else "DRY"
    print(f"{mode} COMPLETE rows={totals['n']} changed={totals['changed']}")
    if not args.apply:
        print("Re-run with --apply after reviewing counts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
