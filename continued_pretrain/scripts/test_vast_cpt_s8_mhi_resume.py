#!/usr/bin/env python3
"""Local checks for the S8 m_hi resume plan. No GPU, no vastai."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cpt_runtime as cr  # noqa: E402
import vast_cpt_s8_mhi_resume_plan as plan  # noqa: E402


def test_emit_resume_and_sha_split() -> None:
    text = plan.emit()
    assert "export CPT_RUN_MODE=continue\n" in text
    assert "export CPT_CONTINUE_PROFILE=s8\n" in text
    assert "export CPT_INIT_ADAPTER=/workspace/mhi_lora\n" in text
    assert "export CPT_BASE_MODEL=/workspace/theology_cpt_merged_a70\n" in text
    assert "export PREV_RUN_CHECKPOINT=/workspace/ckpt800\n" in text
    assert "export PREV_RUN_CHECKPOINT=\n" not in text
    assert "export LEARNING_RATE=5e-6\n" in text
    assert "export EMBEDDING_LEARNING_RATE=5e-7\n" in text
    assert "export WARMUP_RATIO=0\n" in text
    assert "export LR_SCHEDULER=constant\n" in text
    assert "export MAX_STEPS=2400\n" in text
    assert "export EARLY_STOP_MIN_STEPS=2400\n" in text
    assert "export ABORT_SPURGEON_STEP=0\n" in text
    assert f"export EXPECTED_ADAPTER_SHA256={plan.INIT_SHA}\n" in text
    assert plan.MERGE_SHA not in text.split("export EXPECTED_ADAPTER_SHA256=", 1)[1].split("\n", 1)[0]
    assert "5e-5" not in text
    assert "15781d96" not in text


def test_continue_profile_keeps_the_floor(tmp_path: Path) -> None:
    env = dict(plan.ENV)
    env["CPT_WORK_ROOT"] = str(tmp_path)
    cfg = cr.resolve_continue_training_config(env=env, packed_epoch_steps=100)
    assert cfg["continue_profile"] == "s8"
    assert cfg["learning_rate"] == 5e-6
    assert cfg["embedding_learning_rate"] == 5e-7
    assert cfg["warmup_ratio"] == 0.0
    assert cfg["lr_scheduler_type"] == "constant"
    assert cfg["lr_scheduler_kwargs"] is None
    assert cfg["continue_max_steps"] == 2400
    assert cfg["early_stop_min_steps"] == 2400
    assert cfg["metric_for_best"] == "eval_puritan_loss"
    ckpt = tmp_path / "ckpt800"
    ckpt.mkdir()
    (ckpt / "adapter_model.safetensors").write_bytes(b"x")
    env["PREV_RUN_CHECKPOINT"] = str(ckpt)
    assert cr.resolve_prev_checkpoint(str(tmp_path), env=env, kaggle_input=str(tmp_path / "none")) == str(ckpt)


def test_readiness_ready() -> None:
    assert plan.readiness() == []


def test_emit_from_workspace_layout(tmp_path: Path) -> None:
    """Pod copies the plan to /workspace, which has no parents[2]."""
    shallow = tmp_path / "vast_cpt_s8_mhi_resume_plan.py"
    shallow.write_bytes((SCRIPTS / "vast_cpt_s8_mhi_resume_plan.py").read_bytes())
    proc = subprocess.run(
        [sys.executable, str(shallow), "--emit"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, combined
    assert "export CPT_RUN_MODE=continue\n" in proc.stdout
    assert "export PREV_RUN_CHECKPOINT=/workspace/ckpt800\n" in proc.stdout
    assert "export MAX_STEPS=2400\n" in proc.stdout
    assert "IndexError" not in combined


def test_remote_requires_optimizer_resume() -> None:
    remote = (SCRIPTS / "vast_cpt_s8_mhi_resume_remote.sh").read_text(encoding="utf-8")
    assert "unset EXPECTED_ADAPTER_SHA256" in remote
    assert 'test -s "$emit_file"' in remote
    assert 'test "$CPT_RUN_MODE" = continue' in remote
    assert 'test "$LEARNING_RATE" = 5e-6' in remote
    assert 'test "$EMBEDDING_LEARNING_RATE" = 5e-7' in remote
    assert 'test "$MAX_STEPS" = 2400' in remote
    assert 'test "$EARLY_STOP_MIN_STEPS" = 2400' in remote
    assert 'test "$LR_SCHEDULER" = constant' in remote
    assert 'test "$CPT_INIT_ADAPTER" = /workspace/mhi_lora' in remote
    assert 'test "$PREV_RUN_CHECKPOINT" = /workspace/ckpt800' in remote
    assert "optimizer.pt" in remote
    assert "RECIPE_OK" in remote
    assert 'eval "$(' not in remote
    assert f'EXPECTED_ADAPTER_SHA256="$MERGE_SHA"' in remote
    assert plan.MERGE_SHA in remote
    assert plan.INIT_SHA in remote
    assert "run_arm m_lo" not in remote
    assert "vast_cpt_s8_sweep_remote.sh" not in remote
    assert "vast_cpt_s8_mhi_continue_remote.sh" not in remote
    assert "\r" not in remote


def test_orchestrator_dry_prints_ready() -> None:
    script = SCRIPTS / "vast_cpt_s8_mhi_resume_orchestrate.ps1"
    text = script.read_text(encoding="utf-8")
    dry_head, _, _go_tail = text.partition("if (-not $Go)")
    assert "vastai" not in dry_head.lower()
    assert "scp" not in dry_head.lower()
    assert "ssh" not in dry_head.lower()
    assert "vast_cpt_s8_sweep_orchestrate.ps1" not in text
    assert "vast_cpt_s8_mhi_continue_orchestrate.ps1" not in text
    go_at = text.find("if (-not $Go)")
    path_at = text.find("# Go path")
    assert "exit 0" in text[go_at:path_at]
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(script)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, combined
    assert "READY" in combined
    assert "DRY COMPLETE" in combined
    assert "5e-6" in combined
    assert "early_stop_min=2400" in combined
    assert "/workspace/ckpt800" in combined
