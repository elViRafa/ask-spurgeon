#!/usr/bin/env python3
"""Local checks for the S8 sweep plan. No GPU, no vastai."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import vast_cpt_s8_sweep_plan as plan  # noqa: E402


def test_three_arms_and_scale() -> None:
    assert [arm["id"] for arm in plan.ARMS] == ["m_lo", "m_hi", "f_hi"]
    for arm in plan.ARMS:
        env = plan.arm_env(arm)
        assert env["LORA_RANK"] == "128"
        assert env["LORA_ALPHA"] == "64"
        assert env["MAX_STEPS"] == "400"
        assert env["ABORT_SPURGEON_STEP"] == "0"
        assert env["EARLY_STOP_MIN_STEPS"] == "400"
        assert env["CPT_RUN_MODE"] == "fresh"
        assert env["PREV_RUN_CHECKPOINT"] == ""
    assert plan.arm_env(plan.ARMS[0])["LEARNING_RATE"] == "2e-5"
    assert plan.arm_env(plan.ARMS[0])["CPT_BASE_MODEL"] == plan.MERGED_DIR
    assert plan.arm_env(plan.ARMS[1])["LEARNING_RATE"] == "5e-5"
    assert plan.arm_env(plan.ARMS[2])["CPT_BASE_MODEL"] == plan.STOCK_BASE
    oom = plan.arm_env(plan.ARMS[1], oom_fallback=True)
    assert oom["LORA_RANK"] == "64"
    assert oom["LORA_ALPHA"] == "45"
    assert abs((64 / (128 ** 0.5)) - (45 / (64 ** 0.5))) < 0.05


def test_emit_arm_from_workspace_layout(tmp_path: Path) -> None:
    shallow = tmp_path / "vast_cpt_s8_sweep_plan.py"
    shallow.write_bytes((SCRIPTS / "vast_cpt_s8_sweep_plan.py").read_bytes())
    proc = subprocess.run(
        [sys.executable, str(shallow), "--emit-arm", "m_hi"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, combined
    assert "export LEARNING_RATE=5e-5\n" in proc.stdout
    assert "IndexError" not in combined


def test_sweep_remote_fails_closed_on_emit() -> None:
    remote = (SCRIPTS / "vast_cpt_s8_sweep_remote.sh").read_text(encoding="utf-8")
    assert 'test -s "$emit_file"' in remote
    assert 'eval "$(' not in remote


def test_emit_arm_is_sourceable() -> None:
    text = plan.emit_arm("m_lo")
    assert "export LEARNING_RATE=2e-5\n" in text
    assert "export EMBEDDING_LEARNING_RATE=2e-6\n" in text
    assert f"export CPT_BASE_MODEL={plan.MERGED_DIR}\n" in text
    assert "export PREV_RUN_CHECKPOINT=\n" in text
    fallback = plan.emit_arm("f_hi", oom_fallback=True)
    assert "export LORA_RANK=64\n" in fallback
    assert f"export CPT_BASE_MODEL={plan.STOCK_BASE}\n" in fallback


def test_readiness_ready() -> None:
    assert plan.readiness() == []


def test_orchestrator_dry_prints_ready() -> None:
    script = SCRIPTS / "vast_cpt_s8_sweep_orchestrate.ps1"
    text = script.read_text(encoding="utf-8")
    dry_head, _, go_tail = text.partition("if (-not $Go)")
    assert "vastai" not in dry_head.lower()
    assert "scp" not in dry_head.lower()
    assert "ssh" not in dry_head.lower()
    assert "exit 0" in text[text.find("if (-not $Go)"): text.find("# Go path")]
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(script)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, combined
    assert "READY" in combined
    assert "DRY COMPLETE" in combined
