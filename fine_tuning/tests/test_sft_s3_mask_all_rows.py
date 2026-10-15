#!/usr/bin/env python3
"""CPU S3 audit over the full weighted mix (no GPU). Last-assistant mask must pass."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "fine_tuning" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from config import SPURGEON_SFT_SYSTEM_PROMPT, THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from train_sft_sota import (  # noqa: E402
    STOCK_MODEL,
    _audit_s3_dataset,
    _load_jsonl,
    _mask_assistant_labels,
    apply_sft_special_token_contract,
    build_weighted_message_rows,
)

RESPONSE_PART = "<|im_start|>assistant\n"
MAX_SEQ = 4608
SEED = 3407


def _tokenizer():
    try:
        from sft_stop_token_utils import load_qwen35_tokenizer
    except ImportError:
        pytest.skip("sft_stop_token_utils unavailable")
    try:
        tok = load_qwen35_tokenizer(STOCK_MODEL)
    except Exception as exc:  # noqa: BLE001 — Hub/cache optional for CI without net
        pytest.skip(f"Qwen tokenizer unavailable: {exc}")
    tok, im_end_id, _ = apply_sft_special_token_contract(tok)
    return tok, int(im_end_id)


def _mask_rows(tokenizer, message_rows: list[dict], *, max_seq: int = MAX_SEQ) -> list[dict]:
    rows = []
    for ex in message_rows:
        text = tokenizer.apply_chat_template(
            ex["messages"], tokenize=False, add_generation_prompt=False
        )
        ids = tokenizer(text, add_special_tokens=False)["input_ids"]
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], (list, tuple)):
            ids = list(ids[0])
        ids = list(ids)[:max_seq]
        labels = _mask_assistant_labels(tokenizer, ids, RESPONSE_PART)
        rows.append({"input_ids": ids, "labels": labels})
    return rows


def _assistant_turn_count(messages: list[dict]) -> int:
    return sum(1 for m in messages if m.get("role") == "assistant")


def test_weighted_mix_all_rows_pass_s3_audit() -> None:
    train_jsonl = REPO / "fine_tuning" / "data" / "qa_mix_train.jsonl"
    theo_jsonl = (
        REPO / "fine_tuning" / "data" / "qa_open_theology" / "sft" / "open_theology_train.jsonl"
    )
    if not train_jsonl.is_file() or not theo_jsonl.is_file():
        pytest.skip("weighted mix JSONL missing")

    rag_rows = _load_jsonl(train_jsonl)
    theo_rows = _load_jsonl(theo_jsonl)
    expected_mix_rows = len(rag_rows) + len(theo_rows)
    mixed = build_weighted_message_rows(
        rag_rows=rag_rows,
        theology_rows=theo_rows,
        rag_system=SPURGEON_SFT_SYSTEM_PROMPT,
        theology_system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        theology_repeat=1,
        seed=SEED,
    )
    assert len(mixed) == expected_mix_rows
    multiturn = sum(1 for r in mixed if _assistant_turn_count(r["messages"]) >= 2)
    assert multiturn > 0, "expected multiturn RAG rows in the weighted mix"

    tokenizer, im_end_id = _tokenizer()
    ds = _mask_rows(tokenizer, mixed)
    assert len(ds) == expected_mix_rows
    audit = _audit_s3_dataset(tokenizer, im_end_id, ds, backend="peft_cpu_test")
    assert audit["pass"] is True
    assert audit["rows_checked"] == expected_mix_rows


def test_synthetic_multiturn_passes_s3() -> None:
    tokenizer, im_end_id = _tokenizer()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "First question?"},
        {"role": "assistant", "content": "First answer."},
        {
            "role": "user",
            "content": "CONTEXT:\nSome retrieved text.\n\nSecond question with CONTEXT?",
        },
        {"role": "assistant", "content": "Final answer grounded in CONTEXT."},
    ]
    ds = _mask_rows(tokenizer, [{"messages": messages}])
    audit = _audit_s3_dataset(tokenizer, im_end_id, ds, backend="peft_cpu_synthetic")
    assert audit["pass"] is True
    assert audit["rows_checked"] == 1
    ids, labs = ds[0]["input_ids"], ds[0]["labels"]
    supervised = [t for t, lab in zip(ids, labs) if lab != -100]
    decoded = tokenizer.decode(supervised)
    assert "<|im_start|>user" not in decoded
    assert "Final answer grounded in CONTEXT" in decoded
    assert "First answer" not in decoded
