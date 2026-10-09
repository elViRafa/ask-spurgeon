#!/usr/bin/env python3
"""Mechanical checks for the open-theology (no-CONTEXT) SFT slice.

Separate from check_assistant: that checker assumes a RAG CONTEXT user turn.
Do not loosen the RAG contract to accept these rows.
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import is_refusal  # noqa: E402
from config import THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from qa_rewrite_checks import QUOTE_RE, caricature_errors, role  # noqa: E402

CONTEXT_LEAK_RE = re.compile(r"\bCONTEXT\b")
ONLY_CONTEXT_RE = re.compile(r"answer\s+based\s+ONLY", re.I)
# Catalog headings look like [Sermon 1 — "Title"] or [Owen — Mortification].
HEADING_CITE_RE = re.compile(r"\[[^\[\]]{3,120}\]")


def load_theology_system_prompt() -> str:
    return THEOLOGY_CHAT_SYSTEM_PROMPT


def user_has_context_leak(user: str) -> bool:
    return bool(CONTEXT_LEAK_RE.search(user) or ONLY_CONTEXT_RE.search(user))


def citation_headings(assistant: str) -> list[str]:
    return HEADING_CITE_RE.findall(assistant)


# Quote-edge punctuation the teacher adapts to its own sentence ("...servant," where
# the passage has "...servant."). Stripped from the quote only; still a containment check.
_QUOTE_EDGE_PUNCT = " \t\n.,;:!?'\"‘’“”"
_MIN_QUOTE_CHARS = 8

# Every dash/hyphen variant the teacher or OCR may emit; all compare as ASCII "-".
_DASHES_RE = re.compile("[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d]")
# OCR line-break hyphenation: "be- \nfore" in the passage, "before" in the quote.
_LINEBREAK_HYPHEN_RE = re.compile(r"(\w)-[ \t]*\r?\n\s*(\w)")


def ot_normalize(text: str, *, dehyphenate: bool = False, keep_hyphen: bool = False) -> str:
    """Single normalizer for quote/passage and heading/cite comparison.

    NFKC (NBSP -> space, ellipsis -> "...", ligatures), drop soft hyphens, dash
    variants -> "-", curly quotes -> straight, optional OCR line-break de-hyphenation,
    collapse whitespace, casefold. No fuzzy matching: callers still use exact containment.
    """
    text = unicodedata.normalize("NFKC", html.unescape(text or ""))
    text = text.replace("\u00ad", "")
    text = _DASHES_RE.sub("-", text)
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    if dehyphenate:
        text = _LINEBREAK_HYPHEN_RE.sub(r"\1-\2" if keep_hyphen else r"\1\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.casefold()


def quote_core(quote: str) -> str:
    """Normalize a quoted span and strip leading/trailing punctuation for matching."""
    return ot_normalize(quote).strip(_QUOTE_EDGE_PUNCT)


def passage_variants(passage: str) -> tuple[str, ...]:
    """Normalized passage, with OCR line-break hyphens joined ("be-fore" -> "before")
    and kept ("Law-\ngiver" -> "Law-giver"), so either quote form is an exact substring."""
    return (
        ot_normalize(passage, dehyphenate=True),
        ot_normalize(passage, dehyphenate=True, keep_hyphen=True),
    )


def quote_in_passage(assistant: str, passage: str) -> int:
    variants = passage_variants(passage)
    hits = 0
    for q in QUOTE_RE.findall(assistant):
        core = quote_core(q)
        if len(core) >= _MIN_QUOTE_CHARS and any(core in v for v in variants):
            hits += 1
    return hits


def heading_cited(assistant: str, heading: str) -> bool:
    """Bracketed catalog heading present, compared after the shared normalization
    (dash variants, NBSP/whitespace, case). Brackets are still required."""
    want = ot_normalize(heading)
    if any(ot_normalize(c) == want for c in citation_headings(assistant)):
        return True
    return want in ot_normalize(assistant)


def check_open_theology_row(
    *,
    system: str,
    user: str,
    assistant: str,
    passage: str,
    heading: str,
    source_path: str = "",
    holdout_paths: set[str] | None = None,
) -> list[str]:
    """Return error strings; empty means the row passes the open-theology contract."""
    errors: list[str] = []
    if system != THEOLOGY_CHAT_SYSTEM_PROMPT:
        errors.append("system prompt is not THEOLOGY_CHAT_SYSTEM_PROMPT")
    if user_has_context_leak(user):
        errors.append("user contains CONTEXT or answer-based-ONLY wording")
    if not (user or "").strip():
        errors.append("empty user question")
    if not (assistant or "").strip():
        errors.append("empty assistant")

    errors.extend(caricature_errors(assistant))

    if quote_in_passage(assistant, passage) < 1:
        errors.append("answerable row has no quote found in source passage")

    heading_n = (heading or "").strip()
    if heading_n:
        if not heading_cited(assistant, heading_n):
            errors.append(f"missing catalog heading cite: {heading_n}")
    else:
        errors.append("empty catalog heading")

    msgs = [{"role": "assistant", "content": assistant}]
    if is_refusal({"messages": msgs}):
        errors.append("open-theology train row must be answerable, not a refusal")

    if holdout_paths and source_path:
        norm = source_path.replace("\\", "/")
        if norm in holdout_paths or any(norm.endswith(h) or h.endswith(norm) for h in holdout_paths):
            errors.append(f"source path is a mix_v7 holdout: {source_path}")

    return errors


def check_open_theology_record(rec: dict, holdout_paths: set[str] | None = None) -> list[str]:
    msgs = rec.get("messages") or []
    meta = rec.get("meta") or {}
    return check_open_theology_row(
        system=role(msgs, "system"),
        user=role(msgs, "user"),
        assistant=role(msgs, "assistant"),
        passage=str(meta.get("passage") or ""),
        heading=str(meta.get("heading") or ""),
        source_path=str(meta.get("source_path") or ""),
        holdout_paths=holdout_paths,
    )


def _self_check() -> None:
    passage = (
        "Christ is the Beloved of the Father. What a remarkable instance you have "
        "of immutable love in the covenant of grace."
    )
    heading = '[Sermon 1 — "The Immutability of God"]'
    ok_ans = (
        f'Spurgeon teaches that Christ is "the Beloved of the Father." {heading} '
        "The sermon argues from the text, not from costume."
    )
    assert (
        check_open_theology_row(
            system=THEOLOGY_CHAT_SYSTEM_PROMPT,
            user="What does Spurgeon teach about Christ as the Beloved?",
            assistant=ok_ans,
            passage=passage,
            heading=heading,
        )
        == []
    ), check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach about Christ as the Beloved?",
        assistant=ok_ans,
        passage=passage,
        heading=heading,
    )

    leak = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="CONTEXT:\nfoo\n\nQUESTION: Why?",
        assistant=ok_ans,
        passage=passage,
        heading=heading,
    )
    assert any("CONTEXT" in e for e in leak), leak

    voc = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant=f'Beloved, hear this: "the Beloved of the Father." {heading}',
        passage=passage,
        heading=heading,
    )
    assert any("vocative" in e for e in voc), voc

    bad_quote = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant=f'Spurgeon says "totally invented phrase here." {heading}',
        passage=passage,
        heading=heading,
    )
    assert any("quote" in e for e in bad_quote), bad_quote

    # Teacher ends the quote with "," where the passage has "." (train-puritan-121 / confession-019).
    comma_end = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant=f'He writes that "Christ is the Beloved of the Father," and so on. {heading}',
        passage=passage,
        heading=heading,
    )
    assert comma_end == [], comma_end

    bad_cite = check_open_theology_row(
        system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        user="What does Spurgeon teach?",
        assistant='Spurgeon teaches that Christ is "the Beloved of the Father." [Sermon 999]',
        passage=passage,
        heading=heading,
    )
    assert any("heading" in e for e in bad_cite), bad_cite


if __name__ == "__main__":
    _self_check()
    print("open_theology_qa_checks: ok")
