"""Shared Qwen3.5 SFT stop-token contract and compliance checks."""

from __future__ import annotations

import re
from typing import Any

IM_START = "<|im_start|>"
IM_END = "<|im_end|>"
EOT = "<|endoftext|>"

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

CORRUPT_RE = re.compile(r"pist|spep|RGAR|据|\ufffd", re.I)
LEAKED_TURN_RE = re.compile(r"<\|im_start\|>\s*(user|system)\b", re.I)


def load_qwen35_tokenizer(model: str, token: str | None = None):
    """Load Qwen3.5 tokenizer; Unsloth configs may set tokenizer_class=TokenizersBackend."""
    from transformers import AutoTokenizer, PreTrainedTokenizerFast

    kwargs = dict(trust_remote_code=True)
    if token:
        kwargs["token"] = token
    try:
        return AutoTokenizer.from_pretrained(model, **kwargs)
    except ValueError as exc:
        msg = str(exc)
        if "TokenizersBackend" not in msg and "does not exist or is not currently imported" not in msg:
            raise
        print("WARN: AutoTokenizer failed — using PreTrainedTokenizerFast")
        return PreTrainedTokenizerFast.from_pretrained(model, **kwargs)


def text_tokenizer(tok):
    inner = tok
    for _ in range(4):
        nxt = getattr(inner, "tokenizer", None)
        if nxt is None or nxt is inner:
            break
        inner = nxt
    return inner


def apply_sft_special_token_contract(tok):
    """Pad safely; inject ChatML template on Base; return (tok, im_end_id, eot_id)."""
    tok = text_tokenizer(tok)
    n0 = len(tok)
    tok.padding_side = "right"
    if tok.pad_token is None or tok.pad_token == IM_END:
        tok.pad_token = EOT
    tok.pad_token_id = tok.convert_tokens_to_ids(tok.pad_token)
    if not getattr(tok, "chat_template", None):
        tok.chat_template = QWEN35_SFT_CHATML
    im_end_id = tok.convert_tokens_to_ids(IM_END)
    eot_id = tok.convert_tokens_to_ids(EOT)
    if tok.pad_token_id == im_end_id:
        raise ValueError("pad_token_id must not equal im_end_id")
    if len(tok) != n0:
        raise ValueError("vocab resize during special-token contract")
    return tok, im_end_id, eot_id


def encode_special(tok, text: str) -> list[int]:
    ids = tok(text, add_special_tokens=False)["input_ids"]
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], (list, tuple)):
        ids = list(ids[0])
    return [int(x) for x in ids]


def audit_tokenizer(tok, *, model_name: str | None = None) -> dict[str, Any]:
    """Phase 0: tokenizer-only contract audit."""
    tok = text_tokenizer(tok)
    errors: list[str] = []
    vocab_before = len(tok)
    tok, im_end_id, eot_id = apply_sft_special_token_contract(tok)
    if len(tok) != vocab_before:
        errors.append("tokenizer grew during pad/template setup")

    required_ids: dict[str, int] = {}
    for t in (IM_START, IM_END, EOT):
        ids = encode_special(tok, t)
        if len(ids) != 1:
            errors.append(f"{t} not atomic: {ids}")
            continue
        required_ids[t] = ids[0]

    if tok.pad_token_id == im_end_id:
        errors.append("pad_token_id == im_end_id")

    demo = tok.apply_chat_template(
        [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "U"},
            {"role": "assistant", "content": "A"},
        ],
        tokenize=False,
        add_generation_prompt=False,
    )
    if IM_END not in demo:
        errors.append("chat template demo missing im_end")

    return {
        "phase": 0,
        "model": model_name or getattr(tok, "name_or_path", None),
        "required_ids": required_ids,
        "eos_token": tok.eos_token,
        "eos_token_id": tok.eos_token_id,
        "pad_token": tok.pad_token,
        "pad_token_id": tok.pad_token_id,
        "im_end_id": im_end_id,
        "eot_id": eot_id,
        "demo": demo,
        "errors": errors,
        "pass": not errors,
    }


def template_has_assistant_stop(text: str) -> bool:
    """Phase 1: training text ends assistant turn with im_end."""
    marker = f"assistant\n"
    idx = text.rfind(marker)
    if idx < 0:
        return False
    tail = text[idx + len(marker) :]
    return IM_END in tail


def analyze_generation(
    text: str,
    *,
    raw_token_ids: list[int] | None = None,
    im_end_id: int | None = None,
    eot_id: int | None = None,
    api_stop: bool = False,
) -> dict[str, Any]:
    """Score one greedy generation for stop-token compliance."""
    clean = text.split(IM_END)[0].strip() if IM_END in text else text.strip()
    raw_token_ids = raw_token_ids or []
    hit_im_end_id = im_end_id is not None and im_end_id in raw_token_ids
    hit_eot_id = eot_id is not None and eot_id in raw_token_ids
    ended_with_im_end = text.strip().endswith(IM_END) or IM_END in text or hit_im_end_id or api_stop
    ended_with_eot = EOT in text or hit_eot_id
    corrupt = bool(CORRUPT_RE.search(text))
    leaked_turn = bool(LEAKED_TURN_RE.search(text))
    stop_id_hit = None
    if hit_im_end_id:
        stop_id_hit = IM_END
    elif hit_eot_id:
        stop_id_hit = EOT
    elif api_stop:
        stop_id_hit = "api_stop"
    ok = ended_with_im_end and not corrupt and not leaked_turn
    return {
        "ended_with_im_end": ended_with_im_end,
        "ended_with_eot": ended_with_eot,
        "stop_id_hit": stop_id_hit,
        "api_stop": api_stop,
        "corrupt": corrupt,
        "leaked_turn": leaked_turn,
        "ok": ok,
        "text_preview": clean[:300],
    }


def summarize_stop_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = max(1, len(rows))
    im_end_rate = sum(1 for r in rows if r.get("ended_with_im_end")) / n
    corrupt_rate = sum(1 for r in rows if r.get("corrupt")) / n
    leak_rate = sum(1 for r in rows if r.get("leaked_turn")) / n
    ok_rate = sum(1 for r in rows if r.get("ok")) / n
    return {
        "n": len(rows),
        "im_end_stop_rate": round(im_end_rate, 4),
        "corrupt_rate": round(corrupt_rate, 4),
        "leaked_turn_rate": round(leak_rate, 4),
        "stop_ok_rate": round(ok_rate, 4),
        "pass": im_end_rate >= 0.85 and corrupt_rate == 0 and leak_rate <= 0.02,
    }
