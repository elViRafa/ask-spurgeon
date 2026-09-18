#!/usr/bin/env python3
"""Merge GATE-0 SFT LoRA into local CPT-merged HF (CausalLM / PEFT)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from sft_stop_token_utils import load_qwen35_tokenizer  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--base",
        default="fine_tuning/kaggle/vast_sft_gate0/theology_cpt_v2_merged_hf",
    )
    p.add_argument(
        "--lora",
        default="fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_lora_v2/lora",
    )
    p.add_argument(
        "--out",
        default="fine_tuning/kaggle/vast_sft_gate0/spurgeon_qa_merged_hf",
    )
    p.add_argument("--dtype", choices=("bf16", "fp16", "fp32"), default="bf16")
    args = p.parse_args(argv)

    base = Path(args.base)
    lora = Path(args.lora)
    out = Path(args.out)
    if not base.is_dir():
        print(f"ERROR: base missing: {base}", file=sys.stderr)
        return 2
    if not lora.is_dir():
        print(f"ERROR: lora missing: {lora}", file=sys.stderr)
        return 2

    dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[args.dtype]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading base on {device} dtype={args.dtype}: {base}")
    tok_src = lora if (lora / "tokenizer.json").exists() else base
    print(f"Loading tokenizer from {tok_src}")
    tokenizer = load_qwen35_tokenizer(str(tok_src))
    model = AutoModelForCausalLM.from_pretrained(
        str(base),
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    if device == "cpu":
        model = model.to(device)

    print(f"Loading LoRA: {lora}")
    model = PeftModel.from_pretrained(model, str(lora))
    print("merge_and_unload...")
    model = model.merge_and_unload()

    out.mkdir(parents=True, exist_ok=True)
    print(f"Saving merged HF -> {out}")
    model.save_pretrained(str(out), max_shard_size="2GB", safe_serialization=True)
    tokenizer.save_pretrained(str(out))
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
