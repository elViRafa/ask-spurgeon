#!/usr/bin/env python3
"""Exact-match remap of the old Spurgeon-persona system prompt.

Does not rebuild the mix. Fails if a system string is neither the old persona
prompt nor the current config.SPURGEON_SFT_SYSTEM_PROMPT.

Usage (repo root):
  python fine_tuning/scripts/remap_qa_mix_system_prompt.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from config import SPURGEON_SFT_SYSTEM_PROMPT  # noqa: E402
from build_qa_mix import read_jsonl  # noqa: E402

OLD_PERSONA_PROMPT = (
    "You are Charles Haddon Spurgeon (1834–1892). Answer using only the information in the "
    "provided CONTEXT from your sermons. Stay faithful to the text: do not invent facts, "
    "quotes, or citations not supported by the context.\n\n"
    "If the CONTEXT does not contain enough information to answer the question, say so briefly "
    "in your own voice—do not speculate or apologize at length.\n\n"
    "When you draw on a specific sermon passage, cite it inline as [Sermon N] when the header "
    "is present in the context."
)

JSONL_FILES = (
    "qa_mix_train.jsonl",
    "qa_mix_val.jsonl",
    "qa_test_frozen.jsonl",
    "qa_rewrite_pilot/qa_gold_rewrite_pilot.jsonl",
    "qa_rewrite_pilot/bulk_pending.jsonl",
)


def remap_system(text: str) -> str:
    if text == SPURGEON_SFT_SYSTEM_PROMPT:
        return text
    if text == OLD_PERSONA_PROMPT:
        return SPURGEON_SFT_SYSTEM_PROMPT
    raise ValueError(f"unexpected system prompt ({len(text)} chars): {text[:80]!r}")


def remap_messages_file(path: Path) -> tuple[int, int]:
    rows = read_jsonl(path)
    replaced = 0
    already = 0
    for row in rows:
        msgs = row.get("messages") or []
        for msg in msgs:
            if msg.get("role") != "system":
                continue
            old = msg["content"]
            new = remap_system(old)
            if new != old:
                msg["content"] = new
                replaced += 1
            else:
                already += 1
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)
    return replaced, already


def remap_sample_json(path: Path) -> tuple[int, int]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    replaced = 0
    already = 0
    for row in rows:
        old = row["system"]
        new = remap_system(old)
        if new != old:
            row["system"] = new
            replaced += 1
        else:
            already += 1
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return replaced, already


def main() -> int:
    data = _REPO / "fine_tuning" / "data"
    total_r = 0
    total_a = 0
    for rel in JSONL_FILES:
        path = data / rel
        if not path.exists():
            print(f"SKIP missing {path.relative_to(_REPO)}")
            continue
        try:
            replaced, already = remap_messages_file(path)
        except ValueError as e:
            print(f"ERROR {path}: {e}", file=sys.stderr)
            return 2
        print(f"{path.relative_to(_REPO)}: replaced={replaced} already={already}")
        total_r += replaced
        total_a += already

    sample = data / "qa_rewrite_pilot" / "sample.json"
    if sample.exists():
        try:
            replaced, already = remap_sample_json(sample)
        except ValueError as e:
            print(f"ERROR {sample}: {e}", file=sys.stderr)
            return 2
        print(f"{sample.relative_to(_REPO)}: replaced={replaced} already={already}")
        total_r += replaced
        total_a += already

    print(f"Done replaced={total_r} already_new={total_a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
