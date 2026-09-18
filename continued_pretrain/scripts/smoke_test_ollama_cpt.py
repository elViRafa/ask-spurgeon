#!/usr/bin/env python3
"""Ollama smoke test for CPT completion model (greedy probes from eval_cpt_sota)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

CORRUPT_RE = re.compile(r"pist|spep|RGAR|据", re.I)

STYLE = [
    "The love of Christ is not a cold, speculative thing. It is",
    "Text: Romans 8:28. 'And we know that all things work together for good to them that love God.' My dear friends,",
    "What, then, is saving faith? Let us examine this question carefully, for",
]
DOCTRINE = [
    "The Westminster Confession teaches that God from all eternity did,",
    "Justification is an act of God's free grace wherein He",
    "True saving faith rests upon Christ alone, for",
]
FORGETTING = [
    "The capital of France is",
    "Photosynthesis in green plants converts light energy into",
    "In the nineteenth century, the Industrial Revolution",
]


def ollama_generate(host: str, model: str, prompt: str, max_tokens: int) -> str:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": max_tokens},
        }
    ).encode()
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp).get("response", "")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ollama smoke test for CPT model")
    p.add_argument("--model", default="spurgeon-cpt")
    p.add_argument("--host", default="http://localhost:11434")
    args = p.parse_args(argv)

    failures: list[str] = []
    total = 0
    for label, prompts, max_tokens in [
        ("STYLE", STYLE, 120),
        ("DOCTRINE", DOCTRINE, 120),
        ("FORGETTING", FORGETTING, 40),
    ]:
        print(f"\n=== {label} ===")
        for prompt in prompts:
            total += 1
            try:
                text = ollama_generate(args.host, args.model, prompt, max_tokens)
            except urllib.error.URLError as e:
                print(f"FAIL connect: {e}", file=sys.stderr)
                return 2
            corrupt = bool(CORRUPT_RE.search(text))
            status = "FAIL" if corrupt else "PASS"
            print(f"\n[{status}] {prompt[:90]}...")
            print(text[:500].encode("ascii", errors="replace").decode("ascii"))
            if corrupt:
                failures.append(prompt)

    if failures:
        print(f"\nREJECT: corrupt output on {len(failures)}/{total} prompts", file=sys.stderr)
        return 1

    print(f"\nOK: all {total} CPT probe prompts clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
