#!/usr/bin/env python3
"""Export the open-theology QA slice as SFT-ready JSONL (dry by default).

Reads  fine_tuning/data/qa_open_theology/{accepted,eval_accepted}.jsonl
Writes fine_tuning/data/qa_open_theology/sft/
         open_theology_train.jsonl   {"id", "slice": "open_theology", "messages": [system, user, assistant]}
         open_theology_eval.jsonl    same shape (held out; never train on it)
         manifest.json               counts, sha256, source commit, exclusions, validation
         meta_wording_ids.json       rows saying "the passage"/"the text"/... (kept, flagged)
         excluded_ids.json           operator exclusions with reasons (created if missing; edit to reinstate)

Row shape matches the side slices already in qa_mix_train.jsonl (id/slice/messages), so a
trainer that reads "messages" loads it unchanged. This slice stays SEPARATE: do not merge it
into qa_mix_train.jsonl / qa_test_frozen.jsonl or run build_qa_mix_v2.py on it.

Rerunnable: rebuilds both files from the current accepted files every time (e.g. after the
remaining eval jobs land).

Usage (repo root):
  python fine_tuning/scripts/export_open_theology_sft.py            # dry: validate + print
  python fine_tuning/scripts/export_open_theology_sft.py --apply    # write sft/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
for p in (_REPO, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from config import THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from open_theology_qa_checks import (  # noqa: E402
    check_open_theology_record,
    meta_wording_warnings,
    ot_normalize,
)
from plan_open_theology_jobs import (  # noqa: E402
    HOLDOUT_DIR,
    OUT_DIR,
    _fingerprint,
    load_holdout_fingerprints,
    load_spurgeon_holdout_numbers,
)

SLICE = "open_theology"
EXPORT_VERSION = "open_theology_sft_v1"
DEFAULT_EXCLUDED = {
    "train-confession-003": "junk passage: list of file:/// CCEL links; Q/A is about URL strings",
    "train-confession-023": "junk passage: CCEL page-header boilerplate; date trivia, 148-char answer",
    "train-puritan-087": "junk passage: book INDEX page",
    "train-spurgeon-083": "teacher openrouter/free (single row from an unvetted free model)",
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _role(msgs: list[dict], name: str) -> str:
    return next((m.get("content") or "" for m in msgs if m.get("role") == name), "")


def ends_with_heading(answer: str, heading: str) -> bool:
    """Diagnostic helper; catalog heading at end is no longer required for export."""
    return bool(heading) and ot_normalize(answer).rstrip(" .)").endswith(ot_normalize(heading))


def row_errors(rec: dict) -> list[str]:
    msgs = rec.get("messages") or []
    errs: list[str] = []
    if [m.get("role") for m in msgs] != ["system", "user", "assistant"]:
        errs.append("messages are not [system, user, assistant]")
    if _role(msgs, "system") != THEOLOGY_CHAT_SYSTEM_PROMPT:
        errs.append("system prompt is not THEOLOGY_CHAT_SYSTEM_PROMPT")
    if not _role(msgs, "user").strip() or not _role(msgs, "assistant").strip():
        errs.append("empty user or assistant")
    errs.extend(check_open_theology_record(rec))
    return sorted(set(errs))


def to_sft(rec: dict) -> dict:
    msgs = rec["messages"]
    return {
        "id": rec["job_id"],
        "slice": SLICE,
        "messages": [{"role": m["role"], "content": m["content"]} for m in msgs],
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def _count(rows: list[dict], key) -> dict:
    out: dict = {}
    for r in rows:
        k = key(r)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def export(
    *,
    data_dir: Path = OUT_DIR,
    holdout_dir: Path = HOLDOUT_DIR,
    apply: bool = False,
    eval_target: int | None = None,
) -> dict:
    sft_dir = data_dir / "sft"
    excl_path = sft_dir / "excluded_ids.json"
    if excl_path.exists():
        excluded = json.loads(excl_path.read_text(encoding="utf-8"))
    else:
        excluded = dict(DEFAULT_EXCLUDED)

    train_src = read_jsonl(data_dir / "accepted.jsonl")
    eval_src = read_jsonl(data_dir / "eval_accepted.jsonl")
    if eval_target is None:
        eval_target = len(read_jsonl(data_dir / "eval_jobs.jsonl")) or None

    holdout_fps = set().union(*load_holdout_fingerprints(holdout_dir).values())
    holdout_nums = load_spurgeon_holdout_numbers(holdout_dir)

    def holdout_hit(rec: dict) -> bool:
        meta = rec.get("meta") or {}
        if meta.get("passage") and _fingerprint(meta["passage"]) in holdout_fps:
            return True
        wid = str(meta.get("work_id") or "")
        if wid.startswith("spurgeon-") and wid.split("-", 1)[1].isdigit():
            return int(wid.split("-", 1)[1]) in holdout_nums
        return False

    report: dict = {"invalid": {}, "duplicates": [], "holdout_hits": [], "overlap_removed": []}

    def clean(rows: list[dict], split: str) -> list[dict]:
        kept, seen_ids, seen_q = [], set(), set()
        for r in rows:
            jid = r.get("job_id", "")
            if split == "train" and jid in excluded:
                continue
            q = ot_normalize(_role(r.get("messages") or [], "user"))
            if jid in seen_ids or q in seen_q:
                report["duplicates"].append(jid)
                continue
            errs = row_errors(r)
            if errs:
                report["invalid"][jid] = errs
                continue
            if holdout_hit(r):
                report["holdout_hits"].append(jid)
                continue
            seen_ids.add(jid)
            seen_q.add(q)
            kept.append(r)
        return kept

    train = clean(train_src, "train")
    ev = clean(eval_src, "eval")

    # Eval must not share job, work, passage, or question with train; drop from TRAIN if so.
    def keys(r: dict) -> set[str]:
        m = r.get("meta") or {}
        return {f"w:{m.get('work_id')}", f"p:{_fingerprint(m.get('passage') or '')}",
                f"q:{ot_normalize(_role(r['messages'], 'user'))}"}
    ev_keys = set().union(*(keys(r) for r in ev)) if ev else set()
    ev_ids = {r["job_id"] for r in ev}
    t2 = []
    for r in train:
        if r["job_id"] in ev_ids or keys(r) & ev_keys:
            report["overlap_removed"].append(r["job_id"])
        else:
            t2.append(r)
    train = t2

    meta_ids = {
        split: {
            "question": [r["job_id"] for r in rows
                         if meta_wording_warnings(_role(r["messages"], "user"), "")],
            "answer": [r["job_id"] for r in rows
                       if meta_wording_warnings("", _role(r["messages"], "assistant"))],
        }
        for split, rows in (("train", train), ("eval", ev))
    }
    for split in meta_ids:
        meta_ids[split]["any"] = sorted(set(meta_ids[split]["question"]) | set(meta_ids[split]["answer"]))

    summary = {
        "apply": apply,
        "train_source_rows": len(train_src),
        "eval_source_rows": len(eval_src),
        "train_rows": len(train),
        "eval_rows": len(ev),
        "eval_target": eval_target,
        "excluded": sorted(j for j in excluded if any(r.get("job_id") == j for r in train_src)),
        "invalid": report["invalid"],
        "duplicates": report["duplicates"],
        "holdout_hits": report["holdout_hits"],
        "overlap_removed": report["overlap_removed"],
        "meta_wording_counts": {s: {k: len(v) for k, v in d.items()} for s, d in meta_ids.items()},
        "by_bucket": {"train": _count(train, lambda r: r["meta"]["bucket"]),
                      "eval": _count(ev, lambda r: r["meta"]["bucket"])},
        "by_teacher": {"train": _count(train, lambda r: f"{r.get('teacher')}/{r.get('model')}"),
                       "eval": _count(ev, lambda r: f"{r.get('teacher')}/{r.get('model')}")},
    }
    if not apply:
        return summary

    sft_dir.mkdir(parents=True, exist_ok=True)
    files = {"train": sft_dir / "open_theology_train.jsonl", "eval": sft_dir / "open_theology_eval.jsonl"}
    for split, rows in (("train", train), ("eval", ev)):
        with files[split].open("w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(to_sft(r), ensure_ascii=False) + "\n")
    if not excl_path.exists():
        excl_path.write_text(json.dumps(excluded, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (sft_dir / "meta_wording_ids.json").write_text(
        json.dumps({"note": "kept in the export; flagged for 'the passage'/'the text'/'the excerpt'/'this quote' wording",
                    **meta_ids}, indent=2) + "\n", encoding="utf-8")
    status = {}
    if (data_dir / "status.json").exists():
        status = json.loads((data_dir / "status.json").read_text(encoding="utf-8"))
    manifest = {
        "export_version": EXPORT_VERSION,
        "slice": SLICE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": _git_head(_REPO),
        "generator_version": status.get("version", ""),
        "format": {"row": {"id": "str (job_id)", "slice": SLICE,
                           "messages": "[system, user, assistant] chat; no CONTEXT turn"},
                   "system_prompt": "config.THEOLOGY_CHAT_SYSTEM_PROMPT",
                   "system_prompt_sha256": hashlib.sha256(THEOLOGY_CHAT_SYSTEM_PROMPT.encode()).hexdigest()},
        "files": {
            split: {"path": f"sft/{p.name}", "rows": n, "sha256": _sha256(p)}
            for split, p, n in (("train", files["train"], len(train)), ("eval", files["eval"], len(ev)))
        },
        "sources": {name: {"rows": n, "sha256": _sha256(data_dir / name)}
                    for name, n in (("accepted.jsonl", len(train_src)), ("eval_accepted.jsonl", len(eval_src)))
                    if (data_dir / name).exists()},
        "eval_partial": bool(eval_target and len(ev) < eval_target),
        "eval_note": (f"eval is partial: {len(ev)}/{eval_target} accepted; rerun this export after the remaining "
                      "eval jobs land" if eval_target and len(ev) < eval_target else "eval complete"),
        "excluded_ids": excluded,
        "validation": {k: summary[k] for k in ("invalid", "duplicates", "holdout_hits", "overlap_removed")},
        "meta_wording_counts": summary["meta_wording_counts"],
        "by_bucket": summary["by_bucket"],
        "by_teacher": summary["by_teacher"],
        "usage": "separate side dataset; add with its own weight; never merge into qa_mix_train.jsonl",
    }
    (sft_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    summary["out_dir"] = str(sft_dir)
    return summary


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Export open-theology QA as SFT JSONL (dry by default)")
    ap.add_argument("--data-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--holdout-dir", type=Path, default=HOLDOUT_DIR)
    ap.add_argument("--apply", action="store_true", help="write sft/ files")
    args = ap.parse_args(argv)
    s = export(data_dir=args.data_dir, holdout_dir=args.holdout_dir, apply=args.apply)
    print(json.dumps(s, indent=2, ensure_ascii=False))
    bad = s["invalid"] or s["holdout_hits"]
    print("EXPORT WRITTEN" if args.apply else "DRY (nothing written; pass --apply)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
