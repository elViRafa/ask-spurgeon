#!/usr/bin/env python3
"""Local unit test for document-isolated manual packing (CPT B)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _gen_sota_notebooks import pack_document_isolated, pack_one_doc_padded  # noqa: E402

EOS = 99
IGNORE = -100


def _load_mix_mod():
    path = SCRIPTS / "07_build_theology_mix.py"
    spec = importlib.util.spec_from_file_location("build_theology_mix", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _flat_ids(rows):
    out = []
    for r in rows:
        out.extend(r["input_ids"])
    return out


def test_no_cross_doc_splice() -> None:
    """Leftover-of-A must not share a row with the start of B when they do not both fit."""
    a = [10, 11, 12, 13, 14, EOS]
    b = [20, 21, 22, 23, 24, EOS]
    rows = pack_document_isolated([a, b], max_seq_len=8, eos_token_id=EOS)
    assert len(rows) == 2, [r["input_ids"] for r in rows]
    assert rows[0]["input_ids"] == a
    assert rows[1]["input_ids"] == b
    assert 20 not in rows[0]["input_ids"]
    assert 10 not in rows[1]["input_ids"]
    assert max(len(r["input_ids"]) for r in rows) <= 8


def test_long_doc_leftover_not_spliced_onto_next() -> None:
    """Split-doc tail must not share a row with the start of the next document."""
    a = list(range(10)) + [EOS]  # 11 tokens
    b = [20, 21, EOS]
    rows = pack_document_isolated([a, b], max_seq_len=8, eos_token_id=EOS)
    assert len(rows) >= 3, [r["input_ids"] for r in rows]
    for r in rows:
        ids = r["input_ids"]
        # token 8 is only in A's split tail; 20 is only in B
        assert not (8 in ids and 20 in ids), ids
    assert _flat_ids(rows) == a + b
    assert rows[-1]["input_ids"] == b
    assert rows[-1]["labels"][0] == 20  # B is its own row — do not mask as a later-doc


def test_no_dropped_tokens() -> None:
    docs = [
        list(range(10)) + [EOS],
        [20, 21, 22, EOS],
        list(range(30, 50)) + [EOS],
        [1, EOS],
        [],
    ]
    rows = pack_document_isolated(docs, max_seq_len=8, eos_token_id=EOS)
    expected = []
    for d in docs:
        if d:
            expected.extend(d)
    assert _flat_ids(rows) == expected
    assert all(len(r["input_ids"]) <= 8 for r in rows)
    assert all(r["input_ids"] for r in rows)


def test_multi_doc_boundary_label() -> None:
    """When two docs fit in one row, CE must not train the first token of the later doc."""
    a = [1, 2, EOS]
    b = [3, 4, EOS]
    rows = pack_document_isolated([a, b], max_seq_len=16, eos_token_id=EOS)
    assert len(rows) == 1, [r["input_ids"] for r in rows]
    ids = rows[0]["input_ids"]
    labs = rows[0]["labels"]
    attn = rows[0]["attention_mask"]
    assert ids == a + b
    assert attn == [1] * len(ids)
    assert labs[len(a)] == IGNORE
    assert ids[len(a)] == 3 and ids[len(a)] != IGNORE
    assert labs[0] == 1
    assert labs[len(a) - 1] == EOS
    # HF causal LM: shift_labels[i] = labels[i+1]. Masking labels[B0] turns off
    # "predict B0 given A+EOS" (logits at EOS).
    shift_targets = labs[1:]
    assert shift_targets[len(a) - 1] == IGNORE


def test_lm_collator_clone_would_undo_isolation() -> None:
    """Document the collator footgun D2 now gates: cloning input_ids wipes post-EOS -100."""
    a = [1, 2, EOS]
    b = [3, 4, EOS]
    rows = pack_document_isolated([a, b], max_seq_len=16, eos_token_id=EOS)
    ids = rows[0]["input_ids"]
    labs = rows[0]["labels"]
    cloned = list(ids)
    assert labs[len(a)] == IGNORE
    assert cloned[len(a)] != IGNORE


def test_long_doc_continuation_mask() -> None:
    ids = list(range(10)) + [EOS]
    rows = pack_document_isolated([ids], max_seq_len=4, eos_token_id=EOS)
    assert len(rows) == 3, [r["input_ids"] for r in rows]
    assert rows[0]["input_ids"] == ids[:4]
    assert rows[0]["labels"][0] == 0
    assert rows[1]["labels"][0] == IGNORE
    assert rows[1]["labels"][1] == IGNORE
    assert all(len(r["input_ids"]) <= 4 for r in rows)
    assert _flat_ids(rows) == ids


def test_empty_docs_skipped() -> None:
    rows = pack_document_isolated([[], [1, EOS], []], max_seq_len=8, eos_token_id=EOS)
    assert len(rows) == 1
    assert rows[0]["input_ids"] == [1, EOS]


def test_one_doc_never_concats_two_short_docs() -> None:
    a = [1, 2, EOS]
    b = [3, 4, EOS]
    rows = pack_one_doc_padded([a, b], max_seq_len=16, eos_token_id=EOS)
    assert len(rows) == 2, [r["input_ids"] for r in rows]
    assert rows[0]["input_ids"] == a
    assert rows[1]["input_ids"] == b
    assert rows[0]["labels"] == a
    assert rows[1]["labels"] == b
    assert 3 not in rows[0]["input_ids"]
    assert all(len(r["input_ids"]) <= 16 for r in rows)


def test_one_doc_long_windows_not_spliced() -> None:
    a = list(range(10)) + [EOS]
    b = [20, 21, EOS]
    rows = pack_one_doc_padded([a, b], max_seq_len=8, eos_token_id=EOS)
    assert len(rows) == 3, [r["input_ids"] for r in rows]
    for r in rows:
        assert not (8 in r["input_ids"] and 20 in r["input_ids"]), r["input_ids"]
    assert _flat_ids(rows) == a + b
    assert rows[-1]["input_ids"] == b
    assert rows[-1]["labels"][0] == 20
    assert rows[1]["labels"][0] == IGNORE


def test_one_doc_pad_to_max() -> None:
    pad = 0
    a = [1, 2, EOS]
    rows = pack_one_doc_padded(
        [a], max_seq_len=8, eos_token_id=EOS, pad_token_id=pad, pad_to_max=True
    )
    assert len(rows) == 1
    r = rows[0]
    assert r["input_ids"] == a + [pad] * 5
    assert r["attention_mask"] == [1, 1, 1, 0, 0, 0, 0, 0]
    assert r["labels"] == a + [IGNORE] * 5
    assert len(r["input_ids"]) == 8


def test_one_doc_pad_to_max_requires_pad_id() -> None:
    try:
        pack_one_doc_padded([[1, EOS]], max_seq_len=4, eos_token_id=EOS, pad_to_max=True)
    except ValueError as e:
        assert "pad_token_id" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_one_doc_empty_skipped() -> None:
    rows = pack_one_doc_padded([[], [1, EOS], []], max_seq_len=8, eos_token_id=EOS)
    assert len(rows) == 1
    assert rows[0]["input_ids"] == [1, EOS]


def test_one_doc_pad_equals_eos_still_one_content_doc() -> None:
    """Qwen pad_token_id == eos_token_id must not look like a second document."""
    a = [1, 2, EOS]
    b = [3, 4, EOS]
    rows = pack_one_doc_padded(
        [a, b], max_seq_len=8, eos_token_id=EOS, pad_token_id=EOS, pad_to_max=True
    )
    assert len(rows) == 2
    for r in rows:
        content = [t for t, m in zip(r["input_ids"], r["attention_mask"]) if m]
        assert content.count(EOS) == 1, content
        assert 3 not in content or 1 not in content


def test_keep_all_other_weight() -> None:
    mix = _load_mix_mod()
    w, capped = mix.other_weight_for_keep_all_spurgeon(100, 20, 0.45, max_weight=5.0)
    assert capped is True
    assert w == 5.0
    w2, c2 = mix.other_weight_for_keep_all_spurgeon(45, 55, 0.45, max_weight=5.0)
    assert c2 is False
    assert abs(w2 - 1.0) < 1e-9


def main() -> None:
    test_no_cross_doc_splice()
    test_long_doc_leftover_not_spliced_onto_next()
    test_no_dropped_tokens()
    test_multi_doc_boundary_label()
    test_lm_collator_clone_would_undo_isolation()
    test_long_doc_continuation_mask()
    test_empty_docs_skipped()
    test_one_doc_never_concats_two_short_docs()
    test_one_doc_long_windows_not_spliced()
    test_one_doc_pad_to_max()
    test_one_doc_pad_to_max_requires_pad_id()
    test_one_doc_empty_skipped()
    test_one_doc_pad_equals_eos_still_one_content_doc()
    test_keep_all_other_weight()
    print("PASS: no leftover-A + start-of-B splice")
    print("PASS: long-doc tail not spliced onto next doc")
    print("PASS: no dropped tokens")
    print("PASS: multi-doc post-EOS label is ignore_index (HF-shift target)")
    print("PASS: cloning input_ids would undo isolation")
    print("PASS: long-doc continuation prefix masked")
    print("PASS: empty docs skipped")
    print("PASS: one_doc_padded never concats two short docs")
    print("PASS: one_doc_padded long windows not spliced")
    print("PASS: one_doc_padded pad_to_max mask/labels")
    print("PASS: one_doc_padded pad_to_max requires pad_token_id")
    print("PASS: one_doc_padded empty docs skipped")
    print("PASS: one_doc_padded pad==eos still one content doc per row")
    print("PASS: keep-all Spurgeon other-bucket weight")


if __name__ == "__main__":
    main()
