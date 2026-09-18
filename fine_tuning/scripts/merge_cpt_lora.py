#!/usr/bin/env python3
"""Merge Hub v2 CPT LoRA into 16-bit HF weights for GATE-0 SFT base.

Run on RunPod (RTX 4090, Ampere bf16) or Vultr A16 after adapter is on disk:

    export SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
    export SFT_CPT_ADAPTER=/workspace/theology_cpt_lora_hub_v2
    export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
    export EXPECTED_ADAPTER_SHA256=319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478
    python3 -u merge_cpt_lora.py --preflight
    python3 -u merge_cpt_lora.py --install   # first boot
    python3 -u merge_cpt_lora.py

Hub v2 LoRA has embed_tokens in modules_to_save — prefer Ampere bf16 GPU merge
(load_in_4bit=False). On 16 GB A16 slices, GPU merge may OOM; then fall back to
CPU PEFT merge_and_unload (needs lots of RAM, e.g. Vultr 128 GB).

    export SFT_MERGE_DEVICE=cpu   # skip GPU merge
    python3 -u merge_cpt_lora.py --cpu
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import os
import shutil
import subprocess
import sys

STOCK_MODEL = "unsloth/Qwen3.5-4B-Base"
HUB_V2_REPO = "rafaelvieirar1r/qwen3.5-4b-theology-cpt-lora-v2"
EXPECTED_SHA_DEFAULT = "319d17a39d193041528914cfb2f83c1decf21e55ffe76dfd2ca565f5e99e1478"
UNSLOTH_PIP_SPEC = "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
TORCH_CU126_INDEX = "https://download.pytorch.org/whl/cu126"


def _work_root() -> str:
    explicit = (os.environ.get("SFT_WORK_ROOT") or "").strip()
    if explicit:
        return os.path.abspath(explicit)
    if os.path.isdir("/workspace"):
        return "/workspace"
    return os.path.abspath(os.getcwd())


def _adapter_path(work: str) -> str:
    return (os.environ.get("SFT_CPT_ADAPTER") or "").strip() or os.path.join(
        work, "theology_cpt_lora_hub_v2"
    )


def _merged_path(work: str) -> str:
    return (os.environ.get("SFT_GATE0_MERGED") or "").strip() or os.path.join(
        work, "theology_cpt_v2_merged_hf"
    )


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _hf_token() -> str | None:
    tok = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or "").strip()
    if tok:
        return tok
    dotenv = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.isfile(dotenv):
        with open(dotenv, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("HF_TOKEN="):
                    value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    return value or None
                if stripped.startswith("HUGGING_FACE_HUB_TOKEN="):
                    value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    return value or None
    return None


def _maybe_upgrade_torch_for_cu124() -> None:
    try:
        import torch
    except ImportError:
        torch = None  # type: ignore[assignment]
    if torch is not None:
        ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
        if ver >= (2, 11):
            return
        print(f"Upgrading torch from {torch.__version__} -> 2.11.0+cu126")
    else:
        print("Installing torch 2.11.0+cu126")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "--break-system-packages",
            "torch==2.11.0",
            "torchvision",
            "torchaudio",
            "--index-url",
            TORCH_CU126_INDEX,
        ]
    )


def _preflight() -> None:
    work = _work_root()
    adapter = _adapter_path(work)
    merged = _merged_path(work)
    weights = os.path.join(adapter, "adapter_model.safetensors")
    cfg = os.path.join(adapter, "adapter_config.json")

    hf_home = (os.environ.get("HF_HOME") or "").strip() or os.path.join(work, "hf_home")
    os.makedirs(hf_home, exist_ok=True)
    print("preflight WORK_ROOT", work)
    print("preflight ADAPTER", adapter)
    print("preflight MERGED", merged)

    if os.path.isfile(os.path.join(merged, "config.json")):
        print("preflight SKIP: merged HF already exists at", merged)
        return

    print("preflight HF_TOKEN", "set" if _hf_token() else "MISSING")
    _download_adapter_if_missing(work, adapter)

    if not os.path.isfile(cfg) or not os.path.isfile(weights):
        raise SystemExit(
            f"preflight FAIL: missing adapter at {adapter}. "
            f"Set HF_TOKEN (Hub v2 repo is private) or copy the adapter to SFT_CPT_ADAPTER."
        )

    want = (os.environ.get("EXPECTED_ADAPTER_SHA256") or EXPECTED_SHA_DEFAULT).strip()
    got = _sha256_file(weights)
    print("preflight adapter SHA256", got)
    if want.lower() not in ("", "none", "skip") and got.lower() != want.lower():
        raise SystemExit(f"preflight FAIL: SHA256 mismatch want {want}")

    free = shutil.disk_usage(hf_home).free
    print("preflight disk_free_gb", round(free / (1024**3), 1))
    if free < 25 * 1024**3:
        raise SystemExit("preflight FAIL: need >=25 GB free for merge output")

    import torch

    if not torch.cuda.is_available():
        raise SystemExit("preflight FAIL: CUDA not available")
    major, _ = torch.cuda.get_device_capability(0)
    if major < 8:
        raise SystemExit("preflight FAIL: need sm_80+ Ampere for embed-FT Hub v2 adapter")
    print("preflight GPU", torch.cuda.get_device_name(0))
    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print("preflight GPU0_vram_gb", round(vram, 1))
    print("Preflight OK")


def _download_adapter_if_missing(work: str, adapter: str) -> None:
    cfg = os.path.join(adapter, "adapter_config.json")
    if os.path.isfile(cfg):
        return
    os.makedirs(adapter, exist_ok=True)
    token = _hf_token()
    if not token:
        raise SystemExit(
            "HF_TOKEN missing — Hub v2 LoRA "
            f"({HUB_V2_REPO}) is private. Set HF_TOKEN on the pod."
        )
    print("Downloading Hub v2 LoRA from", HUB_V2_REPO, "to", adapter)
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=HUB_V2_REPO,
        local_dir=adapter,
        ignore_patterns=["*.md", "*.gguf"],
        token=token,
    )


def _is_oom(exc: BaseException) -> bool:
    name = type(exc).__name__
    if name in ("OutOfMemoryError", "CudaOutOfMemoryError"):
        return True
    msg = str(exc).lower()
    return "out of memory" in msg or "cuda oom" in msg


def _free_cuda() -> None:
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass


def _assert_merged_complete(merged: str) -> None:
    cfg = os.path.join(merged, "config.json")
    if not os.path.isfile(cfg):
        raise SystemExit(f"merge FAIL: missing {cfg}")
    tok_ok = any(
        os.path.isfile(os.path.join(merged, name))
        for name in ("tokenizer.json", "tokenizer.model", "tokenizer_config.json")
    )
    if not tok_ok:
        raise SystemExit(f"merge FAIL: missing tokenizer files in {merged}")
    names = os.listdir(merged)
    shards = [n for n in names if n.endswith(".safetensors")]
    if not shards:
        raise SystemExit(f"merge FAIL: no .safetensors in {merged}")
    index = os.path.join(merged, "model.safetensors.index.json")
    if not os.path.isfile(index) and len(shards) > 1:
        print("WARN: missing model.safetensors.index.json with multiple shards")
    print("merge artifacts OK count", len(names), "shards", len(shards))


def _merge_unsloth_gpu(adapter: str, merged: str) -> None:
    from unsloth import FastLanguageModel

    print("Loading Hub v2 adapter for merge (bf16 Ampere GPU)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter,
        max_seq_length=4096,
        dtype=None,
        load_in_4bit=False,
    )
    os.makedirs(merged, exist_ok=True)
    print("Merging 16-bit HF to", merged)
    model.save_pretrained_merged(merged, tokenizer, save_method="merged_16bit")
    tokenizer.save_pretrained(merged)
    del model
    _free_cuda()


def _merge_peft_cpu(adapter: str, merged: str) -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoConfig, AutoTokenizer

    token = _hf_token()
    print("CPU PEFT merge from", STOCK_MODEL, "adapter", adapter)
    tok_src = adapter if (
        os.path.isfile(os.path.join(adapter, "tokenizer.json"))
        or os.path.isfile(os.path.join(adapter, "tokenizer_config.json"))
    ) else STOCK_MODEL
    try:
        from sft_stop_token_utils import load_qwen35_tokenizer

        tokenizer = load_qwen35_tokenizer(tok_src, token=token)
    except ImportError:
        from transformers import AutoTokenizer, PreTrainedTokenizerFast

        try:
            tokenizer = AutoTokenizer.from_pretrained(tok_src, trust_remote_code=True, token=token)
        except ValueError:
            tokenizer = PreTrainedTokenizerFast.from_pretrained(tok_src, trust_remote_code=True, token=token)
    config = AutoConfig.from_pretrained(STOCK_MODEL, trust_remote_code=True, token=token)
    load_kw = dict(
        torch_dtype=torch.bfloat16,
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        token=token,
    )
    model = None
    arch = (getattr(config, "architectures", None) or [None])[0]
    if arch:
        import transformers

        cls = getattr(transformers, arch, None)
        if cls is not None:
            print("Loading base with", arch)
            try:
                model = cls.from_pretrained(STOCK_MODEL, config=config, **load_kw)
            except Exception as exc:
                print("arch class load failed:", type(exc).__name__, exc)
                model = None
    if model is None:
        try:
            from transformers import AutoModelForCausalLM

            print("Loading base with AutoModelForCausalLM")
            model = AutoModelForCausalLM.from_pretrained(STOCK_MODEL, **load_kw)
        except Exception as exc:
            print("AutoModelForCausalLM failed:", type(exc).__name__, exc)
            from transformers import AutoModel

            print("Loading base with AutoModel")
            model = AutoModel.from_pretrained(STOCK_MODEL, **load_kw)

    print("Applying adapter")
    model = PeftModel.from_pretrained(model, adapter)
    print("merge_and_unload on CPU...")
    model = model.merge_and_unload()
    os.makedirs(merged, exist_ok=True)
    model.save_pretrained(merged, max_shard_size="2GB", safe_serialization=True)
    tokenizer.save_pretrained(merged)
    del model
    _free_cuda()


def _force_cpu_merge() -> bool:
    return (os.environ.get("SFT_MERGE_DEVICE") or "").strip().lower() in (
        "cpu",
        "peft-cpu",
        "peft_cpu",
    )


def _merge() -> None:
    work = _work_root()
    adapter = _adapter_path(work)
    merged = _merged_path(work)
    hf_home = (os.environ.get("HF_HOME") or "").strip() or os.path.join(work, "hf_home")
    os.makedirs(hf_home, exist_ok=True)
    os.environ.setdefault("HF_HOME", hf_home)

    if os.path.isfile(os.path.join(merged, "config.json")):
        print("Merged HF already exists — skip:", merged)
        return

    _download_adapter_if_missing(work, adapter)
    weights = os.path.join(adapter, "adapter_model.safetensors")
    want = (os.environ.get("EXPECTED_ADAPTER_SHA256") or EXPECTED_SHA_DEFAULT).strip()
    if want.lower() not in ("", "none", "skip"):
        got = _sha256_file(weights)
        if got.lower() != want.lower():
            raise SystemExit(f"SHA256 mismatch at merge time: {got}")

    if _force_cpu_merge():
        _merge_peft_cpu(adapter, merged)
    else:
        try:
            _merge_unsloth_gpu(adapter, merged)
        except Exception as exc:
            if not _is_oom(exc):
                raise
            print("GPU merge OOM — falling back to CPU PEFT merge:", type(exc).__name__)
            _free_cuda()
            _merge_peft_cpu(adapter, merged)

    _assert_merged_complete(merged)
    print("Merge complete:", merged)
    print(
        "GGUF note: load tokenizer FROM the merged folder when exporting "
        "(see bugs/ollama-tokenizer-corruption-fix)."
    )


def main() -> None:
    os.environ.setdefault("EXPECTED_ADAPTER_SHA256", EXPECTED_SHA_DEFAULT)
    parser = argparse.ArgumentParser(description="Merge Hub v2 CPT LoRA for GATE-0 SFT")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--cpu", action="store_true", help="Force CPU PEFT merge (A16 16GB fallback)")
    args = parser.parse_args()

    if args.cpu:
        os.environ["SFT_MERGE_DEVICE"] = "cpu"

    if args.preflight:
        _preflight()
        if not args.install:
            print("Preflight OK. Re-run without --preflight to merge (or pass --install).")
            return

    if args.install:
        _maybe_upgrade_torch_for_cu124()
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "--break-system-packages",
                "huggingface_hub",
                "peft",
                "transformers",
                UNSLOTH_PIP_SPEC,
            ]
        )
        print("Install done. Re-run without --install to merge.")
        return

    _preflight()
    _merge()


if __name__ == "__main__":
    main()
