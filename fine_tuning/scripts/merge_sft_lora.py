#!/usr/bin/env python3
"""
Merge Spurgeon QA SFT LoRA into CPT-merged Qwen3.5-4B HF (PEFT merge_and_unload).

Prefer GPU bf16 on Vast RTX 4090. Tokenizer always from CPT-merged (or adapter)
— never from stock Qwen — to avoid Ollama vocab-shift junk.

Usage on box:
  source /workspace/.sft_env
  python3 -u /workspace/merge_sft_lora.py
  python3 -u /workspace/merge_sft_lora.py --install
"""

from __future__ import annotations

import argparse
import gc
import os
import sys
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _hf_token() -> str | None:
    return _env("HF_TOKEN") or _env("HUGGING_FACE_HUB_TOKEN") or None


def _free_cuda() -> None:
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def _install() -> None:
    import subprocess

    pkgs = [
        "peft",
        "transformers>=4.51.0",
        "accelerate",
        "safetensors",
        "huggingface_hub",
        "sentencepiece",
        "protobuf",
    ]
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", *pkgs]
    )
    print("merge_sft_lora deps installed")


def _download_adapter_if_needed(adapter: Path, hub_id: str, token: str | None) -> Path:
    marker = adapter / "adapter_config.json"
    if marker.is_file():
        print("SFT adapter present:", adapter)
        return adapter
    if not hub_id:
        raise SystemExit(f"Missing adapter at {adapter} and SFT_LORA_HUB empty")
    from huggingface_hub import snapshot_download

    print("Downloading SFT LoRA from Hub:", hub_id)
    adapter.parent.mkdir(parents=True, exist_ok=True)
    path = snapshot_download(
        repo_id=hub_id,
        local_dir=str(adapter),
        token=token,
        ignore_patterns=["*.md", "*.gguf", ".gitattributes"],
    )
    print("Downloaded to", path)
    return Path(path)


def _load_tokenizer(tok_src: str, token: str | None):
    try:
        from sft_stop_token_utils import load_qwen35_tokenizer

        return load_qwen35_tokenizer(tok_src, token=token)
    except ImportError:
        from transformers import AutoTokenizer, PreTrainedTokenizerFast

        try:
            return AutoTokenizer.from_pretrained(
                tok_src, trust_remote_code=True, token=token
            )
        except ValueError:
            return PreTrainedTokenizerFast.from_pretrained(
                tok_src, trust_remote_code=True, token=token
            )


def _merge() -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoConfig, AutoModelForCausalLM

    work = Path(_env("SFT_WORK_ROOT", "/workspace"))
    base = Path(_env("SFT_GATE0_MERGED", str(work / "theology_cpt_v2_merged_hf")))
    adapter = Path(
        _env("SFT_LORA_DIR", str(work / "spurgeon_qa_lora_v2" / "lora"))
    )
    out = Path(_env("SFT_MERGED_OUT", str(work / "spurgeon_qa_merged_hf")))
    hub_id = _env(
        "SFT_LORA_HUB", "rafaelvieirar1r/qwen3.5-4b-spurgeon-qa-lora-v2"
    )
    token = _hf_token()

    if not (base / "config.json").is_file():
        raise SystemExit(f"CPT-merged base missing: {base}")

    adapter = _download_adapter_if_needed(adapter, hub_id, token)
    if not (adapter / "adapter_config.json").is_file():
        # Hub repo may put files at repo root
        if (adapter.parent / "adapter_config.json").is_file():
            adapter = adapter.parent
        elif list(adapter.rglob("adapter_config.json")):
            adapter = list(adapter.rglob("adapter_config.json"))[0].parent
        else:
            raise SystemExit(f"No adapter_config.json under {adapter}")

    tok_src = str(base)
    if (adapter / "tokenizer_config.json").is_file() or (
        adapter / "tokenizer.json"
    ).is_file():
        # Prefer adapter tokenizer only if present; CPT base is safer default.
        print("Tokenizer source: CPT-merged base (adapter also has tokenizer files)")
    tokenizer = _load_tokenizer(tok_src, token)

    prefer_cpu = _env("SFT_MERGE_DEVICE").lower() in ("cpu", "peft-cpu", "peft_cpu")
    use_cuda = (not prefer_cpu) and torch.cuda.is_available()
    dtype = torch.bfloat16 if use_cuda else torch.bfloat16
    device_map = "auto" if use_cuda else "cpu"
    print(
        f"Loading CPT base={base} cuda={use_cuda} device_map={device_map} dtype={dtype}"
    )

    # GATE-0 SFT used AutoModelForCausalLM (Qwen3_5ForCausalLM → model.layers.*).
    # Do NOT load Qwen3_5ForConditionalGeneration (model.language_model.layers.*) —
    # PEFT adapter keys will miss and merge becomes a no-op.
    load_kw = dict(
        torch_dtype=dtype,
        device_map=device_map,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        token=token,
    )
    print("Loading with AutoModelForCausalLM (matches SFT training paths)")
    model = AutoModelForCausalLM.from_pretrained(str(base), **load_kw)
    q_paths = [n for n, _ in model.named_modules() if n.endswith("self_attn.q_proj")]
    print("sample q_proj path:", q_paths[0] if q_paths else "NONE")
    if q_paths and "language_model" in q_paths[0]:
        raise SystemExit(
            "Refusing merge: model has language_model nesting; "
            "SFT LoRA expects model.layers.*"
        )

    print("Applying SFT adapter", adapter)
    model = PeftModel.from_pretrained(model, str(adapter))
    # Fail closed if adapter weights did not bind.
    missing = getattr(model, "_peft_missing_keys", None)
    loaded = 0
    try:
        from peft.utils.save_and_load import get_peft_model_state_dict

        loaded = len(get_peft_model_state_dict(model))
    except Exception as exc:
        print("WARN: could not count peft state:", type(exc).__name__, exc)
    print("peft_state_keys", loaded)
    if loaded < 100:
        raise SystemExit(f"Adapter bind looks wrong: only {loaded} peft keys")

    print("merge_and_unload...")
    model = model.merge_and_unload()

    if out.exists():
        import shutil

        print("Removing previous merge output", out)
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    print("Saving merged HF to", out)
    model.save_pretrained(str(out), max_shard_size="2GB", safe_serialization=True)
    tokenizer.save_pretrained(str(out))
    # Prefer CausalLM architecture in saved config for GGUF converters.
    try:
        cfg_path = out / "config.json"
        import json

        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["architectures"] = ["Qwen3_5ForCausalLM"]
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        print("Wrote architectures=Qwen3_5ForCausalLM")
    except Exception as exc:
        print("WARN: could not patch architectures:", type(exc).__name__, exc)
    del model
    _free_cuda()

    if not (out / "config.json").is_file():
        raise SystemExit("merge failed: no config.json in output")
    shards = list(out.glob("*.safetensors"))
    print("SFT_MERGE_DONE", out, "shards", len(shards))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Merge SFT LoRA into CPT-merged base")
    p.add_argument("--install", action="store_true")
    args = p.parse_args(argv)
    if args.install:
        _install()
        return 0
    _merge()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
