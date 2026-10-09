#!/usr/bin/env python3
"""SFT-on-S8 decision is wired and dry. No GPU."""
from __future__ import annotations

from pathlib import Path

import sft_s8_plan as plan

REPO = Path(__file__).resolve().parents[2]
REMOTE = REPO / "fine_tuning/scripts/sft_remote_train_s8.sh"
ORCH = REPO / "fine_tuning/scripts/vast_sft_s8_orchestrate.ps1"
RUNBOOK = REPO / "fine_tuning/NEXT_SFT_S8.md"


def test_decision_is_sft_on_s8_merge() -> None:
    assert plan.next_stage() == "sft"
    assert plan.contract_errors() == []
    assert plan.ENV["SFT_GATE0_MERGED"] == plan.S8_MERGED_REMOTE
    assert plan.ENV["SFT_BASE_REPO"] == plan.S8_MERGED_REPO
    assert plan.ENV["SFT_EXPORT"] == "0"
    assert plan.ENV["SFT_BACKEND"] == "peft"
    assert plan.GATE0_MERGED_REMOTE not in plan.ENV.values()
    assert plan.HUB_LORA_REPO not in plan.ENV.values()
    text = plan.emit()
    assert "SFT_GATE0_MERGED=/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit" in text
    assert "theology_cpt_v2_merged_hf" not in text
    assert "SFT_EXPORT=0" in text


def test_runbook_records_the_gap_and_the_refusal_watch() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "1.6605" in text
    assert "1.6349" in text
    assert "2269803948b2accbb132ad7d8386b542aa8c0a10c86cd7b7098b8857fcd2c207" in text
    assert "06354dfc" in text
    assert "0.54" in text
    assert "vast_sft_s8_orchestrate.ps1" in text
    assert "sft_remote_train_s8.sh" in text
    assert "SFT_EXPORT=0" in text


def test_remote_launcher_forces_s8_and_skips_hub_v2_merge() -> None:
    text = REMOTE.read_text(encoding="utf-8")
    assert "source /workspace/.sft_env" in text
    source_at = text.index("source /workspace/.sft_env")
    force_at = text.index("export SFT_GATE0_MERGED=/workspace/qwen35-4b-theology-cpt-s8-mhi-resume-merged-16bit")
    assert force_at > source_at
    assert "rafaelvieirar1r/qwen3.5-4b-theology-cpt-s8-mhi-resume-merged-16bit" in text
    assert "sft_remote_merge.sh" not in text
    assert "upload_" not in text
    assert "SFT_BACKEND=peft" in text
    assert "SFT_EXPORT=0" in text
    assert "snapshot_download" in text
    assert "train_sft_sota.py --preflight" in text


def test_orchestrator_dry_path_does_not_rent() -> None:
    text = ORCH.read_text(encoding="utf-8")
    assert "vast_provision" not in text
    assert "Invoke-Vastai" not in text
    assert "Refusing -Go" in text
    assert "sft_s8_plan.py" in text
    assert "DRY COMPLETE" in text


def test_readiness_passes_when_local_merge_is_present() -> None:
    paths = plan.local_paths()
    if not paths["merged_config"].is_file():
        return
    assert plan.evaluate(paths) == []
