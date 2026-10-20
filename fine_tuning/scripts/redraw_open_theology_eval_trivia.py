#!/usr/bin/env python3
"""Replace junk/trivia open-theology eval rows with doctrinal Q&A from the same works.

Targets CCEL URL-index passages and entry-number / TOC questions that reward
invent-cite. Does not call a teacher. Soft-strips answers after rewrite.

Usage (repo root):
  python fine_tuning/scripts/redraw_open_theology_eval_trivia.py
  python fine_tuning/scripts/redraw_open_theology_eval_trivia.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
for p in (_REPO, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from config import THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from open_theology_qa_checks import check_open_theology_record  # noqa: E402
from plan_open_theology_jobs import OUT_DIR  # noqa: E402
from qa_rewrite_checks import role  # noqa: E402
from soft_strip_open_theology_gold import soft_strip_assistant  # noqa: E402

# Hand-curated redraws: same job_id / heading / source_path / work_id; new passage+Q+A.
# Passages are contiguous excerpts from the source files (file:/// lines removed upstream).
REDRAWS: dict[str, dict[str, str]] = {
    "eval-puritan-003": {
        "passage": (
            "Blessed are the poor in spirit.\n\n"
            "   Matthew 5:3\n\n"
            "   Having done with the occasion, I come now to the sermon itself. Blessed\n"
            "   are the poor in spirit'. Christ does not begin his Sermon on the Mount\n"
            "   as the Law was delivered on the mount, with commands and threatenings,\n"
            "   the trumpet sounding, the fire flaming, the earth quaking, and the\n"
            "   hearts of the Israelites too for fear; but our Saviour (whose lips\n"
            "   dropped as the honeycomb') begins with promises and blessings. So sweet\n"
            "   and ravishing was the doctrine of this heavenly Orpheus that, like\n"
            "   music, it was able to charm the most savage natures, yea, to draw\n"
            "   hearts of stone to him.\n\n"
            "   To begin then with this first word, Blessed"
        ),
        "question": (
            "How does Watson contrast Christ's opening of the Sermon on the Mount "
            "with the giving of the Law on Sinai?"
        ),
        "answer": (
            "Watson teaches that Christ begins the Sermon on the Mount with promises "
            "and blessings rather than with commands and threatenings. Where the Law "
            "on the mount came with trumpet, flame, quaking earth, and fear, the "
            "Saviour whose lips dropped as the honeycomb opens with sweet, ravishing "
            "doctrine that draws even hard hearts."
        ),
    },
    "eval-puritan-004": {
        "passage": (
            "Our Father which art in heaven.\n\n"
            "   I HAVE insisted upon the foregoing verses, which do concern the duty of\n"
            "   prayer; let me now come to the Lord's Prayer itself. This prayer was\n"
            "   formed and indited by Christ, and therefore to be highly esteemed by\n"
            "   Christians: Jesus Christ, who was the wisdom of God, he knew both our\n"
            "   necessities and the Father's good-will towards us; and therefore surely\n"
            "   he would give us a perfect form and directory. We are not absolutely\n"
            "   tied to this form. We do not read that it was ever used by the\n"
            "   apostles, though we have many of their prayers upon record"
        ),
        "question": (
            "Why does Manton say Christians should highly esteem the Lord's Prayer, "
            "and are they absolutely tied to its exact form?"
        ),
        "answer": (
            "Manton teaches that the Lord's Prayer was formed and indited by Christ, "
            "who as the wisdom of God knew both our necessities and the Father's "
            "good-will, and so gave a perfect form and directory. He adds that "
            "believers are not absolutely tied to that form; the apostles' recorded "
            "prayers do not show them using it as a fixed liturgy."
        ),
    },
    "eval-puritan-008": {
        "passage": (
            "AFFLICTION.\n"
            "The  greatnesse  shewM  the  owner.    So  I  went\n"
            "To  fetch  a  sacrifice  out  of  my  fold.\n"
            "Thinking  with  that,  which  I  did  thus  present.\n"
            "To  warm  his  love,  which  I  did  fear  grew  cold.\n"
            "But  as  my  heart  did  tender  it,  the  man\n"
            "Who  was  to  take  it  from  me,  slipt  his  hand.\n\n"
            "THE  CHURCH  163\n\n"
            "And  threw  my  heart  into  the  scalding  pan  ;"
        ),
        "question": (
            "In Herbert's Affliction poem, what does the speaker try to offer to warm "
            "God's love, and what happens to that offering?"
        ),
        "answer": (
            "Herbert's speaker goes to fetch a sacrifice from his fold, thinking that "
            "presenting it would warm love he feared had grown cold. As he tenders "
            "his heart, the man who should receive it slips his hand and throws the "
            "heart into the scalding pan—so the intended offering becomes the "
            "speaker's own suffering."
        ),
    },
    "eval-confession-002": {
        "passage": (
            "Of the Being of God\n\n"
            "   Having undertaken to write a System of Theology, or a Body of Doctrinal\n"
            "   Divinity; and Theology being nothing else than a speaking of God, or a\n"
            "   discoursing concerning him; his nature, names, perfections, and\n"
            "   persons; his purposes, providences, ways, works, and word: I shall\n"
            "   begin with the Being of God, and the proof and evidence of it; which is\n"
            "   the foundation of all religion; for if there is no God, religion is a\n"
            "   vain thing; and it matters not neither what we believe, nor what we do;\n"
            "   since there is no superior Being to whom we are accountable for either\n"
            "   faith or practice. Some, because the being of God is a first principle,\n"
            "   which is not to be disputed; and because that there is one is a\n"
            "   self-evident proposition, not to be disproved; have thought it s"
        ),
        "question": (
            "Why does Gill begin his Body of Doctrinal Divinity with the Being of God "
            "and the proof of it?"
        ),
        "answer": (
            "Gill teaches that theology is a discoursing concerning God—his nature, "
            "names, perfections, persons, purposes, providences, ways, works, and "
            "word—so he begins with God's being and its evidence as the foundation of "
            "all religion. If there were no God, religion would be vain, and neither "
            "belief nor practice would matter, for there would be no superior Being "
            "to whom we are accountable."
        ),
    },
}


def _verify_passage_in_source(source_path: str, passage: str) -> bool:
    path = _REPO / source_path.replace("\\", "/")
    if not path.exists():
        return False
    raw = path.read_text(encoding="utf-8", errors="replace")
    # Compare with whitespace collapsed.
    def norm(t: str) -> str:
        return re.sub(r"\s+", " ", t).strip()

    return norm(passage)[:80] in norm(raw)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def apply_redraw(rec: dict, spec: dict[str, str]) -> dict:
    passage = spec["passage"]
    question = spec["question"]
    answer, _ = soft_strip_assistant(spec["answer"], passage)
    out = dict(rec)
    meta = dict(rec.get("meta") or {})
    meta["passage"] = passage
    meta["redraw"] = "trivia_to_doctrine_v1"
    out["meta"] = meta
    new_msgs = []
    for m in rec.get("messages") or []:
        role_name = m.get("role")
        if role_name == "system":
            new_msgs.append({"role": "system", "content": THEOLOGY_CHAT_SYSTEM_PROMPT})
        elif role_name == "user":
            new_msgs.append({"role": "user", "content": question})
        elif role_name == "assistant":
            new_msgs.append({"role": "assistant", "content": answer})
        else:
            new_msgs.append(dict(m))
    out["messages"] = new_msgs
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    path = OUT_DIR / "eval_accepted.jsonl"
    rows = read_jsonl(path)
    changed = 0
    errors: list[str] = []
    out_rows: list[dict] = []
    for rec in rows:
        jid = rec.get("job_id") or ""
        if jid not in REDRAWS:
            out_rows.append(rec)
            continue
        spec = REDRAWS[jid]
        src = str((rec.get("meta") or {}).get("source_path") or "")
        if not _verify_passage_in_source(src, spec["passage"]):
            errors.append(f"{jid}: passage not found in {src}")
            out_rows.append(rec)
            continue
        new_rec = apply_redraw(rec, spec)
        errs = check_open_theology_record(new_rec)
        if errs:
            errors.append(f"{jid}: check failed {errs}")
            out_rows.append(rec)
            continue
        out_rows.append(new_rec)
        changed += 1
        print(f"REDRAW {jid}: {role(new_rec['messages'], 'user')[:90]}")

    print(f"redraw_candidates={len(REDRAWS)} changed={changed} errors={len(errors)}")
    for e in errors:
        print(f"  ERR {e}")

    if errors:
        return 1
    if not args.apply:
        print("DRY — pass --apply to write eval_accepted.jsonl")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = path.with_suffix(path.suffix + f".bak-eval-redraw-{stamp}")
    shutil.copy2(path, bak)
    write_jsonl(path, out_rows)
    print(f"wrote {path} backup={bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
