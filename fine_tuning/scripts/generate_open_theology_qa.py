#!/usr/bin/env python3
"""Generate open-theology (no-CONTEXT) SFT rows from the planned job queue.

Default is dry: print the next batch and write nothing.
--apply calls the teacher API and appends accepted/rejected rows.

Usage (repo root):
  python fine_tuning/scripts/generate_open_theology_qa.py
  python fine_tuning/scripts/generate_open_theology_qa.py --limit 25
  python fine_tuning/scripts/generate_open_theology_qa.py --apply --limit 25 --provider groq
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
from open_theology_qa_checks import check_open_theology_row  # noqa: E402
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
1. The question must be answerable from the passage alone. Specific, not a generic template.
2. The answer uses knowledge-assistant voice in the third person ("Spurgeon teaches…", "Owen argues…", "the catechism answers…"). You are not Spurgeon, Owen, Calvin, or any Puritan.
3. Do not address the reader with vocatives such as "Beloved", "My beloved", "Dear friends", "My brethren", "amados", or "meus queridos irmãos". No first-person preacher roleplay.
4. Include at least one quotation that is a verbatim contiguous substring of the SOURCE PASSAGE, wrapped in ASCII double quotes. Copy character-for-character. Do not paraphrase inside quotes.
5. Cite the work using exactly this catalog heading string (copy it unchanged): the HEADING value provided.
6. Do not mention CONTEXT, retrieval, or "based only on the context."
7. Return JSON only: {"question": "...", "answer": "..."}
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


def teacher_user_prompt(job: dict) -> str:
    return (
        f"HEADING: {job['heading']}\n\n"
        f"SOURCE PASSAGE:\n{job['passage']}\n\n"
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
) -> dict:
    jobs_path = out_dir / "jobs.jsonl"
    status_path = out_dir / "status.json"
    accepted_path = out_dir / "accepted.jsonl"
    rejected_path = out_dir / "rejected.jsonl"

    jobs = read_jsonl(jobs_path)
    if not jobs:
        raise SystemExit(f"ERROR: no jobs in {jobs_path}; run plan_open_theology_jobs.py")

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
                teacher_user_prompt(job),
                slice_name="open_theology",
                system_prompt=OPEN_THEOLOGY_TEACHER_SYSTEM,
                max_tokens=700,
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
                append_jsonl(
                    accepted_path,
                    build_accepted_row(job, question, answer, provider, model),
                )
                _log("  ACCEPT")
        except Exception as e:
            consecutive_fail += 1
            rejected_n += 1
            report["rejected_new"] += 1
            err = f"teacher error: {e}"
            append_jsonl(
                rejected_path,
                {
                    "job_id": job["job_id"],
                    "ok": False,
                    "errors": [err],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "meta": {
                        "bucket": job["bucket"],
                        "work_id": job["work_id"],
                        "source_path": job["source_path"],
                        "heading": job["heading"],
                    },
                },
            )
            status["last_error"] = err
            _log(f"  ERROR: {e}")

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
            "train_jobs": len(jobs),
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
    args = p.parse_args(argv)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = _REPO / out_dir

    status_path = out_dir / "status.json"
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
