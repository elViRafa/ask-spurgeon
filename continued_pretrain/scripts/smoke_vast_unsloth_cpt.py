#!/usr/bin/env python3
"""Minimal Unsloth CPT + LoRA smoke for Vast.ai.

Reproduces the historical failure mode (Unsloth + first train step) without
a full corpus epoch. Exit 0 + CPT_UNSLOTH_SMOKE_PASS on success.
"""
from __future__ import annotations

import inspect
import os
import sys
import time
import traceback

# Unsloth must patch before trl/transformers/peft.
os.environ.setdefault("HF_HOME", "/workspace/hf_home")
os.environ.setdefault("UNSLOTH_DISABLE_STATISTICS", "1")


def _filter_kwargs(fn, kwargs: dict) -> dict:
    params = inspect.signature(fn).parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return kwargs
    return {k: v for k, v in kwargs.items() if k in params}


def main() -> int:
    steps = int(os.environ.get("CPT_SMOKE_STEPS", "3"))
    seq = int(os.environ.get("CPT_SMOKE_SEQ", "512"))
    model_name = os.environ.get("CPT_SMOKE_MODEL", "unsloth/Qwen3.5-4B-Base")

    print(f"CPT Unsloth smoke: model={model_name} steps={steps} seq={seq}", flush=True)
    t0 = time.time()

    try:
        import unsloth  # noqa: F401
        import torch
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        from unsloth import FastLanguageModel
    except Exception:
        traceback.print_exc()
        print("CPT_UNSLOTH_SMOKE_FAIL import", flush=True)
        return 2

    if not torch.cuda.is_available():
        print("CPT_UNSLOTH_SMOKE_FAIL no_cuda", flush=True)
        return 3
    major, minor = torch.cuda.get_device_capability(0)
    print(
        f"cuda={torch.cuda.get_device_name(0)} cap={major}.{minor} "
        f"torch={torch.__version__}",
        flush=True,
    )
    if major < 8:
        print("CPT_UNSLOTH_SMOKE_FAIL need_ampere", flush=True)
        return 3

    try:
        flm_kwargs = dict(
            model_name=model_name,
            max_seq_length=seq,
            dtype=None,
            load_in_4bit=False,
        )
        try:
            flm_kwargs["load_in_16bit"] = True
            model, tokenizer = FastLanguageModel.from_pretrained(**flm_kwargs)
        except TypeError:
            flm_kwargs.pop("load_in_16bit", None)
            model, tokenizer = FastLanguageModel.from_pretrained(**flm_kwargs)

        model = FastLanguageModel.get_peft_model(
            model,
            r=16,
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            lora_alpha=16,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
        )
        print("LoRA attached", flush=True)

        texts = [
            (
                "The love of Christ constrains us. Justification is an act of God's "
                "free grace wherein He accepts sinners as righteous for Christ's sake. "
            )
            * 8,
            (
                "True saving faith rests upon Christ alone, for by grace are ye saved "
                "through faith; and that not of yourselves: it is the gift of God. "
            )
            * 8,
            (
                "The Westminster Confession teaches that God from all eternity did, "
                "by the most wise and holy counsel of His own will, freely ordain. "
            )
            * 8,
            (
                "Photosynthesis converts light energy into chemical energy; this line "
                "is general replay to keep the smoke closer to a mixed CPT batch. "
            )
            * 8,
        ] * 2
        train_ds = Dataset.from_dict({"text": texts})

        sft_cfg_kwargs = dict(
            output_dir="/workspace/cpt_unsloth_smoke_out",
            max_steps=steps,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=1e-5,
            logging_steps=1,
            save_strategy="no",
            report_to="none",
            bf16=True,
            dataset_text_field="text",
            packing=False,
            remove_unused_columns=False,
            max_length=seq,
        )
        sft_cfg_kwargs = _filter_kwargs(SFTConfig.__init__, sft_cfg_kwargs)
        if "max_length" not in sft_cfg_kwargs:
            cfg_params = inspect.signature(SFTConfig.__init__).parameters
            if "max_seq_length" in cfg_params:
                sft_cfg_kwargs["max_seq_length"] = seq
        args = SFTConfig(**sft_cfg_kwargs)
        trainer = SFTTrainer(
            model=model,
            args=args,
            train_dataset=train_ds,
            processing_class=tokenizer,
        )
        print(
            "Starting trainer.train() — first step is the Unsloth SIGSEGV trap",
            flush=True,
        )
        result = trainer.train()
        print(result, flush=True)
        print(
            f"CPT_UNSLOTH_SMOKE_PASS steps={steps} "
            f"wall_s={time.time() - t0:.1f}",
            flush=True,
        )
        return 0
    except Exception:
        traceback.print_exc()
        print(
            f"CPT_UNSLOTH_SMOKE_FAIL train wall_s={time.time() - t0:.1f}",
            flush=True,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
