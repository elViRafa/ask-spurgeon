#!/usr/bin/env python3
"""SOTA SFT eval + gated export (F) for RunPod/Kaggle.

    export SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
    export USE_CPT_MERGE=1
    export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
    export SFT_EXPORT=0
    python3 -u eval_sft_sota.py --install   # first boot
    python3 -u eval_sft_sota.py

Set SFT_EXPORT=1 only after §5 gates pass.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

STOCK_MODEL = "unsloth/Qwen3.5-4B-Base"
KAGGLE_GATE0 = "/kaggle/input/datasets/rafaelvieira1/theology-cpt-v2/theology_cpt_v2_merged_hf"
RUNPOD_GATE0 = "/workspace/theology_cpt_v2_merged_hf"
UNSLOTH_PIP_SPEC = "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
TORCH_CU126_INDEX = "https://download.pytorch.org/whl/cu126"

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

def _load_stop_utils():
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from sft_stop_token_utils import analyze_generation, summarize_stop_metrics

    return analyze_generation, summarize_stop_metrics


def _work_root() -> Path:
    explicit = (os.environ.get("SFT_WORK_ROOT") or "").strip()
    if explicit:
        return Path(explicit)
    if Path("/workspace").is_dir():
        return Path("/workspace")
    if Path("/kaggle/working").is_dir():
        return Path("/kaggle/working")
    return Path.cwd()


def _kaggle_working() -> Path:
    if Path("/kaggle/working").is_dir():
        return Path("/kaggle/working")
    return _work_root()


def _maybe_upgrade_torch_for_cu124() -> None:
    try:
        import torch
    except ImportError:
        return
    ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
    if ver >= (2, 8):
        return
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "--break-system-packages",
            "torch==2.8.0",
            "torchvision",
            "torchaudio",
            "--index-url",
            TORCH_CU126_INDEX,
        ]
    )


def text_tokenizer(tok):
    inner = tok
    for _ in range(4):
        nxt = getattr(inner, "tokenizer", None)
        if nxt is None or nxt is inner:
            break
        inner = nxt
    return inner


def apply_sft_special_token_contract(tok):
    IM_START, IM_END, EOT = "<|im_start|>", "<|im_end|>", "<|endoftext|>"
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
    assert len(tok) == n0, "vocab resize during S2 — abort"
    return tok, im_end_id, eot_id


def _test_jsonl(work: Path) -> Path:
    kaggle = Path("/kaggle/input/datasets/spurgeon-qa-mix-v1/qa_test_frozen.jsonl")
    if kaggle.is_file():
        return kaggle
    local = work / "spurgeon-qa-mix-v1" / "qa_test_frozen.jsonl"
    if local.is_file():
        return local
    repo = Path(__file__).resolve().parent.parent
    data = repo / "data" / "qa_test_frozen.jsonl"
    if data.is_file():
        return data
    raise FileNotFoundError("qa_test_frozen.jsonl not found")


def _eval_and_maybe_export() -> None:
    from unsloth import FastLanguageModel

    _load_stop_utils()
    from sft_eval_core import analyze_output, load_jsonl, release_gates, sha256_file, summarize_records

    work = _work_root()
    kwork = _kaggle_working()
    use_merge = os.environ.get("USE_CPT_MERGE", "0").strip().lower() in ("1", "true", "yes")
    gate0 = os.environ.get("SFT_GATE0_MERGED", RUNPOD_GATE0 if work == Path("/workspace") else KAGGLE_GATE0)
    base_model = gate0 if use_merge else STOCK_MODEL
    export = os.environ.get("SFT_EXPORT", "0").strip().lower() in ("1", "true", "yes")
    max_seq_length = int(os.environ.get("SFT_MAX_SEQ_LENGTH", "4096"))

    lora_dir = kwork / "spurgeon_qa_lora_v2" / "lora"
    out_metrics = kwork / "sft_eval_metrics.json"
    out_merged = kwork / "spurgeon_qa_v2_merged_hf"

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )
    tokenizer, im_end_id, eot_id = apply_sft_special_token_contract(tokenizer)
    IM_END = "<|im_end|>"

    if lora_dir.is_dir():
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(lora_dir))
    else:
        raise FileNotFoundError(f"LoRA adapter missing: {lora_dir}")

    FastLanguageModel.for_inference(model)

    def generate(messages, max_new_tokens=400):
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text=prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.0,
            eos_token_id=[im_end_id, eot_id],
            pad_token_id=tokenizer.pad_token_id,
        )
        new_ids = out[0][inputs["input_ids"].shape[1] :].tolist()
        raw = tokenizer.decode(new_ids, skip_special_tokens=False)
        pred = raw.split(IM_END)[0].strip() if IM_END in raw else raw.strip()
        return pred, raw, new_ids

    test_path = _test_jsonl(work)
    items = load_jsonl(test_path)
    records = []

    for index, ex in enumerate(items):
        msgs = ex["messages"]
        started = time.perf_counter()
        pred, raw, new_ids = generate(msgs[:-1])
        records.append(
            analyze_output(
                index,
                msgs,
                pred,
                raw_text=raw,
                raw_token_ids=new_ids,
                im_end_id=im_end_id,
                eot_id=eot_id,
                latency_seconds=round(time.perf_counter() - started, 4),
            )
        )
        print(f"Evaluated {index + 1}/{len(items)}", flush=True)

    metrics = summarize_records(records)
    gates = release_gates(metrics)
    payload = {
        "schema_version": "1.0",
        "dataset": {
            "path": str(test_path),
            "sha256": sha256_file(test_path),
            "declared_count": len(items),
            "evaluated_count": len(records),
        },
        "model": {"base": str(base_model), "adapter": str(lora_dir)},
        "generation": {"temperature": 0.0, "max_new_tokens": 400},
        "metrics": metrics,
        "gates": gates,
        "records": records,
        # Compatibility aliases used by phase 3 and older fetch tooling.
        "samples": [
            {"q": row["question"], "pred": row["prediction"]} for row in records
        ],
        "stop_probes": [row["stop"] for row in records],
    }
    out_metrics.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print("Stop-token phase 3:", json.dumps(metrics["stop_token"]))
    if not metrics["stop_token"]["pass"]:
        print("WARN: stop-token gates failed — do not set SFT_EXPORT=1", file=sys.stderr)
    print("Samples written to", out_metrics)

    if not export:
        print("SFT_EXPORT=0 — skip merge/GGUF/HF upload until §5 gates pass.")
        return

    approved_path = Path(os.environ.get("SFT_APPROVED_EVAL_REPORT", ""))
    if not approved_path.is_file():
        raise RuntimeError(
            "SFT_EXPORT=1 requires SFT_APPROVED_EVAL_REPORT with persisted passing gates"
        )
    approved = json.loads(approved_path.read_text(encoding="utf-8"))
    if not (approved.get("gates") or {}).get("pass"):
        raise RuntimeError("Approved evaluation report does not pass every release gate")
    if (approved.get("dataset") or {}).get("sha256") != sha256_file(test_path):
        raise RuntimeError("Approved evaluation dataset hash does not match this eval dataset")
    adapter_file = lora_dir / "adapter_model.safetensors"
    source_adapter = (approved.get("candidate") or {}).get("source_adapter") or {}
    if not adapter_file.is_file() or source_adapter.get("sha256") != sha256_file(adapter_file):
        raise RuntimeError("Approved evaluation source adapter does not match loaded SFT adapter")

    print("Merging 16-bit to", out_merged)
    model.save_pretrained_merged(str(out_merged), tokenizer, save_method="merged_16bit")
    tokenizer.save_pretrained(str(out_merged))
    print(
        "Next: convert to GGUF (f16 + Q4_K_M), upload, Ollama Modelfile, smoke_test_ollama.py"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="SOTA SFT eval (F)")
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()

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
                "peft",
                UNSLOTH_PIP_SPEC,
            ]
        )
        print("Install done. Re-run without --install to eval.")
        return

    _eval_and_maybe_export()


if __name__ == "__main__":
    main()
