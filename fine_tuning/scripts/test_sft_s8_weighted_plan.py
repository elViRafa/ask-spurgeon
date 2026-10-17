#!/usr/bin/env python3
"""Weighted SFT-on-S8 is wired and dry. No GPU."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

import sft_s8_weighted_plan as plan

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "fine_tuning" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from config import SPURGEON_SFT_SYSTEM_PROMPT, THEOLOGY_CHAT_SYSTEM_PROMPT  # noqa: E402
from train_sft_sota import (  # noqa: E402
    build_weighted_message_rows,
    normalize_rag_messages,
    validate_theology_row,
)

REMOTE = SCRIPTS / "sft_remote_train_s8_weighted.sh"
ORCH = SCRIPTS / "vast_sft_s8_weighted_orchestrate.ps1"
RUNBOOK = REPO / "fine_tuning" / "NEXT_SFT_S8_WEIGHTED.md"


def test_decision_is_weighted_sft_on_s8_merge() -> None:
    assert plan.next_stage() == "sft_weighted"
    assert plan.contract_errors() == []
    assert plan.ENV["SFT_GATE0_MERGED"] == plan.S8_MERGED_REMOTE
    assert plan.ENV["SFT_BASE_REPO"] == plan.S8_MERGED_REPO
    assert plan.ENV["SFT_EXPORT"] == "0"
    assert plan.ENV["SFT_BACKEND"] == "peft"
    assert plan.ENV["SFT_MAX_SEQ_LENGTH"] == "4608"
    assert plan.ENV["SFT_OPEN_THEOLOGY"] == "1"
    assert plan.ENV["SFT_OPEN_THEOLOGY_REPEAT"] == "1"
    assert plan.ENV["SFT_OUTPUT_DIR"] == plan.WEIGHTED_OUTPUT
    assert plan.GATE0_MERGED_REMOTE not in plan.ENV.values()
    assert plan.HUB_LORA_REPO not in plan.ENV.values()
    text = plan.emit()
    assert "SFT_OPEN_THEOLOGY=1" in text
    assert "SFT_OUTPUT_DIR=/workspace/sft_s8_weighted/adapter" in text
    assert "theology_cpt_v2_merged_hf" not in text
    assert "spurgeon_qa_lora_v2" not in text


def test_remote_launcher_forces_weighted_s8() -> None:
    text = REMOTE.read_text(encoding="utf-8")
    assert "source /workspace/.sft_env" in text
    source_at = text.index("source /workspace/.sft_env")
    force_at = text.index(
        "export SFT_GATE0_MERGED=/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit"
    )
    assert force_at > source_at
    assert "SFT_OPEN_THEOLOGY=1" in text
    assert "SFT_OPEN_THEOLOGY_REPEAT=1" in text
    assert "SFT_FORCE_DATAPREP=1" in text
    assert "SFT_OUTPUT_DIR=/workspace/sft_s8_weighted/adapter" in text
    # Default peft; RunPod may override to unsloth via env / .sft_env.
    assert 'SFT_BACKEND:-peft' in text or '_backend_in="${SFT_BACKEND:-peft}"' in text
    assert "unsloth|peft" in text
    assert "SFT_SMOKE_ONLY" in text
    assert "SMOKE_ONLY_DONE" in text
    assert "SFT_MAX_SEQ_LENGTH=4608" in text
    assert "SFT_EXPORT=0" in text
    assert "sft_remote_merge.sh" not in text
    assert "upload_" not in text
    assert "theology_cpt_v2_merged_hf" in text  # refuse guard
    assert "REFUSING Hub v2 merge path" in text
    assert "train_sft_sota.py --preflight" in text


def test_orchestrator_dry_path_does_not_rent() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "sft_s8_weighted_plan.py" in text
    assert "DRY COMPLETE" in text
    assert "vast_sft_s8_weighted_session.json" in text
    assert "vast_sft_s8_weighted" in text
    assert "sft-s8-weighted" in text
    assert "AllowLowCredit" in text
    assert "vast_orchestrate.ps1" in text  # named only as do-not
    assert "Do NOT call vast_orchestrate.ps1" in text
    assert "sft_remote_train_s8_weighted.sh" in text
    assert "LogLevel=ERROR" in text
    assert "gunzip" in text
    assert "No vastai, scp, or ssh calls were made." in text
    # Dry exit before vast_common / show user
    dry_end = text.index("DRY COMPLETE")
    go_marker = text.index("-Go only")
    assert dry_end < go_marker
    assert "Invoke-VastaiJson" in text[go_marker:]
    assert "Invoke-VastaiJson" not in text[:dry_end]


def _orchestrator_invoke_weighted_ssh_body(text: str) -> str:
    start = text.index("function Invoke-WeightedSsh")
    nxt = text.find("\nfunction ", start + 1)
    assert nxt > start
    return text[start:nxt]


def test_orchestrator_strips_cr_from_remote_ssh_scripts() -> None:
    """Windows CRLF here-strings must not reach bash; Invoke-WeightedSsh strips \\r."""
    text = ORCH.read_text(encoding="utf-8")
    body = _orchestrator_invoke_weighted_ssh_body(text)
    assert '-replace "`r"' in body
    # Contract: every remote payload is sanitized the same way PowerShell does.
    dirty = "set -euo pipefail\r\necho ok\r"
    clean = dirty.replace("\r", "")
    assert "\r" not in clean
    assert clean == "set -euo pipefail\necho ok"
    # Embedded remote scripts in the orchestrator must themselves be LF-only in git.
    raw = ORCH.read_bytes()
    assert b"\r" not in raw, "orchestrator .ps1 must be LF-only so remote here-strings stay clean"
    for name in (
        "sft_remote_setup.sh",
        "sft_remote_train_s8_weighted.sh",
    ):
        sh = (SCRIPTS / name).read_bytes()
        assert b"\r" not in sh, f"{name} must not contain CR (bash over SSH)"


def test_orchestrator_loading_timeout_about_twenty_minutes() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "LoadingTimeoutMinutes = 20" in text
    assert "loading_timeout_min=" in text
    assert "loading timeout" in text.lower()
    # Old ~40m idle-poll gate and the too-short 10m default must not remain.
    assert "idlePolls -ge 8" not in text
    assert "~40m" not in text
    assert "LoadingTimeoutMinutes = 10" not in text


def test_runbook_walk_away_gates() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "SFT_OPEN_THEOLOGY=1" in text
    assert "RAG_PROMPT_OK" in text
    assert "THEOLOGY_PROMPT_OK" in text
    assert "SFT_BACKEND=peft" in text
    assert "SFT_EXPORT=0" in text
    assert "sft_s8_weighted" in text
    assert "spurgeon_qa_lora_v2" in text
    assert "vast_sft_s8_weighted_orchestrate.ps1" in text


def test_readiness_passes_when_artifacts_present() -> None:
    paths = plan.local_paths()
    required = [
        "train_jsonl",
        "val_jsonl",
        "open_theology_train",
        "open_theology_eval",
        "open_theology_manifest",
        "train_py",
        "remote",
        "runbook",
        "orchestrator",
    ]
    if any(not paths[k].is_file() for k in required):
        pytest.skip("weighted SFT artifacts not all present yet")
    assert plan.evaluate(paths) == []


def test_mix_builder_preserves_theology_prompt_and_rewrites_rag() -> None:
    rag_rows = [
        {
            "id": "rag-1",
            "slice": "answerable",
            "messages": [
                {"role": "system", "content": "wrong"},
                {"role": "user", "content": "Q?"},
                {"role": "assistant", "content": "A from CONTEXT."},
            ],
        }
    ]
    theo_rows = [
        {
            "id": "train-puritan-1",
            "slice": "open_theology",
            "messages": [
                {"role": "system", "content": THEOLOGY_CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": "What did Owen teach?"},
                {"role": "assistant", "content": 'Quote. [Owen — Works]'},
            ],
        }
    ]
    eval_ids = {"eval-puritan-1"}
    mixed = build_weighted_message_rows(
        rag_rows=rag_rows,
        theology_rows=theo_rows,
        rag_system=SPURGEON_SFT_SYSTEM_PROMPT,
        theology_system=THEOLOGY_CHAT_SYSTEM_PROMPT,
        theology_repeat=1,
        seed=1,
    )
    assert len(mixed) == 2
    by_id = {r["id"]: r for r in mixed}
    assert by_id["rag-1"]["messages"][0]["content"] == SPURGEON_SFT_SYSTEM_PROMPT
    assert by_id["train-puritan-1"]["messages"][0]["content"] == THEOLOGY_CHAT_SYSTEM_PROMPT
    assert by_id["train-puritan-1"]["slice"] == "open_theology"
    assert not (set(by_id) & eval_ids)


def test_validate_theology_rejects_wrong_prompt_or_slice() -> None:
    good = {
        "slice": "open_theology",
        "messages": [
            {"role": "system", "content": THEOLOGY_CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": "Q"},
            {"role": "assistant", "content": "A"},
        ],
    }
    assert validate_theology_row(good, THEOLOGY_CHAT_SYSTEM_PROMPT)[0]["content"] == (
        THEOLOGY_CHAT_SYSTEM_PROMPT
    )
    bad_slice = dict(good, slice="rag")
    with pytest.raises(ValueError, match="open_theology"):
        validate_theology_row(bad_slice, THEOLOGY_CHAT_SYSTEM_PROMPT)
    bad_prompt = {
        "slice": "open_theology",
        "messages": [
            {"role": "system", "content": SPURGEON_SFT_SYSTEM_PROMPT},
            {"role": "user", "content": "Q"},
            {"role": "assistant", "content": "A"},
        ],
    }
    with pytest.raises(ValueError, match="system prompt"):
        validate_theology_row(bad_prompt, THEOLOGY_CHAT_SYSTEM_PROMPT)


def test_normalize_rag_messages_rewrites_system() -> None:
    msgs = normalize_rag_messages(
        [
            {"role": "system", "content": "other"},
            {"role": "user", "content": "Q"},
            {"role": "assistant", "content": "A"},
        ],
        SPURGEON_SFT_SYSTEM_PROMPT,
    )
    assert msgs[0]["content"] == SPURGEON_SFT_SYSTEM_PROMPT
    assert msgs[1]["content"] == "Q"
