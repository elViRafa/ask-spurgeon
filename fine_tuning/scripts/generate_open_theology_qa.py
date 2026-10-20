#!/usr/bin/env python3
"""Generate open-theology (no-CONTEXT) SFT rows from the planned job queue.

Default is dry: print the next batch and write nothing.
--apply calls the teacher API and appends accepted/rejected rows.

Usage (repo root):
  python fine_tuning/scripts/generate_open_theology_qa.py
  python fine_tuning/scripts/generate_open_theology_qa.py --limit 25
  python fine_tuning/scripts/generate_open_theology_qa.py --apply --limit 25 --provider groq
  python fine_tuning/scripts/generate_open_theology_qa.py --split eval --apply --limit 40 --provider groq
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from config import THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from open_theology_qa_checks import check_open_theology_row, meta_wording_warnings  # noqa: E402
from rewrite_qa_answers_teacher import (  # noqa: E402
    CONSECUTIVE_FAIL_ABORT,
    DEFAULT_MODELS,
    call_teacher,
    parse_answer,
)

OUT_DIR = _REPO / "fine_tuning" / "data" / "qa_open_theology"
REJECT_RATE_HALT = 0.40

OPEN_THEOLOGY_TEACHER_SYSTEM = """You write training pairs for an open theological Q&A assistant on Spurgeon, the Puritans, and confessions/catechisms.

You are given a SOURCE PASSAGE and its CATALOG HEADING. Invent one natural question a reader would ask, and one gold answer.

Rules:
1. Prefer a doctrinal, comparative, or summary question a reader could ask without seeing the passage. Do not ask for entry numbers, verse indexes in a table of contents, sermon-number trivia alone, or URL lists. The question must still be answerable from the passage alone. Specific, not a generic template.
2. The answer uses knowledge-assistant voice in the third person ("Spurgeon teaches…", "Owen argues…", "the catechism answers…"). You are not Spurgeon, Owen, Calvin, or any Puritan.
3. Do not address the reader with vocatives such as "Beloved", "My beloved", "Dear friends", "My brethren", "amados", or "meus queridos irmãos". No first-person preacher roleplay.
4. A verbatim quotation from the SOURCE PASSAGE is optional. If you include one, wrap it in ASCII double quotes and copy character-for-character as a contiguous substring. Do not paraphrase inside quotes. Do not invent a quotation.
4a. When quoting: use ASCII double quotes only, never single quotes (' or ‘ ’). Never correct spelling, archaic forms, or OCR errors inside the quote; copy them exactly as they appear. Never use the sermon or work title as the quotation; quote the passage body. Inside JSON strings write apostrophes as a plain ' (never \\'), and do not put backslash-escaped quotes inside the quotation.
5. A catalog heading cite is optional. If you include one, use the HEADING string exactly as given, including its square brackets, e.g. [Boston — Fourfold State]. Do not invent a heading, sermon number, or work title. Do not put a heading in parentheses, and do not turn it into a sentence ('The Boston — Fourfold State teaches…').
6. Do not mention CONTEXT, retrieval, or "based only on the context."
6a. The user will never see the SOURCE PASSAGE. Never write "the passage", "the text", "the excerpt", or "this quote" in the question or the answer. Attribute to the author or work instead (e.g. "Boston teaches…", "According to Owen…", "the Westminster Confession states…").
7. Return JSON only: {"question": "...", "answer": "..."}
"""

OPEN_THEOLOGY_HONESTY_TEACHER_SYSTEM = """You write honesty / anti-invent training pairs for an open theological Q&A assistant on Spurgeon, the Puritans, and confessions/catechisms.

You are given a SOURCE PASSAGE and its CATALOG HEADING. Invent one natural question that would tempt a weak model to invent a sermon number, fake work title, catalog heading, or verbatim quotation it does not have, and one gold answer that refuses to invent while still teaching the doctrine from the passage.

Rules:
1. The question should sound like a reader asking for a precise citation, sermon number, or exact title that is easy to hallucinate. Prefer doctrinal substance underneath (not pure trivia about entry numbers or URL lists).
2. The answer uses knowledge-assistant voice in the third person. Explicitly refuse to invent: e.g. say you do not recall the exact sermon number / will not invent a title, then state the doctrine the passage teaches.
3. Do not invent sermon numbers, quotations, works, or authors. A catalog heading cite is optional; if present it must be the HEADING string exactly. A verbatim quote is optional; if present it must be a contiguous substring of the SOURCE PASSAGE.
4. Do not address the reader with vocatives such as "Beloved", "My beloved", "Dear friends", "My brethren", "amados", or "meus queridos irmãos". No first-person preacher roleplay.
5. Do not mention CONTEXT, retrieval, or "based only on the context." Never write "the passage", "the text", "the excerpt", or "this quote" in the question or the answer.
6. Return JSON only: {"question": "...", "answer": "..."}
"""


def _log(msg: str) -> None:
    print(msg, flush=True)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_status(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"ERROR: missing {path}; run plan_open_theology_jobs.py first")
    return json.loads(path.read_text(encoding="utf-8"))


def save_status(path: Path, status: dict) -> None:
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")


def done_job_ids(accepted: list[dict], rejected: list[dict]) -> set[str]:
    ids: set[str] = set()
    for row in accepted + rejected:
        jid = row.get("job_id") or (row.get("meta") or {}).get("job_id")
        if jid:
            ids.add(str(jid))
    return ids


def parse_qa(raw: str) -> tuple[str, str]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1).strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            q = str(obj.get("question") or "").strip()
            a = str(obj.get("answer") or "").strip()
            if q and a:
                return q, a
    except json.JSONDecodeError:
        pass
    # Fallback: some models return only {"answer": ...} — reject.
    ans = parse_answer(raw)
    return "", ans


def teacher_user_prompt(job: dict, *, honesty: bool = False) -> str:
    extra = ""
    if honesty or job.get("honesty"):
        extra = (
            "\n\nHonesty mode: the question must tempt invent-cite; "
            "the answer must refuse to invent while teaching the doctrine.\n"
        )
    return (
        f"HEADING: {job['heading']}\n\n"
        f"SOURCE PASSAGE:\n{job['passage']}\n"
        f"{extra}\n"
        "Return JSON: {\"question\": \"...\", \"answer\": \"...\"}"
    )


def build_accepted_row(job: dict, question: str, answer: str, provider: str, model: str) -> dict:
    return {
        "job_id": job["job_id"],
        "slice": "open_theology",
        "teacher": provider,
        "model": model,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": [
            {"role": "system", "content": THEOLOGY_CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "meta": {
            "slice": "open_theology",
            "bucket": job["bucket"],
            "work_id": job["work_id"],
            "source_path": job["source_path"],
            "heading": job["heading"],
            "passage": job["passage"],
            "job_id": job["job_id"],
        },
    }


def is_rate_limit_error(err: str) -> bool:
    """True for provider quota / rate-limit failures (e.g. groq TPD 429)."""
    low = (err or "").lower()
    return "429" in low or "rate limit" in low or "rate_limit" in low


SPLIT_FILES = {
    "train": {"jobs": "jobs.jsonl", "status": "status.json",
              "accepted": "accepted.jsonl", "rejected": "rejected.jsonl"},
    "eval": {"jobs": "eval_jobs.jsonl", "status": "eval_status.json",
             "accepted": "eval_accepted.jsonl", "rejected": "eval_rejected.jsonl"},
    "honesty": {"jobs": "honesty_jobs.jsonl", "status": "honesty_status.json",
                "accepted": "honesty_accepted.jsonl", "rejected": "honesty_rejected.jsonl"},
}


def split_paths(out_dir: Path, split: str) -> dict[str, Path]:
    """File set for a split; eval never touches the train files."""
    if split not in SPLIT_FILES:
        raise SystemExit(f"ERROR: unknown split {split!r}")
    return {k: out_dir / v for k, v in SPLIT_FILES[split].items()}


def reject_rate(accepted_n: int, rejected_n: int) -> float:
    total = accepted_n + rejected_n
    if total == 0:
        return 0.0
    return rejected_n / total


def run_batch(
    *,
    out_dir: Path,
    limit: int,
    apply: bool,
    provider: str,
    model: str,
    sleep_s: float,
    split: str = "train",
) -> dict:
    paths = split_paths(out_dir, split)
    jobs_path = paths["jobs"]
    status_path = paths["status"]
    accepted_path = paths["accepted"]
    rejected_path = paths["rejected"]

    jobs = read_jsonl(jobs_path)
    if not jobs:
        raise SystemExit(f"ERROR: no jobs in {jobs_path}; run plan_open_theology_jobs.py")

    if split == "eval" and not status_path.exists():
        # First eval run: fresh status in memory; written only when apply=True.
        status = {"split": "eval", "halted": False, "halt_reason": "", "last_error": "",
                  "counts": {}}
    else:
        status = load_status(status_path)
    if status.get("halted"):
        _log(f"HALTED: {status.get('halt_reason') or 'campaign halted'}")
        return {"halted": True, "status": status}

    accepted = read_jsonl(accepted_path)
    rejected = read_jsonl(rejected_path)
    done = done_job_ids(accepted, rejected)
    pending = [j for j in jobs if j["job_id"] not in done]

    batch = pending[: max(0, limit)]
    report = {
        "apply": apply,
        "pending": len(pending),
        "batch": len(batch),
        "next_job_ids": [j["job_id"] for j in batch],
        "accepted_before": len(accepted),
        "rejected_before": len(rejected),
        "accepted_new": 0,
        "rejected_new": 0,
        "halted": False,
        "halt_reason": "",
    }

    if not apply:
        _log(
            json.dumps(
                {
                    "mode": "dry",
                    "pending": len(pending),
                    "would_process": len(batch),
                    "next_job_ids": report["next_job_ids"],
                    "provider": provider,
                    "model": model or DEFAULT_MODELS.get(provider, ""),
                },
                indent=2,
            )
        )
        _log("DRY COMPLETE (wrote nothing)")
        return report

    model = model or DEFAULT_MODELS.get(provider, "")
    consecutive_fail = 0
    accepted_n = len(accepted)
    rejected_n = len(rejected)

    for job in batch:
        _log(f"JOB {job['job_id']} bucket={job['bucket']} {job['heading']}")
        try:
            raw = call_teacher(
                provider,
                model,
                teacher_user_prompt(job, honesty=(split == "honesty")),
                slice_name="open_theology",
                system_prompt=(
                    OPEN_THEOLOGY_HONESTY_TEACHER_SYSTEM
                    if split == "honesty"
                    else OPEN_THEOLOGY_TEACHER_SYSTEM
                ),
                max_tokens=1500,
                temperature=0.5,
            )
            question, answer = parse_qa(raw)
            errs = []
            if not question:
                errs.append("teacher JSON missing question")
            errs.extend(
                check_open_theology_row(
                    system=THEOLOGY_CHAT_SYSTEM_PROMPT,
                    user=question,
                    assistant=answer,
                    passage=job["passage"],
                    heading=job["heading"],
                    source_path=job["source_path"],
                )
            )
            if errs:
                consecutive_fail += 1
                rejected_n += 1
                report["rejected_new"] += 1
                append_jsonl(
                    rejected_path,
                    {
                        "job_id": job["job_id"],
                        "ok": False,
                        "errors": errs,
                        "raw": (raw or "")[:2000],
                        "question": question,
                        "answer": answer,
                        "meta": {
                            "bucket": job["bucket"],
                            "work_id": job["work_id"],
                            "source_path": job["source_path"],
                            "heading": job["heading"],
                            "passage": job["passage"],
                        },
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                _log(f"  REJECT: {errs[0]}")
            else:
                consecutive_fail = 0
                accepted_n += 1
                report["accepted_new"] += 1
                row = build_accepted_row(job, question, answer, provider, model)
                warns = meta_wording_warnings(question, answer)
                if warns:
                    # Measured, not rejected (rule 6a).
                    row["meta"]["warnings"] = warns
                    report["meta_wording_warnings"] = report.get("meta_wording_warnings", 0) + 1
                    counts = status.setdefault("counts", {})
                    counts["meta_wording_warnings"] = counts.get("meta_wording_warnings", 0) + 1
                append_jsonl(accepted_path, row)
                _log("  ACCEPT" + (f" (warn: {warns[0]})" if warns else ""))
        except Exception as e:
            # Teacher transport failure (429 quota, network, bad response): not a quality
            # reject. Do not write rejected.jsonl and do not count toward the reject rate,
            # so the job stays pending and is retried on the next run.
            err = f"teacher error: {e}"
            status["last_error"] = err
            report["teacher_errors"] = report.get("teacher_errors", 0) + 1
            _log(f"  TEACHER ERROR (job left pending): {e}")
            if is_rate_limit_error(err):
                halt_reason = (
                    "teacher rate limit/quota (429); job left pending, rerun after quota resets"
                )
                status["halted"] = True
                status["halt_reason"] = halt_reason
                status["updated_at"] = datetime.now(timezone.utc).isoformat()
                report["halted"] = True
                report["halt_reason"] = halt_reason
                save_status(status_path, status)
                _log(f"HALT: {halt_reason}")
                break
            consecutive_fail += 1

        rate = reject_rate(
            report["accepted_new"],
            report["rejected_new"],
        )
        # Halt on batch reject rate once we have enough samples in this run.
        batch_done = report["accepted_new"] + report["rejected_new"]
        halt_reason = ""
        if consecutive_fail >= CONSECUTIVE_FAIL_ABORT:
            halt_reason = (
                f"consecutive teacher/check failures >= {CONSECUTIVE_FAIL_ABORT}"
            )
        elif batch_done >= 5 and rate > REJECT_RATE_HALT:
            halt_reason = (
                f"batch reject rate {rate:.2f} exceeds {REJECT_RATE_HALT:.2f}"
            )

        remaining = len(jobs) - accepted_n - rejected_n
        # remaining should count unfinished train jobs
        still = [j for j in jobs if j["job_id"] not in done_job_ids(
            read_jsonl(accepted_path), read_jsonl(rejected_path)
        )]
        remaining = len(still)
        status["counts"] = {
            **status.get("counts", {}),
            "accepted": accepted_n,
            "rejected": rejected_n,
            "remaining": remaining,
            f"{split}_jobs": len(jobs),
        }
        status["next_job_id"] = still[0]["job_id"] if still else ""
        status["updated_at"] = datetime.now(timezone.utc).isoformat()

        if halt_reason:
            status["halted"] = True
            status["halt_reason"] = halt_reason
            report["halted"] = True
            report["halt_reason"] = halt_reason
            save_status(status_path, status)
            _log(f"HALT: {halt_reason}")
            break

        save_status(status_path, status)
        if sleep_s > 0:
            time.sleep(sleep_s)

    _log(json.dumps(report, indent=2))
    return report


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description="Generate open-theology QA (dry by default)")
    p.add_argument("--out-dir", default=str(OUT_DIR))
    p.add_argument("--limit", type=int, default=25, help="Max jobs this run")
    p.add_argument("--apply", action="store_true", help="Call the teacher API")
    p.add_argument(
        "--provider",
        choices=("openrouter", "groq", "gemini", "cerebras", "ollama"),
        default="groq",
    )
    p.add_argument("--model", default="")
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument(
        "--clear-halt",
        action="store_true",
        help="Clear halted flag in status.json before running",
    )
    p.add_argument(
        "--split",
        choices=tuple(SPLIT_FILES),
        default="train",
        help="train: jobs.jsonl -> accepted/rejected/status; "
        "eval: eval_jobs.jsonl -> eval_accepted/eval_rejected/eval_status; "
        "honesty: honesty_jobs.jsonl -> honesty_accepted/rejected/status",
    )
    p.add_argument(
        "--honesty",
        action="store_true",
        help="Shortcut for --split honesty (anti-invent teacher batch)",
    )
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = _REPO / out_dir

    split = "honesty" if args.honesty else args.split
    status_path = split_paths(out_dir, split)["status"]
    if args.clear_halt and status_path.exists():
        status = load_status(status_path)
        status["halted"] = False
        status["halt_reason"] = ""
        save_status(status_path, status)
        _log("cleared halt flag")

    run_batch(
        out_dir=out_dir,
        limit=args.limit,
        apply=args.apply,
        provider=args.provider,
        model=args.model,
        sleep_s=args.sleep,
        split=split,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
