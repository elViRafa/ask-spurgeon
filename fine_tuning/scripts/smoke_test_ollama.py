#!/usr/bin/env python3
"""
Ollama smoke test for Spurgeon SFT v2 exports.

Rejects models that emit vocab-shift junk (pist/spep/Chinese artifacts)
or fail stop-token compliance at temp 0 (Phase 5).

Usage:
  python fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2
  python fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2 --host http://localhost:11434
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO = _SCRIPT_DIR.parent.parent
for search_path in (_SCRIPT_DIR, _REPO):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

from config import SPURGEON_SFT_SYSTEM_PROMPT  # noqa: E402
from sft_stop_token_utils import analyze_generation, summarize_stop_metrics  # noqa: E402

BATTERY = [
    "what is hell?",
    "who is the king of kings?",
    "What does Spurgeon teach about Romans 8:28?",
]


def ollama_generate(host: str, model: str, prompt: str, temperature: float = 0.0) -> dict:
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
                "temperature": temperature,
                "num_predict": 256,
                "stop": ["<|im_end|>"],
            },
        }
    ).encode()
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ollama smoke test for Spurgeon QA model")
    p.add_argument("--model", default="spurgeon-qa-v2")
    p.add_argument("--host", default="http://localhost:11434")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument(
        "--out",
        default=str(_SCRIPT_DIR.parent / "eval_results" / "ollama_smoke.json"),
        help="Persist prompts, full responses, and stop summary as JSON",
    )
    p.add_argument(
        "--skip-stop-check",
        action="store_true",
        help="Only reject corrupt tokens (legacy behavior)",
    )
    args = p.parse_args(argv)

    stop_rows: list[dict] = []
    corrupt_failures: list[str] = []

    for prompt in BATTERY:
        try:
            result = ollama_generate(args.host, args.model, prompt, args.temperature)
        except urllib.error.URLError as e:
            print(f"FAIL connect: {e}", file=sys.stderr)
            return 2
        text = result.get("response", "")
        row = analyze_generation(text)
        row["prompt"] = prompt
        row["response"] = text
        row["done_reason"] = result.get("done_reason")
        # Ollama strips stop sequences from the returned text; treat API stop as im_end success.
        if row.get("done_reason") == "stop" and not row.get("leaked_turn"):
            row["ended_with_im_end"] = True
            row["ok"] = (not row.get("corrupt")) and (not row.get("leaked_turn"))
        stop_rows.append(row)
        corrupt = row.get("corrupt", False)
        status = "FAIL" if corrupt else "PASS"
        print(f"\n[{status}] {prompt}")
        print(text[:500])
        if corrupt:
            corrupt_failures.append(prompt)

    summary = summarize_stop_metrics(stop_rows)
    print("\nStop-token summary:", json.dumps(summary, indent=2))
    report = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "host": args.host,
        "temperature": args.temperature,
        "probes": stop_rows,
        "summary": summary,
        "pass": not corrupt_failures and (args.skip_stop_check or summary["pass"]),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Wrote", out)

    if corrupt_failures:
        print(f"\nREJECT: corrupt output on {len(corrupt_failures)}/{len(BATTERY)} prompts", file=sys.stderr)
        return 1

    if not args.skip_stop_check and not summary["pass"]:
        print(
            "\nREJECT: stop-token phase 5 failed "
            f"(im_end_stop_rate={summary['im_end_stop_rate']}, "
            f"leaked_turn_rate={summary['leaked_turn_rate']})",
            file=sys.stderr,
        )
        print("Hint: ensure Modelfile stops include <|im_end|> and <|endoftext|>", file=sys.stderr)
        return 1

    print(f"\nOK: all {len(BATTERY)} smoke prompts clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
