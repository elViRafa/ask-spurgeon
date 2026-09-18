#!/usr/bin/env python3
"""SOTA SFT training v2 — data prep (D) + LoRA train (E) for RunPod/Kaggle.

Run on GPU pod after qa mix is on the volume:

    export SFT_WORK_ROOT=/workspace HF_HOME=/workspace/hf_home PYTHONUNBUFFERED=1
    export USE_CPT_MERGE=1
    export SFT_GATE0_MERGED=/workspace/theology_cpt_v2_merged_hf
    python3 -u train_sft_sota.py --preflight
    python3 -u train_sft_sota.py --install   # first boot
    python3 -u train_sft_sota.py

See fine_tuning/RUNPOD_RUNBOOK_SFT.md.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Must be set before Unsloth/torch.compile — Vast hosts often SIGSEGV at step 0 otherwise.
os.environ.setdefault("UNSLOTH_COMPILE_DISABLE", "1")
os.environ.setdefault("UNSLOTH_DISABLE_FAST_GENERATION", "1")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("CUDA_VISIBLE_DEVICES", "0"))
if "PYTORCH_CUDA_ALLOC_CONF" not in os.environ:
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

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


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here.parent.parent, Path("/workspace")):
        cfg = candidate / "config.py"
        if cfg.is_file():
            return candidate
    return here.parent.parent


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
    work = _work_root()
    if Path("/kaggle/working").is_dir():
        return Path("/kaggle/working")
    return work


def _maybe_upgrade_torch_for_cu124() -> None:
    try:
        import torch
    except ImportError:
        return
    ver = tuple(int(x) for x in torch.__version__.split("+")[0].split(".")[:2])
    if ver >= (2, 11):
        return
    print(f"Upgrading torch from {torch.__version__} -> 2.11.0+cu126")
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


def _canonical_system() -> str:
    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from config import SPURGEON_SFT_SYSTEM_PROMPT

    return SPURGEON_SFT_SYSTEM_PROMPT


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
    root = tok
    inner = text_tokenizer(tok)
    n0 = len(inner)
    targets = []
    for candidate in (root, inner):
        if candidate is not None and all(c is not candidate for c in targets):
            targets.append(candidate)

    eot_id = inner.convert_tokens_to_ids(EOT)
    if eot_id is None or int(eot_id) < 0:
        raise SystemExit(f"SFT token contract FAIL: {EOT} missing from vocab")

    for t in targets:
        t.padding_side = "right"
        # Always overwrite Unsloth placeholders (<EOS_TOKEN>, <|vision_pad|>).
        # TRL >=0.24 validates processing_class.eos_token against real vocab ids.
        t.pad_token = EOT
        t.pad_token_id = eot_id
        t.eos_token = EOT
        t.eos_token_id = eot_id
        if not getattr(t, "chat_template", None):
            t.chat_template = QWEN35_SFT_CHATML

    for t in (IM_START, IM_END, EOT):
        ids = inner(t, add_special_tokens=False)["input_ids"]
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], (list, tuple)):
            ids = list(ids[0])
        assert len(ids) == 1, f"{t} not atomic: {ids}"
        print(t, "->", ids[0], "(atomic)")
    im_end_id = inner.convert_tokens_to_ids(IM_END)
    assert inner.pad_token_id != im_end_id, "pad must not be <|im_end|>"
    assert inner.pad_token_id == eot_id, "pad must be <|endoftext|>"
    assert len(inner) == n0, "vocab resize during S2 — abort"
    print("pad:", inner.pad_token, inner.pad_token_id, "eos:", inner.eos_token, inner.eos_token_id)
    return inner, im_end_id, eot_id


def _filter_kwargs(callable_obj, kwargs: dict) -> dict:
    """Keep only kwargs accepted by callable_obj (drops obsolete TRL args)."""
    try:
        params = inspect.signature(callable_obj).parameters
    except (TypeError, ValueError):
        return dict(kwargs)
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        # UnslothSFTTrainer accepts **kwargs then forwards to TRL — do NOT pass
        # obsolete keys (dataset_text_field) or TRL 0.18+ raises TypeError.
        return {k: v for k, v in kwargs.items() if k in params and k != "kwargs"}
    return {k: v for k, v in kwargs.items() if k in params}


def _qa_mix_root(work: Path) -> Path:
    kaggle = Path("/kaggle/input/datasets/spurgeon-qa-mix-v1")
    if kaggle.is_dir() and (kaggle / "qa_mix_train.jsonl").is_file():
        return kaggle
    local = work / "spurgeon-qa-mix-v1"
    if (local / "qa_mix_train.jsonl").is_file():
        return local
    repo = _repo_root()
    data = repo / "fine_tuning" / "data"
    if (data / "qa_mix_train.jsonl").is_file():
        return data
    raise FileNotFoundError("qa_mix_train.jsonl not found under kaggle shim or fine_tuning/data")


def _preflight() -> None:
    work = _work_root()
    use_merge = os.environ.get("USE_CPT_MERGE", "0").strip().lower() in ("1", "true", "yes")
    gate0 = os.environ.get("SFT_GATE0_MERGED", RUNPOD_GATE0 if work == Path("/workspace") else KAGGLE_GATE0)
    base = gate0 if use_merge else STOCK_MODEL

    hf_home = (os.environ.get("HF_HOME") or "").strip() or str(work / "hf_home")
    os.makedirs(hf_home, exist_ok=True)
    print("preflight WORK_ROOT", work)
    print("preflight USE_CPT_MERGE", use_merge)
    print("preflight BASE_MODEL", base)

    if use_merge and not Path(base).joinpath("config.json").is_file():
        raise SystemExit(f"preflight FAIL: GATE-0 merged HF missing at {base}")

    root = _qa_mix_root(work)
    for name in ("qa_mix_train.jsonl", "qa_mix_val.jsonl"):
        if not (root / name).is_file():
            raise SystemExit(f"preflight FAIL: missing {root / name}")

    import torch

    if not torch.cuda.is_available():
        raise SystemExit("preflight FAIL: CUDA not available")
    print("preflight GPU", torch.cuda.get_device_name(0))
    print("Preflight OK")


def _dataprep(max_seq_length: int = 4096) -> tuple[Path, Path]:
    import numpy as np
    from datasets import Dataset

    work = _work_root()
    kwork = _kaggle_working()
    out_train = kwork / "qa_dataset_train"
    out_val = kwork / "qa_dataset_val"
    if out_train.is_dir() and out_val.is_dir():
        print("Tokenized datasets exist — skip D prep:", out_train, out_val)
        return out_train, out_val

    root = _qa_mix_root(work)
    canonical = _canonical_system()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from sft_stop_token_utils import load_qwen35_tokenizer

        tokenizer = load_qwen35_tokenizer(STOCK_MODEL)
    except ImportError:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(STOCK_MODEL, trust_remote_code=True)
    tokenizer, _, _ = apply_sft_special_token_contract(tokenizer)

    def load_jsonl(path: Path):
        rows = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def build_ds(jsonl_path: Path):
        texts = []
        for ex in load_jsonl(jsonl_path):
            msgs = ex["messages"]
            if msgs[0]["content"] != canonical:
                msgs = [{"role": "system", "content": canonical}] + msgs[1:]
            texts.append(
                {
                    "text": tokenizer.apply_chat_template(
                        msgs, tokenize=False, add_generation_prompt=False
                    ),
                    "messages": msgs,
                }
            )
        return Dataset.from_list(texts)

    train_ds = build_ds(root / "qa_mix_train.jsonl")
    val_ds = build_ds(root / "qa_mix_val.jsonl")
    print("train/val:", len(train_ds), len(val_ds))

    lens = [len(tokenizer(x["text"])["input_ids"]) for x in train_ds]
    print("S1 p50/p90/p99/max:", np.percentile(lens, [50, 90, 99]).astype(int), max(lens))
    over = sum(length > max_seq_length for length in lens)
    pct = 100 * over / max(1, len(lens))
    print(f"over {max_seq_length}:", over, f"({pct:.1f}%)")
    if over > len(lens) * 0.02:
        print("WARNING: >2% examples exceed MAX_SEQ_LENGTH")

    out_train.mkdir(parents=True, exist_ok=True)
    out_val.mkdir(parents=True, exist_ok=True)
    train_ds.save_to_disk(str(out_train))
    val_ds.save_to_disk(str(out_val))
    print("Saved", out_train, out_val)
    return out_train, out_val


def _sft_backend() -> str:
    raw = (os.environ.get("SFT_BACKEND") or "unsloth").strip().lower()
    if raw in ("peft", "transformers", "hf", "no_unsloth"):
        return "peft"
    return "unsloth"


def _eval_strategy() -> str:
    """Eval strategy from env. Default ``no`` — mid-train eval OOMs on 24GB @ seq 2048."""
    raw = (os.environ.get("SFT_EVAL_STRATEGY") or "no").strip().lower()
    if raw in ("no", "none", "false", "0", "off"):
        return "no"
    if raw in ("epoch", "steps"):
        return raw
    return "no"


def _latest_checkpoint(ckpt_root: Path) -> str | None:
    if not ckpt_root.is_dir():
        return None
    candidates = sorted(
        (p for p in ckpt_root.glob("checkpoint-*") if p.is_dir()),
        key=lambda p: int(p.name.split("-", 1)[1]) if p.name.split("-", 1)[1].isdigit() else -1,
    )
    return str(candidates[-1]) if candidates else None


def _mask_assistant_labels(tokenizer, input_ids: list[int], response_part: str) -> list[int]:
    """Mask everything before the first assistant response (completion-only)."""
    resp = tokenizer.encode(response_part, add_special_tokens=False)
    if hasattr(resp, "tolist"):
        resp = resp.tolist()
    if resp and isinstance(resp[0], (list, tuple)):
        resp = list(resp[0])
    labels = [-100] * len(input_ids)
    n = len(resp)
    if n == 0:
        return list(input_ids)
    for i in range(0, len(input_ids) - n + 1):
        if input_ids[i : i + n] == resp:
            start = i + n
            labels[start:] = input_ids[start:]
            return labels
    # Fallback: train all tokens so we do not silently empty-supervise.
    return list(input_ids)


def _train() -> None:
    backend = _sft_backend()
    print("SFT_BACKEND:", backend)
    if backend == "peft":
        _train_peft()
    else:
        _train_unsloth()


def _train_peft() -> None:
    """Transformers + PEFT + TRL path (Unsloth SIGSEGVs on some Vast hosts)."""
    import torch
    from datasets import load_from_disk
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq
    from trl import SFTConfig, SFTTrainer

    work = _work_root()
    kwork = _kaggle_working()
    use_merge = os.environ.get("USE_CPT_MERGE", "0").strip().lower() in ("1", "true", "yes")
    gate0 = os.environ.get("SFT_GATE0_MERGED", RUNPOD_GATE0 if work == Path("/workspace") else KAGGLE_GATE0)
    base_model = gate0 if use_merge else STOCK_MODEL

    max_seq_length = int(os.environ.get("SFT_MAX_SEQ_LENGTH", "4096"))
    lora_rank = int(os.environ.get("SFT_LORA_RANK", "32"))
    per_device_batch = int(os.environ.get("SFT_PER_DEVICE_BATCH", "2"))
    grad_accum = int(os.environ.get("SFT_GRAD_ACCUM", "8"))
    num_epochs = int(os.environ.get("SFT_NUM_EPOCHS", "2"))
    learning_rate = float(os.environ.get("SFT_LEARNING_RATE", "1e-4"))
    seed = int(os.environ.get("SFT_SEED", "3407"))

    data_train, data_val = _dataprep(max_seq_length)
    out_dir = kwork / "spurgeon_qa_lora_v2"
    run_config = kwork / "sft_run_config.json"
    hf_home = (os.environ.get("HF_HOME") or "").strip() or str(work / "hf_home")
    os.makedirs(hf_home, exist_ok=True)

    print("BASE_MODEL:", base_model)
    print("USE_CPT_MERGE:", use_merge)
    print("PEFT path: bf16 LoRA (no Unsloth)")

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer, im_end_id, _ = apply_sft_special_token_contract(tokenizer)

    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        dtype=dtype,
        device_map="cuda",
        trust_remote_code=True,
    )
    model.enable_input_require_grads()
    model = get_peft_model(
        model,
        LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_rank,
            lora_alpha=lora_rank,
            lora_dropout=0.0,
            bias="none",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        ),
    )
    model.gradient_checkpointing_enable()
    if hasattr(model, "config"):
        model.config.use_cache = False
    tokenizer, im_end_id, _ = apply_sft_special_token_contract(tokenizer)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    train_ds = load_from_disk(str(data_train))
    val_ds = load_from_disk(str(data_val))
    drop_cols = [c for c in train_ds.column_names if c != "text"]
    if drop_cols:
        train_ds = train_ds.remove_columns(drop_cols)
    drop_cols_v = [c for c in val_ds.column_names if c != "text"]
    if drop_cols_v:
        val_ds = val_ds.remove_columns(drop_cols_v)
    print("Loaded", len(train_ds), len(val_ds), "cols", train_ds.column_names)

    steps_per_epoch = max(1, len(train_ds) // (per_device_batch * grad_accum))
    eval_strategy = _eval_strategy()
    eval_steps = int(os.environ.get("SFT_EVAL_STEPS") or max(200, steps_per_epoch // 2))
    save_steps = int(os.environ.get("SFT_SAVE_STEPS") or max(40, steps_per_epoch // 5))
    if eval_strategy == "steps" and save_steps % eval_steps != 0:
        # Keep saves aligned with eval only when both run on steps.
        save_steps = ((save_steps // eval_steps) + 1) * eval_steps
    per_device_eval_batch = int(os.environ.get("SFT_PER_DEVICE_EVAL_BATCH", "1"))
    print(
        "eval_strategy",
        eval_strategy,
        "eval_steps",
        eval_steps,
        "save_steps",
        save_steps,
        "eval_batch",
        per_device_eval_batch,
    )

    bf16 = torch.cuda.is_bf16_supported()
    sft_cfg_kwargs = dict(
        per_device_train_batch_size=per_device_batch,
        per_device_eval_batch_size=per_device_eval_batch,
        gradient_accumulation_steps=grad_accum,
        num_train_epochs=num_epochs,
        learning_rate=learning_rate,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        optim="adamw_torch",
        weight_decay=0.01,
        fp16=not bf16,
        bf16=bf16,
        logging_steps=10,
        eval_strategy=eval_strategy,
        eval_steps=eval_steps if eval_strategy == "steps" else None,
        save_strategy="steps",
        save_steps=save_steps,
        load_best_model_at_end=eval_strategy != "no",
        metric_for_best_model="eval_loss" if eval_strategy != "no" else None,
        seed=seed,
        report_to="none",
        output_dir=str(out_dir / "checkpoints"),
        dataset_text_field="text",
        packing=False,
        eos_token="<|endoftext|>",
        pad_token="<|endoftext|>",
        max_length=max_seq_length,
        gradient_checkpointing=True,
        prediction_loss_only=True,
    )
    # Drop None values — SFTConfig may reject explicit None for some fields.
    sft_cfg_kwargs = {k: v for k, v in sft_cfg_kwargs.items() if v is not None}
    sft_cfg_kwargs = _filter_kwargs(SFTConfig.__init__, sft_cfg_kwargs)
    if "max_length" not in sft_cfg_kwargs:
        cfg_params = inspect.signature(SFTConfig.__init__).parameters
        if "max_seq_length" in cfg_params:
            sft_cfg_kwargs["max_seq_length"] = max_seq_length
    sft_args = SFTConfig(**sft_cfg_kwargs)

    processing = text_tokenizer(tokenizer)
    sft_kwargs = dict(
        model=model,
        train_dataset=train_ds,
        args=sft_args,
    )
    if eval_strategy != "no":
        sft_kwargs["eval_dataset"] = val_ds
    trainer_params = inspect.signature(SFTTrainer.__init__).parameters
    if "processing_class" in trainer_params:
        sft_kwargs["processing_class"] = processing
    elif "tokenizer" in trainer_params:
        sft_kwargs["tokenizer"] = processing
    sft_kwargs = _filter_kwargs(SFTTrainer.__init__, sft_kwargs)
    print("SFTTrainer kwargs:", sorted(sft_kwargs.keys()))
    trainer = SFTTrainer(**sft_kwargs)

    response_part = "<|im_start|>assistant\n"

    def _map_mask(batch):
        out_labels = []
        for ids in batch["input_ids"]:
            if hasattr(ids, "tolist"):
                ids = ids.tolist()
            out_labels.append(_mask_assistant_labels(processing, ids, response_part))
        return {"labels": out_labels}

    if "input_ids" in trainer.train_dataset.column_names:
        trainer.train_dataset = trainer.train_dataset.map(_map_mask, batched=True)
        if trainer.eval_dataset is not None and "input_ids" in trainer.eval_dataset.column_names:
            trainer.eval_dataset = trainer.eval_dataset.map(_map_mask, batched=True)

    collator_tok = processing
    trainer.data_collator = DataCollatorForSeq2Seq(
        collator_tok, padding=True, label_pad_token_id=-100
    )
    print("data_collator", type(trainer.data_collator).__name__)

    row = trainer.train_dataset[0]
    ids, labs = row["input_ids"], row["labels"]
    if hasattr(ids, "tolist"):
        ids, labs = ids.tolist(), labs.tolist()
    kept = [t for t, label in zip(ids, labs) if label != -100]
    decoded = tokenizer.decode(kept)
    assert im_end_id in kept, "S3 FAIL: <|im_end|> not in supervised labels"
    assert "<|im_start|>user" not in decoded, "S3 FAIL: user turn leaked into labels"
    s3_audit = {
        "phase": "s3_train_mask",
        "backend": "peft",
        "im_end_id": im_end_id,
        "im_end_in_supervised": im_end_id in kept,
        "supervised_fraction": round(len(kept) / max(1, len(ids)), 4),
        "supervised_decode_tail": decoded[-120:],
        "pass": True,
    }
    (kwork / "stop_token_s3_audit.json").write_text(json.dumps(s3_audit, indent=2), encoding="utf-8")
    print("S3 masking OK, supervised fraction:", f"{len(kept) / max(1, len(ids)):.1%}")
    print("Wrote", kwork / "stop_token_s3_audit.json")

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    resume_env = (os.environ.get("SFT_RESUME_FROM_CHECKPOINT") or "").strip()
    resume_ckpt = resume_env or _latest_checkpoint(out_dir / "checkpoints")
    if resume_ckpt:
        print("Resuming from checkpoint:", resume_ckpt)
    else:
        print("No checkpoint — starting fresh")
    stats = trainer.train(resume_from_checkpoint=resume_ckpt if resume_ckpt else None)
    print(stats)

    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out_dir / "lora"))
    tokenizer.save_pretrained(str(out_dir / "lora"))

    cfg = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "peft",
        "base_model": base_model,
        "use_cpt_merge": use_merge,
        "max_seq_length": max_seq_length,
        "lora_rank": lora_rank,
        "epochs": num_epochs,
        "train_rows": len(train_ds),
        "val_rows": len(val_ds),
        "peak_vram_gb": round(torch.cuda.max_memory_reserved() / 1e9, 2)
        if torch.cuda.is_available()
        else None,
    }
    try:
        cfg["pip_freeze"] = subprocess.check_output(["pip", "freeze"], text=True)[:8000]
    except Exception:
        pass
    run_config.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print("Saved adapter to", out_dir / "lora")
    print("Run config:", run_config)
    print("SOTA SFT v2 complete")


def _train_unsloth() -> None:
    import torch
    from datasets import load_from_disk
    from transformers import DataCollatorForSeq2Seq
    # Unsloth must patch before TRL import — otherwise SFTConfig.eos_token
    # gets overwritten to placeholder "<EOS_TOKEN>" (unsloth#2797).
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only
    from trl import SFTConfig, SFTTrainer

    work = _work_root()
    kwork = _kaggle_working()
    use_merge = os.environ.get("USE_CPT_MERGE", "0").strip().lower() in ("1", "true", "yes")
    gate0 = os.environ.get("SFT_GATE0_MERGED", RUNPOD_GATE0 if work == Path("/workspace") else KAGGLE_GATE0)
    base_model = gate0 if use_merge else STOCK_MODEL

    max_seq_length = int(os.environ.get("SFT_MAX_SEQ_LENGTH", "4096"))
    lora_rank = int(os.environ.get("SFT_LORA_RANK", "32"))
    per_device_batch = int(os.environ.get("SFT_PER_DEVICE_BATCH", "2"))
    grad_accum = int(os.environ.get("SFT_GRAD_ACCUM", "8"))
    num_epochs = int(os.environ.get("SFT_NUM_EPOCHS", "2"))
    learning_rate = float(os.environ.get("SFT_LEARNING_RATE", "1e-4"))
    seed = int(os.environ.get("SFT_SEED", "3407"))

    data_train, data_val = _dataprep(max_seq_length)
    out_dir = kwork / "spurgeon_qa_lora_v2"
    run_config = kwork / "sft_run_config.json"

    hf_home = (os.environ.get("HF_HOME") or "").strip() or str(work / "hf_home")
    os.makedirs(hf_home, exist_ok=True)
    os.makedirs(kwork / "unsloth_offload", exist_ok=True)

    print("BASE_MODEL:", base_model)
    print("USE_CPT_MERGE:", use_merge)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )
    tokenizer, im_end_id, _ = apply_sft_special_token_contract(tokenizer)

    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_rank,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=lora_rank,
        lora_dropout=0,
        bias="none",
        # "unsloth" checkpointing + smart gradient offload segfaults on some
        # Vast fractional-GPU / TRL 0.24 stacks at the first train step.
        use_gradient_checkpointing=True,
        random_state=seed,
    )
    # get_peft_model / Unsloth may reinject <EOS_TOKEN> — re-assert before TRL.
    tokenizer, im_end_id, _ = apply_sft_special_token_contract(tokenizer)

    train_ds = load_from_disk(str(data_train))
    val_ds = load_from_disk(str(data_val))
    # Prefer ChatML `text` for train_on_responses_only. Drop `messages` so TRL
    # 0.24+ does not auto-switch to conversational formatting.
    drop_cols = [c for c in train_ds.column_names if c != "text"]
    if drop_cols:
        train_ds = train_ds.remove_columns(drop_cols)
    drop_cols_v = [c for c in val_ds.column_names if c != "text"]
    if drop_cols_v:
        val_ds = val_ds.remove_columns(drop_cols_v)
    print("Loaded", len(train_ds), len(val_ds), "cols", train_ds.column_names)

    steps_per_epoch = max(1, len(train_ds) // (per_device_batch * grad_accum))
    eval_strategy = _eval_strategy()
    eval_steps = int(os.environ.get("SFT_EVAL_STEPS") or max(200, steps_per_epoch // 2))
    save_steps = int(os.environ.get("SFT_SAVE_STEPS") or max(40, steps_per_epoch // 5))
    if eval_strategy == "steps" and save_steps % eval_steps != 0:
        save_steps = ((save_steps // eval_steps) + 1) * eval_steps
    per_device_eval_batch = int(os.environ.get("SFT_PER_DEVICE_EVAL_BATCH", "1"))
    print(
        "eval_strategy",
        eval_strategy,
        "eval_steps",
        eval_steps,
        "save_steps",
        save_steps,
        "eval_batch",
        per_device_eval_batch,
    )

    bf16 = torch.cuda.is_bf16_supported()
    # TRL >=0.18: dataset_text_field / packing / max_length live on SFTConfig only.
    # Never pass them to SFTTrainer — Unsloth **kwargs forwards them and TRL raises.
    sft_cfg_kwargs = dict(
        per_device_train_batch_size=per_device_batch,
        per_device_eval_batch_size=per_device_eval_batch,
        gradient_accumulation_steps=grad_accum,
        num_train_epochs=num_epochs,
        learning_rate=learning_rate,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        optim="adamw_8bit",
        weight_decay=0.01,
        fp16=not bf16,
        bf16=bf16,
        logging_steps=10,
        eval_strategy=eval_strategy,
        eval_steps=eval_steps if eval_strategy == "steps" else None,
        save_strategy="steps",
        save_steps=save_steps,
        load_best_model_at_end=eval_strategy != "no",
        metric_for_best_model="eval_loss" if eval_strategy != "no" else None,
        seed=seed,
        report_to="none",
        output_dir=str(out_dir / "checkpoints"),
        dataset_text_field="text",
        packing=False,
        # Real vocab tokens (not Unsloth's <EOS_TOKEN> placeholder).
        eos_token="<|endoftext|>",
        pad_token="<|endoftext|>",
        max_length=max_seq_length,
        gradient_checkpointing=True,
        prediction_loss_only=True,
    )
    sft_cfg_kwargs = {k: v for k, v in sft_cfg_kwargs.items() if v is not None}
    sft_cfg_kwargs = _filter_kwargs(SFTConfig.__init__, sft_cfg_kwargs)
    if "max_length" not in sft_cfg_kwargs:
        cfg_params = inspect.signature(SFTConfig.__init__).parameters
        if "max_seq_length" in cfg_params:
            sft_cfg_kwargs["max_seq_length"] = max_seq_length
    sft_args = SFTConfig(**sft_cfg_kwargs)

    processing = text_tokenizer(tokenizer)
    sft_kwargs = dict(
        model=model,
        train_dataset=train_ds,
        args=sft_args,
    )
    if eval_strategy != "no":
        sft_kwargs["eval_dataset"] = val_ds
    trainer_params = inspect.signature(SFTTrainer.__init__).parameters
    if "processing_class" in trainer_params:
        sft_kwargs["processing_class"] = processing
    elif "tokenizer" in trainer_params:
        sft_kwargs["tokenizer"] = processing
    else:
        sft_kwargs["processing_class"] = processing
    sft_kwargs = _filter_kwargs(SFTTrainer.__init__, sft_kwargs)
    print("SFTTrainer kwargs:", sorted(sft_kwargs.keys()))
    trainer = SFTTrainer(**sft_kwargs)

    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|im_start|>user\n",
        response_part="<|im_start|>assistant\n",
    )
    # Keep Unsloth/TRL collator after train_on_responses_only when possible.
    # Forcing DataCollatorForSeq2Seq(TokenizersBackend) segfaulted at step 0 on
    # Vast TRL 0.24 / Unsloth 2026.9.2 (exit 139). Only override if needed.
    if trainer.data_collator is None:
        collator_tok = processing
        if not hasattr(collator_tok, "pad") and hasattr(collator_tok, "tokenizer"):
            collator_tok = collator_tok.tokenizer
        trainer.data_collator = DataCollatorForSeq2Seq(
            collator_tok, padding=True, label_pad_token_id=-100
        )
    print(
        "data_collator",
        type(trainer.data_collator).__name__ if trainer.data_collator else None,
    )

    row = trainer.train_dataset[0]
    ids, labs = row["input_ids"], row["labels"]
    if hasattr(ids, "tolist"):
        ids, labs = ids.tolist(), labs.tolist()
    kept = [t for t, label in zip(ids, labs) if label != -100]
    decoded = tokenizer.decode(kept)
    assert im_end_id in kept, "S3 FAIL: <|im_end|> not in supervised labels"
    assert "<|im_start|>user" not in decoded, "S3 FAIL: user turn leaked into labels"
    s3_audit = {
        "phase": "s3_train_mask",
        "im_end_id": im_end_id,
        "im_end_in_supervised": im_end_id in kept,
        "supervised_fraction": round(len(kept) / max(1, len(ids)), 4),
        "supervised_decode_tail": decoded[-120:],
        "pass": True,
    }
    (kwork / "stop_token_s3_audit.json").write_text(json.dumps(s3_audit, indent=2), encoding="utf-8")
    print("S3 masking OK, supervised fraction:", f"{len(kept) / max(1, len(ids)):.1%}")
    print("Wrote", kwork / "stop_token_s3_audit.json")

    stats = trainer.train()
    print(stats)

    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out_dir / "lora"))
    tokenizer.save_pretrained(str(out_dir / "lora"))

    cfg = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "unsloth",
        "base_model": base_model,
        "use_cpt_merge": use_merge,
        "max_seq_length": max_seq_length,
        "lora_rank": lora_rank,
        "epochs": num_epochs,
        "train_rows": len(train_ds),
        "val_rows": len(val_ds),
        "peak_vram_gb": round(torch.cuda.max_memory_reserved() / 1e9, 2)
        if torch.cuda.is_available()
        else None,
    }
    try:
        cfg["pip_freeze"] = subprocess.check_output(["pip", "freeze"], text=True)[:8000]
    except Exception:
        pass
    run_config.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print("Saved adapter to", out_dir / "lora")
    print("Run config:", run_config)
    print("SOTA SFT v2 complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="SOTA SFT train (D+E)")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--dataprep-only", action="store_true")
    args = parser.parse_args()

    if args.preflight:
        _preflight()
        if not args.install:
            print("Preflight OK. Re-run without --preflight to train (or pass --install).")
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
                "datasets",
                "peft",
                "trl",
                "transformers",
                UNSLOTH_PIP_SPEC,
            ]
        )
        print("Install done. Re-run without --install to train.")
        return

    if args.dataprep_only:
        _dataprep()
        return

    _preflight()
    _train()


if __name__ == "__main__":
    main()
