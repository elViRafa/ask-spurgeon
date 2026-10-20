#!/usr/bin/env python3
"""Tests for export_open_theology_sft.py (synthetic data, no corpus needed)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_REPO = _SCRIPTS.parent.parent
for p in (_REPO, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from config import THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from export_open_theology_sft import DEFAULT_EXCLUDED, export  # noqa: E402

H = "[Boston \u2014 Fourfold State]"


def _row(jid: str, i: int, *, q: str | None = None, ans: str | None = None, work: str | None = None) -> dict:
    passage = f"Grace number {i} is free and sovereign in the covenant of God, said the divine plainly."
    return {
        "job_id": jid, "slice": "open_theology", "teacher": "groq", "model": "m", "created_at": "t",
        "messages": [
            {"role": "system", "content": THEOLOGY_CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": q or f"What does Boston teach about grace {i}?"},
            {"role": "assistant", "content": ans or f'Boston teaches that "grace number {i} is free and sovereign." {H}'},
        ],
        "meta": {"slice": "open_theology", "bucket": "puritan", "work_id": work or f"w-{jid}",
                 "source_path": "x.txt", "heading": H, "passage": passage, "job_id": jid},
    }


def _write(d: Path, train: list[dict], ev: list[dict], n_eval_jobs: int = 4) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / "accepted.jsonl").write_text("".join(json.dumps(r) + "\n" for r in train), encoding="utf-8")
    (d / "eval_accepted.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ev), encoding="utf-8")
    (d / "eval_jobs.jsonl").write_text("".join(json.dumps({"job_id": f"e{i}"}) + "\n" for i in range(n_eval_jobs)),
                                       encoding="utf-8")
    (d / "status.json").write_text(json.dumps({"version": "qa_open_theology_v1"}), encoding="utf-8")
    return d


def _base(tmp_path: Path) -> Path:
    train = [_row(f"train-puritan-{i:03d}", i) for i in range(5)]
    train.append(_row("train-confession-003", 50))  # default-excluded
    train.append(_row("train-puritan-005", 0, q="What does Boston teach about grace 0?"))  # dup question
    # Fabricated quote fails the relaxed corpus-chat contract (heading at end is optional).
    train.append(
        _row(
            "train-puritan-006",
            6,
            ans=f'Boston teaches "totally invented phrase about grace six." {H}',
        )
    )
    train.append(_row("train-puritan-007", 7, ans=f'The passage says "grace number 7 is free and sovereign." {H}'))
    train.append(_row("train-puritan-008", 8, work="w-shared"))  # overlaps eval work_id
    # Optional-cite row (no trailing heading) must still export.
    train.append(
        _row(
            "train-puritan-009",
            9,
            ans='Boston teaches that "grace number 9 is free and sovereign" in the covenant.',
        )
    )
    ev = [_row("eval-puritan-000", 100), _row("eval-puritan-001", 101, work="w-shared")]
    return _write(tmp_path / "qa", train, ev)


def test_dry_run_writes_nothing_and_validates(tmp_path: Path):
    d = _base(tmp_path)
    before = sorted(p.name for p in d.rglob("*"))
    s = export(data_dir=d, holdout_dir=tmp_path / "noholdouts", apply=False)
    assert sorted(p.name for p in d.rglob("*")) == before
    assert s["excluded"] == ["train-confession-003"]
    assert s["duplicates"] == ["train-puritan-005"]
    assert list(s["invalid"]) == ["train-puritan-006"]
    assert any("fabricated quote" in e for e in s["invalid"]["train-puritan-006"])
    assert s["overlap_removed"] == ["train-puritan-008"]
    assert s["train_rows"] == 7 and s["eval_rows"] == 2
    assert s["meta_wording_counts"]["train"]["answer"] == 1


def test_apply_writes_format_manifest_and_is_rerunnable(tmp_path: Path):
    d = _base(tmp_path)
    export(data_dir=d, holdout_dir=tmp_path / "noholdouts", apply=True)
    sft = d / "sft"
    rows = [json.loads(l) for l in (sft / "open_theology_train.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 7
    assert "train-puritan-009" in {r["id"] for r in rows}
    for r in rows:
        assert set(r) == {"id", "slice", "messages"} and r["slice"] == "open_theology"
        assert [m["role"] for m in r["messages"]] == ["system", "user", "assistant"]
        assert set(r["messages"][0]) == {"role", "content"}
        assert r["messages"][0]["content"] == THEOLOGY_CHAT_SYSTEM_PROMPT
    ev_ids = {json.loads(l)["id"] for l in (sft / "open_theology_eval.jsonl").read_text().splitlines()}
    assert ev_ids == {"eval-puritan-000", "eval-puritan-001"} and not ev_ids & {r["id"] for r in rows}
    m = json.loads((sft / "manifest.json").read_text(encoding="utf-8"))
    assert m["files"]["train"]["rows"] == 7 and len(m["files"]["train"]["sha256"]) == 64
    assert m["eval_partial"] is True and "2/4" in m["eval_note"]
    assert m["generator_version"] == "qa_open_theology_v1"
    excl = json.loads((sft / "excluded_ids.json").read_text(encoding="utf-8"))
    assert excl == DEFAULT_EXCLUDED
    mw = json.loads((sft / "meta_wording_ids.json").read_text(encoding="utf-8"))
    assert mw["train"]["answer"] == ["train-puritan-007"]

    # Reinstate one id and add eval rows: rerun rebuilds from sources.
    excl.pop("train-confession-003")
    (sft / "excluded_ids.json").write_text(json.dumps(excl), encoding="utf-8")
    ev = [json.loads(l) for l in (d / "eval_accepted.jsonl").read_text().splitlines()]
    ev += [_row("eval-puritan-002", 102), _row("eval-puritan-003", 103)]
    (d / "eval_accepted.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ev), encoding="utf-8")
    s2 = export(data_dir=d, holdout_dir=tmp_path / "noholdouts", apply=True)
    assert s2["train_rows"] == 8 and s2["eval_rows"] == 4
    m2 = json.loads((sft / "manifest.json").read_text(encoding="utf-8"))
    assert m2["eval_partial"] is False


def test_holdout_hit_is_dropped(tmp_path: Path):
    d = _write(tmp_path / "qa", [_row("train-spurgeon-001", 1, work="spurgeon-2806")], [])
    hd = tmp_path / "holdouts"
    hd.mkdir()
    (hd / "spurgeon_holdout.txt").write_text("Sermon 2806 | Jesus Our Lord\nbody\n", encoding="utf-8")
    s = export(data_dir=d, holdout_dir=hd, apply=False)
    assert s["holdout_hits"] == ["train-spurgeon-001"] and s["train_rows"] == 0
