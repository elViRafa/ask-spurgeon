#!/usr/bin/env python3
"""Build a Puritan Catechism CONTEXT slice for SFT (knowledge voice, not persona).

Writes a side JSONL. Does NOT patch qa_mix_train until RAG can retrieve the same
docs (see fine_tuning/scripts/ingest_catechism.py).

Usage (repo root):
  python fine_tuning/scripts/build_catechism_qa_slice.py
  python fine_tuning/scripts/build_catechism_qa_slice.py --limit 20
"""

from __future__ import annotations

import argparse
import json
import random
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
from qa_rewrite_checks import QUOTE_RE, caricature_errors, context_of, norm_ws  # noqa: E402

SEED = 3407
DEFAULT_SRC = _REPO / "data" / "catechism" / "puritan_catechism.json"
OUT_JSONL = _REPO / "fine_tuning" / "data" / "qa_catechism_slice.jsonl"
OUT_MANIFEST = _REPO / "fine_tuning" / "data" / "qa_catechism_slice_manifest.json"

# Alternate QUESTION lines for the same CONTEXT (merge key = Q.N|QUESTION).
QUESTION_VARIANTS = (
    "What does the Puritan Catechism teach regarding: {q}",
    "According to this catechism excerpt, {q}",
    "Summarize the catechism's answer to: {q}",
    "From the CONTEXT, how does the catechism answer: {q}",
    "Explain from this text: {q}",
)


def header_for(n: int, title: str = "Puritan Catechism") -> str:
    return f'[Puritan Catechism Q.{n} — "{title}"]'


def context_block(item: dict) -> str:
    n = int(item["Number"])
    q = item["Question"].strip()
    a = item.get("AnswerWithProofs") or item["Answer"]
    a = a.strip()
    return f"{header_for(n)}\nQ. {q}\nA. {a}\n"


def pick_quote(item: dict, context_answer: str) -> str:
    """Pick a contiguous substring that appears in the CONTEXT answer line."""
    # Prefer plain Answer when it is contained in the CONTEXT text.
    plain = (item.get("Answer") or "").strip()
    if len(plain) >= 8 and norm_ws(plain) in norm_ws(context_answer):
        return plain if len(plain) <= 180 else plain[:177].rsplit(" ", 1)[0]
    text = context_answer.strip()
    if len(text) <= 180:
        return text
    return text[:177].rsplit(" ", 1)[0]


def answerable_assistant(item: dict, context_answer: str) -> str:
    n = int(item["Number"])
    quote = pick_quote(item, context_answer)
    return (
        f"The Puritan Catechism answers that "
        f'"{quote}" '
        f"[Puritan Catechism Q.{n}] "
        f"This is the catechism's own teaching, grounded in the text set before us."
    )


def refusal_assistant() -> str:
    return (
        "These excerpts do not address that question, and I will not invent an "
        "answer beyond the catechism passage provided. The context is insufficient."
    )


def user_msg(ctx: str, question: str) -> str:
    return (
        "CONTEXT (excerpts from Spurgeon and, when present, Puritan or confession texts):\n\n"
        f"{ctx}\n\nQUESTION: {question}"
    )


def validate_answerable(user: str, ans: str) -> list[str]:
    errs: list[str] = []
    ctx_n = norm_ws(context_of(user))
    ok_q = sum(1 for q in QUOTE_RE.findall(ans) if norm_ws(q) in ctx_n)
    if ok_q < 1:
        errs.append("no CONTEXT quote")
    if "Puritan Catechism Q." not in ans:
        errs.append("missing catechism cite")
    errs.extend(caricature_errors(ans))
    return errs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build Puritan Catechism SFT CONTEXT slice")
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--limit", type=int, default=0, help="0 = all Qs as answerable + ~10% refusal")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument(
        "--variants",
        type=int,
        default=0,
        help="Extra answerable rows per Q using QUESTION_VARIANTS (0 = base only).",
    )
    p.add_argument(
        "--extra-refusals",
        type=int,
        default=0,
        help="Additional refusal rows beyond the default ~10%% pool.",
    )
    p.add_argument(
        "--target-new",
        type=int,
        default=0,
        help="If >0 with --variants, stop once this many new rows are built (after shuffle cap).",
    )
    p.add_argument("--output", default="", help="Override output JSONL path")
    p.add_argument("--manifest", default="", help="Override output manifest path")
    args = p.parse_args(argv)

    src = Path(args.src)
    if not src.exists():
        print(f"ERROR: missing {src}", file=sys.stderr)
        return 2
    raw = json.loads(src.read_text(encoding="utf-8"))
    items = list(raw.get("Data") or [])
    if args.limit > 0:
        items = items[: args.limit]

    out_jsonl = Path(args.output) if args.output else OUT_JSONL
    out_manifest = Path(args.manifest) if args.manifest else OUT_MANIFEST
    if not out_jsonl.is_absolute():
        out_jsonl = _REPO / out_jsonl
    if not out_manifest.is_absolute():
        out_manifest = _REPO / out_manifest

    rng = random.Random(args.seed)
    rows: list[dict] = []
    warn = 0
    variant_only = args.variants > 0 and args.target_new > 0

    for item in items:
        ctx = context_block(item)
        context_answer = (item.get("AnswerWithProofs") or item["Answer"]).strip()
        q = item["Question"].strip()
        ans = answerable_assistant(item, context_answer)
        n = int(item["Number"])

        questions: list[tuple[str, str]] = []
        if not variant_only:
            questions.append((q, f"catechism-{n:02d}"))
        n_var = max(0, int(args.variants))
        for vi, tmpl in enumerate(QUESTION_VARIANTS[:n_var]):
            questions.append((tmpl.format(q=q), f"catechism-{n:02d}-v{vi + 1}"))

        for question, row_id in questions:
            user = user_msg(ctx, question)
            errs = validate_answerable(user, ans)
            if errs:
                warn += 1
                print(f"WARN Q.{n}: {errs[0]}", file=sys.stderr)
            rows.append(
                {
                    "id": row_id,
                    "slice": "answerable",
                    "source": "puritan_catechism",
                    "messages": [
                        {"role": "system", "content": SPURGEON_SFT_SYSTEM_PROMPT},
                        {"role": "user", "content": user},
                        {"role": "assistant", "content": ans},
                    ],
                }
            )

    anachronisms = [
        "What does this teach about livestreaming the Lord's Supper?",
        "How should a church use AI chatbots according to this text?",
        "What is the catechism's view of electric lighting in worship?",
        "Does this passage approve cryptocurrency tithes?",
        "How should pastors use social media algorithms according to this catechism?",
        "What does the catechism say about virtual-reality worship services?",
    ]
    n_ref = 0 if variant_only else max(1, len(items) // 10)
    n_ref += max(0, int(args.extra_refusals))
    for i in range(n_ref):
        item = items[i % len(items)]
        ctx = context_block(item)
        question = anachronisms[i % len(anachronisms)]
        # Distinct question text so merge key does not collide with base refusals.
        if i >= (0 if variant_only else max(1, len(items) // 10)):
            question = f"{question} (variant {i + 1})"
        ans = refusal_assistant()
        user = user_msg(ctx, question)
        rows.append(
            {
                "id": f"catechism-ref-{i + 1:02d}",
                "slice": "refusal",
                "source": "puritan_catechism",
                "messages": [
                    {"role": "system", "content": SPURGEON_SFT_SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": ans},
                ],
            }
        )

    rng.shuffle(rows)
    if args.target_new > 0 and len(rows) > args.target_new:
        # Prefer answerable variants; keep a small refusal share (~10%).
        answerable = [r for r in rows if r["slice"] == "answerable"]
        refusals = [r for r in rows if r["slice"] == "refusal"]
        n_ref_keep = min(len(refusals), max(1, args.target_new // 10))
        n_ans_keep = args.target_new - n_ref_keep
        rows = answerable[:n_ans_keep] + refusals[:n_ref_keep]
        rng.shuffle(rows)

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(src.relative_to(_REPO)).replace("\\", "/"),
        "rows": len(rows),
        "answerable": sum(1 for r in rows if r["slice"] == "answerable"),
        "refusal": sum(1 for r in rows if r["slice"] == "refusal"),
        "warnings": warn,
        "seed": args.seed,
        "variants_per_q": int(args.variants),
        "target_new": int(args.target_new),
        "merge_into_train": False,
        "reason": "Merge only after ingest_catechism.py indexes the same docs for RAG parity.",
        "output": str(out_jsonl.relative_to(_REPO)).replace("\\", "/"),
        "ingest": "python fine_tuning/scripts/ingest_catechism.py",
    }
    out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_jsonl} rows={len(rows)} warnings={warn}")
    print(f"Wrote {out_manifest}")
    print("Not merged into qa_mix_train (RAG parity gate).")
    return 0 if warn == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
