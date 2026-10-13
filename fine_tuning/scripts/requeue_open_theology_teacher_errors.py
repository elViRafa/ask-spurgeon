#!/usr/bin/env python3
"""Queue maintenance for the open-theology QA slice (dry by default).

1. Requeue: move rejected.jsonl rows whose ONLY errors are teacher transport errors
   ("teacher error: ..." e.g. groq 429 TPD quota) out of rejected.jsonl and append them to
   requeued_from_rejected.jsonl, so those jobs are pending again. Quality rejects stay.
   With --ids JOB_ID ..., also requeue those specific rejected rows (any error type),
   e.g. teacher-format quote rejects worth retrying after a prompt change.
2. Skip (optional, --skip JOB_ID ...): append a rejected row for pending jobs whose
   passage is unusable (link lists, index pages), so the teacher is never called for them.

3. Requeue ACCEPTED rows (--requeue-accepted, with --ids and/or --ids-file): move them out
   of accepted.jsonl (train) / eval_accepted.jsonl (eval) so the generator regenerates them
   (e.g. rows flagged in sft/meta_wording_ids.json). Split by --split or auto by id prefix.
   With --apply: timestamped backup <file>.bak-requeue-accepted-<ts>, moved rows appended to
   requeued_from_accepted.jsonl, status.json / eval_status.json counts refreshed. jobs files
   are not rewritten: a job is pending as soon as it is in neither accepted nor rejected.

Modes 1-2 never touch accepted.jsonl. Nothing ever touches catalog.json, qa_mix_train.jsonl or
qa_test_frozen.jsonl. With --apply every rewritten file is backed up first; line endings kept.

Usage (repo root):
  python fine_tuning/scripts/requeue_open_theology_teacher_errors.py
  python fine_tuning/scripts/requeue_open_theology_teacher_errors.py --ids train-puritan-057 train-puritan-049
  python fine_tuning/scripts/requeue_open_theology_teacher_errors.py \
      --skip train-confession-030 train-confession-032 --apply
  python fine_tuning/scripts/requeue_open_theology_teacher_errors.py --requeue-accepted \
      --ids-file fine_tuning/data/qa_open_theology/sft/meta_wording_ids.json          # dry
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from plan_open_theology_jobs import OUT_DIR  # noqa: E402


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _newline(path: Path) -> str:
    return "\r\n" if path.exists() and b"\r\n" in path.read_bytes()[:65536] else "\n"


def is_teacher_error_only(row: dict) -> bool:
    errs = row.get("errors") or []
    return bool(errs) and all(str(e).startswith("teacher error:") for e in errs)


def maintain(
    data_dir: Path,
    *,
    skip: list[str] | None = None,
    ids: list[str] | None = None,
    apply: bool = False,
) -> dict:
    rejected_p = data_dir / "rejected.jsonl"
    requeued_p = data_dir / "requeued_from_rejected.jsonl"
    rejected = _read(rejected_p)
    accepted_ids = {r.get("job_id") for r in _read(data_dir / "accepted.jsonl")}
    jobs = {j["job_id"]: j for j in _read(data_dir / "jobs.jsonl")}

    want = set(ids or [])
    rejected_ids = {r.get("job_id") for r in rejected}
    ids_missing = sorted(want - rejected_ids)

    def _move(r: dict) -> bool:
        return is_teacher_error_only(r) or r.get("job_id") in want

    move = [r for r in rejected if _move(r)]
    keep = [r for r in rejected if not _move(r)]
    kept_ids = {r.get("job_id") for r in keep}

    skip_rows, skip_bad = [], []
    for jid in skip or []:
        if jid not in jobs or jid in accepted_ids or jid in kept_ids:
            skip_bad.append(jid)
            continue
        j = jobs[jid]
        skip_rows.append({
            "job_id": jid,
            "ok": False,
            "errors": ["skipped: unusable source passage (operator skip)"],
            "meta": {k: j.get(k) for k in ("bucket", "work_id", "source_path", "heading")},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    print(f"[{'APPLY' if apply else 'DRY RUN'}] {data_dir}")
    print(f"rejected.jsonl: {len(rejected)} rows; {len(move)} -> requeue "
          f"(teacher-error-only or --ids), {len(keep)} kept")
    if ids_missing:
        print(f"  --ids not in rejected.jsonl (ignored): {ids_missing}")
    for r in move:
        print(f"  requeue {r.get('job_id')}: {str(r['errors'][0])[:90]}")
    print(f"skip: {len(skip_rows)} job(s) {[r['job_id'] for r in skip_rows]}"
          + (f"; ignored (unknown/already done) {skip_bad}" if skip_bad else ""))

    if apply and (move or skip_rows):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        nl = _newline(rejected_p)
        if rejected_p.exists():
            shutil.copy2(rejected_p, rejected_p.with_name(f"rejected.jsonl.bak-{stamp}"))
        with rejected_p.open("w", encoding="utf-8", newline="") as f:
            for r in keep + skip_rows:
                f.write(json.dumps(r, ensure_ascii=False) + nl)
        if move:
            rq_nl = _newline(requeued_p) if requeued_p.exists() else nl
            with requeued_p.open("a", encoding="utf-8", newline="") as f:
                for r in move:
                    f.write(json.dumps(r, ensure_ascii=False) + rq_nl)
        print(f"written; backup rejected.jsonl.bak-{stamp}")
    elif not apply:
        print("dry run: nothing written (pass --apply)")
    return {"requeue": [r.get("job_id") for r in move], "skip": [r["job_id"] for r in skip_rows],
            "ignored": skip_bad, "ids_missing": ids_missing}


SPLIT_FILES = {
    "train": ("accepted.jsonl", "jobs.jsonl", "rejected.jsonl", "status.json"),
    "eval": ("eval_accepted.jsonl", "eval_jobs.jsonl", "eval_rejected.jsonl", "eval_status.json"),
}


def load_ids_file(path: Path) -> list[str]:
    """Flat JSON list, or sft/meta_wording_ids.json shape ({split: {either|any: [...]}})."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(x) for x in data]
    out: list[str] = []

    def pick(d: dict) -> list:
        for key in ("either", "any", "ids"):
            if isinstance(d.get(key), list):
                return d[key]
        return []

    out.extend(pick(data))
    for split in SPLIT_FILES:
        if isinstance(data.get(split), dict):
            out.extend(pick(data[split]))
        elif isinstance(data.get(split), list):
            out.extend(data[split])
    return list(dict.fromkeys(str(x) for x in out))


def split_of(job_id: str) -> str | None:
    if job_id.startswith("train-"):
        return "train"
    if job_id.startswith("eval-"):
        return "eval"
    return None


def requeue_accepted(
    data_dir: Path, ids: list[str], *, split: str | None = None, apply: bool = False
) -> dict:
    want = list(dict.fromkeys(ids))
    by_split: dict[str, list[str]] = {s: [] for s in SPLIT_FILES}
    unknown: list[str] = []
    for jid in want:
        sp = split or split_of(jid)
        if sp in by_split:
            by_split[sp].append(jid)
        else:
            unknown.append(jid)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_p = data_dir / "requeued_from_accepted.jsonl"
    result: dict = {"apply": apply, "unknown": unknown, "splits": {}}
    print(f"[{'APPLY' if apply else 'DRY RUN'}] requeue-accepted in {data_dir}")
    for sp, sp_ids in by_split.items():
        if not sp_ids:
            continue
        acc_name, jobs_name, rej_name, status_name = SPLIT_FILES[sp]
        acc_p, jobs_p = data_dir / acc_name, data_dir / jobs_name
        accepted = _read(acc_p)
        job_ids = {j.get("job_id") for j in _read(jobs_p)}
        acc_ids = {r.get("job_id") for r in accepted}
        wanted = set(sp_ids)
        not_accepted = [j for j in sp_ids if j not in acc_ids]
        no_job = [j for j in sp_ids if j in acc_ids and j not in job_ids]
        movable = wanted & acc_ids & job_ids
        move = [r for r in accepted if r.get("job_id") in movable]
        keep = [r for r in accepted if r.get("job_id") not in movable]
        result["splits"][sp] = {"requested": len(sp_ids), "requeue": [r["job_id"] for r in move],
                                "not_in_accepted": not_accepted, "no_job_row": no_job}
        print(f"  {sp}: {len(sp_ids)} requested; {len(move)} found in {acc_name} -> requeue; "
              f"{len(not_accepted)} not in {acc_name}; {len(no_job)} without a job row")
        if not_accepted:
            print(f"    not in {acc_name} (ignored): {not_accepted[:20]}{' ...' if len(not_accepted) > 20 else ''}")
        if not (apply and move):
            continue
        nl = _newline(acc_p)
        shutil.copy2(acc_p, acc_p.with_name(f"{acc_name}.bak-requeue-accepted-{stamp}"))
        with acc_p.open("w", encoding="utf-8", newline="") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + nl)
        log_nl = _newline(log_p) if log_p.exists() else nl
        now = datetime.now(timezone.utc).isoformat()
        with log_p.open("a", encoding="utf-8", newline="") as f:
            for r in move:
                f.write(json.dumps({**r, "requeued_split": sp, "requeued_at": now},
                                   ensure_ascii=False) + log_nl)
        st_p = data_dir / status_name
        if st_p.exists():
            st_nl = _newline(st_p)
            status = json.loads(st_p.read_text(encoding="utf-8"))
            rejected_ids = {r.get("job_id") for r in _read(data_dir / rej_name)}
            done = {r.get("job_id") for r in keep} | rejected_ids
            jobs = _read(jobs_p)
            pending = [j for j in jobs if j.get("job_id") not in done]
            counts = status.setdefault("counts", {})
            counts.update({"accepted": len(keep), "rejected": len(rejected_ids),
                           "remaining": len(pending)})
            status["next_job_id"] = pending[0]["job_id"] if pending else ""
            status["updated_at"] = now
            with st_p.open("w", encoding="utf-8", newline="") as f:
                f.write(json.dumps(status, indent=2).replace("\n", st_nl))
        print(f"    written: {acc_name} (backup .bak-requeue-accepted-{stamp}), "
              f"{log_p.name}, {status_name}")
    if unknown:
        print(f"  unknown ids (no train-/eval- prefix; use --split): {unknown}")
    if not apply:
        print("dry run: nothing written (pass --apply)")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--skip", nargs="*", default=[], help="pending job_ids to mark skipped")
    ap.add_argument("--ids", nargs="*", default=[], help="rejected job_ids to requeue (any error)")
    ap.add_argument("--requeue-accepted", action="store_true",
                    help="requeue ACCEPTED rows named by --ids / --ids-file")
    ap.add_argument("--ids-file", type=Path, help="flat JSON list or sft/meta_wording_ids.json")
    ap.add_argument("--split", choices=tuple(SPLIT_FILES),
                    help="with --requeue-accepted: force split (default: by id prefix)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.requeue_accepted:
        ids = list(args.ids or [])
        if args.ids_file:
            ids += load_ids_file(args.ids_file)
        if not ids:
            ap.error("--requeue-accepted needs --ids and/or --ids-file")
        requeue_accepted(args.data_dir, ids, split=args.split, apply=args.apply)
        return
    maintain(args.data_dir, skip=args.skip, ids=args.ids, apply=args.apply)


if __name__ == "__main__":
    main()
