#!/usr/bin/env python3
"""Tokenizer-only audit of Qwen3.5-4B special tokens for SFT.

Does not load GPU weights. Fails if ChatML tokens are missing, non-atomic,
or if pad would equal <|im_end|>.

Usage (repo root):
  python fine_tuning/scripts/audit_qwen35_special_tokens.py
  python fine_tuning/scripts/audit_qwen35_special_tokens.py --model unsloth/Qwen3.5-4B-Base
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

STOCK_MODEL = "unsloth/Qwen3.5-4B-Base"
IM_START = "<|im_start|>"
IM_END = "<|im_end|>"
EOT = "<|endoftext|>"
REQUIRED = (IM_START, IM_END, EOT)

# Plain ChatML for SFT on the *Base* tokenizer (no chat_template on HF).
# Do not copy Qwen3.5 Instruct's thinking/vision/tool jinja onto Base SFT.
QWEN35_SFT_CHATML = (
    "{%- for message in messages %}"
    "{%- if message['role'] == 'system' %}"
    "{{- '<|im_start|>system\\n' + message['content'] + '<|im_end|>\\n' }}"
    "{%- elif message['role'] == 'user' %}"
    "{{- '<|im_start|>user\\n' + message['content'] + '<|im_end|>\\n' }}"
    "{%- elif message['role'] == 'assistant' %}"
    "{{- '<|im_start|>assistant\\n' + message['content'] + '<|im_end|>\\n' }}"
    "{%- endif %}"
    "{%- endfor %}"
    "{%- if add_generation_prompt %}"
    "{{- '<|im_start|>assistant\\n' }}"
    "{%- endif %}"
)
OPTIONAL = (
    "<|fim_pad|>",
    "<|fim_prefix|>",
    "<|fim_middle|>",
    "<|fim_suffix|>",
    "<|vision_start|>",
    "<|vision_end|>",
    "<|image_pad|>",
    "<|video_pad|>",
    "<|object_ref_start|>",
    "<|object_ref_end|>",
)


def text_tokenizer(tok):
    """Unwrap VL Processor → inner PreTrainedTokenizer (Qwen3.5 is multimodal)."""
    inner = tok
    for _ in range(4):
        nxt = getattr(inner, "tokenizer", None)
        if nxt is None or nxt is inner:
            break
        inner = nxt
    return inner


def encode_special(tok, s: str) -> list[int]:
    ids = tok(s, add_special_tokens=False)["input_ids"]
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], (list, tuple)):
        ids = list(ids[0])
    return [int(x) for x in ids]


def apply_pad_contract(tok) -> None:
    """Pad with <|endoftext|>, never <|im_end|>. Do not reassign eos_token."""
    if tok.pad_token is None or tok.pad_token == IM_END:
        tok.pad_token = EOT
    tok.pad_token_id = tok.convert_tokens_to_ids(tok.pad_token)
    tok.padding_side = "right"


def ensure_sft_chat_template(tok) -> bool:
    """Base has no chat_template. Inject plain ChatML (no thinking/vision)."""
    if getattr(tok, "chat_template", None):
        return False
    tok.chat_template = QWEN35_SFT_CHATML
    return True


def audit(tok) -> dict:
    tok = text_tokenizer(tok)
    errors: list[str] = []
    vocab_before = len(tok)
    apply_pad_contract(tok)
    injected = ensure_sft_chat_template(tok)
    if len(tok) != vocab_before:
        errors.append("tokenizer grew during pad assignment — vocab resize")
    # Qwen3.5: vocab_size is the BPE size; specials live in added_tokens (len > vocab_size).
    # Never require len == vocab_size — that would abort a stock Qwen3.5 tokenizer.

    required_ids: dict[str, int] = {}
    for t in REQUIRED:
        ids = encode_special(tok, t)
        atomic = len(ids) == 1
        print(f"{t:20} -> {ids}  {'atomic' if atomic else 'NOT ATOMIC'}")
        if not atomic:
            errors.append(f"{t} not atomic: {ids}")
            continue
        required_ids[t] = ids[0]
        cid = tok.convert_tokens_to_ids(t)
        if cid != ids[0]:
            errors.append(f"{t} convert_tokens_to_ids={cid} != encode={ids[0]}")

    optional: dict[str, int | None] = {}
    for t in OPTIONAL:
        ids = encode_special(tok, t)
        if len(ids) == 1:
            optional[t] = ids[0]
            print(f"{t:20} -> {ids[0]}  (optional, atomic)")
        else:
            optional[t] = None
            print(f"{t:20} -> {ids}  (absent or not atomic)")

    im_end_id = required_ids.get(IM_END)
    pad_id = tok.pad_token_id
    if im_end_id is not None and pad_id == im_end_id:
        errors.append("pad_token_id == im_end_id — would pad with the ChatML stop token")
    n_tok = len(tok)
    if pad_id is None or pad_id < 0 or pad_id >= n_tok:
        errors.append(f"pad_token_id {pad_id} is not an existing tokenizer id (len={n_tok})")

    demo = tok.apply_chat_template(
        [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "U"},
            {"role": "assistant", "content": "A"},
        ],
        tokenize=False,
        add_generation_prompt=False,
    )
    print("--- ChatML demo ---")
    print(demo)
    if IM_END not in demo:
        errors.append("apply_chat_template demo missing <|im_end|>")
    if IM_START not in demo:
        errors.append("apply_chat_template demo missing <|im_start|>")

    report = {
        "model": getattr(tok, "name_or_path", None),
        "vocab_size": tok.vocab_size,
        "len_tokenizer": len(tok),
        "len_unchanged": len(tok) == vocab_before,
        "eos_token": tok.eos_token,
        "eos_token_id": tok.eos_token_id,
        "pad_token": tok.pad_token,
        "pad_token_id": pad_id,
        "chat_template_injected": injected,
        "required_ids": required_ids,
        "optional_ids": {k: v for k, v in optional.items() if v is not None},
        "errors": errors,
    }
    print("eos:", tok.eos_token, tok.eos_token_id)
    print("pad:", tok.pad_token, pad_id)
    print("chat_template_injected:", injected)
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Audit Qwen3.5-4B special tokens (tokenizer only)")
    p.add_argument("--model", default=STOCK_MODEL)
    p.add_argument(
        "--out",
        default=str(
            Path(__file__).resolve().parent.parent / "data" / "qwen35_special_token_audit.json"
        ),
    )
    args = p.parse_args(argv)

    from transformers import AutoTokenizer

    raw = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    report = audit(raw)
    report["requested_model"] = args.model
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", out)
    if report["errors"]:
        print("FAIL")
        for e in report["errors"]:
            print("ERROR:", e, file=sys.stderr)
        return 2
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
