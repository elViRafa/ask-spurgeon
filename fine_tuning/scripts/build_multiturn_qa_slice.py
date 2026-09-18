#!/usr/bin/env python3
"""Build a 2-turn grounded follow-up slice matching build_chat_messages shape.

Shape (mirrors utils.prompts.build_chat_messages + Streamlit history):
  system
  user: bare prior QUESTION (no CONTEXT)           # history
  assistant: prior answer
  user: CONTEXT + QUESTION (follow-up)             # new retrieval turn
  assistant: follow-up answer (supervised target)

Writes a side JSONL. Does NOT patch qa_mix_train.

Usage (repo root):
  python fine_tuning/scripts/build_multiturn_qa_slice.py
  python fine_tuning/scripts/build_multiturn_qa_slice.py --target 100
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from config import SPURGEON_SFT_SYSTEM_PROMPT  # noqa: E402
from build_qa_mix import is_refusal, read_jsonl  # noqa: E402
from qa_rewrite_checks import QUOTE_RE, caricature_errors, context_of, norm_ws  # noqa: E402

SEED = 3407
OUT_JSONL = _REPO / "fine_tuning" / "data" / "qa_multiturn_slice.jsonl"
OUT_MANIFEST = _REPO / "fine_tuning" / "data" / "qa_multiturn_slice_manifest.json"
TRAIN = _REPO / "fine_tuning" / "data" / "qa_mix_train.jsonl"

_QUESTION_RE = re.compile(r"QUESTION:\s*(.+)\s*$", re.S)
_CITE_RE = re.compile(r"\[Sermon\s+\d+[^\]]*\]|\[Puritan Catechism Q\.\d+[^\]]*\]")

FOLLOWUPS = (
    "Can you say more about that from the same CONTEXT?",
    "Which part of the CONTEXT most clearly supports that point?",
    "How does the CONTEXT distinguish this from a related error?",
    "Please quote one short phrase from the CONTEXT that anchors your answer.",
    "What else in these excerpts bears on the same question?",
)


def bare_question(user: str) -> str:
    m = _QUESTION_RE.search(user)
    if not m:
        return ""
    return m.group(1).strip().split("\n")[0].strip()


def pick_quote(ctx: str, max_len: int = 140) -> str | None:
    # Prefer a mid-length sentence-ish span present in CONTEXT.
    text = ctx.strip()
    if len(text) < 24:
        return None
    # Skip header line(s)
    body = "\n".join(
        ln for ln in text.splitlines() if not ln.strip().startswith("[") and ln.strip()
    )
    body = body.strip() or text
    # Take a contiguous window of words.
    words = body.split()
    if len(words) < 6:
        candidate = body[:max_len]
    else:
        start = min(3, max(0, len(words) // 10))
        window = words[start : start + 18]
        candidate = " ".join(window)
        if len(candidate) > max_len:
            candidate = candidate[: max_len - 1].rsplit(" ", 1)[0]
    candidate = candidate.strip().strip('"')
    if len(candidate) < 12:
        return None
    if norm_ws(candidate) not in norm_ws(ctx):
        # Fall back to exact substring search for a short clause.
        for size in (12, 10, 8):
            for i in range(0, max(1, len(body) - size * 4), 17):
                chunk = body[i : i + size * 8].strip()
                if len(chunk) >= 12 and norm_ws(chunk) in norm_ws(ctx):
                    return chunk[:max_len]
        return None
    return candidate


def first_cite(ctx: str) -> str:
    m = _CITE_RE.search(ctx)
    return m.group(0) if m else "[Sermon ?]"


def followup_assistant(ctx: str, prior_ans: str) -> str | None:
    quote = pick_quote(ctx)
    if not quote:
        return None
    cite = first_cite(ctx)
    ans = (
        f'From the same excerpts: "{quote}" {cite} '
        f"That phrase anchors the prior point and keeps the answer inside the CONTEXT."
    )
    if caricature_errors(ans):
        return None
    ctx_n = norm_ws(ctx)
    if not any(norm_ws(q) in ctx_n for q in QUOTE_RE.findall(ans)):
        return None
    return ans


def source_key(row: dict, idx: int) -> str:
    raw = json.dumps(row.get("messages") or [], ensure_ascii=False)
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"mt-{idx}-{h}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build 2-turn grounded QA slice")
    p.add_argument("--target", type=int, default=100, help="Number of multi-turn rows to emit")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--train", default=str(TRAIN))
    p.add_argument("--output", default=str(OUT_JSONL))
    p.add_argument("--manifest", default=str(OUT_MANIFEST))
    args = p.parse_args(argv)

    train_path = Path(args.train)
    if not train_path.is_absolute():
        train_path = _REPO / train_path
    out_jsonl = Path(args.output)
    if not out_jsonl.is_absolute():
        out_jsonl = _REPO / out_jsonl
    out_manifest = Path(args.manifest)
    if not out_manifest.is_absolute():
        out_manifest = _REPO / out_manifest

    rows_in = read_jsonl(train_path)
    rng = random.Random(args.seed)
    candidates: list[tuple[int, dict]] = []
    for i, row in enumerate(rows_in):
        msgs = row.get("messages") or []
        if len(msgs) != 3:
            continue
        if is_refusal(row):
            continue
        user = next((m.get("content") or "" for m in msgs if m.get("role") == "user"), "")
        ans = next((m.get("content") or "" for m in msgs if m.get("role") == "assistant"), "")
        if "Puritan Catechism Q." in user:
            continue  # keep multi-turn sermon-shaped for now
        if not user.startswith("CONTEXT") or "QUESTION:" not in user:
            continue
        q0 = bare_question(user)
        ctx = context_of(user)
        if len(q0) < 8 or len(ctx) < 80 or len(ans) < 40:
            continue
        candidates.append((i, row))

    rng.shuffle(candidates)
    out_rows: list[dict] = []
    skipped = 0
    for idx, row in candidates:
        if len(out_rows) >= args.target:
            break
        msgs = row["messages"]
        user = next(m["content"] for m in msgs if m["role"] == "user")
        ans1 = next(m["content"] for m in msgs if m["role"] == "assistant")
        q0 = bare_question(user)
        ctx = context_of(user)
        # Rebuild user2 with same CONTEXT prefix + follow-up question.
        follow = FOLLOWUPS[len(out_rows) % len(FOLLOWUPS)]
        # Keep CONTEXT block identical to turn-1 user (everything before QUESTION).
        ctx_block = user.split("QUESTION:", 1)[0].rstrip()
        user2 = f"{ctx_block}\n\nQUESTION: {follow}"
        ans2 = followup_assistant(ctx, ans1)
        if not ans2:
            skipped += 1
            continue
        sid = source_key(row, idx)
        out_rows.append(
            {
                "id": sid,
                "slice": "multiturn",
                "source_train_index": idx,
                "messages": [
                    {"role": "system", "content": SPURGEON_SFT_SYSTEM_PROMPT},
                    {"role": "user", "content": q0},
                    {"role": "assistant", "content": ans1},
                    {"role": "user", "content": user2},
                    {"role": "assistant", "content": ans2},
                ],
            }
        )

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_train": str(train_path.relative_to(_REPO)).replace("\\", "/"),
        "rows": len(out_rows),
        "target": args.target,
        "skipped_no_quote": skipped,
        "seed": args.seed,
        "shape": "system,user(bare),assistant,user(CONTEXT+QUESTION),assistant",
        "serve_mirror": "utils.prompts.build_chat_messages + Streamlit bare-question history",
        "merge_into_train": False,
        "output": str(out_jsonl.relative_to(_REPO)).replace("\\", "/"),
    }
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_jsonl} rows={len(out_rows)} skipped={skipped}")
    print(f"Wrote {out_manifest}")
    return 0 if out_rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
