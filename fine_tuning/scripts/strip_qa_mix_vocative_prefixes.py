#!/usr/bin/env python3
"""Strip leading vocative prefixes from qa_mix_train assistants.

Does not rewrite theology. Safe after gold/bulk merges.

Usage (repo root):
  python fine_tuning/scripts/strip_qa_mix_vocative_prefixes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_qa_mix import read_jsonl, repo_root  # noqa: E402
from qa_rewrite_checks import role, strip_leading_vocative  # noqa: E402


def main() -> int:
    train_path = repo_root() / "fine_tuning" / "data" / "qa_mix_train.jsonl"
    rows = read_jsonl(train_path)
    n = 0
    for row in rows:
        msgs = row["messages"]
        ans = role(msgs, "assistant")
        new = strip_leading_vocative(ans)
        if new != ans:
            n += 1
            for msg in msgs:
                if msg.get("role") == "assistant":
                    msg["content"] = new
                    break
    tmp = train_path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(train_path)
    print(f"Stripped leading vocatives on {n} train assistants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
