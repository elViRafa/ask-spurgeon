#!/usr/bin/env python3
"""CPU tests for completion-only label masking (no GPU, no Hub)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from train_sft_sota import (  # noqa: E402
    _assert_s3_row,
    _mask_assistant_labels,
)

RESPONSE_PART = "<|im_start|>assistant\n"
MARKER_IDS = [9001, 9002, 9003]
IM_END_ID = 9100
USER_LEAK_TOKEN = 9200


class _StubTokenizer:
    """Minimal tokenizer: fixed marker encode + decode of known ids."""

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        if text == RESPONSE_PART:
            return list(MARKER_IDS)
        if not text:
            return []
        # One id per character keeps tests deterministic without a vocab.
        return [ord(c) % 500 + 1 for c in text]

    def decode(self, ids) -> str:
        out = []
        for t in ids:
            if t == USER_LEAK_TOKEN:
                out.append("<|im_start|>user")
            elif t == IM_END_ID:
                out.append("<|im_end|>")
            elif t in MARKER_IDS:
                out.append("A")
            else:
                out.append("x")
        return "".join(out)


def test_mask_finds_assistant_and_supervises_tail() -> None:
    tok = _StubTokenizer()
    prompt = [1, 2, 3, USER_LEAK_TOKEN, 4]
    answer = [10, 11, IM_END_ID]
    ids = prompt + MARKER_IDS + answer
    labels = _mask_assistant_labels(tok, ids, RESPONSE_PART)
    assert labels[: len(prompt) + len(MARKER_IDS)] == [-100] * (len(prompt) + len(MARKER_IDS))
    assert labels[-len(answer) :] == answer


def test_missing_marker_masks_all_labels() -> None:
    tok = _StubTokenizer()
    # ~3000-token prompt truncated to 2048 with no assistant marker left.
    ids = [USER_LEAK_TOKEN, 1, 2, 3] * 750  # 3000 tokens
    truncated = ids[:2048]
    assert len(truncated) == 2048
    assert MARKER_IDS[0] not in truncated  # marker never appears
    labels = _mask_assistant_labels(tok, truncated, RESPONSE_PART)
    assert len(labels) == 2048
    assert all(label == -100 for label in labels)


def test_empty_response_part_masks_all() -> None:
    class EmptyMarkerTok(_StubTokenizer):
        def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
            return []

    ids = [1, 2, 3, IM_END_ID]
    labels = _mask_assistant_labels(EmptyMarkerTok(), ids, RESPONSE_PART)
    assert labels == [-100, -100, -100, -100]


def test_s3_row_rejects_user_leak() -> None:
    tok = _StubTokenizer()
    ids = [1, USER_LEAK_TOKEN, IM_END_ID]
    labs = [1, USER_LEAK_TOKEN, IM_END_ID]  # train-all fallback would look like this
    try:
        _assert_s3_row(tok, IM_END_ID, ids, labs, row_index=7)
        raise AssertionError("expected S3 FAIL for user leak")
    except AssertionError as exc:
        assert "row 7" in str(exc)
        assert "user turn leaked" in str(exc)


def test_s3_row_accepts_assistant_only() -> None:
    tok = _StubTokenizer()
    ids = [1, 2, 10, IM_END_ID]
    labs = [-100, -100, 10, IM_END_ID]
    audit = _assert_s3_row(tok, IM_END_ID, ids, labs, row_index=0)
    assert audit["im_end_in_supervised"] is True
    assert audit["supervised_fraction"] == 0.5
