#!/usr/bin/env python3
"""Rotate QA teacher rewrites across cloud providers until each is exhausted.

Runs rewrite_qa_answers_teacher.py --apply in batches; on 3 consecutive API
failures (provider abort) switches to the next provider. Merges ok rows after
each batch that produced at least one ok answer.

Usage (repo root):
  python -u fine_tuning/scripts/rewrite_qa_rotate_providers.py
  python -u fine_tuning/scripts/rewrite_qa_rotate_providers.py --limit 30 --max-rounds 20
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl, repo_root  # noqa: E402
from rewrite_qa_answers_teacher import _provider_key  # noqa: E402

PROVIDERS: list[tuple[str, str]] = [
    ("cerebras", ""),
    ("groq", "openai/gpt-oss-120b"),
    ("groq", "openai/gpt-oss-20b"),
    ("openrouter", ""),
    ("gemini", ""),
    ("ollama", ""),
]


def _log(msg: str) -> None:
    text = str(msg)
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        sys.stdout.buffer.write(text.encode(enc, errors="replace") + b"\n")
        sys.stdout.flush()
    except Exception:
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"), flush=True)


def remaining_candidates(train_len: int, skip: set[int], done: set[int]) -> int:
    return sum(1 for i in range(1, train_len + 1) if i not in skip and i not in done)


def load_state(*, retry_drops: bool) -> tuple[int, set[int], set[int]]:
    repo = repo_root()
    data = repo / "fine_tuning" / "data"
    train = read_jsonl(data / "qa_mix_train.jsonl")
    manifest = json.loads((data / "qa_mix_manifest.json").read_text(encoding="utf-8"))
    skip = {int(n) for n in (manifest.get("gold_overlay") or {}).get("source_lines") or []}
    pending_path = data / "qa_rewrite_pilot" / "bulk_pending.jsonl"
    done: set[int] = set()
    if pending_path.exists():
        for rec in read_jsonl(pending_path):
            if retry_drops:
                if rec.get("ok") is True:
                    done.add(int(rec["source_line"]))
            else:
                done.add(int(rec["source_line"]))
    return len(train), skip, done


def run_merge_pipeline() -> bool:
    py = sys.executable
    root = repo_root()
    for script in (
        "fine_tuning/scripts/review_qa_rewrite_bulk.py",
        "fine_tuning/scripts/merge_qa_bulk_rewrite.py",
        "fine_tuning/scripts/audit_qa_mix_quality.py",
    ):
        _log(f"==> {script}")
        proc = subprocess.run([py, str(root / script)], cwd=root)
        if proc.returncode != 0:
            _log(f"WARN: {script} exited {proc.returncode}; continuing rotation")
            return False
    return True


def run_batch(*, provider: str, model: str, limit: int, sleep: float, retry_drops: bool) -> tuple[str, int]:
    py = sys.executable
    root = repo_root()
    cmd = [
        py,
        "-u",
        str(root / "fine_tuning" / "scripts" / "rewrite_qa_answers_teacher.py"),
        "--apply",
        "--limit",
        str(limit),
        "--provider",
        provider,
        "--sleep",
        str(sleep),
    ]
    if retry_drops:
        cmd.append("--retry-drops")
    if model:
        cmd.extend(["--model", model])
    _log(f"==> {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    _log(out.rstrip())
    return out, proc.returncode


def parse_batch(out: str) -> dict:
    stats = {
        "this_run": 0,
        "ok": 0,
        "dropped": 0,
        "abort": "Abort:" in out,
        "no_candidates": "this_run=0" in out,
    }
    m = re.search(r"this_run=(\d+)", out)
    if m:
        stats["this_run"] = int(m.group(1))
    m = re.search(r"ok=(\d+)\s+dropped=(\d+)", out)
    if m:
        stats["ok"] = int(m.group(1))
        stats["dropped"] = int(m.group(2))
    return stats


def available_providers() -> list[tuple[str, str]]:
    load_dotenv()
    out: list[tuple[str, str]] = []
    for provider, model in PROVIDERS:
        if provider == "ollama":
            try:
                import requests

                requests.get("http://localhost:11434/api/tags", timeout=3).raise_for_status()
            except Exception:
                continue
        elif not _provider_key(provider):
            continue
        out.append((provider, model))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Rotate QA teacher providers until exhausted")
    p.add_argument("--limit", type=int, default=30, help="Rows per rewrite batch")
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument(
        "--max-rounds",
        type=int,
        default=0,
        help="Max full provider cycles (0 = until all exhausted or no work)",
    )
    p.add_argument(
        "--providers",
        default="",
        help="Comma-separated subset, e.g. groq,openrouter,gemini (default: all with keys)",
    )
    p.add_argument("--no-merge", action="store_true", help="Skip review/merge/audit")
    p.add_argument(
        "--retry-drops",
        action="store_true",
        help="Re-attempt bulk_pending rows that failed validation (ok=false)",
    )
    args = p.parse_args(argv)

    if args.providers.strip():
        want = {x.strip().lower() for x in args.providers.split(",") if x.strip()}
        providers = [(p, m) for p, m in PROVIDERS if p in want]
        # Drop entries without keys (except ollama probe).
        filtered: list[tuple[str, str]] = []
        load_dotenv()
        for provider, model in providers:
            if provider == "ollama":
                try:
                    import requests

                    requests.get("http://localhost:11434/api/tags", timeout=3).raise_for_status()
                    filtered.append((provider, model))
                except Exception:
                    pass
            elif _provider_key(provider):
                filtered.append((provider, model))
        providers = filtered
    else:
        providers = available_providers()
    if not providers:
        _log("No providers available (missing keys / Ollama down).")
        return 2

    _log("Provider queue: " + ", ".join(f"{prov}{('/' + m) if m else ''}" for prov, m in providers))

    rounds = 0
    while True:
        if args.max_rounds and rounds >= args.max_rounds:
            _log(f"Stopped: max_rounds={args.max_rounds}")
            break
        rounds += 1
        any_provider_progress = False

        train_len, skip, done = load_state(retry_drops=args.retry_drops)
        left = remaining_candidates(train_len, skip, done)
        mode = "retry_drops" if args.retry_drops else "new"
        _log(f"\n=== Round {rounds} ({mode}) | remaining={left} done_keys={len(done)} ===")
        if left <= 0:
            _log("All train rows already in bulk_pending (or gold). Done.")
            break

        for provider, model in providers:
            train_len, skip, done = load_state(retry_drops=args.retry_drops)
            left = remaining_candidates(train_len, skip, done)
            if left <= 0:
                break

            label = f"{provider}" + (f"/{model}" if model else "")
            _log(f"\n--- Provider {label} ({left} rows left) ---")
            provider_ok_total = 0

            while True:
                out, code = run_batch(
                    provider=provider,
                    model=model,
                    limit=args.limit,
                    sleep=args.sleep,
                    retry_drops=args.retry_drops,
                )
                stats = parse_batch(out)
                provider_ok_total += stats["ok"]

                if stats["no_candidates"]:
                    _log("No candidates left.")
                    if not args.no_merge and provider_ok_total > 0:
                        run_merge_pipeline()
                    return 0

                if stats["ok"] > 0 and not args.no_merge:
                    run_merge_pipeline()

                if stats["abort"]:
                    _log(f"Provider {label} exhausted (abort). ok_this_batch={stats['ok']}")
                    break

                if stats["this_run"] == 0:
                    break

                if stats["ok"] == 0 and stats["dropped"] == 0 and code != 0:
                    _log(f"Provider {label} failed (exit {code}); switching.")
                    break

                any_provider_progress = True

                train_len, skip, done = load_state(retry_drops=args.retry_drops)
                if remaining_candidates(train_len, skip, done) <= 0:
                    break

            if provider_ok_total > 0:
                any_provider_progress = True

        if not any_provider_progress:
            _log("No provider made progress this round; stopping.")
            break

    if not args.no_merge:
        _log("\nFinal audit:")
        run_merge_pipeline()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
