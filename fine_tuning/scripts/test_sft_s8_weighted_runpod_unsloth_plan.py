#!/usr/bin/env python3
"""RunPod Unsloth weighted SFT plan is wired and dry. No GPU."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "fine_tuning" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import sft_s8_weighted_runpod_unsloth_plan as plan  # noqa: E402

REMOTE = SCRIPTS / "sft_remote_train_s8_weighted.sh"
ORCH = SCRIPTS / "runpod_sft_s8_weighted_orchestrate.ps1"
RUNBOOK = REPO / "fine_tuning" / "NEXT_SFT_S8_WEIGHTED_RUNPOD_UNSLOTH.md"
VAST_ORCH = SCRIPTS / "vast_sft_s8_weighted_orchestrate.ps1"


def test_decision_is_runpod_unsloth_weighted() -> None:
    assert plan.next_stage() == "sft_weighted_runpod_unsloth"
    assert plan.HOST == "runpod"
    assert plan.BACKEND == "unsloth"
    assert plan.contract_errors() == []
    assert plan.ENV["SFT_BACKEND"] == "unsloth"
    assert plan.ENV["SFT_MAX_SEQ_LENGTH"] == "4608"
    assert plan.ENV["SFT_EXPORT"] == "0"
    assert plan.ENV["SFT_OPEN_THEOLOGY"] == "1"
    assert plan.ENV["SFT_OUTPUT_DIR"] == plan.WEIGHTED_OUTPUT
    assert plan.GATE0_MERGED_REMOTE not in plan.ENV.values()
    text = plan.emit()
    assert "SFT_BACKEND=unsloth" in text
    assert "SFT_EXPORT=0" in text
    assert "theology_cpt_v2_merged_hf" not in text


def test_remote_allows_unsloth_and_smoke_only() -> None:
    text = REMOTE.read_text(encoding="utf-8")
    assert '_backend_in="${SFT_BACKEND:-peft}"' in text or "SFT_BACKEND:-peft" in text
    assert "unsloth|peft" in text
    assert "SFT_SMOKE_ONLY" in text
    assert "SMOKE_ONLY_DONE" in text
    assert "SFT_MAX_SEQ_LENGTH=4608" in text
    assert "REFUSING Hub v2 merge path" in text


def test_orchestrator_dry_path_does_not_rent() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "sft_s8_weighted_runpod_unsloth_plan.py" in text
    assert "DRY COMPLETE" in text
    assert "runpod_sft_s8_weighted_session.json" in text
    assert "runpod_sft_s8_weighted" in text
    assert "sft-s8-weighted-unsloth" in text
    assert "SmokeOnly" in text
    assert "SFT_BACKEND=unsloth" in text
    assert "Do NOT call vast_sft_s8_weighted_orchestrate.ps1" in text
    assert "sft_orchestrate.ps1" in text
    assert "No runpodctl, scp, or ssh calls were made." in text
    dry_end = text.index("DRY COMPLETE")
    go_marker = text.index("-Go only")
    assert dry_end < go_marker
    assert "sft_provision_pod.ps1" in text[go_marker:]
    assert "sft_provision_pod.ps1" not in text[:dry_end]
    assert "Invoke-RunpodRestV1" in text[go_marker:]
    assert "Invoke-RunpodRestV1" not in text[:dry_end]


def test_orchestrator_strips_cr_and_is_lf_only() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert '-replace "`r"' in text
    raw = ORCH.read_bytes()
    assert b"\r" not in raw, "orchestrator .ps1 must be LF-only so remote here-strings stay clean"
    sh = REMOTE.read_bytes()
    assert b"\r" not in sh, "sft_remote_train_s8_weighted.sh must not contain CR"


def test_runbook_walk_away_gates() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "SFT_BACKEND=unsloth" in text
    assert "SFT_EXPORT=0" in text
    assert "SMOKE_ONLY_DONE" in text
    assert "runpod_sft_s8_weighted_orchestrate.ps1" in text
    assert "vast_sft_s8_weighted_orchestrate.ps1" in text
    assert "4608" in text


def test_vast_fallback_orchestrator_still_present() -> None:
    assert VAST_ORCH.is_file()


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
        "vast_orchestrator",
        "vast_runbook",
    ]
    if any(not paths[k].is_file() for k in required):
        pytest.skip("weighted RunPod Unsloth artifacts not all present yet")
    assert plan.evaluate(paths) == []
