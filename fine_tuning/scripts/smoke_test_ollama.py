#!/usr/bin/env python3
"""
Ollama smoke test for Spurgeon SFT v2 exports.

Rejects models that emit vocab-shift junk (pist/spep/Chinese artifacts).

Usage:
  python fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2
  python fine_tuning/scripts/smoke_test_ollama.py --model spurgeon-qa-v2 --host http://localhost:11434
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

CORRUPT_RE = re.compile(r"pist|spep|RGAR|据", re.I)
BATTERY = [
    "what is hell?",
    "who is the king of kings?",
    "What did you teach about Romans 8:28?",
]


def ollama_generate(host: str, model: str, prompt: str, temperature: float = 0.0) -> dict:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 256},
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
    args = p.parse_args(argv)

    failures: list[str] = []
    for prompt in BATTERY:
        try:
            result = ollama_generate(args.host, args.model, prompt, args.temperature)
        except urllib.error.URLError as e:
            print(f"FAIL connect: {e}", file=sys.stderr)
            return 2
        text = result.get("response", "")
        corrupt = bool(CORRUPT_RE.search(text))
        status = "FAIL" if corrupt else "PASS"
        print(f"\n[{status}] {prompt}")
        print(text[:500])
        if corrupt:
            failures.append(prompt)

    if failures:
        print(f"\nREJECT: corrupt output on {len(failures)}/{len(BATTERY)} prompts", file=sys.stderr)
        return 1

    print(f"\nOK: all {len(BATTERY)} smoke prompts clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
