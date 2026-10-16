#!/usr/bin/env python3
"""CPU-only tokenizer smoke. Does not import torch and does not touch the GPU.

Loads the base-model tokenizer and the dataprep tokenizer source, applies the
SFT special-token contract, and tokenizes one chat row. Missing protobuf fails
here, before the GPU smoke variants.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Keep this process off the GPU. train_sft_sota setdefault will not override.
os.environ["CUDA_VISIBLE_DEVICES"] = ""

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

SAMPLE_MESSAGES = [
    {"role": "system", "content": "Answer from the sermons."},
    {"role": "user", "content": "What is grace?"},
    {"role": "assistant", "content": "Grace is the unmerited favor of God."},
]


def _fail(message: str) -> None:
    print(f"TOKENIZER_CPU_SMOKE_FAIL {message}", flush=True)
    raise SystemExit(1)


def _require_tokenizer_dir(path: Path, label: str) -> Path:
    if not path.is_dir() or not (path / "tokenizer_config.json").is_file():
        _fail(f"{label} tokenizer_config.json missing: {path}")
    return path


def _require_protobuf() -> str:
    try:
        from importlib.metadata import version

        return version("protobuf")
    except Exception as exc:
        _fail(f"protobuf missing ({exc})")
    return ""


def _maybe_require_sentencepiece(model_dir: Path) -> None:
    needs = any(model_dir.glob("*.model")) or any(model_dir.glob("sentencepiece*"))
    if not needs:
        return
    try:
        import sentencepiece  # noqa: F401
    except ImportError as exc:
        _fail(f"sentencepiece missing for {model_dir.name} ({exc})")


def _ids_of(tokenizer, text: str) -> list[int]:
    encoded = tokenizer(text, add_special_tokens=False)["input_ids"]
    if hasattr(encoded, "tolist"):
        encoded = encoded.tolist()
    if encoded and isinstance(encoded[0], (list, tuple)):
        encoded = list(encoded[0])
    return [int(x) for x in encoded]


def smoke_one(model_dir: Path, label: str) -> int:
    from sft_stop_token_utils import load_qwen35_tokenizer
    from train_sft_sota import apply_sft_special_token_contract

    _maybe_require_sentencepiece(model_dir)
    tokenizer = load_qwen35_tokenizer(str(model_dir))
    tokenizer, im_end_id, eot_id = apply_sft_special_token_contract(tokenizer)
    text = tokenizer.apply_chat_template(
        SAMPLE_MESSAGES,
        tokenize=False,
        add_generation_prompt=False,
    )
    ids = _ids_of(tokenizer, text)
    if not ids:
        _fail(f"{label} produced no token ids")
    if im_end_id not in ids:
        _fail(f"{label} row missing im_end id {im_end_id}")
    print(
        "TOKENIZER_CPU_SMOKE_ROW",
        label,
        "n_ids",
        len(ids),
        "im_end",
        im_end_id,
        "eot",
        eot_id,
        flush=True,
    )
    return len(ids)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CPU tokenizer smoke for weighted SFT")
    parser.add_argument("--base", required=True, help="Base model directory (merged CPT)")
    parser.add_argument(
        "--dataprep",
        default="",
        help="Dataprep tokenizer source. Defaults to --base.",
    )
    args = parser.parse_args(argv)
    base = _require_tokenizer_dir(Path(args.base), "base")
    dataprep = _require_tokenizer_dir(Path(args.dataprep or args.base), "dataprep")
    protobuf_ver = _require_protobuf()
    print("TOKENIZER_CPU_SMOKE_PROTOBUF", protobuf_ver, flush=True)
    smoke_one(base, "base")
    if dataprep.resolve() != base.resolve():
        smoke_one(dataprep, "dataprep")
    else:
        print("TOKENIZER_CPU_SMOKE_DATAPREP_SAME_AS_BASE", dataprep, flush=True)
    print("TOKENIZER_CPU_SMOKE_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
