#!/usr/bin/env python3
"""Shared mechanical checks for assistant rewrites (gold + bulk)."""

from __future__ import annotations

import html
import re

from build_qa_mix import is_refusal

SERMON_CITE_RE = re.compile(r"\[Sermon\s+(\d+)\]")
HEADER_RE = re.compile(r"\[Sermon\s+(\d+)", re.I)
QUOTE_RE = re.compile(r'["“]([^"”]{8,})["”]')

# Vocative-shaped only (Song of Solomon "the Beloved" must pass).
VOCATIVE_RE = re.compile(
    r"(?:^|[.!?]\s+|Oh!?\s+)(?:O\s+)?"
    r"(?:"
    r"(?:(?:my|dear)\s+)?beloved(?:\s+(?:brethren(?:\s+and\s+sisters)?|friends|souls|hearts|hearers))?"
    r"|dear\s+friends"
    r"|(?:my|dear)\s+brethren"
    r")\b",
    re.I,
)
PT_VOCATIVE_RE = re.compile(
    r"(?:^|[.!?]\s+)(?:amados|meus\s+queridos(?:\s+irm[ãa]os)?|queridos\s+irm[ãa]os)\b",
    re.I,
)
ROLEPLAY_RE = re.compile(
    r"when\s+I\s+preached|in\s+my\s+pulpit|you\s+are\s+charles"
    r"|as\s+spurgeon\s+I|these\s+lips\s+must",
    re.I,
)
# Leading openings + common mid-sentence vocative clauses.
LEADING_VOCATIVE_PREFIX_RE = re.compile(
    r"^(?:Oh!?\s+)?"
    r"(?:O\s+)?"
    r"(?:"
    r"(?:(?:my|dear)\s+)?beloved(?:\s+(?:brethren(?:\s+and\s+sisters)?|friends|souls|hearts|hearers))?"
    r"|dear\s+friends"
    r"|(?:my|dear)\s+brethren"
    r")\s*,\s*",
    re.I,
)
MID_VOCATIVE_CLAUSE_RE = re.compile(
    r"(?<=[.!?])\s+"
    r"(?:Oh!?\s+)?"
    r"(?:O\s+)?"
    r"(?:"
    r"(?:(?:my|dear)\s+)?beloved(?:\s+(?:brethren(?:\s+and\s+sisters)?|friends|souls|hearts|hearers))?"
    r"|dear\s+friends"
    r"|(?:my|dear)\s+brethren"
    r")\s*,\s*",
    re.I,
)


def norm_ws(text: str) -> str:
    text = html.unescape(text)
    for ch in ("\u2014", "\u2013", "\u2012", "\u2011", "\u2212", "\u00ad", "‑"):
        text = text.replace(ch, "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def context_of(user: str) -> str:
    return user.split("QUESTION:")[0]


def role(msgs: list, name: str) -> str:
    return next((m["content"] for m in msgs if m.get("role") == name), "")


def text_outside_quotes(text: str) -> str:
    return QUOTE_RE.sub(" ", text)


def caricature_errors(assistant: str) -> list[str]:
    """Fail vocatives/roleplay outside quoted spans. Do not ban every 'I' or 'beloved'."""
    body = text_outside_quotes(assistant)
    errors: list[str] = []
    if VOCATIVE_RE.search(body):
        errors.append("caricature vocative outside quotes")
    if PT_VOCATIVE_RE.search(body):
        errors.append("caricature vocative (PT) outside quotes")
    if ROLEPLAY_RE.search(body):
        errors.append("preacher roleplay phrase outside quotes")
    return errors


def strip_leading_vocative(assistant: str) -> str:
    """Remove leading and mid-sentence Beloved,/My brethren, costume openings."""
    text = LEADING_VOCATIVE_PREFIX_RE.sub("", assistant, count=1).lstrip()
    text = MID_VOCATIVE_CLAUSE_RE.sub(". ", text)
    text = re.sub(r"\.\s+\.", ".", text)
    return text.strip()


def check_assistant(user: str, assistant: str, slice_name: str) -> list[str]:
    """Return error strings; empty means the assistant passes the gold contract."""
    errors: list[str] = []
    headers = {int(n) for n in HEADER_RE.findall(user)}
    cites = [int(n) for n in SERMON_CITE_RE.findall(assistant)]
    for n in cites:
        if n not in headers:
            errors.append(f"[Sermon {n}] not in user headers {sorted(headers)}")

    ctx_n = norm_ws(context_of(user))
    quotes = QUOTE_RE.findall(assistant)
    ok_quotes = 0
    for q in quotes:
        if norm_ws(q) in ctx_n:
            ok_quotes += 1
        else:
            errors.append(f"quote not in CONTEXT: {q[:80]!r}")

    msgs = [{"role": "assistant", "content": assistant}]
    if slice_name == "answerable" and ok_quotes < 1:
        errors.append("answerable row has no quote found in CONTEXT")
    if slice_name == "refusal" and not is_refusal({"messages": msgs}):
        errors.append("refusal row does not match REFUSAL_PATTERNS")
    errors.extend(caricature_errors(assistant))
    return errors


def quote_cite_counts(user: str, assistant: str) -> tuple[int, list[int]]:
    ctx_n = norm_ws(context_of(user))
    ok = sum(1 for q in QUOTE_RE.findall(assistant) if norm_ws(q) in ctx_n)
    cites = [int(n) for n in SERMON_CITE_RE.findall(assistant)]
    return ok, cites


def _self_check() -> None:
    user = (
        'CONTEXT (excerpts):\n\n[Sermon 1 — "T", Volume 1 | Text: John 1:1]\n'
        "Christ is the Beloved of the Father. What a remarkable instance you have.\n\n"
        "QUESTION: Why?"
    )
    ok = (
        'Spurgeon teaches that Christ is "the Beloved of the Father." '
        "[Sermon 1] The sermon argues from the text, not from costume."
    )
    assert check_assistant(user, ok, "answerable") == [], check_assistant(user, ok, "answerable")

    bad_voc = 'Beloved, God pleads the cause. Hear it: "What a remarkable instance you have." [Sermon 1]'
    assert any("vocative" in e for e in check_assistant(user, bad_voc, "answerable")), check_assistant(
        user, bad_voc, "answerable"
    )

    for sample in (
        "My beloved brethren, put away strife.",
        "Beloved brethren, Holy knowledge is useful.",
        "O Beloved, do not sit still.",
        "Beloved souls, pray earnestly.",
        "My beloved friends, consider this.",
    ):
        assert caricature_errors(sample), sample
        stripped = strip_leading_vocative(sample)
        assert caricature_errors(stripped) == [], (sample, stripped, caricature_errors(stripped))

    mid = "Christ died for us. My brethren, consider His love."
    assert caricature_errors(mid)
    assert caricature_errors(strip_leading_vocative(mid)) == [], strip_leading_vocative(mid)

    quoted_voc = (
        'The excerpt itself says "Beloved, God pleads the cause of His people" '
        "and Spurgeon cites Jacob. [Sermon 1]"
    )
    assert caricature_errors(quoted_voc) == [], caricature_errors(quoted_voc)

    roleplay = 'When I preached this, I said "What a remarkable instance you have." [Sermon 1]'
    assert any("roleplay" in e for e in check_assistant(user, roleplay, "answerable"))

    refuse = "These excerpts do not address that question, and I will not invent an answer."
    assert check_assistant(user, refuse, "refusal") == [], check_assistant(user, refuse, "refusal")

    stripped = strip_leading_vocative("Beloved, God sometimes pleads the cause.")
    assert stripped.startswith("God sometimes"), stripped
    print("qa_rewrite_checks self-check PASS")


if __name__ == "__main__":
    _self_check()
