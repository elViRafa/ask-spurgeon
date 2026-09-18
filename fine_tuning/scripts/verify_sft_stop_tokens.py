#!/usr/bin/env python3
"""Phased verification of SFT end-of-answer (stop) token contract.

Phases:
  0  Tokenizer audit (local, no GPU)
  1  Training template check on qa_mix sample (local, no GPU)
  2  CPT merged-base greedy stop probe (GPU)
  3  Post-SFT eval metrics analysis (local, reads sft_eval_metrics.json)
  4  Merged HF export tokenizer check (local/pod)
  5  Ollama serve smoke with stop compliance (local Ollama)

Examples:
  python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 0
  python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 1
  python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 2 --base /workspace/theology_cpt_v2_merged_hf
  python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 3 --metrics fine_tuning/kaggle/runpod_sft_gate0/sft_eval_metrics.json
  python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 4 --merged ./spurgeon_qa_v2_merged_hf
  python fine_tuning/scripts/verify_sft_stop_tokens.py --phase 5 --model spurgeon-qa-v2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_SCRIPT_DIR = Path(__file__).resolve().parent
for p in (_REPO, _SCRIPT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from sft_stop_token_utils import (  # noqa: E402
    IM_END,
    analyze_generation,
    apply_sft_special_token_contract,
    audit_tokenizer,
    load_qwen35_tokenizer,
    summarize_stop_metrics,
    template_has_assistant_stop,
)

STOCK_MODEL = "unsloth/Qwen3.5-4B-Base"
PROBE_PROMPTS = [
    "Answer in one short sentence: what is grace?",
    "Say 'hello' and stop.",
]


def phase0(model: str, out: Path | None) -> int:
    raw = load_qwen35_tokenizer(model)
    report = audit_tokenizer(raw, model_name=model)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Wrote", out)
    if report["errors"]:
        for e in report["errors"]:
            print("ERROR:", e, file=sys.stderr)
        return 2
    print("Phase 0 PASS", report["required_ids"])
    return 0


def phase1(data_root: Path | None, out: Path | None) -> int:
    sys.path.insert(0, str(_REPO))
    from config import SPURGEON_SFT_SYSTEM_PROMPT

    if data_root is None:
        data_root = _REPO / "fine_tuning" / "data"
    train_path = data_root / "qa_mix_train.jsonl"
    if not train_path.is_file():
        print(f"ERROR: missing {train_path}", file=sys.stderr)
        return 2

    row = json.loads(train_path.read_text(encoding="utf-8").splitlines()[0])
    msgs = row["messages"]
    if msgs[0]["content"] != SPURGEON_SFT_SYSTEM_PROMPT:
        msgs = [{"role": "system", "content": SPURGEON_SFT_SYSTEM_PROMPT}] + msgs[1:]

    tok = load_qwen35_tokenizer(STOCK_MODEL)
    tok, im_end_id, eot_id = apply_sft_special_token_contract(tok)
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    ok = template_has_assistant_stop(text)
    ids = tok(text)["input_ids"]
    report = {
        "phase": 1,
        "train_text_ends_with_im_end": ok,
        "im_end_id": im_end_id,
        "eot_id": eot_id,
        "seq_len": len(ids),
        "tail": text[-120:],
        "pass": ok,
    }
    if out:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Wrote", out)
    if not ok:
        print("Phase 1 FAIL: assistant turn missing im_end in training text", file=sys.stderr)
        return 2
    print("Phase 1 PASS: template ends assistant turn with", IM_END)
    return 0


def phase2(base: str, out: Path | None) -> int:
    import torch
    from unsloth import FastLanguageModel

    if not torch.cuda.is_available():
        print("Phase 2 requires CUDA", file=sys.stderr)
        return 2

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base,
        max_seq_length=512,
        dtype=None,
        load_in_4bit=True,
    )
    tokenizer, im_end_id, eot_id = apply_sft_special_token_contract(tokenizer)
    FastLanguageModel.for_inference(model)

    sys.path.insert(0, str(_REPO))
    from config import SPURGEON_SFT_SYSTEM_PROMPT

    rows = []
    for prompt in PROBE_PROMPTS:
        messages = [
            {"role": "system", "content": SPURGEON_SFT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        chat = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(chat, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        out_ids = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=False,
            temperature=0.0,
            eos_token_id=[im_end_id, eot_id],
            pad_token_id=tokenizer.pad_token_id,
        )
        new_ids = out_ids[0][inputs["input_ids"].shape[1] :].tolist()
        text = tokenizer.decode(new_ids, skip_special_tokens=False)
        row = analyze_generation(text, raw_token_ids=new_ids, im_end_id=im_end_id, eot_id=eot_id)
        row["prompt"] = prompt
        rows.append(row)
        print(json.dumps(row, indent=2))

    summary = summarize_stop_metrics(rows)
    report = {"phase": 2, "base": base, "probes": rows, "summary": summary, "pass": summary["pass"]}
    if out:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Wrote", out)
    if not summary["pass"]:
        print("Phase 2 FAIL: CPT merged base stop probe", summary, file=sys.stderr)
        return 2
    print("Phase 2 PASS", summary)
    return 0


def phase3(metrics_path: Path, out: Path | None) -> int:
    if not metrics_path.is_file():
        print(f"ERROR: missing {metrics_path}", file=sys.stderr)
        return 2
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics_block = (
        ((data.get("candidate") or {}).get("metrics"))
        or data.get("metrics")
        or {}
    )
    saved_summary = metrics_block.get("stop_token")
    stop_probes = data.get("stop_probes") or [
        record.get("stop") for record in ((data.get("candidate") or {}).get("records") or [])
        if record.get("stop")
    ]
    if not stop_probes:
        print(
            "ERROR: metrics file must contain raw stop_probes for phase 3",
            file=sys.stderr,
        )
        return 2
    summary = summarize_stop_metrics(stop_probes)
    comparable_keys = (
        "n",
        "im_end_stop_rate",
        "corrupt_rate",
        "leaked_turn_rate",
        "stop_ok_rate",
        "pass",
    )
    if saved_summary and any(
        saved_summary.get(key) != summary.get(key) for key in comparable_keys
    ):
        print(
            "ERROR: saved metrics.stop_token disagrees with recomputed stop_probes",
            file=sys.stderr,
        )
        return 2
    report = {
        "phase": 3,
        "metrics_path": str(metrics_path),
        "summary": summary,
        "pass": summary["pass"],
    }
    if out:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Wrote", out)
    if not summary["pass"]:
        print("Phase 3 FAIL", summary, file=sys.stderr)
        return 2
    print("Phase 3 PASS", summary)
    return 0


def phase4(merged: Path, out: Path | None) -> int:
    cfg = merged / "config.json"
    if not cfg.is_file():
        print(f"ERROR: not a HF folder: {merged}", file=sys.stderr)
        return 2
    tok = load_qwen35_tokenizer(str(merged))
    report = audit_tokenizer(tok, model_name=str(merged))
    report["phase"] = 4
    report["pass"] = not report["errors"]
    if out:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Wrote", out)
    if report["errors"]:
        for e in report["errors"]:
            print("ERROR:", e, file=sys.stderr)
        return 2
    print("Phase 4 PASS: export tokenizer atomic im_end")
    return 0


def phase5(model: str, host: str, out: Path | None) -> int:
    import urllib.error
    import urllib.request

    from sft_stop_token_utils import CORRUPT_RE
    from config import SPURGEON_SFT_SYSTEM_PROMPT

    rows = []
    for prompt in PROBE_PROMPTS:
        raw_prompt = (
            f"<|im_start|>system\n{SPURGEON_SFT_SYSTEM_PROMPT}<|im_end|>\n"
            f"<|im_start|>user\n{prompt}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        body = json.dumps(
            {
                "model": model,
                "prompt": raw_prompt,
                "raw": True,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 200,
                    "stop": ["<|im_end|>"],
                },
            }
        ).encode()
        req = urllib.request.Request(
            f"{host.rstrip('/')}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.load(resp)
        except urllib.error.URLError as exc:
            print(f"Phase 5 FAIL connect: {exc}", file=sys.stderr)
            return 2
        text = result.get("response", "")
        done_reason = result.get("done_reason")
        row = analyze_generation(text, api_stop=done_reason == "stop")
        row["prompt"] = prompt
        row["done_reason"] = done_reason
        rows.append(row)
        print(json.dumps(row, indent=2))

    summary = summarize_stop_metrics(rows)
    report = {"phase": 5, "model": model, "host": host, "probes": rows, "summary": summary, "pass": summary["pass"]}
    if out:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("Wrote", out)
    if not summary["pass"]:
        print("Phase 5 FAIL: stop-token compliance", summary, file=sys.stderr)
        return 2
    print("Phase 5 PASS", summary)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Phased SFT stop-token verification")
    p.add_argument("--phase", type=int, choices=[0, 1, 2, 3, 4, 5], required=True)
    p.add_argument("--model", default=STOCK_MODEL, help="Phase 0 tokenizer model")
    p.add_argument("--base", default="", help="Phase 2 merged CPT HF path")
    p.add_argument("--merged", default="", help="Phase 4 SFT merged export path")
    p.add_argument("--metrics", default="", help="Phase 3 sft_eval_metrics.json path")
    p.add_argument("--ollama-model", default="spurgeon-qa-v2")
    p.add_argument("--ollama-host", default="http://localhost:11434")
    p.add_argument(
        "--out",
        default="",
        help="Write JSON report (default: fine_tuning/data/stop_token_phase<N>.json)",
    )
    args = p.parse_args(argv)

    out = Path(args.out) if args.out else _REPO / "fine_tuning" / "data" / f"stop_token_phase{args.phase}.json"

    if args.phase == 0:
        return phase0(args.model, out)
    if args.phase == 1:
        return phase1(None, out)
    if args.phase == 2:
        base = args.base or "/workspace/theology_cpt_v2_merged_hf"
        return phase2(base, out)
    if args.phase == 3:
        metrics = Path(args.metrics) if args.metrics else _REPO / "fine_tuning" / "kaggle" / "runpod_sft_gate0" / "sft_eval_metrics.json"
        return phase3(metrics, out)
    if args.phase == 4:
        if not args.merged:
            print("ERROR: --merged required for phase 4", file=sys.stderr)
            return 2
        return phase4(Path(args.merged), out)
    return phase5(args.ollama_model, args.ollama_host, out)


if __name__ == "__main__":
    raise SystemExit(main())
