"""Golden strings for knowledge-not-persona rewrite checks."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "fine_tuning" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from qa_rewrite_checks import (  # noqa: E402
    caricature_errors,
    check_assistant,
    strip_leading_vocative,
)

USER = (
    'CONTEXT (excerpts):\n\n[Sermon 1 — "T", Volume 1 | Text: John 1:1]\n'
    "Christ is the Beloved of the Father. What a remarkable instance you have.\n\n"
    "QUESTION: Why?"
)


def test_theological_beloved_passes():
    ans = (
        'Spurgeon teaches that Christ is "the Beloved of the Father." '
        "[Sermon 1] The sermon argues from the text."
    )
    assert check_assistant(USER, ans, "answerable") == []


def test_leading_vocative_fails():
    ans = 'Beloved, God pleads. Hear it: "What a remarkable instance you have." [Sermon 1]'
    errs = check_assistant(USER, ans, "answerable")
    assert any("vocative" in e for e in errs)


def test_quoted_vocative_not_caricature():
    ans = 'The excerpt itself says "Beloved, God pleads the cause of His people."'
    assert caricature_errors(ans) == []


def test_roleplay_fails():
    ans = 'When I preached this, I said "What a remarkable instance you have." [Sermon 1]'
    errs = check_assistant(USER, ans, "answerable")
    assert any("roleplay" in e for e in errs)


def test_refusal_plain():
    ans = "These excerpts do not address that question, and I will not invent an answer."
    assert check_assistant(USER, ans, "refusal") == []


def test_strip_leading_vocative():
    assert strip_leading_vocative("Beloved, God sometimes pleads.").startswith("God sometimes")
    assert strip_leading_vocative("My brethren, hear the word.").startswith("hear the word")
    assert strip_leading_vocative("Dear friends, look to Christ.").startswith("look to Christ")
    assert strip_leading_vocative("My beloved brethren, put away strife.").startswith("put away")
    assert strip_leading_vocative("Beloved brethren, Holy knowledge is useful.").startswith("Holy")
    assert strip_leading_vocative("O Beloved, do not sit still.").startswith("do not")


def test_mid_vocative_forms_fail():
    for sample in (
        "My beloved brethren, put away strife.",
        "Beloved brethren, Holy knowledge is useful.",
        "O Beloved, do not sit still.",
    ):
        assert any("vocative" in e for e in caricature_errors(sample)), sample
